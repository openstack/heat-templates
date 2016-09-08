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

import salt.cli.caller
import salt.config
from salt import exceptions
import yaml


WORKING_DIR = os.environ.get('HEAT_SALT_WORKING',
                             '/var/lib/heat-config/heat-config-salt')
SALT_MINION_CONFIG = os.environ.get('SALT_MINION_CONFIG',
                                    '/etc/salt/minion')


def prepare_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path, 0o700)


def main(argv=sys.argv):
    log = logging.getLogger('heat-config')
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            '[%(asctime)s] (%(name)s) [%(levelname)s] %(message)s'))
    log.addHandler(handler)
    log.setLevel('DEBUG')

    prepare_dir(WORKING_DIR)
    os.chdir(WORKING_DIR)

    c = json.load(sys.stdin)

    opts = salt.config.minion_config(SALT_MINION_CONFIG)

    opts['file_roots'] = {'base': [WORKING_DIR]}
    opts['file_client'] = 'local'
    opts['local'] = 'local'
    opts['fun'] = 'state.sls'
    opts['arg'] = [c['id']]

    for input in c['inputs']:
        key = input['name']
        opts[key] = input.get('value', '')

    state_file = '%s.sls' % c['id']
    config = c.get('config', '')

    if isinstance(config, dict):
        yaml_config = yaml.safe_dump(config, default_flow_style=False)
    else:
        yaml_config = config

    fn = os.path.join(WORKING_DIR, state_file)
    with os.fdopen(os.open(fn, os.O_CREAT | os.O_WRONLY, 0o700), 'w') as f:
        f.write(yaml_config.encode('utf-8'))

    caller = salt.cli.caller.Caller.factory(opts)

    log.debug('Applying Salt state %s' % state_file)

    stdout, stderr = None, None
    ret = {}

    try:
        ret = caller.call()
    except exceptions.SaltInvocationError as err:
        log.error(
            'Salt invocation error while applying Salt sate %s' % state_file)
        stderr = err

    if ret:

        log.info('Results: %s' % ret)
        output = yaml.safe_dump(ret['return'])

        # returncode of 0 means there were successful changes
        if ret['retcode'] == 0:
            log.info('Completed applying salt state %s' % state_file)
            stdout = output
        else:
            # Salt doesn't always return sane return codes so we have to check
            # individual results
            runfailed = False
            for state, data in ret['return'].items():
                if not data['result']:
                    runfailed = True
                    break
            if runfailed:
                log.error('Error applying Salt state %s. [%s]\n'
                          % (state_file, ret['retcode']))
                stderr = output
            else:
                ret['retcode'] = 0
                stdout = output

    response = {}

    for output in c.get('outputs', []):
        output_name = output['name']
        response[output_name] = ret.get(output_name)

    response.update({
        'deploy_stdout': stdout,
        'deploy_stderr': stderr,
        'deploy_status_code': ret['retcode'],
    })
    json.dump(response, sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
