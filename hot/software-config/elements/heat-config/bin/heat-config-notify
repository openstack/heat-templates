#!/usr/bin/env python
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
import sys

import requests

try:
    from heatclient import client as heatclient
except ImportError:
    heatclient = None

try:
    from keystoneclient.v3 import client as ksclient
except ImportError:
    ksclient = None

try:
    from zaqarclient.queues.v1 import client as zaqarclient
except ImportError:
    zaqarclient = None


MAX_RESPONSE_SIZE = 950000


def init_logging():
    log = logging.getLogger('heat-config-notify')
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            '[%(asctime)s] (%(name)s) [%(levelname)s] %(message)s'))
    log.addHandler(handler)
    log.setLevel('DEBUG')
    return log


def trim_response(response, trimmed_values=None):
    """Trim selected values from response.

    Makes given response smaller or the same size as MAX_RESPONSE_SIZE by
    trimming given trimmed_values from response dict from the left side
    (beginning). Returns trimmed and serialized JSON response itself.
    """

    trimmed_values = trimmed_values or ('deploy_stdout', 'deploy_stderr')
    str_response = json.dumps(response, ensure_ascii=True, encoding='utf-8')
    len_total = len(str_response)
    offset = MAX_RESPONSE_SIZE - len_total
    if offset >= 0:
        return str_response
    offset = abs(offset)
    for key in trimmed_values:
        len_value = len(response[key])
        cut = int(round(float(len_value) / len_total * offset))
        response[key] = response[key][cut:]
    str_response = json.dumps(response, ensure_ascii=True, encoding='utf-8')
    return str_response


def main(argv=sys.argv, stdin=sys.stdin):

    log = init_logging()
    usage = ('Usage:\n  heat-config-notify /path/to/config.json '
             '< /path/to/signal_data.json')

    if len(argv) < 2:
        log.error(usage)
        return 1

    try:
        signal_data = json.load(stdin)
    except ValueError:
        log.warn('No valid json found on stdin')
        signal_data = {}

    conf_file = argv[1]
    if not os.path.exists(conf_file):
        log.error('No config file %s' % conf_file)
        log.error(usage)
        return 1

    c = json.load(open(conf_file))

    iv = dict((i['name'], i['value']) for i in c['inputs'])

    if 'deploy_signal_id' in iv:
        sigurl = iv.get('deploy_signal_id')
        sigverb = iv.get('deploy_signal_verb', 'POST')
        log.debug('Signaling to %s via %s' % (sigurl, sigverb))
        # we need to trim log content because Heat response size is limited
        # by max_json_body_size = 1048576
        str_signal_data = trim_response(signal_data)
        if sigverb == 'PUT':
            r = requests.put(sigurl, data=str_signal_data,
                             headers={'content-type': 'application/json'})
        else:
            r = requests.post(sigurl, data=str_signal_data,
                              headers={'content-type': 'application/json'})
        log.debug('Response %s ' % r)

    if 'deploy_queue_id' in iv:
        queue_id = iv.get('deploy_queue_id')
        log.debug('Signaling to queue %s' % (queue_id,))

        ks = ksclient.Client(
            auth_url=iv['deploy_auth_url'],
            user_id=iv['deploy_user_id'],
            password=iv['deploy_password'],
            project_id=iv['deploy_project_id'])
        endpoint = ks.service_catalog.url_for(
            service_type='messaging', endpoint_type='publicURL')

        conf = {
            'auth_opts': {
                'backend': 'keystone',
                'options': {
                    'os_auth_token': ks.auth_token,
                    'os_project_id': iv['deploy_project_id'],
                }
            }
        }
        cli = zaqarclient.Client(endpoint, conf=conf, version=1.1)
        queue = cli.queue(queue_id)
        r = queue.post({'body': signal_data, 'ttl': 600})
        log.debug('Response %s ' % r)

    elif 'deploy_auth_url' in iv:
        ks = ksclient.Client(
            auth_url=iv['deploy_auth_url'],
            user_id=iv['deploy_user_id'],
            password=iv['deploy_password'],
            project_id=iv['deploy_project_id'])
        endpoint = ks.service_catalog.url_for(
            service_type='orchestration', endpoint_type='publicURL')
        log.debug('Signalling to %s' % endpoint)
        heat = heatclient.Client(
            '1', endpoint, token=ks.auth_token)
        r = heat.resources.signal(
            iv.get('deploy_stack_id'),
            iv.get('deploy_resource_name'),
            data=signal_data)
        log.debug('Response %s ' % r)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv, sys.stdin))
