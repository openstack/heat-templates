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
import re
import subprocess
import sys


WORKING_DIR = os.environ.get('HEAT_PUPPET_WORKING',
                             '/var/lib/heat-config/heat-config-puppet')
OUTPUTS_DIR = os.environ.get('HEAT_PUPPET_OUTPUTS',
                             '/var/run/heat-config/heat-config-puppet')
PUPPET_CMD = os.environ.get('HEAT_PUPPET_CMD', 'puppet')
PUPPET_LOGDIR = os.environ.get(
    'HEAT_PUPPET_LOGDIR', '/var/run/heat-config/deployed'
)
HIERA_DATADIR = os.environ.get('HEAT_PUPPET_HIERA_DATADIR',
                               '/etc/puppet/hieradata')


def prepare_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path, 0o700)


def get_hostname_f(log):
    subproc = subprocess.Popen(['hostname', '-f'], stdout=subprocess.PIPE)
    out = subproc.communicate()[0]
    if subproc.returncode == 0:
        return out.strip()
    else:
        log.warn("Failed to retrieve 'hostname -f' output")
        return None


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

    use_hiera = c['options'].get('enable_hiera', False)
    use_facter = c['options'].get('enable_facter', True)
    modulepath = c['options'].get('modulepath')
    tags = c['options'].get('tags')
    debug = c['options'].get('enable_debug', False)
    verbose = c['options'].get('enable_verbose', False)

    facts = {}
    hiera = {}

    fqdn = get_hostname_f(log)
    if fqdn:
        facts['FACTER_fqdn'] = fqdn

    for input in c['inputs']:
        input_name = input['name']
        input_value = input.get('value', '')
        if use_facter:
            fact_name = 'FACTER_%s' % input_name
            facts[fact_name] = input_value
        if use_hiera:
            hiera[input_name] = input_value

    if use_hiera:
        prepare_dir(HIERA_DATADIR)
        hiera_data = os.path.join(HIERA_DATADIR,
                                  'heat_config_%s.json' % c['name'])
        with os.fdopen(os.open(hiera_data,
                               os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600),
                       'w') as hiera_file:
            hiera_file.write(json.dumps(hiera).encode('utf8'))
        facts['FACTER_deploy_config_name'] = c['name']

    fn = os.path.join(WORKING_DIR, '%s.pp' % c['id'])
    heat_outputs_path = os.path.join(OUTPUTS_DIR, c['id'])
    facts['FACTER_heat_outputs_path'] = heat_outputs_path

    env_debug = ' '.join('%s="%s" ' % (k, v) for k, v in facts.items())

    env = os.environ.copy()
    env.update(facts)

    with os.fdopen(os.open(fn, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o700),
                   'w') as f:
        f.write(c.get('config', '').encode('utf-8'))

    cmd = [PUPPET_CMD, 'apply', '--detailed-exitcodes', fn]
    # This is the default log destination to print out to the console and
    # captured by heat via the subprocess method below.
    cmd.insert(-1, '--logdest')
    cmd.insert(-1, 'console')
    if modulepath:
        cmd.insert(-1, '--modulepath')
        cmd.insert(-1, modulepath)
    if tags:
        cmd.insert(-1, '--tags')
        cmd.insert(-1, tags)
    if debug:
        cmd.insert(-1, '--debug')
        cmd.insert(-1, '--logdest')
        cmd.insert(-1, '/var/log/puppet/heat-debug.log')
    if verbose:
        cmd.insert(-1, '--verbose')
        cmd.insert(-1, '--logdest')
        cmd.insert(-1, '/var/log/puppet/heat-verbose.log')

    prepare_dir(PUPPET_LOGDIR)
    timestamp = re.sub('[:T]', '-', c['creation_time'])
    base_path = os.path.join(
        PUPPET_LOGDIR, '{timestamp}-{c[id]}'.format(**locals())
    )
    stdout_log = open('{0}-stdout.log'.format(base_path), 'w')
    stderr_log = open('{0}-stderr.log'.format(base_path), 'w')
    log.debug('Running %s %s' % (env_debug, ' '.join(cmd)))
    try:
        subproc = subprocess.Popen(
            cmd, stdout=stdout_log, stderr=stderr_log, env=env
        )
        subproc.wait()
    except OSError:
        log.warn('puppet not installed yet')
        return
    finally:
        stdout_log.close()
        stderr_log.close()

    log.info('Return code %s' % subproc.returncode)
    response = {}
    for i in 'stdout', 'stderr':
        with open('{0}-{1}.log'.format(base_path, i)) as logfile:
            content = logfile.read()
        if content.strip():
            log.info(content)
        response['deploy_{0}'.format(i)] = content

    # returncode of 2 means there were successful changes
    if subproc.returncode in (0, 2):
        returncode = 0
        log.info('Completed %s' % fn)
    else:
        returncode = subproc.returncode
        log.error("Error running %s. [%s]\n" % (fn, subproc.returncode))

    for output in c.get('outputs') or []:
        output_name = output['name']
        try:
            with open('%s.%s' % (heat_outputs_path, output_name)) as out:
                response[output_name] = out.read()
        except IOError:
            pass

    response.update({
        'deploy_status_code': returncode,
    })
    json.dump(response, sys.stdout)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
