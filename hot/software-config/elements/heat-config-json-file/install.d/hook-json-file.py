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

    for fname in c.keys():
        prepare_dir(os.path.dirname(fname))
        data = c.get(fname)
        with open(fname, 'w') as json_data_file:
            json.dump(data, json_data_file, indent=4, sort_keys=True)

    response = {
        'deploy_stdout': '',
        'deploy_stderr': '',
        'deploy_status_code': 0,
    }

    json.dump(response, sys.stdout)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
