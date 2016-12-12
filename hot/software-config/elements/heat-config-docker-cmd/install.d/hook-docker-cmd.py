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
import yaml


DOCKER_CMD = os.environ.get('HEAT_DOCKER_CMD', 'docker')


log = None


def build_response(deploy_stdout, deploy_stderr, deploy_status_code):
    return {
        'deploy_stdout': deploy_stdout,
        'deploy_stderr': deploy_stderr,
        'deploy_status_code': deploy_status_code,
    }


def docker_arg_map(key, value):
    value = str(value).encode('ascii', 'ignore')
    return {
        'container_step_config': None,
        'environment': "--env=%s" % value,
        'image': value,
        'net': "--net=%s" % value,
        'pid': "--pid=%s" % value,
        'privileged': "--privileged=%s" % 'true' if value else 'false',
        'restart': "--restart=%s" % value,
        'user': "--user=%s" % value,
        'volumes': "--volume=%s" % value,
        'volumes_from': "--volumes-from=%s" % value,
    }.get(key, None)


def main(argv=sys.argv):
    global log
    log = logging.getLogger('heat-config')
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            '[%(asctime)s] (%(name)s) [%(levelname)s] %(message)s'))
    log.addHandler(handler)
    log.setLevel('DEBUG')

    c = json.load(sys.stdin)

    input_values = dict((i['name'], i['value']) for i in c.get('inputs', {}))

    if input_values.get('deploy_action') == 'DELETE':
        json.dump(build_response(
            '', '', 0), sys.stdout)
        return

    config = c.get('config', '')
    if not config:
        log.debug("No 'config' input found, nothing to do.")
        json.dump(build_response(
            '', '', 0), sys.stdout)
        return

    stdout = []
    stderr = []
    deploy_status_code = 0

    # convert config to dict
    if not isinstance(config, dict):
        config = yaml.safe_load(config)

    for container in sorted(config):
        container_name = '%s__%s' % (c['name'], container)
        cmd = [
            DOCKER_CMD,
            'run',
            '--detach=true',
            '--name',
            container_name.encode('ascii', 'ignore'),
        ]
        image_name = ''
        for key in sorted(config[container]):
            # These ones contain a list of values
            if key in ['environment', 'volumes', 'volumes_from']:
                for value in config[container][key]:
                    # Somehow the lists get empty values sometimes
                    if type(value) is unicode and not value.strip():
                        continue
                    cmd.append(docker_arg_map(key, value))
            elif key == 'image':
                image_name = config[container][key].encode('ascii', 'ignore')
            else:
                arg = docker_arg_map(key, config[container][key])
                if arg:
                    cmd.append(arg)

        # Image name must come last.
        cmd.append(image_name)

        log.debug(' '.join(cmd))
        subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        cmd_stdout, cmd_stderr = subproc.communicate()
        log.debug(cmd_stdout)
        log.debug(cmd_stderr)
        if cmd_stdout:
            stdout.append(cmd_stdout)
        if cmd_stderr:
            stderr.append(cmd_stderr)

        if subproc.returncode:
            log.error("Error running %s. [%s]\n" % (cmd, subproc.returncode))
        else:
            log.debug('Completed %s' % cmd)

        if subproc.returncode != 0:
            deploy_status_code = subproc.returncode

    json.dump(build_response(
        '\n'.join(stdout), '\n'.join(stderr), deploy_status_code), sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
