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

APPLY_CONFIG_CMD = os.environ.get('HEAT_APPLY_CONFIG_CMD', 'os-apply-config')


def main(argv=sys.argv):
    log = logging.getLogger('heat-config')
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            '[%(asctime)s] (%(name)s) [%(levelname)s] %(message)s'))
    log.addHandler(handler)
    log.setLevel('DEBUG')

    env = os.environ.copy()

    log.debug('Running %s' % APPLY_CONFIG_CMD)
    subproc = subprocess.Popen([APPLY_CONFIG_CMD], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=env)
    stdout, stderr = subproc.communicate()

    log.info(stdout)
    log.debug(stderr)

    if subproc.returncode:
        log.error("Error running apply-config: [%s]\n" % subproc.returncode)
    else:
        log.info('Completed apply-config.')

    response = {
        'deploy_stdout': stdout,
        'deploy_stderr': stderr,
        'deploy_status_code': subproc.returncode,
    }

    json.dump(response, sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
