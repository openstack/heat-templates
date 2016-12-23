================================================
Boot config for installing software-config agent
================================================

This directory has environment files which each declare a resource type
Heat::InstallConfigAgent.

This can be used by server user_data when booting a pristine image
to install the agent required to use software deployment resources in
templates.

The environments only install the heat-config-script hook. If other hooks are
required then define your own environment file which defines a resource
template based on one of the templates in template/

To install the agent during boot, include the following in the template:

  boot_config:
    type: Heat::InstallConfigAgent

  server:
    type: OS::Nova::Server
    properties:
      user_data_format: SOFTWARE_CONFIG
      user_data: {get_attr: [boot_config, config]}
      # ...

When creating the stack, reference the desired environment, eg:

  openstack stack create -e fedora_yum_env.yaml \
       -t ../example-templates/example-config-pristine-image.yaml \
       deploy-to-pristine

=====================================
Boot config with heat-container-agent
=====================================

When creating the stack to deploy containers with docker-compose,
include the following in the template:

  boot_config:
    type: Heat::InstallConfigAgent

  server:
    type: OS::Nova::Server
    properties:
      user_data_format: SOFTWARE_CONFIG
      user_data: {get_attr: [boot_config, config]}
      # ...

and reference the desired environment, eg:

  openstack stack create -e container_agent_env.yaml \
       -t ../example-templates/example-pristine-atomic-docker-compose.yaml \
       deploy-to-pristine
