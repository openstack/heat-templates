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
import tempfile

import fixtures
import requests_mock
from testtools import matchers

from tests.software_config import common


class HeatConfigTest(common.RunScriptTest):

    fake_hooks = ['cfn-init', 'chef', 'puppet', 'salt', 'script']

    data = [
        {
            'group': 'chef',
            'inputs': [{
                'name': 'deploy_signal_id',
                'value': 'mock://192.0.2.2/foo'
            }],
            'config': 'one'
        }, {
            'group': 'cfn-init',
            'inputs': [],
            'config': 'two'
        }, {
            'group': 'salt',
            'inputs': [{'name': 'foo', 'value': 'bar'}],
            'outputs': [{'name': 'foo'}],
            'config': 'three'
        }, {
            'group': 'puppet',
            'inputs': [],
            'config': 'four'
        }, {
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
            'group': 'no-such-hook',
            'inputs': [],
            'config': 'six'
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

        with open(self.fake_hook_path) as f:
            fake_hook = f.read()

        for hook in self.fake_hooks:
            hook_name = self.hooks_dir.join(hook)
            with open(hook_name, 'w') as f:
                os.utime(hook_name, None)
                f.write(fake_hook)
                f.flush()
            os.chmod(hook_name, 0o755)

    def write_config_file(self, data):
        config_file = tempfile.NamedTemporaryFile()
        config_file.write(json.dumps(data))
        config_file.flush()
        return config_file

    @requests_mock.Mocker(kw='mock_request')
    def test_run_heat_config(self, mock_request):
        mock_request.register_uri('POST', 'mock://192.0.2.2/foo')
        mock_request.register_uri('POST', 'mock://192.0.2.3/foo')

        with self.write_config_file(self.data) as config_file:

            env = os.environ.copy()
            env.update({
                'HEAT_CONFIG_HOOKS': self.hooks_dir.join(),
                'HEAT_SHELL_CONFIG': config_file.name
            })
            returncode, stdout, stderr = self.run_cmd(
                [self.heat_config_path], env)

            self.assertEqual(0, returncode, stderr)

        for config in self.data:
            hook = config['group']
            hook_path = self.hooks_dir.join(hook)
            stdin_path = self.hooks_dir.join('%s.stdin' % hook)
            stdout_path = self.hooks_dir.join('%s.stdout' % hook)

            if hook == 'no-such-hook':
                self.assertThat(
                    hook_path, matchers.Not(matchers.FileExists()))
                self.assertThat(
                    stdin_path, matchers.Not(matchers.FileExists()))
                self.assertThat(
                    stdout_path, matchers.Not(matchers.FileExists()))
                continue

            self.assertTrue(hook_path, matchers.FileExists())
            self.assertTrue(stdin_path, matchers.FileExists())
            self.assertTrue(stdout_path, matchers.FileExists())

            # parsed stdin should match the config item
            self.assertEqual(config,
                             self.json_from_file(stdin_path))

            self.assertEqual(self.outputs[hook],
                             self.json_from_file(stdout_path))
