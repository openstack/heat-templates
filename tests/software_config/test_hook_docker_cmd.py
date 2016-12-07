#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import json
import os
import tempfile

import fixtures
from testtools import matchers

from tests.software_config import common


class HookDockerCmdTest(common.RunScriptTest):
    data = {
        "name": "abcdef001",
        "group": "docker-cmd",
        "config": {
            "web": {
                "name": "x",
                "image": "xxx"
            },
            "db": {
                "name": "y",
                "image": "xxx",
                "net": "host",
                "restart": "always",
                "privileged": True,
                "user": "root",
                "volumes": [
                    "/run:/run",
                    "db:/var/lib/db"
                ],
                "environment": [
                    "KOLLA_CONFIG_STRATEGY=COPY_ALWAYS",
                    "FOO=BAR"
                ]

            }
        }
    }

    def setUp(self):
        super(HookDockerCmdTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-docker-cmd/install.d/hook-docker-cmd.py')

        self.cleanup_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements/heat-config-docker-cmd/',
            'os-refresh-config/configure.d/50-heat-config-docker-cmd')

        self.fake_tool_path = self.relative_path(
            __file__,
            'config-tool-fake.py')

        self.working_dir = self.useFixture(fixtures.TempDir())
        self.outputs_dir = self.useFixture(fixtures.TempDir())
        self.test_state_path = self.outputs_dir.join('test_state.json')

        self.env = os.environ.copy()
        self.env.update({
            'HEAT_DOCKER_CMD_WORKING': self.working_dir.join(),
            'HEAT_DOCKER_CMD': self.fake_tool_path,
            'TEST_STATE_PATH': self.test_state_path,
        })

    def test_hook(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': '',
                'stderr': 'Creating abcdef001_db_1...'
            })
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)

        self.assertEqual({
            'deploy_stdout': '',
            'deploy_stderr': 'Creating abcdef001_db_1...\n'
                             'Creating abcdef001_db_1...',
            'deploy_status_code': 0
        }, json.loads(stdout))

        state_0 = self.json_from_file(self.test_state_path)
        state_1 = self.json_from_file('%s_1' % self.test_state_path)
        self.assertEqual([
            self.fake_tool_path,
            'run',
            '--detach=true',
            '--name',
            'abcdef001__db',
            '--env=KOLLA_CONFIG_STRATEGY=COPY_ALWAYS',
            '--env=FOO=BAR',
            '--net=host',
            '--privileged=true',
            '--restart=always',
            '--user=root',
            '--volume=/run:/run',
            '--volume=db:/var/lib/db',
            'xxx'
        ], state_0['args'])
        self.assertEqual([
            self.fake_tool_path,
            'run',
            '--detach=true',
            '--name',
            'abcdef001__web',
            'xxx'
        ], state_1['args'])

    def test_hook_failed(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': '',
                'stderr': 'Error: image library/xxx:latest not found',
                'returncode': 1
            })
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual({
            'deploy_stdout': '',
            'deploy_stderr': 'Error: image library/xxx:latest not found\n'
                             'Error: image library/xxx:latest not found',
            'deploy_status_code': 1
        }, json.loads(stdout))

        state_0 = self.json_from_file(self.test_state_path)
        state_1 = self.json_from_file('%s_1' % self.test_state_path)
        self.assertEqual([
            self.fake_tool_path,
            'run',
            '--detach=true',
            '--name',
            'abcdef001__db',
            '--env=KOLLA_CONFIG_STRATEGY=COPY_ALWAYS',
            '--env=FOO=BAR',
            '--net=host',
            '--privileged=true',
            '--restart=always',
            '--user=root',
            '--volume=/run:/run',
            '--volume=db:/var/lib/db',
            'xxx'
        ], state_0['args'])
        self.assertEqual([
            self.fake_tool_path,
            'run',
            '--detach=true',
            '--name',
            'abcdef001__web',
            'xxx'
        ], state_1['args'])

    def test_cleanup_deleted(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(json.dumps([self.data]))
            f.flush()
            self.env['HEAT_SHELL_CONFIG'] = f.name

            returncode, stdout, stderr = self.run_cmd(
                [self.cleanup_path], self.env)

        # on the first run, abcdef001.json is written out, no docker calls made
        configs_path = os.path.join(self.env['HEAT_DOCKER_CMD_WORKING'],
                                    'abcdef001.json')
        self.assertThat(configs_path, matchers.FileExists())
        self.assertThat(self.test_state_path,
                        matchers.Not(matchers.FileExists()))

        # run again with empty config data
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(json.dumps([]))
            f.flush()
            self.env['HEAT_SHELL_CONFIG'] = f.name

            returncode, stdout, stderr = self.run_cmd(
                [self.cleanup_path], self.env)

        # on the second run, abcdef001.json is deleted, docker rm is run on
        # both containers
        configs_path = os.path.join(self.env['HEAT_DOCKER_CMD_WORKING'],
                                    'abcdef001.json')
        self.assertThat(configs_path,
                        matchers.Not(matchers.FileExists()))
        state_0 = self.json_from_file(self.test_state_path)
        state_1 = self.json_from_file('%s_1' % self.test_state_path)
        self.assertEqual([
            self.fake_tool_path,
            'rm',
            '-f',
            'abcdef001__db',
        ], state_0['args'])
        self.assertEqual([
            self.fake_tool_path,
            'rm',
            '-f',
            'abcdef001__web',
        ], state_1['args'])

    def test_cleanup_changed(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(json.dumps([self.data]))
            f.flush()
            self.env['HEAT_SHELL_CONFIG'] = f.name

            returncode, stdout, stderr = self.run_cmd(
                [self.cleanup_path], self.env)

        # on the first run, abcdef001.json is written out, no docker calls made
        configs_path = os.path.join(self.env['HEAT_DOCKER_CMD_WORKING'],
                                    'abcdef001.json')
        self.assertThat(configs_path, matchers.FileExists())
        self.assertThat(self.test_state_path,
                        matchers.Not(matchers.FileExists()))

        # run again with changed config data
        new_data = copy.deepcopy(self.data)
        new_data['config']['web']['image'] = 'yyy'
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(json.dumps([new_data]))
            f.flush()
            self.env['HEAT_SHELL_CONFIG'] = f.name

            returncode, stdout, stderr = self.run_cmd(
                [self.cleanup_path], self.env)

        # on the second run, abcdef001.json is written with the new data,
        # docker rm is run on both containers
        configs_path = os.path.join(self.env['HEAT_DOCKER_CMD_WORKING'],
                                    'abcdef001.json')
        self.assertThat(configs_path, matchers.FileExists())
        state_0 = self.json_from_file(self.test_state_path)
        state_1 = self.json_from_file('%s_1' % self.test_state_path)
        self.assertEqual([
            self.fake_tool_path,
            'rm',
            '-f',
            'abcdef001__db',
        ], state_0['args'])
        self.assertEqual([
            self.fake_tool_path,
            'rm',
            '-f',
            'abcdef001__web',
        ], state_1['args'])
