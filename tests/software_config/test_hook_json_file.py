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
import logging
import os
import tempfile
import yaml

from tests.software_config import common

log = logging.getLogger('test_hook_json_file')


class HookKollaConfigTest(common.RunScriptTest):

    def setUp(self):
        super(HookKollaConfigTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-json-file/install.d/hook-json-file.py')

        self.conf = tempfile.NamedTemporaryFile(mode='w', delete=False).name
        os.unlink(self.conf)

        self.env = os.environ.copy()
        self.data = {
            'id': 'test_json_file',
            'name': 'fake_resource_name',
            'group': 'json-file',
            'config': {
                self.conf: {
                  'command': 'foo'
                }
            }
        }

    def test_hook(self):

        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        ret = yaml.safe_load(stdout)
        self.assertIsNotNone(ret['deploy_stderr'])
        self.assertEqual('', ret['deploy_stdout'])
        self.assertEqual(0, ret['deploy_status_code'])

        with open(os.path.join(self.conf)) as data:
            self.assertEqual("{\n    \"command\": \"foo\"\n}", data.read())
