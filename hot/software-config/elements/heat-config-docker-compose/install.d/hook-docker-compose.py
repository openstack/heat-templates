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


WORKING_DIR = os.environ.get('HEAT_DOCKER_COMPOSE_WORKING',
                             '/var/lib/heat-config/heat-config-docker-compose')

DOCKER_COMPOSE_CMD = os.environ.get('HEAT_DOCKER_COMPOSE_CMD',
                                    'docker-compose')


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

    c = json.load(sys.stdin)

    input_values = dict((i['name'], i['value']) for i in c['inputs'])

    proj = os.path.join(WORKING_DIR, c.get('id'))
    prepare_dir(proj)

    stdout, stderr = {}, {}

    if input_values.get('deploy_action') == 'DELETE':
        response = {
            'deploy_stdout': stdout,
            'deploy_stderr': stderr,
            'deploy_status_code': 0,
        }
        json.dump(response, sys.stdout)
        return

    config = c.get('config', '')
    if not config:
        log.debug("No 'config' input found, nothing to do.")
        response = {
            'deploy_stdout': stdout,
            'deploy_stderr': stderr,
            'deploy_status_code': 0,
        }
        json.dump(response, sys.stdout)
        return

    cmd = [
        DOCKER_COMPOSE_CMD,
        'up',
        '-d',
        '--no-build',
    ]

    log.debug('Running %s' % cmd)

    os.chdir(proj)

    subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = subproc.communicate()

    log.debug(stdout)
    log.debug(stderr)

    if subproc.returncode:
        log.error("Error running %s. [%s]\n" % (cmd, subproc.returncode))
    else:
        log.debug('Completed %s' % cmd)

    response = {}

    response.update({
        'deploy_stdout': stdout,
        'deploy_stderr': stderr,
        'deploy_status_code': subproc.returncode,
    })

    json.dump(response, sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
