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
import shutil
import six
import subprocess
import sys

DEPLOY_KEYS = ("deploy_server_id",
               "deploy_action",
               "deploy_stack_id",
               "deploy_resource_name",
               "deploy_signal_transport",
               "deploy_signal_id",
               "deploy_signal_verb")
WORKING_DIR = os.environ.get('HEAT_CHEF_WORKING',
                             '/var/lib/heat-config/heat-config-chef')
OUTPUTS_DIR = os.environ.get('HEAT_CHEF_OUTPUTS',
                             '/var/run/heat-config/heat-config-chef')


def prepare_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path, 0o700)


def run_subproc(fn, **kwargs):
    env = os.environ.copy()
    for k, v in kwargs.items():
        env[six.text_type(k)] = v
    try:
        subproc = subprocess.Popen(fn, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   env=env)
        stdout, stderr = subproc.communicate()
    except OSError as exc:
        ret = -1
        stderr = six.text_type(exc)
        stdout = ""
    else:
        ret = subproc.returncode
    if not ret:
        ret = 0
    return ret, stdout, stderr


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

    client_config = ("log_level :debug\n"
                     "log_location STDOUT\n"
                     "local_mode true\n"
                     "chef_zero.enabled true")

    # configure/set up the kitchen
    kitchen = c['options'].get('kitchen')
    kitchen_path = c['options'].get('kitchen_path', os.path.join(WORKING_DIR,
                                                                 "kitchen"))
    cookbook_path = os.path.join(kitchen_path, "cookbooks")
    role_path = os.path.join(kitchen_path, "roles")
    environment_path = os.path.join(kitchen_path, "environments")
    client_config += "\ncookbook_path '%s'" % cookbook_path
    client_config += "\nrole_path '%s'" % role_path
    client_config += "\nenvironment_path '%s'" % environment_path
    if kitchen:
        log.debug("Cloning kitchen from %s", kitchen)
        # remove the existing kitchen on update so we get a fresh clone
        dep_action = next((input['value'] for input in c['inputs']
                           if input['name'] == "deploy_action"), None)
        if dep_action == "UPDATE":
            shutil.rmtree(kitchen_path, ignore_errors=True)
        cmd = ["git", "clone", kitchen, kitchen_path]
        ret, out, err = run_subproc(cmd)
        if ret != 0:
            log.error("Error cloning kitchen from %s into %s: %s", kitchen,
                      kitchen_path, err)
            json.dump({'deploy_status_code': ret,
                       'deploy_stdout': out,
                       'deploy_stderr': err},
                      sys.stdout)
            return 0

    # write the json attributes
    ret, out, err = run_subproc(['hostname', '-f'])
    if ret == 0:
        fqdn = out.strip()
    else:
        err = "Could not determine hostname with hostname -f"
        json.dump({'deploy_status_code': ret,
                   'deploy_stdout': "",
                   'deploy_stderr': err}, sys.stdout)
        return 0
    node_config = {}
    for input in c['inputs']:
        if input['name'] == 'environment':
            client_config += "\nenvironment '%s'" % input['value']
        elif input['name'] not in DEPLOY_KEYS:
            node_config.update({input['name']: input['value']})
    node_config.update({"run_list": json.loads(c['config'])})
    node_path = os.path.join(WORKING_DIR, "node")
    prepare_dir(node_path)
    node_file = os.path.join(node_path, "%s.json" % fqdn)
    with os.fdopen(os.open(node_file, os.O_CREAT | os.O_WRONLY, 0o600),
                   'w') as f:
        f.write(json.dumps(node_config, indent=4))
    client_config += "\nnode_path '%s'" % node_path

    # write out the completed client config
    config_path = os.path.join(WORKING_DIR, "client.rb")
    with os.fdopen(os.open(config_path, os.O_CREAT | os.O_WRONLY, 0o600),
                   'w') as f:
        f.write(client_config)

    # run chef
    heat_outputs_path = os.path.join(OUTPUTS_DIR, c['id'])
    cmd = ['chef-client', '-z', '--config', config_path, "-j", node_file]
    ret, out, err = run_subproc(cmd, heat_outputs_path=heat_outputs_path)
    resp = {'deploy_status_code': ret,
            'deploy_stdout': out,
            'deploy_stderr': err}
    log.debug("Chef output: %s", out)
    if err:
        log.error("Chef return code %s:\n%s", ret, err)
    for output in c.get('outputs', []):
        output_name = output['name']
        try:
            with open('%s.%s' % (heat_outputs_path, output_name)) as out:
                resp[output_name] = out.read()
        except IOError:
            pass
    json.dump(resp, sys.stdout)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
