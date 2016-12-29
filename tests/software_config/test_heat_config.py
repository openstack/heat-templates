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
import shutil
import tempfile

import fixtures
from testtools import matchers

from tests.software_config import common


class HeatConfigTest(common.RunScriptTest):

    fake_hooks = ['cfn-init', 'chef', 'puppet', 'salt', 'script',
                  'apply-config', 'hiera', 'json-file']

    data = [
        {
            'id': '1111',
            'group': 'chef',
            'inputs': [{
                'name': 'deploy_signal_id',
                'value': 'mock://192.0.2.2/foo'
            }],
            'config': 'one'
        }, {
            'id': '2222',
            'group': 'cfn-init',
            'inputs': [],
            'config': 'two'
        }, {
            'id': '3333',
            'group': 'salt',
            'inputs': [{'name': 'foo', 'value': 'bar'}],
            'outputs': [{'name': 'foo'}],
            'config': 'three'
        }, {
            'id': '4444',
            'group': 'puppet',
            'inputs': [],
            'config': 'four'
        }, {
            'id': '5555',
            'group': 'script',
            'inputs': [{
                'name': 'deploy_status_code', 'value': '-1'
            }, {
                'name': 'deploy_stderr', 'value': 'A bad thing happened'
            }, {
                'name': 'deploy_signal_id',
                'value': 'mock://192.0.2.3/foo'
            }],
            'config': 'five'
        }, {
            'id': '6666',
            'group': 'apply-config',
            'inputs': [{'name': 'foo', 'value': 'bar'}],
            'config': 'six'
        }, {
            'id': '7777',
            'group': 'hiera',
            'inputs': [],
            'config': 'seven'
        }, {
            'id': '8888',
            'group': 'json-file',
            'inputs': [],
            'config': 'eight'
        }, {
            'id': '9999',
            'group': 'no-such-hook',
            'inputs': [],
            'config': 'nine'
        }]

    outputs = {
        'chef': {
            'deploy_status_code': '0',
            'deploy_stderr': 'stderr',
            'deploy_stdout': 'stdout'
        },
        'cfn-init': {
            'deploy_status_code': '0',
            'deploy_stderr': 'stderr',
            'deploy_stdout': 'stdout'
        },
        'salt': {
            'deploy_status_code': '0',
            'deploy_stderr': 'stderr',
            'deploy_stdout': 'stdout',
            'foo': 'bar'
        },
        'puppet': {
            'deploy_status_code': '0',
            'deploy_stderr': 'stderr',
            'deploy_stdout': 'stdout'
        },
        'script': {
            'deploy_status_code': '-1',
            'deploy_stderr': 'A bad thing happened',
            'deploy_stdout': 'stdout'
        },
        'hiera': {
            'deploy_status_code': '0',
            'deploy_stderr': 'stderr',
            'deploy_stdout': 'stdout'
        },
        'json-file': {
            'deploy_status_code': '0',
            'deploy_stderr': 'stderr',
            'deploy_stdout': 'stdout'
        },
        'apply-config': {
            'deploy_status_code': '0',
            'deploy_stderr': 'stderr',
            'deploy_stdout': 'stdout'
        }
    }

    def setUp(self):
        super(HeatConfigTest, self).setUp()

        self.fake_hook_path = self.relative_path(__file__, 'hook-fake.py')

        self.heat_config_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config/os-refresh-config/configure.d/55-heat-config')

        self.hooks_dir = self.useFixture(fixtures.TempDir())
        self.deployed_dir = self.useFixture(fixtures.TempDir())

        with open(self.fake_hook_path) as f:
            fake_hook = f.read()

        for hook in self.fake_hooks:
            hook_name = self.hooks_dir.join(hook)
            with open(hook_name, 'w') as f:
                os.utime(hook_name, None)
                f.write(fake_hook)
                f.flush()
            os.chmod(hook_name, 0o755)
        self.env = os.environ.copy()

    def write_config_file(self, data):
        config_file = tempfile.NamedTemporaryFile()
        config_file.write(json.dumps(data))
        config_file.flush()
        return config_file

    def run_heat_config(self, data):
        with self.write_config_file(data) as config_file:

            self.env.update({
                'HEAT_CONFIG_HOOKS': self.hooks_dir.join(),
                'HEAT_CONFIG_DEPLOYED': self.deployed_dir.join(),
                'HEAT_SHELL_CONFIG': config_file.name
            })
            returncode, stdout, stderr = self.run_cmd(
                [self.heat_config_path], self.env)

            self.assertEqual(0, returncode, stderr)

    def test_hooks_exist(self):
        self.assertThat(
            self.hooks_dir.join('no-such-hook'),
            matchers.Not(matchers.FileExists()))

        for hook in self.fake_hooks:
            hook_path = self.hooks_dir.join(hook)
            self.assertThat(hook_path, matchers.FileExists())

    def test_run_heat_config(self):

        self.run_heat_config(self.data)

        for config in self.data:
            hook = config['group']
            stdin_path = self.hooks_dir.join('%s.stdin' % hook)
            stdout_path = self.hooks_dir.join('%s.stdout' % hook)
            deployed_file = self.deployed_dir.join('%s.json' % config['id'])

            if hook == 'no-such-hook':
                self.assertThat(
                    stdin_path, matchers.Not(matchers.FileExists()))
                self.assertThat(
                    stdout_path, matchers.Not(matchers.FileExists()))
                continue

            self.assertThat(stdin_path, matchers.FileExists())
            self.assertThat(stdout_path, matchers.FileExists())

            # parsed stdin should match the config item
            self.assertEqual(config,
                             self.json_from_file(stdin_path))

            # parsed stdin should match the written deployed file
            self.assertEqual(config,
                             self.json_from_file(deployed_file))

            self.assertEqual(self.outputs[hook],
                             self.json_from_file(stdout_path))

            # clean up files in preparation for second run
            os.remove(stdin_path)
            os.remove(stdout_path)

        # run again with no changes, assert no new files
        self.run_heat_config(self.data)
        for config in self.data:
            hook = config['group']
            stdin_path = self.hooks_dir.join('%s.stdin' % hook)
            stdout_path = self.hooks_dir.join('%s.stdout' % hook)

            self.assertThat(
                stdin_path, matchers.Not(matchers.FileExists()))
            self.assertThat(
                stdout_path, matchers.Not(matchers.FileExists()))

        # run again changing the puppet config
        data = copy.deepcopy(self.data)
        for config in data:
            if config['id'] == '4444':
                config['id'] = '44444444'
        self.run_heat_config(data)
        for config in self.data:
            hook = config['group']
            stdin_path = self.hooks_dir.join('%s.stdin' % hook)
            stdout_path = self.hooks_dir.join('%s.stdout' % hook)

            if hook == 'puppet':
                self.assertThat(stdin_path, matchers.FileExists())
                self.assertThat(stdout_path, matchers.FileExists())
            else:
                self.assertThat(
                    stdin_path, matchers.Not(matchers.FileExists()))
                self.assertThat(
                    stdout_path, matchers.Not(matchers.FileExists()))

        # run again with a different deployed_dir
        old_deployed_dir = self.deployed_dir
        self.env['HEAT_CONFIG_DEPLOYED_OLD'] = old_deployed_dir.join()
        self.deployed_dir = self.useFixture(fixtures.TempDir())
        # make sure the new deployed_dir doesn't exist to trigger the migration
        shutil.rmtree(self.deployed_dir.join())

        self.run_heat_config(data)
        for config in self.data:
            hook = config['group']
            if hook == 'no-such-hook':
                continue
            deployed_file = self.deployed_dir.join('%s.json' % config['id'])
            old_deployed_file = old_deployed_dir.join('%s.json' % config['id'])
            self.assertEqual(config,
                             self.json_from_file(deployed_file))
            self.assertThat(
                old_deployed_file, matchers.Not(matchers.FileExists()))
