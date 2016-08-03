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

log = logging.getLogger('test_hook_apply_config')


class HookApplyConfigTest(common.RunScriptTest):

    data = {
        'id': 'test_apply_config',
        'name': 'fake_resource_name',
        'group': 'apply-config',
        'config': {'foo': 'bar'}
    }

    def setUp(self):
        super(HookApplyConfigTest, self).setUp()
        self.hook_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-apply-config/install.d/hook-apply-config.py')

        self.metadata_dir = self.useFixture(fixtures.TempDir())
        self.templates_dir = self.useFixture(fixtures.TempDir())
        tmp_dir = tempfile.NamedTemporaryFile(mode='w', delete=False).name
        os.unlink(tmp_dir)
        self.tmp_file = os.path.basename(tmp_dir)
        self.out_dir = self.templates_dir.join('tmp')

        self.metadata = self.metadata_dir.join(self.tmp_file)

        self.env = os.environ.copy()
        self.env.update({
            'OS_CONFIG_FILES': self.metadata,
            'OS_CONFIG_APPLIER_TEMPLATES': self.templates_dir.join(),
        })

        # our fake metadata file
        with open(self.metadata, "w+") as md:
            md.write(json.dumps({'foo': 'bar'}))

        # This is our fake template root we use to verify os-apply-config
        # works as expected
        os.mkdir(self.out_dir)
        with open(os.path.join(self.out_dir, self.tmp_file), "w+") as template:
            template.write("foo={{foo}}")

    def test_hook(self):

        returncode, stdout, stderr = self.run_cmd(
            [self.hook_path], self.env, json.dumps(self.data))

        self.assertEqual(0, returncode, stderr)
        ret = yaml.safe_load(stdout)
        self.assertIsNotNone(ret['deploy_stderr'])
        self.assertEqual('', ret['deploy_stdout'])
        self.assertEqual(0, ret['deploy_status_code'])
        f = os.path.join('/tmp', self.tmp_file)
        with open(f) as out_file:
            self.assertEqual('foo=bar', out_file.read())
        os.unlink(f)
