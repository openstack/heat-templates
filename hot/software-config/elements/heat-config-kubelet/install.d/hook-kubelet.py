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

import cStringIO
import json
import logging
import os
import re
import six
import sys
import time

try:
    import docker
except ImportError:
    docker = None


DOCKER_BASE_URL = os.environ.get('DOCKER_HOST',
                                 'unix:///var/run/docker.sock')


DEFAULT_IMAGES_TIMEOUT = 600


DEFAULT_CONTAINERS_TIMEOUT = 120


DEFAULT_POLL_PERIOD = 5


def get_client(log):
    kwargs = {}
    kwargs['base_url'] = DOCKER_BASE_URL
    log.debug('Connecting to %s' % DOCKER_BASE_URL)
    client = docker.Client(**kwargs)
    client._version = client.version()['ApiVersion']
    log.debug('Connected to version %s' % client._version)
    return client


def id_to_pod_name_part(config_id):
    return config_id.replace('-', '')[:15]


def container_pattern(config_id, container_name):
    return '^/k8s_%s\.[0-9a-z]{8}_%s' % (
        container_name, id_to_pod_name_part(config_id))


def required_images(c):
    containers = c['config'].get('containers', [])
    return set(container['image'] for container in containers)


def required_container_patterns(c):
    config_id = c['id']
    containers = c['config'].get('containers', [])
    return dict((container['name'], container_pattern(
        config_id, container['name'])) for container in containers)


def configure_logging():
    log = logging.getLogger('heat-config')
    log.setLevel('DEBUG')
    formatter = logging.Formatter(
        '[%(asctime)s] (%(name)s) [%(levelname)s] %(message)s')

    # debug log to stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    log.addHandler(handler)

    deploy_stdout = cStringIO.StringIO()
    handler = logging.StreamHandler(deploy_stdout)
    handler.setFormatter(formatter)
    handler.setLevel('DEBUG')
    log.addHandler(handler)

    deploy_stderr = cStringIO.StringIO()
    handler = logging.StreamHandler(deploy_stderr)
    handler.setFormatter(formatter)
    handler.setLevel('WARN')
    log.addHandler(handler)

    return log, deploy_stdout, deploy_stderr


def wait_required_images(client, log, images_timeout, poll_period, images):
    log.info(
        'Waiting for images: %s' % ', '.join(images))
    timeout = time.time() + images_timeout

    def image_prefixes(images):
        for image in images:
            if ':' in image:
                yield image
            else:
                yield '%s:' % image

    matching_prefixes = list(image_prefixes(images))

    def image_names(all_images):
        for image in all_images:
            for name in image['RepoTags']:
                yield name

    while matching_prefixes:
        all_images = list(image_names(client.images()))
        for image_prefix in matching_prefixes:
            for image in all_images:
                if image.startswith(image_prefix):
                    log.info('Found image: %s' % image)
                    matching_prefixes.remove(image_prefix)

        if time.time() > timeout:
            raise Exception('Timed out after %s seconds waiting for '
                            'matching images: %s' % (
                                images_timeout,
                                ', '.join(matching_prefixes)))
        if poll_period:
            time.sleep(poll_period)


def wait_required_containers(client, log,
                             containers_timeout, poll_period,
                             container_patterns):
    patterns = container_patterns.values()
    log.info(
        'Waiting for containers matching: %s' % ', '.join(patterns))

    timeout = time.time() + containers_timeout

    def containers_names(containers):
        for container in containers:
            for name in container['Names']:
                yield name

    waiting_for = dict((v, re.compile(v)) for v in patterns)
    while waiting_for:
        for name in containers_names(client.containers()):
            for k, v in six.iteritems(waiting_for):
                if v.match(name):
                    log.info('Pattern %s matches: %s' % (k, name))
                    del(waiting_for[k])
                    break
        if time.time() > timeout:
            raise Exception('Timed out after %s seconds waiting for '
                            'matching containers: %s' % (
                                containers_timeout,
                                ', '.join(waiting_for.keys)))
        if poll_period:
            time.sleep(poll_period)


def main(argv=sys.argv, sys_stdin=sys.stdin, sys_stdout=sys.stdout):
    (log, deploy_stdout, deploy_stderr) = configure_logging()
    client = get_client(log)

    c = json.load(sys.stdin)

    images_timeout = c['options'].get(
        'images_timeout', DEFAULT_IMAGES_TIMEOUT)
    containers_timeout = c['options'].get(
        'containers_timeout', DEFAULT_CONTAINERS_TIMEOUT)
    poll_period = c['options'].get(
        'poll_period', DEFAULT_POLL_PERIOD)

    pod_state = 0

    try:
        wait_required_images(
            client,
            log,
            images_timeout,
            poll_period,
            required_images(c))

        wait_required_containers(
            client,
            log,
            containers_timeout,
            poll_period,
            required_container_patterns(c))

    except Exception as ex:
        pod_state = 1
        log.error('An error occurred deploying pod %s' % c['id'])
        log.exception(ex)

    response = {
        'deploy_stdout': deploy_stdout.getvalue(),
        'deploy_stderr': deploy_stderr.getvalue(),
        'deploy_status_code': pod_state,
    }
    json.dump(response, sys_stdout)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
