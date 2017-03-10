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

import ast
import dpath
import json
import logging
import os
import subprocess
import sys
import yaml


WORKING_DIR = os.environ.get('HEAT_DOCKER_COMPOSE_WORKING',
                             '/var/lib/heat-config/heat-config-docker-compose')

DOCKER_COMPOSE_CMD = os.environ.get('HEAT_DOCKER_COMPOSE_CMD',
                                    'docker-compose')


def prepare_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path, 0o700)


def write_input_file(file_path, content):
    prepare_dir(os.path.dirname(file_path))
    with os.fdopen(os.open(
            file_path, os.O_CREAT | os.O_WRONLY, 0o600), 'w') as f:
        f.write(content.encode('utf-8'))


def build_response(deploy_stdout, deploy_stderr, deploy_status_code):
    return {
        'deploy_stdout': deploy_stdout,
        'deploy_stderr': deploy_stderr,
        'deploy_status_code': deploy_status_code,
    }


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

    proj = os.path.join(WORKING_DIR, c.get('name'))
    prepare_dir(proj)

    stdout, stderr = {}, {}

    if input_values.get('deploy_action') == 'DELETE':
        json.dump(build_response(stdout, stderr, 0), sys.stdout)
        return

    config = c.get('config', '')
    if not config:
        log.debug("No 'config' input found, nothing to do.")
        json.dump(build_response(stdout, stderr, 0), sys.stdout)
        return

    # convert config to dict
    if not isinstance(config, dict):
        config = ast.literal_eval(json.dumps(yaml.safe_load(config)))

    os.chdir(proj)

    compose_env_files = []
    for value in dpath.util.values(config, '*/env_file'):
        if isinstance(value, list):
            compose_env_files.extend(value)
        elif isinstance(value, basestring):
            compose_env_files.extend([value])

    input_env_files = {}
    if input_values.get('env_files'):
        input_env_files = dict(
            (i['file_name'], i['content'])
            for i in ast.literal_eval(input_values.get('env_files')))

    for file in compose_env_files:
        if file in input_env_files.keys():
            write_input_file(file, input_env_files.get(file))

    cmd = [
        DOCKER_COMPOSE_CMD,
        'up',
        '-d',
        '--no-build',
    ]

    log.debug('Running %s' % cmd)

    subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = subproc.communicate()

    log.debug(stdout)
    log.debug(stderr)

    if subproc.returncode:
        log.error("Error running %s. [%s]\n" % (cmd, subproc.returncode))
    else:
        log.debug('Completed %s' % cmd)

    json.dump(build_response(stdout, stderr, subproc.returncode), sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
