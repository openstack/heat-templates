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


class HookScriptTest(common.RunScriptTest):

    def setUp(self):
        super(HookScriptTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-script/install.d/hook-script.py')

        self.fake_tool_path = self.relative_path(
            __file__,
            'config-tool-fake.py')

        with open(self.fake_tool_path) as f:
            self.fake_tool_contents = f.read()

        self.data = {
            'id': '1234',
            'group': 'script',
            'inputs': [
                {'name': 'foo', 'value': 'bar'},
                {'name': 'another', 'value': 'input'},
                {'name': 'a_dict', 'value': '{"key": "value"}'},
                {'name': 'a_list', 'value': '["v1", 12]'},
            ],
            'outputs': [
                {'name': 'first_output'},
                {'name': 'second_output'}
            ],
            'config': self.fake_tool_contents
        }

        self.working_dir = self.useFixture(fixtures.TempDir())
        self.outputs_dir = self.useFixture(fixtures.TempDir())
        self.test_state_path = self.outputs_dir.join('test_state.json')

        self.env = os.environ.copy()
        self.env.update({
            'HEAT_SCRIPT_WORKING': self.working_dir.join(),
            'HEAT_SCRIPT_OUTPUTS': self.outputs_dir.join(),
            'TEST_STATE_PATH': self.test_state_path,
        })

    def test_hook(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'script success',
                'stderr': 'thing happened',
                'files': {
                    self.outputs_dir.join('1234.first_output'): 'output 1',
                    self.outputs_dir.join('1234.second_output'): 'output 2',
                }
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': 'script success',
            'deploy_stderr': 'thing happened',
            'deploy_status_code': 0,
            'first_output': 'output 1',
            'second_output': 'output 2',
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        script = self.working_dir.join('1234')
        with open(script) as f:
            self.assertEqual(self.fake_tool_contents, f.read())

        self.assertEqual([script], state['args'])
        self.assertEqual('bar', state['env']['foo'])
        self.assertEqual('input', state['env']['another'])
        self.assertEqual('{"key": "value"}', state['env']['a_dict'])
        self.assertEqual('["v1", 12]', state['env']['a_list'])
        self.assertEqual(self.outputs_dir.join('1234'),
                         state['env']['heat_outputs_path'])

    def test_hook_failed(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'script failed',
                'stderr': 'bad thing happened',
                'returncode': 1
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': 'script failed',
            'deploy_stderr': 'bad thing happened',
            'deploy_status_code': 1,
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        script = self.working_dir.join('1234')
        with open(script) as f:
            self.assertEqual(self.fake_tool_contents, f.read())

        self.assertEqual([script], state['args'])
        self.assertEqual('bar', state['env']['foo'])
        self.assertEqual('input', state['env']['another'])
        self.assertEqual('{"key": "value"}', state['env']['a_dict'])
        self.assertEqual('["v1", 12]', state['env']['a_list'])
        self.assertEqual(self.outputs_dir.join('1234'),
                         state['env']['heat_outputs_path'])
