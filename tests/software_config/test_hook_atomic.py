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


class HookAtomicTest(common.RunScriptTest):
    data = {
        "id": "abcdef001",
        "group": "atomic",
        "inputs": [],
        "config": {
            "command": "install",
            "image": "imain/atomic-install-rabbitmq"
        }
    }

    def setUp(self):
        super(HookAtomicTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/heat-container-agent',
            'scripts/hooks/atomic')

        self.fake_tool_path = self.relative_path(
            __file__,
            'config-tool-fake.py')

        self.working_dir = self.useFixture(fixtures.TempDir())
        self.outputs_dir = self.useFixture(fixtures.TempDir())
        self.test_state_path = self.outputs_dir.join('test_state.json')

        self.env = os.environ.copy()
        self.env.update({
            'HEAT_ATOMIC_WORKING': self.working_dir.join(),
            'HEAT_ATOMIC_CMD': self.fake_tool_path,
            'TEST_STATE_PATH': self.test_state_path,
        })

    def test_hook(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'Downloading xxx',
                'stderr': ''
            })
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)

        self.assertEqual({
            'deploy_stdout': 'Downloading xxx',
            'deploy_stderr': '',
            'deploy_status_code': 0
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        self.assertEqual(
            [
                self.fake_tool_path,
                'install',
                'imain/atomic-install-rabbitmq',
                '-n abcdef001',
                ''
            ],
            state['args'])

    def test_hook_failed(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': '',
                'stderr': 'Container exists...',
                'returncode': 1
            })
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)

        self.assertEqual({
            'deploy_stdout': '',
            'deploy_stderr': 'Container exists...',
            'deploy_status_code': 1
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        self.assertEqual(
            [
                self.fake_tool_path,
                'install',
                'imain/atomic-install-rabbitmq',
                '-n abcdef001',
                ''
            ],
            state['args'])
