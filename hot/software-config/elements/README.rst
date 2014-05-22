============================
Software configuration hooks
============================

This directory contains `diskimage-builder <https://github.com/openstack/diskimage-builder>`_
elements to build an image which contains the software configuration hook
required to use your preferred configuration method.

These elements depend on some elements found in the
`tripleo-image-elements <https://github.com/openstack/tripleo-image-elements>`_
repository. These elements will build an image which uses
`os-collect-config <https://github.com/openstack/os-collect-config>`_,
`os-refresh-config <https://github.com/openstack/os-refresh-config>`_, and
`os-apply-config <https://github.com/openstack/os-apply-config>`_ together to
invoke a hook with the supplied configuration data, and return any outputs back
to heat.

When building an image, the heat-config element is required, along with the elements
for the hooks which enable the preferred configuration methods.

An example fedora based image containing all hooks can be built and uploaded to glance
with the following:

::

  git clone https://git.openstack.org/openstack/diskimage-builder.git
  git clone https://git.openstack.org/openstack/tripleo-image-elements.git
  git clone https://git.openstack.org/openstack/heat-templates.git
  export ELEMENTS_PATH=tripleo-image-elements/elements:heat-templates/hot/software-config/elements
  diskimage-builder/bin/disk-image-create vm \
    fedora selinux-permissive \
    heat-config \
    os-collect-config \
    os-refresh-config \
    os-apply-config \
    heat-config-cfn-init \
    heat-config-puppet \
    heat-config-script \
    -o fedora-software-config.qcow2
  glance image-create --disk-format qcow2 --container-format bare --name fedora-software-config < \
    fedora-software-config.qcow2
