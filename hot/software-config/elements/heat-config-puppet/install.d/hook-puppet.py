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

WORKING_DIR = os.environ.get('HEAT_PUPPET_WORKING',
                             '/var/lib/heat-config/heat-config-puppet')
OUTPUTS_DIR = os.environ.get('HEAT_PUPPET_OUTPUTS',
                             '/var/run/heat-config/heat-config-puppet')
PUPPET_CMD = os.environ.get('HEAT_PUPPET_CMD', 'puppet')


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

    facts = {}
    for input in c['inputs']:
        input_name = input['name']
        fact_name = 'FACTER_%s' % input_name
        facts[fact_name] = input.get('value', '')

    fn = os.path.join(WORKING_DIR, '%s.pp' % c['id'])
    heat_outputs_path = os.path.join(OUTPUTS_DIR, c['id'])
    facts['FACTER_heat_outputs_path'] = heat_outputs_path

    env_debug = ' '.join('%s="%s" ' % (k, v) for k, v in facts.items())

    env = os.environ.copy()
    env.update(facts)

    with os.fdopen(os.open(fn, os.O_CREAT | os.O_WRONLY, 0o700), 'w') as f:
        f.write(c.get('config', '').encode('utf-8'))

    cmd = [PUPPET_CMD, 'apply', '--detailed-exitcodes', fn]
    log.debug('Running %s %s' % (env_debug, ' '.join(cmd)))
    try:
        subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=env)
    except OSError:
        log.warn('puppet not installed yet')
        return
    stdout, stderr = subproc.communicate()

    log.info('Return code %s' % subproc.returncode)
    if stdout:
        log.info(stdout)
    if stderr:
        log.info(stderr)

    # returncode of 2 means there were successfull changes
    if subproc.returncode in (0, 2):
        returncode = 0
        log.info('Completed %s' % fn)
    else:
        returncode = subproc.returncode
        log.error("Error running %s. [%s]\n" % (fn, subproc.returncode))

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
        'deploy_status_code': returncode,
    })

    json.dump(response, sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
