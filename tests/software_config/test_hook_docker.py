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


import cStringIO
import json
import mock
import testtools
from testtools import matchers

from tests.software_config import hook_docker


class HookDockerTest(testtools.TestCase):

    def setUp(self):
        super(HookDockerTest, self).setUp()
        docker = mock.MagicMock()
        self.docker_client = mock.MagicMock()
        docker.Client.return_value = self.docker_client
        self.docker_client.version.return_value = {
            'ApiVersion': '1.3.0'
        }
        hook_docker.docker = docker

    def assertLogEntries(self, entries, log):
        for (entry, line) in zip(entries, log.split('\n')):
            self.assertThat(line, matchers.EndsWith(entry))

    def test_empty_input(self):
        config = {
            'name': 'deployment_name',
            'options': {},
            'inputs': [],
            'outputs': [],
            'config': {}
        }
        sys_stdin = cStringIO.StringIO(json.dumps(config))
        sys_stdout = cStringIO.StringIO()
        hook_docker.main([], sys_stdin, sys_stdout)

        response = json.loads(sys_stdout.getvalue())

        self.assertLogEntries([
            'Connecting to unix:///var/run/docker.sock',
            'Connected to version 1.3.0',
            'Removing all containers from deployment_name'
        ], response.pop('deploy_stdout'))

        self.assertLogEntries([], response.pop('deploy_stderr'))

        self.assertEqual(
            {"deploy_status_code": 0}, response)
