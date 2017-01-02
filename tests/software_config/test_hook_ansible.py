# Copyright 2015 NEC Corporation.  All rights reserved.
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


class HookAnsibleTest(common.RunScriptTest):

    data = {
        'id': '1234',
        'name': 'fake_resource_name',
        'group': 'ansible',
        'options': {},
        'inputs': [
            {'name': 'foo', 'value': 'bar'},
            {'name': 'another', 'value': 'input'}
        ],
        'config': 'the ansible playbook'
    }

    data_tags = {
        'id': '1234',
        'name': 'fake_resource_name_tags',
        'group': 'ansible',
        'options': {'tags': 'abc,def'},
        'inputs': [
            {'name': 'foo', 'value': 'bar'},
            {'name': 'another', 'value': 'input'}
        ],
        'config': 'the ansible playbook'
    }

    data_modulepath = data.copy()
    data_modulepath.update({
        'options': {'modulepath': '/opt/ansible:/usr/share/ansible'},
    })

    data_tags_modulepath = data.copy()
    data_tags_modulepath.update({
        'options': {'modulepath': '/opt/ansible:/usr/share/ansible',
                    'tags':       'abc,def'},
    })

    def setUp(self):
        super(HookAnsibleTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-ansible/install.d/hook-ansible.py')

        self.fake_tool_path = self.relative_path(
            __file__,
            'config-tool-fake.py')

        self.working_dir = self.useFixture(fixtures.TempDir())
        self.outputs_dir = self.useFixture(fixtures.TempDir())
        self.test_state_path = self.outputs_dir.join('test_state.json')
        self.test_inventory = "localhost test_var=123,"

        self.env = os.environ.copy()
        self.env.update({
            'HEAT_ANSIBLE_WORKING': self.working_dir.join(),
            'HEAT_ANSIBLE_OUTPUTS': self.outputs_dir.join(),
            'HEAT_ANSIBLE_CMD': self.fake_tool_path,
            'TEST_STATE_PATH': self.test_state_path
        })

    def test_hook(self):
        self._hook_run()

    def test_hook_tags(self):
        self._hook_run(data=self.data_tags, options=['--tags', 'abc,def'])

    def test_hook_modulepath(self):
        self._hook_run(data=self.data_modulepath,
                       options=['--module-path',
                                '/opt/ansible:/usr/share/ansible'])

    def test_hook_tags_modulepath(self):
        self._hook_run(data=self.data_tags_modulepath,
                       options=['--module-path',
                                '/opt/ansible:/usr/share/ansible',
                                '--tags', 'abc,def'])

    def _hook_run(self, data=None, options=None):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'ansible success',
                'stderr': 'thing happened',
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(data or self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': 'ansible success',
            'deploy_stderr': 'thing happened',
            'deploy_status_code': 0,
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        ansible_playbook = self.working_dir.join('1234_playbook.yaml')
        vars_filename = self.working_dir.join('1234_variables.json')

        expected_args = [
            self.fake_tool_path,
            '-i',
            'localhost,']
        if options:
            expected_args += options
        expected_args += [
            ansible_playbook,
            '--extra-vars']
        expected_args.append('@%s' % vars_filename)
        self.assertEqual(expected_args, state['args'])

        # Write 'variables' to file
        variables = self.json_from_file(vars_filename)
        self.assertEqual('bar', variables['foo'])
        self.assertEqual('input', variables['another'])
        self.assertEqual(self.outputs_dir.join('1234'),
                         variables['heat_outputs_path'])

        # Write the executable 'config' to file
        with open(ansible_playbook) as f:
            self.assertEqual('the ansible playbook', f.read())

    def test_hook_inventory(self):

        self.env.update({
            'HEAT_ANSIBLE_INVENTORY': self.test_inventory,
            'TEST_RESPONSE': json.dumps({
                'stdout': 'ansible success',
                'stderr': 'thing happened',
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': 'ansible success',
            'deploy_stderr': 'thing happened',
            'deploy_status_code': 0,
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        ansible_playbook = self.working_dir.join('1234_playbook.yaml')
        vars_filename = self.working_dir.join('1234_variables.json')

        self.assertEqual(
            [
                self.fake_tool_path,
                '-i',
                self.test_inventory,
                ansible_playbook,
                '--extra-vars',
                '@%s' % vars_filename
            ],
            state['args'])

    def test_hook_ansible_failed(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'ansible failed',
                'stderr': 'bad thing happened',
                'returncode': 4
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': 'ansible failed',
            'deploy_stderr': 'bad thing happened',
            'deploy_status_code': 4,
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        ansible_playbook = self.working_dir.join('1234_playbook.yaml')
        vars_filename = self.working_dir.join('1234_variables.json')

        self.assertEqual(
            [
                self.fake_tool_path,
                '-i',
                'localhost,',
                ansible_playbook,
                '--extra-vars',
                '@%s' % vars_filename
            ],
            state['args'])

        # Write 'variables' to file
        variables = self.json_from_file(vars_filename)
        self.assertEqual('bar', variables['foo'])
        self.assertEqual('input', variables['another'])
        self.assertEqual(self.outputs_dir.join('1234'),
                         variables['heat_outputs_path'])

        # Write the executable 'config' to file
        with open(ansible_playbook) as f:
            self.assertEqual('the ansible playbook', f.read())
