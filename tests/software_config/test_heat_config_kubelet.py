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
from testtools import matchers

from tests.software_config import common


class HeatConfigKubeletORCTest(common.RunScriptTest):

    fake_hooks = ['kubelet']

    data = [{
        "id": "abcdef001",
        "group": "kubelet",
        "name": "mysql",
        "config": {
            "version": "v1beta2",
            "volumes": [{
                "name": "mariadb-data"
            }],
            "containers": [{
                "image": "mariadb_image",
                "volumeMounts": [{
                    "mountPath": "/var/lib/mysql",
                    "name": "mariadb-data"
                }],
                "name": "mariadb",
                "env": [{
                    "name": "DB_ROOT_PASSWORD",
                    "value": "mariadb_password"
                }],
                "ports": [{
                    "containerPort": 3306
                }]
            }]}
    }, {
        "id": "abcdef002",
        "group": "kubelet",
        "name": "rabbitmq",
        "config": {
            "version": "v1beta2",
            "containers": [{
                "image": "rabbitmq_image",
                "name": "rabbitmq",
                "ports": [{
                    "containerPort": 5672
                }]
            }]
        }
    }, {
        "id": "abcdef003",
        "group": "kubelet",
        "name": "heat_api_engine",
        "config": {
            "version": "v1beta2",
            "containers": [{
                "image": "heat_engine_image",
                "name": "heat-engine",
                "env": [{
                    "name": "DB_ROOT_PASSWORD",
                    "value": "mariadb_password"
                }, {
                    "name": "HEAT_DB_PASSWORD",
                    "value": "heatdb_password"
                }, {
                    "name": "HEAT_KEYSTONE_PASSWORD",
                    "value": "password"
                }]
            }, {
                "image": "heat_api_image",
                "name": "heat-api",
                "ports": [{
                    "containerPort": 8004
                }]
            }]
        }
    }]

    def setUp(self):
        super(HeatConfigKubeletORCTest, self).setUp()

        self.fake_hook_path = self.relative_path(__file__, 'hook-fake.py')

        self.heat_config_kubelet_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-kubelet/os-refresh-config/configure.d/'
            '50-heat-config-kubelet')

        self.manifests_dir = self.useFixture(fixtures.TempDir())

        with open(self.fake_hook_path) as f:
            fake_hook = f.read()

        for hook in self.fake_hooks:
            hook_name = self.manifests_dir.join(hook)
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

    def test_run_heat_config(self):

        with self.write_config_file(self.data) as config_file:

            env = os.environ.copy()
            env.update({
                'HEAT_KUBELET_MANIFESTS': self.manifests_dir.join(),
                'HEAT_SHELL_CONFIG': config_file.name
            })
            returncode, stdout, stderr = self.run_cmd(
                [self.heat_config_kubelet_path], env)

            self.assertEqual(0, returncode, stderr)

        for config in self.data:
            manifest_name = '%s.json' % config['id']
            manifest_path = self.manifests_dir.join(manifest_name)
            self.assertThat(manifest_path, matchers.FileExists())

            # manifest file should match manifest config
            self.assertEqual(config['config'],
                             self.json_from_file(manifest_path))
