#!/usr/bin/env python
import json
import logging
import os
import salt.cli
import salt.config
import sys
import yaml

from salt.exceptions import SaltInvocationError


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
        f.write(yaml_config)

    caller = salt.cli.caller.Caller(opts)

    log.debug('Applying Salt state %s' % state_file)

    stdout, stderr = None, None

    try:
        ret = caller.call()
    except SaltInvocationError as err:
        log.error(
            'Salt invocation error while applying Salt sate %s' % state_file)
        stderr = err
    log.info('Return code %s' % ret['retcode'])

    # returncode of 0 means there were successfull changes
    if ret['retcode'] == 0:
        log.info('Completed applying salt state %s' % state_file)
        stdout = ret
    else:
        log.error('Error applying Salt state %s. [%s]\n'
                  % (state_file, ret['retcode']))
        stderr = ret

    response = {}

    for output in c.get('outputs') or []:
        output_name = output['name']
        response[output_name] = ret[output_name]

    response.update({
        'deploy_stdout': stdout,
        'deploy_stderr': stderr,
        'deploy_status_code': ret['retcode'],
    })
    json.dump(response, sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
