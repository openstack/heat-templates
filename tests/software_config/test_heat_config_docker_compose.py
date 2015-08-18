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
import yaml

from tests.software_config import common


class HeatConfigDockerComposeORCTest(common.RunScriptTest):

    fake_hooks = ['docker-compose']

    data = [
        {
            "name": "abcdef001",
            "group": "docker-compose",
            "inputs": {},
            "config": {
                "web": {
                    "image": "nginx",
                    "links": [
                        "db"
                    ],
                    "ports": [
                        "8000:8000"
                    ]
                },
                "db": {
                    "image": "redis"
                }
            }
        },
        {
            "name": "abcdef002",
            "group": "docker-compose",
            "inputs": {},
            "config": {
                "web": {
                    "image": "httpd",
                    "links": [
                        "db"
                    ],
                    "ports": [
                        "80:8001"
                    ]
                },
                "db": {
                    "image": "postgress"
                }
            }
        }
    ]

    def setUp(self):
        super(HeatConfigDockerComposeORCTest, self).setUp()

        self.fake_hook_path = self.relative_path(__file__, 'hook-fake.py')
        self.heat_config_docker_compose_path = self.relative_path(
            __file__,
            '../..',
            'hot/software-config/elements',
            'heat-config-docker-compose/os-refresh-config/configure.d/'
            '50-heat-config-docker-compose')

        self.docker_compose_dir = self.useFixture(fixtures.TempDir())

        with open(self.fake_hook_path) as f:
            fake_hook = f.read()

        for hook in self.fake_hooks:
            hook_name = self.docker_compose_dir.join(hook)
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
                'HEAT_DOCKER_COMPOSE_WORKING': self.docker_compose_dir.join(),
                'HEAT_SHELL_CONFIG': config_file.name
            })

            returncode, stdout, stderr = self.run_cmd(
                [self.heat_config_docker_compose_path], env)

            self.assertEqual(0, returncode, stderr)

            compose_yml = self.docker_compose_dir.join(
                'abcdef001/docker-compose.yml')
            with open(compose_yml) as f:
                    self.assertEqual(yaml.safe_dump(
                        self.data[0].get('config'),
                        default_flow_style=False), f.read())
