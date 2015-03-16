#!/bin/bash
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# known good values of DISTRO are
# fedora-heat-test, ubuntu-heat-test, centos7-heat-test
export DISTRO=${DISTRO:-fedora-heat-test}

export ELEMENTS_PATH=${ELEMENTS_PATH:-`dirname "$0"`/elements}
export IMAGE_NAME=${IMAGE_NAME:-$DISTRO-image}

disk-image-create -x --no-tmpfs -o $IMAGE_NAME $DISTRO \
    vm python-dev heat-agent-pkg-requires heat-config-hook-requires
