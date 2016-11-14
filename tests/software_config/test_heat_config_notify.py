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
import tempfile

import fixtures
import mock

from tests.software_config import common
from tests.software_config import heat_config_notify as hcn


class HeatConfigNotifyTest(common.RunScriptTest):

    data_signal_id = {
        'id': '5555',
        'group': 'script',
        'inputs': [{
            'name': 'deploy_signal_id',
            'value': 'mock://192.0.2.3/foo'
        }],
        'config': 'five'
    }

    data_signal_id_put = {
        'id': '5555',
        'group': 'script',
        'inputs': [{
            'name': 'deploy_signal_id',
            'value': 'mock://192.0.2.3/foo'
        }, {
            'name': 'deploy_signal_verb',
            'value': 'PUT'
        }],
        'config': 'five'
    }

    data_heat_signal = {
        'id': '5555',
        'group': 'script',
        'inputs': [{
            'name': 'deploy_auth_url',
            'value': 'mock://192.0.2.3/auth'
        }, {
            'name': 'deploy_user_id',
            'value': 'aaaa'
        }, {
            'name': 'deploy_password',
            'value': 'password'
        }, {
            'name': 'deploy_project_id',
            'value': 'bbbb'
        }, {
            'name': 'deploy_stack_id',
            'value': 'cccc'
        }, {
            'name': 'deploy_resource_name',
            'value': 'the_resource'
        }],
        'config': 'five'
    }

    def setUp(self):
        super(HeatConfigNotifyTest, self).setUp()
        self.deployed_dir = self.useFixture(fixtures.TempDir())
        hcn.init_logging = mock.MagicMock()

    def write_config_file(self, data):
        config_file = tempfile.NamedTemporaryFile()
        config_file.write(json.dumps(data))
        config_file.flush()
        return config_file

    def test_notify_missing_file(self):

        signal_data = json.dumps({'foo': 'bar'})
        stdin = cStringIO.StringIO(signal_data)

        with self.write_config_file(self.data_signal_id) as config_file:
            config_file_name = config_file.name

        self.assertEqual(
            1, hcn.main(['heat-config-notify', config_file_name], stdin))

    def test_notify_missing_file_arg(self):

        signal_data = json.dumps({'foo': 'bar'})
        stdin = cStringIO.StringIO(signal_data)

        self.assertEqual(
            1, hcn.main(['heat-config-notify'], stdin))

    def test_notify_signal_id(self):
        requests = mock.MagicMock()
        hcn.requests = requests

        requests.post.return_value = '[200]'

        signal_data = json.dumps({'foo': 'bar'})
        stdin = cStringIO.StringIO(signal_data)

        with self.write_config_file(self.data_signal_id) as config_file:
            self.assertEqual(
                0, hcn.main(['heat-config-notify', config_file.name], stdin))

        requests.post.assert_called_once_with(
            'mock://192.0.2.3/foo',
            data=signal_data,
            headers={'content-type': 'application/json'})

    def test_notify_signal_id_put(self):
        requests = mock.MagicMock()
        hcn.requests = requests

        requests.post.return_value = '[200]'

        signal_data = json.dumps({'foo': 'bar'})
        stdin = cStringIO.StringIO(signal_data)

        with self.write_config_file(self.data_signal_id_put) as config_file:
            self.assertEqual(
                0, hcn.main(['heat-config-notify', config_file.name], stdin))

        requests.put.assert_called_once_with(
            'mock://192.0.2.3/foo',
            data=signal_data,
            headers={'content-type': 'application/json'})

    def test_notify_signal_id_empty_data(self):
        requests = mock.MagicMock()
        hcn.requests = requests

        requests.post.return_value = '[200]'

        stdin = cStringIO.StringIO()

        with self.write_config_file(self.data_signal_id) as config_file:
            self.assertEqual(
                0, hcn.main(['heat-config-notify', config_file.name], stdin))

        requests.post.assert_called_once_with(
            'mock://192.0.2.3/foo',
            data='{}',
            headers={'content-type': 'application/json'})

    def test_notify_signal_id_invalid_json_data(self):
        requests = mock.MagicMock()
        hcn.requests = requests

        requests.post.return_value = '[200]'

        stdin = cStringIO.StringIO('{{{"hi')

        with self.write_config_file(self.data_signal_id) as config_file:
            self.assertEqual(
                0, hcn.main(['heat-config-notify', config_file.name], stdin))

        requests.post.assert_called_once_with(
            'mock://192.0.2.3/foo',
            data='{}',
            headers={'content-type': 'application/json'})

    def test_notify_heat_signal(self):
        ksclient = mock.MagicMock()
        hcn.ksclient = ksclient
        ks = mock.MagicMock()
        ksclient.Client.return_value = ks

        heatclient = mock.MagicMock()
        hcn.heatclient = heatclient
        heat = mock.MagicMock()
        heatclient.Client.return_value = heat

        signal_data = json.dumps({'foo': 'bar'})
        stdin = cStringIO.StringIO(signal_data)

        ks.service_catalog.url_for.return_value = 'mock://192.0.2.3/heat'
        heat.resources.signal.return_value = 'all good'

        with self.write_config_file(self.data_heat_signal) as config_file:
            self.assertEqual(
                0, hcn.main(['heat-config-notify', config_file.name], stdin))

        ksclient.Client.assert_called_once_with(
            auth_url='mock://192.0.2.3/auth',
            user_id='aaaa',
            password='password',
            project_id='bbbb')
        ks.service_catalog.url_for.assert_called_once_with(
            service_type='orchestration', endpoint_type='publicURL')

        heatclient.Client.assert_called_once_with(
            '1', 'mock://192.0.2.3/heat', token=ks.auth_token)
        heat.resources.signal.assert_called_once_with(
            'cccc',
            'the_resource',
            data={'foo': 'bar'})
