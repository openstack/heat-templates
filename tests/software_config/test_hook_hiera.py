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
import tempfile
import yaml

from tests.software_config import common

log = logging.getLogger('test_hook_hiera_config')

HIERA_CONFIG_BASE = """
---
:backends:
  - json
:json:
  :datadir: %(datadir)s
:hierarchy:
  - %(datafile)s
"""


class HookHieraTest(common.RunScriptTest):

    data = {
        'id': 'test_hiera',
        'name': 'fake_resource_name',
        'group': 'hiera',
        'config': {
            'hierarchy': ['compute'],
            'datafiles': {
                'compute': {'foo': 'bar'}
            }
        }
    }

    def setUp(self):
        super(HookHieraTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-hiera/install.d/hook-hiera.py')

        self.hieradata_dir = self.useFixture(fixtures.TempDir()).join()
        self.conf = tempfile.NamedTemporaryFile(mode='w', delete=False).name
        os.unlink(self.conf)

        self.env = os.environ.copy()
        self.env.update({
            'HEAT_HIERA_CONFIG': self.conf,
            'HEAT_PUPPET_HIERA_DATADIR': self.hieradata_dir,
        })

    def test_hook(self):

        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        ret = yaml.safe_load(stdout)
        self.assertIsNotNone(ret['deploy_stderr'])
        self.assertEqual('', ret['deploy_stdout'])
        self.assertEqual(0, ret['deploy_status_code'])

        conf_data = HIERA_CONFIG_BASE % {'datadir': self.hieradata_dir,
                                         'datafile': 'compute'}
        with open(self.conf) as conf_file:
            self.assertEqual(conf_data, conf_file.read())

        with open(os.path.join(self.hieradata_dir, 'compute.json')) as data:
            self.assertEqual("{\n    \"foo\": \"bar\"\n}", data.read())
