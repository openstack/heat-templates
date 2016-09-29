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


HIERA_DATADIR = os.environ.get('HEAT_PUPPET_HIERA_DATADIR',
                               '/etc/puppet/hieradata')
HIERA_CONFIG = os.environ.get('HEAT_HIERA_CONFIG', '/etc/puppet/hiera.yaml')

HIERA_CONFIG_BASE = """
---
:backends:
  - json
:json:
  :datadir: %(datadir)s
:hierarchy:
""" % {'datadir': HIERA_DATADIR}


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

    c = json.load(sys.stdin)['config']

    prepare_dir(HIERA_DATADIR)

    hiera_config_file = os.path.join(HIERA_CONFIG)

    # allow the end user to order the hiera config as they wish
    if 'hierarchy' in c:
        with os.fdopen(os.open(hiera_config_file,
                               os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600),
                       'w') as config_file:
            config_file.write(HIERA_CONFIG_BASE)
            for item in c['hierarchy']:
                config_file.write('  - %s\n' % item)

    # write out the datafiles as YAML
    if 'datafiles' in c:
        for name, data in c['datafiles'].iteritems():
            hiera_data = os.path.join(HIERA_DATADIR, '%s.json' % name)
            with os.fdopen(os.open(hiera_data,
                                   os.O_CREAT | os.O_TRUNC | os.O_WRONLY,
                                   0o600),
                           'w') as hiera_data_file:
                json.dump(data, hiera_data_file, indent=4, sort_keys=True)

    response = {
        'deploy_stdout': '',
        'deploy_stderr': '',
        'deploy_status_code': 0,
    }

    json.dump(response, sys.stdout)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
