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
import subprocess
import sys

WORKING_DIR = os.environ.get('HEAT_SCRIPT_WORKING',
                             '/var/lib/heat-config/heat-config-script')
OUTPUTS_DIR = os.environ.get('HEAT_SCRIPT_OUTPUTS',
                             '/var/run/heat-config/heat-config-script')


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

    prepare_dir(OUTPUTS_DIR)
    prepare_dir(WORKING_DIR)
    os.chdir(WORKING_DIR)

    c = json.load(sys.stdin)

    env = os.environ.copy()
    for input in c['inputs']:
        input_name = input['name']
        value = input.get('value', '')
        if isinstance(value, dict) or isinstance(value, list):
            env[input_name] = json.dumps(value)
        else:
            env[input_name] = value
        log.info('%s=%s' % (input_name, env[input_name]))

    fn = os.path.join(WORKING_DIR, c['id'])
    heat_outputs_path = os.path.join(OUTPUTS_DIR, c['id'])
    env['heat_outputs_path'] = heat_outputs_path

    with os.fdopen(os.open(fn, os.O_CREAT | os.O_WRONLY, 0o700), 'w') as f:
        f.write(c.get('config', '').encode('utf-8'))

    log.debug('Running %s' % fn)
    subproc = subprocess.Popen([fn], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=env)
    stdout, stderr = subproc.communicate()

    log.info(stdout)
    log.debug(stderr)

    if subproc.returncode:
        log.error("Error running %s. [%s]\n" % (fn, subproc.returncode))
    else:
        log.info('Completed %s' % fn)

    response = {}

    for output in c.get('outputs') or []:
        output_name = output['name']
        try:
            with open('%s.%s' % (heat_outputs_path, output_name)) as out:
                response[output_name] = out.read()
        except IOError:
            pass

    response.update({
        'deploy_stdout': stdout,
        'deploy_stderr': stderr,
        'deploy_status_code': subproc.returncode,
    })

    json.dump(response, sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
