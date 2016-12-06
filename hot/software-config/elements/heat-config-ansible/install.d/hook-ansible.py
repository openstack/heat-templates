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

WORKING_DIR = os.environ.get('HEAT_ANSIBLE_WORKING',
                             '/var/lib/heat-config/heat-config-ansible')
OUTPUTS_DIR = os.environ.get('HEAT_ANSIBLE_OUTPUTS',
                             '/var/run/heat-config/heat-config-ansible')
ANSIBLE_CMD = os.environ.get('HEAT_ANSIBLE_CMD', 'ansible-playbook')
ANSIBLE_INVENTORY = os.environ.get('HEAT_ANSIBLE_INVENTORY', 'localhost,')


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

    variables = {}
    for input in c['inputs']:
        variables[input['name']] = input.get('value', '')

    tags = c['options'].get('tags')

    fn = os.path.join(WORKING_DIR, '%s_playbook.yaml' % c['id'])
    vars_filename = os.path.join(WORKING_DIR, '%s_variables.json' % c['id'])
    heat_outputs_path = os.path.join(OUTPUTS_DIR, c['id'])
    variables['heat_outputs_path'] = heat_outputs_path

    config_text = c.get('config', '')
    if not config_text:
        log.warn("No 'config' input found, nothing to do.")
        return
    # Write 'variables' to file
    with os.fdopen(os.open(
            vars_filename, os.O_CREAT | os.O_WRONLY, 0o600), 'w') as var_file:
        json.dump(variables, var_file)
    # Write the executable, 'config', to file
    with os.fdopen(os.open(fn, os.O_CREAT | os.O_WRONLY, 0o600), 'w') as f:
        f.write(c.get('config', '').encode('utf-8'))

    cmd = [
        ANSIBLE_CMD,
        '-i',
        ANSIBLE_INVENTORY,
        fn,
        '--extra-vars',
        '@%s' % vars_filename
    ]
    if tags:
        cmd.insert(3, '--tags')
        cmd.insert(4, tags)
    log.debug('Running %s' % (' '.join(cmd),))
    try:
        subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except OSError:
        log.warn("ansible not installed yet")
        return
    stdout, stderr = subproc.communicate()

    log.info('Return code %s' % subproc.returncode)
    if stdout:
        log.info(stdout)
    if stderr:
        log.info(stderr)

    # TODO(stevebaker): Test if ansible returns any non-zero
    # return codes in success.
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
