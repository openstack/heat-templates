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


# Ideally this path would be /var/lib/heat-cfntools/cfn-init-data
# but this is where all boot metadata is stored
LAST_METADATA_DIR = os.environ.get('HEAT_CFN_INIT_LAST_METADATA_DIR',
                                   '/var/cache/heat-cfntools')


CFN_INIT_CMD = os.environ.get('HEAT_CFN_INIT_CMD',
                              'cfn-init')


def main(argv=sys.argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    log = logging.getLogger('heat-config')
    handler = logging.StreamHandler(stderr)
    handler.setFormatter(
        logging.Formatter(
            '[%(asctime)s] (%(name)s) [%(levelname)s] %(message)s'))
    log.addHandler(handler)
    log.setLevel('DEBUG')

    c = json.load(stdin)

    config = c.get('config', {})
    if not isinstance(config, dict):
        config = json.loads(config)
    meta = {'AWS::CloudFormation::Init': config}

    if not os.path.isdir(LAST_METADATA_DIR):
        os.makedirs(LAST_METADATA_DIR, 0o700)

    fn = os.path.join(LAST_METADATA_DIR, 'last_metadata')
    with os.fdopen(os.open(fn, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o700),
                   'w') as f:
        json.dump(meta, f)

    log.debug('Running %s' % CFN_INIT_CMD)
    subproc = subprocess.Popen([CFN_INIT_CMD], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    cstdout, cstderr = subproc.communicate()

    if cstdout:
        log.info(cstdout)
    if cstderr:
        log.info(cstderr)

    if subproc.returncode:
        log.error("Error running %s. [%s]\n" % (
            CFN_INIT_CMD, subproc.returncode))
    else:
        log.info('Completed %s' % CFN_INIT_CMD)

    response = {
        'deploy_stdout': cstdout,
        'deploy_stderr': cstderr,
        'deploy_status_code': subproc.returncode,
    }

    json.dump(response, stdout)


if __name__ == '__main__':
    sys.exit(main())
