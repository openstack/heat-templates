==========================
OpenShift Origin Templates
==========================

This directory contains files for deploying OpenShift Origin to an OpenStack environment via Heat.
The template has been tested with the OpenStack Icehouse-2 release.

It includes the following files:

* `OpenShift.template` - heat template for launching OpenShift Origin with a single broker instance and a single node instance
* `elements` - diskimage-builder elements to build images

To build with diskimage-builder, do the following in the parent directory of heat-templates::

  git clone https://github.com/openstack/diskimage-builder.git
  apt-get install -y qemu-utils kpartx
  mkdir $HOME/tmp
  export DIB_RELEASE=19
  export ELEMENTS_PATH=heat-templates/openshift-origin/F19/elements
  export TMP_DIR=$HOME/tmp
  export DIB_IMAGE_SIZE=5
  diskimage-builder/bin/disk-image-create --no-tmpfs -a amd64 vm fedora openshift-origin-broker -o F19-x86_64-openshift-origin-broker
  glance image-create --name F19-x86_64-openshift-origin-broker --is-public true --disk-format qcow2 --container-format bare < F19-x86_64-openshift-origin-broker.qcow2
  export DIB_IMAGE_SIZE=20
  diskimage-builder/bin/disk-image-create --no-tmpfs -a amd64 vm fedora openshift-origin-node -o F19-x86_64-openshift-origin-node
  glance image-create --name F19-x86_64-openshift-origin-node --is-public true --disk-format qcow2 --container-format bare < F19-x86_64-openshift-origin-node.qcow2
