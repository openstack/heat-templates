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

import fixtures

from tests.software_config import common


class HookPuppetTest(common.RunScriptTest):

    data = {
        'id': '1234',
        'creation_time': '2015-07-16T11:40:20',
        'name': 'fake_resource_name',
        'group': 'puppet',
        'options': {
            'enable_hiera': True,
            'enable_facter': True,
            'enable_debug': True,
            'enable_verbose': True,
        },
        'inputs': [
            {'name': 'foo', 'value': 'bar'},
            {'name': 'another', 'value': 'input'}
        ],
        'outputs': [
            {'name': 'first_output'},
            {'name': 'second_output'}
        ],
        'config': 'the puppet script'
    }

    def setUp(self):
        super(HookPuppetTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-puppet/install.d/hook-puppet.py')

        self.fake_tool_path = self.relative_path(
            __file__,
            'config-tool-fake.py')

        self.working_dir = self.useFixture(fixtures.TempDir())
        self.outputs_dir = self.useFixture(fixtures.TempDir())
        self.log_dir = self.useFixture(fixtures.TempDir())
        self.hiera_datadir = self.useFixture(fixtures.TempDir())
        self.test_state_path = self.outputs_dir.join('test_state.json')

        self.env = os.environ.copy()
        self.env.update({
            'HEAT_PUPPET_WORKING': self.working_dir.join(),
            'HEAT_PUPPET_OUTPUTS': self.outputs_dir.join(),
            'HEAT_PUPPET_LOGDIR': self.log_dir.join(),
            'HEAT_PUPPET_HIERA_DATADIR': self.hiera_datadir.join(),
            'HEAT_PUPPET_CMD': self.fake_tool_path,
            'TEST_STATE_PATH': self.test_state_path,
        })

    def test_hook(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'puppet success',
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
            'deploy_stdout': 'puppet success',
            'deploy_stderr': 'thing happened',
            'deploy_status_code': 0,
            'first_output': 'output 1',
            'second_output': 'output 2',
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        puppet_script = self.working_dir.join('1234.pp')
        self.assertEqual(
            [
                self.fake_tool_path,
                'apply',
                '--detailed-exitcodes',
                '--logdest',
                'console',
                '--debug',
                '--logdest',
                '/var/log/puppet/heat-debug.log',
                '--verbose',
                '--logdest',
                '/var/log/puppet/heat-verbose.log',
                puppet_script
            ],
            state['args'])

        self.assertEqual('bar', state['env']['FACTER_foo'])
        self.assertEqual('input', state['env']['FACTER_another'])
        self.assertEqual(self.outputs_dir.join('1234'),
                         state['env']['FACTER_heat_outputs_path'])
        with open(puppet_script) as f:
            self.assertEqual('the puppet script', f.read())

    def test_hook_no_debug(self):
        self.data['options']['enable_debug'] = False
        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'success',
                'stderr': '',
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        state = self.json_from_file(self.test_state_path)
        puppet_script = self.working_dir.join('1234.pp')
        self.assertEqual(
            [
                self.fake_tool_path,
                'apply',
                '--detailed-exitcodes',
                '--logdest',
                'console',
                '--verbose',
                '--logdest',
                '/var/log/puppet/heat-verbose.log',
                puppet_script
            ],
            state['args'])
        self.data['options']['enable_debug'] = True

    def test_hook_no_verbose(self):
        self.data['options']['enable_verbose'] = False
        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'success',
                'stderr': '',
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        state = self.json_from_file(self.test_state_path)
        puppet_script = self.working_dir.join('1234.pp')
        self.assertEqual(
            [
                self.fake_tool_path,
                'apply',
                '--detailed-exitcodes',
                '--logdest',
                'console',
                '--debug',
                '--logdest',
                '/var/log/puppet/heat-debug.log',
                puppet_script
            ],
            state['args'])
        self.data['options']['enable_verbose'] = True

    def test_hook_puppet_failed(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'puppet failed',
                'stderr': 'bad thing happened',
                'returncode': 4
            }),
        })
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': 'puppet failed',
            'deploy_stderr': 'bad thing happened',
            'deploy_status_code': 4,
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        puppet_script = self.working_dir.join('1234.pp')
        self.assertEqual(
            [
                self.fake_tool_path,
                'apply',
                '--detailed-exitcodes',
                '--logdest',
                'console',
                '--debug',
                '--logdest',
                '/var/log/puppet/heat-debug.log',
                '--verbose',
                '--logdest',
                '/var/log/puppet/heat-verbose.log',
                puppet_script
            ],
            state['args'])

        self.assertEqual('bar', state['env']['FACTER_foo'])
        self.assertEqual('input', state['env']['FACTER_another'])
        self.assertEqual(self.outputs_dir.join('1234'),
                         state['env']['FACTER_heat_outputs_path'])
        with open(puppet_script) as f:
            self.assertEqual('the puppet script', f.read())

    def test_hook_hiera(self):

        self.env.update({
            'TEST_RESPONSE': json.dumps({
                'stdout': 'puppet success',
                'stderr': 'thing happened',
                'files': {
                    self.outputs_dir.join('1234.first_output'): 'output 1',
                    self.outputs_dir.join('1234.second_output'): 'output 2',
                }
            }),
        })
        modulepath = self.working_dir.join()
        data = copy.deepcopy(self.data)
        data['options']['modulepath'] = modulepath
        data['options']['tags'] = 'package,file'
        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(data))

        self.assertEqual(0, returncode, stderr)
        self.assertEqual({
            'deploy_stdout': 'puppet success',
            'deploy_stderr': 'thing happened',
            'deploy_status_code': 0,
            'first_output': 'output 1',
            'second_output': 'output 2',
        }, json.loads(stdout))

        state = self.json_from_file(self.test_state_path)
        puppet_script = self.working_dir.join('1234.pp')
        hiera_datafile = self.hiera_datadir.join('heat_config_%s.json'
                                                 % self.data['name'])
        self.assertEqual(
            [
                self.fake_tool_path,
                'apply',
                '--detailed-exitcodes',
                '--logdest',
                'console',
                '--modulepath',
                modulepath,
                '--tags',
                'package,file',
                '--debug',
                '--logdest',
                '/var/log/puppet/heat-debug.log',
                '--verbose',
                '--logdest',
                '/var/log/puppet/heat-verbose.log',
                puppet_script
            ],
            state['args'])

        self.assertEqual(self.outputs_dir.join('1234'),
                         state['env']['FACTER_heat_outputs_path'])
        with open(puppet_script) as f:
            self.assertEqual('the puppet script', f.read())
        with open(hiera_datafile) as f:
            self.assertEqual({
                'foo': 'bar',
                'another': 'input',
            }, json.loads(f.read()))
