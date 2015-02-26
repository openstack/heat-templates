=============================================
HOT software configuration hooks and examples
=============================================

The Heat software configuration resources can be combined with a server agent
and hooks to configure software on servers using a variety of techniques.

Contained here are the following directories:

boot-config
-----------
This directory has environment files which each declare a resource type
Heat::InstallConfigAgent.

This can be used by server user_data when booting a pristine image
to install the agent required to use software deployment resources in
templates.

elements
--------
This contains `diskimage-builder <https://github.com/openstack/diskimage-builder>`_
elements which will install the hooks for different configuration tools onto
a custom-built image.

example-templates
-----------------
This contains example heat templates which demonstrate how the software config
resources and the hooks work together to perform software configuration.

test-image
----------
This contains `diskimage-builder <https://github.com/openstack/diskimage-builder>`_
elements which will install the distro packages required for a base test image.