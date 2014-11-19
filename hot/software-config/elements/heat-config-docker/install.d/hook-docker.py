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

import docker
import yaml


DOCKER_BASE_URL = os.environ.get('DOCKER_HOST',
                                 'unix:///var/run/docker.sock')


def is_running(client, container_id):
    container_info = get_container_info(client, container_id)
    if container_info:
        return container_info.get('State', {}).get('Running')
    return False


def remove_container(client, container_id):
        if is_running(client, container_id):
            client.kill(container_id)
        client.remove_container(container_id, False)


def build_container_name(pod_name, container_name):
    return pod_name + '.' + container_name


def remove_all_containers_for_pod(client, pod_name):
    containers = client.containers(all=True)
    for x in containers:
        if pod_name in x['Names'][0]:
            remove_container(client, x['Id'])


def get_container_info(client, container):
    return client.inspect_container(container)


def pull_image(client, image):
    try:
        client.inspect_image(image)
    except Exception:
        client.pull(image, tag=None)


def get_client():
    kwargs = {}
    kwargs['base_url'] = DOCKER_BASE_URL
    client = docker.Client(**kwargs)
    client._version = client.version()['ApiVersion']
    return client


def volume_exists(volumes, volume_mount):
    for volume in volumes:
        if volume_mount['name'] == volume['name']:
            return True
    return False


def make_binds(volume_mounts, volumes):
    binds = {}
    mountpoints = {}
    if isinstance(volume_mounts, list):
        for volume_mount in volume_mounts:
            if volume_exists(volumes, volume_mount):
                b = {}
                if volume_mount['mountPath']:
                    b['bind'] = volume_mount['mountPath']
                else:
                    b['bind'] = volume_mount['name']
                mountpoints[b['bind']] = {}
                if volume_mount['readOnly']:
                    b['ro'] = True
                binds[get_path('/', volume_mount['name'])] = b
    return mountpoints, binds


def make_env_vars(env):
    env_vars = {}
    for e in env:
        env_vars[e['name']] = e['value']
    return env_vars


def get_path(root_dir, vol_name):
    return root_dir + vol_name


def mount_external_volumes(volumes):
    root_dir = '/'
    for vol in volumes:
        vol_path = get_path(root_dir, vol['name'])
        if not os.path.exists(vol_path):
            os.makedirs(vol_path)


def make_port_bindings(client, container_id, ports):
    if not is_running(client, container_id):
        bindings = {}
        if isinstance(ports, list):
            for port in ports:
                if port['hostPort']:
                    exposed_port = port['hostPort']
                else:
                    exposed_port = port['containerPort']
                bindings[port['containerPort']] = exposed_port
    return bindings


def update_pod_state(pod_state, is_container_running):
    if pod_state == 0 and is_container_running:
        return 0  # pod without error
    else:
        return 1  # pod with error


def main(argv=sys.argv):
    log = logging.getLogger('heat-config')
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            '[%(asctime)s] (%(name)s) [%(levelname)s] %(message)s'))
    log.addHandler(handler)
    log.setLevel('DEBUG')

    c = json.load(sys.stdin)

    client = get_client()
    pod_name = c.get('name')

    config = c.get('config')
    log.debug('Received Config %s' % config)

    if isinstance(config, dict):
        yaml_config = config
    else:
        yaml_config = yaml.load(config)

    containers = yaml_config.get('containers')
    volumes = yaml_config.get('volumes')

    remove_all_containers_for_pod(client, pod_name)

    mount_external_volumes(volumes)

    stdout, stderr = {}, {}

    pod_state = 0

    for container in containers:
        image = container.get('image')
        name = container.get('name')
        command = container.get('command')
        working_dir = container.get('workingDir')
        volume_mounts = container.get('volumeMounts')
        ports = container.get('ports')
        env_vars = make_env_vars(container.get('env'))

        container_id = None
        log.debug('Pulling docker image %s.' % image)

        try:
            log.debug('Pulling docker image %s.' % image)
            pull_image(client, image)

            log.debug('Making volume bindings.')

            mountpoints, binds = make_binds(volume_mounts, volumes)

            container_info = client.create_container(
                image=image,
                command=command,
                working_dir=working_dir,
                ports=ports,
                environment=env_vars,
                volumes=mountpoints,
                name=build_container_name(pod_name, name)
            )

            log.debug('Container created for image: %s, container info: %s.'
                      % (image, container_info))

            container_id = container_info['Id']

            log.debug('Building volume mounts.')
            bindings = make_port_bindings(client, container_id, ports)

            if not is_running(client, container_id):
                client.start(container_id,
                             binds=binds,
                             port_bindings=bindings)

                log.debug('Started Container %s.' % container_id)

            stdout[container_id] = get_container_info(client, container_id)
            pod_state = update_pod_state(pod_state, True)

        except Exception as ex:
            log.error('An error occurred deploying container %s with error %s.'
                      % (image, ex))
            if container_id:
                stderr[container_id] = ex
            else:
                stderr[image] = ex
            pod_state = update_pod_state(pod_state, False)
            remove_all_containers_for_pod(client, pod_name)

    response = {
        'deploy_stdout': stdout,
        'deploy_stderr': stderr,
        'deploy_status_code': pod_state,
    }
    json.dump(response, sys.stdout)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
