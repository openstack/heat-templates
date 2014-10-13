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


class HookCfnInitTest(common.RunScriptTest):

    data = {
        'group': 'cfn-init',
        'inputs': [],
        'config': {'foo': 'bar'}
    }

    def setUp(self):
        super(HookCfnInitTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-cfn-init/install.d/hook-cfn-init.py')

        self.fake_tool_path = self.relative_path(
            __file__,
            'config-tool-fake.py')

        self.metadata_dir = self.useFixture(fixtures.TempDir())
        # use the temp dir to store the fake config tool state too
        self.test_state_path = self.metadata_dir.join('test_state.json')
        self.env = os.environ.copy()
        self.env.update({
            'HEAT_CFN_INIT_LAST_METADATA_DIR': self.metadata_dir.join(),
            'HEAT_CFN_INIT_CMD': self.fake_tool_path,
            'TEST_STATE_PATH': self.test_state_path,
        })

    def test_hook(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'cfn-init success',
                'stderr': 'thing happened'
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': 'cfn-init success',
            'deploy_stderr': 'thing happened',
            'deploy_status_code': 0
        }, json.loads(stdout))

        # assert last_metadata was written with cfn-init metadata
        self.assertEqual(
            {'AWS::CloudFormation::Init': {'foo': 'bar'}},
            self.json_from_file(self.metadata_dir.join('last_metadata')))

        # assert cfn-init was called with no args
        self.assertEqual(
            [self.fake_tool_path],
            self.json_from_file(self.test_state_path)['args'])

    def test_hook_cfn_init_failed(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stderr': 'bad thing happened',
                'returncode': 1
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': '',
            'deploy_stderr': 'bad thing happened',
            'deploy_status_code': 1
        }, json.loads(stdout))

        self.assertEqual(
            {'AWS::CloudFormation::Init': {'foo': 'bar'}},
            self.json_from_file(self.metadata_dir.join('last_metadata')))

        # assert cfn-init was called with no args
        self.assertEqual(
            [self.fake_tool_path],
            self.json_from_file(self.test_state_path)['args'])

    def test_hook_invalid_json(self):

        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, "{::::")

        self.assertEqual(1, returncode, stderr)
