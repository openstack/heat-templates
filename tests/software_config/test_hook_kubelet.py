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


import mock
import re
import testtools

from tests.software_config import hook_kubelet


class HookKubeletTest(testtools.TestCase):

    config = {
        "id": "a50ae8dd-b0c4-407f-8732-3571b3a0f28b",
        "group": "kubelet",
        "inputs": [],
        "name": "20_apache_deployment",
        "outputs": [],
        "options": {},
        "config": {
            "version": "v1beta2",
            "volumes": [{
                "name": "mariadb-data"
            }],
            "containers": [{
                "image": "kollaglue/fedora-rdo-rabbitmq",
                "name": "rabbitmq",
                "ports": [{
                    "containerPort": 5672,
                    "hostPort": 5672}]
            }, {
                "image": "kollaglue/fedora-rdo-heat-engine",
                "name": "heat-engine",
                "env": [{
                    "name": "AUTH_ENCRYPTION_KEY",
                    "value": "Vegu95l2jwkucD9RSYAoFpRbUlh0PGF7"}]
            }, {
                "image": "kollaglue/fedora-rdo-heat-engine",
                "name": "heat-engine2",
                "env": [{
                    "name": "AUTH_ENCRYPTION_KEY",
                    "value": "Vegu95l2jwkucD9RSYAoFpRbUlh0PGF7"}]
            }]
        }
    }

    def setUp(self):
        super(HookKubeletTest, self).setUp()
        docker = mock.MagicMock()
        self.docker_client = mock.MagicMock()
        docker.Client.return_value = self.docker_client
        self.docker_client.version.return_value = {
            'ApiVersion': '1.3.0'
        }
        hook_kubelet.docker = docker

    def test_id_to_pod_name_part(self):
        self.assertEqual(
            'fc9070b3ba4e4f2',
            hook_kubelet.id_to_pod_name_part(
                'fc9070b3-ba4e-4f22-b732-5ffdcdb40b74'))

    def test_container_pattern(self):
        pattern = hook_kubelet.container_pattern(
            'fc9070b3-ba4e-4f22-b732-5ffdcdb40b74', 'mariadb')
        self.assertEqual(
            '^/k8s_mariadb\\.[0-9a-z]{8}_fc9070b3ba4e4f2', pattern)

        pat = re.compile(pattern)

        self.assertIsNotNone(pat.match(
            '/k8s_mariadb.dac8ccce_fc9070b3ba4e4f2'
            'uv6pejpu5nqbmrqoungurhtob5gvt.default.'
            'file_2c8cf9fc94674e8buv6pejpu5nqbmrqoungurhtob5gvt_dcd1e1d9'))
        self.assertIsNotNone(pat.match(
            '/k8s_mariadb.dac8ccce_fc9070b3ba4e4f2a'))

        self.assertIsNone(pat.match(
            'k8s_mariadb.dac8ccce_fc9070b3ba4e4f2a'))
        self.assertIsNone(pat.match(
            '/k8s_mysqldb.dac8ccce_fc9070b3ba4e4f2a'))
        self.assertIsNone(pat.match(
            '/k8s_mariadb.dac8ccc_fc9070b3ba4e4f2a'))
        self.assertIsNone(pat.match(
            '/k8s_mariadb.dac8ccce_gc9070b3ba4e4f22a'))

    def test_required_images(self):
        self.assertEqual(
            set([
                'kollaglue/fedora-rdo-heat-engine',
                'kollaglue/fedora-rdo-rabbitmq']),
            hook_kubelet.required_images(self.config))

        self.assertEqual(
            set(), hook_kubelet.required_images({'config': {}}))

    def test_required_container_patterns(self):
        patterns = hook_kubelet.required_container_patterns(self.config)
        self.assertEqual({
            'heat-engine': '^/k8s_heat-engine\\.[0-9a-z]{8}_a50ae8ddb0c4407',
            'heat-engine2': '^/k8s_heat-engine2\\.[0-9a-z]{8}_a50ae8ddb0c4407',
            'rabbitmq': '^/k8s_rabbitmq\\.[0-9a-z]{8}_a50ae8ddb0c4407'
        }, patterns)
