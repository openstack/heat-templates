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

import fixtures
import json
import logging
import os
import yaml

from tests.software_config import common

log = logging.getLogger('test_hook_salt')

slsok = """
testit:
  environ.setenv:
  - name: does_not_matter
  - value:
      foo: {{ opts['fooval'] }}
      bar: {{ opts['barval'] }}
"""

slsfail = """
failure:
  test.echo:
  - text: I don't work
"""

slsnotallowed = """
install_service:
  pkg.installed:
  - name: {{ opts['fooval'] }}
"""


class HookSaltTest(common.RunScriptTest):

    data = {
        'id': 'fake_stack',
        'name': 'fake_resource_name',
        'group': 'salt',
        'inputs': [
            {'name': 'fooval', 'value': 'bar'},
            {'name': 'barval', 'value': 'foo'}
        ],
        'outputs': [
            {'name': 'first_output'},
            {'name': 'second_output'}
        ],
        'config': None
    }

    def setUp(self):
        super(HookSaltTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-salt/install.d/hook-salt.py')

        self.working_dir = self.useFixture(fixtures.TempDir())
        self.minion_config_dir = self.useFixture(fixtures.TempDir())
        self.minion_cach_dir = self.useFixture(fixtures.TempDir())

        self.minion_conf = self.minion_config_dir.join("minion")

        self.env = os.environ.copy()
        self.env.update({
            'HEAT_SALT_WORKING': self.working_dir.join(),
            'SALT_MINION_CONFIG': self.minion_conf
        })

        with open(self.minion_conf, "w+") as conf_file:
            conf_file.write("cachedir: %s\n" % self.minion_cach_dir.join())
            conf_file.write("log_level: DEBUG\n")

    def test_hook(self):

        self.data['config'] = slsok

        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        ret = yaml.safe_load(stdout)
        self.assertEqual(0, ret['deploy_status_code'])
        self.assertIsNone(ret['deploy_stderr'])
        self.assertIsNotNone(ret['deploy_stdout'])
        resp = yaml.safe_load(ret['deploy_stdout'])
        self.assertTrue(resp.values()[0]['result'])
        self.assertEqual({'bar': 'foo', 'foo': 'bar'},
                         resp.values()[0]['changes'])

    def test_hook_salt_failed(self):

        self.data['config'] = slsfail

        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode)
        self.assertIsNotNone(stderr)
        self.assertIsNotNone(stdout)
        jsonout = json.loads(stdout)
        self.assertIsNone(jsonout.get("deploy_stdout"),
                          jsonout.get("deploy_stdout"))
        self.assertEqual(2, jsonout.get("deploy_status_code"))
        self.assertIsNotNone(jsonout.get("deploy_stderr"))
        self.assertIn("was not found in SLS", jsonout.get("deploy_stderr"))

    def test_hook_salt_retcode(self):

        self.data['config'] = slsnotallowed

        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        self.assertIsNotNone(stdout)
        self.assertIsNotNone(stderr)
        ret = json.loads(stdout)
        self.assertIsNone(ret['deploy_stdout'])
        self.assertIsNotNone(ret['deploy_stderr'])
        resp = yaml.safe_load(ret['deploy_stderr']).values()[0]
        self.assertFalse(resp['result'])
