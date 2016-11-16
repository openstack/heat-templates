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
'''
A fake config tool for unit testing the software-config hooks.

JSON containing the current environment variables and command line arguments
are written to the file specified by the path in environment variable
TEST_STATE_PATH.

Environment variable TEST_RESPONSE defines JSON specifying what files to write
out, and what to print to stdout and stderr.
'''

import json
import os
import sys


def main(argv=sys.argv):

    state_path = os.environ.get('TEST_STATE_PATH')

    # handle multiple invocations by writing to numbered state path files
    suffix = 0
    while os.path.isfile(state_path):
        suffix += 1
        state_path = '%s_%s' % (os.environ.get('TEST_STATE_PATH'), suffix)

    with open(state_path, 'w') as f:
        json.dump({'env': dict(os.environ), 'args': argv}, f)

    if 'TEST_RESPONSE' not in os.environ:
        return

    response = json.loads(os.environ.get('TEST_RESPONSE'))
    for k, v in response.get('files', {}).iteritems():
        open(k, 'w')
        with open(k, 'w') as f:
            f.write(v)

    sys.stdout.write(response.get('stdout', ''))
    sys.stderr.write(response.get('stderr', ''))
    return response.get('returncode', 0)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
