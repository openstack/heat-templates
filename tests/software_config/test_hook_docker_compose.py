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

import json
import os

import fixtures

from tests.software_config import common


class HookDockerComposeTest(common.RunScriptTest):
    data = {
        "name": "abcdef001",
        "group": "docker-compose",
        "inputs": [
            {
                "name": "env_files",
                "value": u'[ { "file_name": "./common.env", '
                         u'"content": "xxxxx" }, '
                         u'{ "file_name": "./test.env", '
                         u'"content": "yyyy" }, '
                         u'{ "file_name": "./test1.env", '
                         u'"content": "zzz" } ]'
            }
        ],
        "config": {
            "web": {
                "name": "x",
                "env_file": [
                    "./common.env",
                    "./test.env"
                ]
            },
            "db": {
                "name": "y",
                "env_file": "./test1.env"
            }
        }
    }

    data_without_input = {
        "name": "abcdef001",
        "group": "docker-compose",
        "inputs": [],
        "config": {
            "web": {
                "name": "x",
                "env_file": [
                    "./common.env",
                    "./test.env"
                ]
            },
            "db": {
                "name": "y",
                "env_file": "./test1.env"
            }
        }
    }

    def setUp(self):
        super(HookDockerComposeTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-docker-compose/install.d/hook-docker-compose.py')

        self.fake_tool_path = self.relative_path(
            __file__,
            'config-tool-fake.py')

        self.working_dir = self.useFixture(fixtures.TempDir())
        self.outputs_dir = self.useFixture(fixtures.TempDir())
        self.test_state_path = self.outputs_dir.join('test_state.json')

        self.env = os.environ.copy()
        self.env.update({
            'HEAT_DOCKER_COMPOSE_WORKING': self.working_dir.join(),
            'HEAT_DOCKER_COMPOSE_CMD': self.fake_tool_path,
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
            'deploy_stderr': 'Creating abcdef001_db_1...',
            'deploy_status_code': 0
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        self.assertEqual(
            [
                self.fake_tool_path,
                'up',
                '-d',
                '--no-build',
            ],
            state['args'])

    def test_hook_without_inputs(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': '',
                'stderr': 'env_file_not found...',
                'returncode': 1
            })
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data_without_input))

        self.assertEqual({
            'deploy_stdout': '',
            'deploy_stderr': 'env_file_not found...',
            'deploy_status_code': 1
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        self.assertEqual(
            [
                self.fake_tool_path,
                'up',
                '-d',
                '--no-build',
            ],
            state['args'])

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
            'deploy_stderr': 'Error: image library/xxx:latest not found',
            'deploy_status_code': 1
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        self.assertEqual(
            [
                self.fake_tool_path,
                'up',
                '-d',
                '--no-build',
            ],
            state['args'])
