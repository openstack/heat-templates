#!/bin/bash
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is executed inside post_test_hook function in devstack gate.

set -x

source $BASE/new/devstack/openrc admin admin
source $BASE/new/devstack/functions-common
neutron_service=$(get_or_create_service "neutron" "network" "Neutron Service")
get_or_create_endpoint $neutron_service "$REGION_NAME" "http://localhost"
aodh_service=$(get_or_create_service "aodh" "alarming" "OpenStack Alarming Service")
get_or_create_endpoint $aodh_service "$REGION_NAME" "http://localhost"
mistral_service=$(get_or_create_service "mistral" "workflowv2" "Workflow Service v2")
get_or_create_endpoint $mistral_service "$REGION_NAME" "http://localhost"
senlin_service=$(get_or_create_service "senlin" "clustering" "Senlin Clustering Service")
get_or_create_endpoint $senlin_service "$REGION_NAME" "http://localhost"
monasca_service=$(get_or_create_service "monasca" "monitoring" "Monasca Monitoring Service")
get_or_create_endpoint $monasca_service "$REGION_NAME" "http://localhost"
zaqar_service=$(get_or_create_service "zaqar" "messaging" "Zaqar Service")
get_or_create_endpoint $zaqar_service "$REGION_NAME" "http://localhost"
designate_service=$(get_or_create_service "designate" "dns" "Designate DNS Service")
get_or_create_endpoint $designate_service "$REGION_NAME" "http://localhost"
barbican_service=$(get_or_create_service "barbican" "key-manager" "Barbican Service")
get_or_create_endpoint $barbican_service "$REGION_NAME" "http://localhost"

source $BASE/new/devstack/openrc demo demo
python $BASE/new/heat-templates/tools/validate-templates $BASE/new/heat-templates
