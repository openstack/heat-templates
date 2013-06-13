This directory contains files for deploying OpenShift Origin to an OpenStack environment via heat.

It includes the following files
* F18-x86_64-openshift-origin-broker-cfntools.tdl - oz template for building a broker image
* F18-x86_64-openshift-origin-node-cfntools.tdl - oz template for building a node image
* OpenShift.template - heat template for launching OpenShift Origin with a single broker server and a single node server
* openshift-origin - diskimage-builder elements to build images, as an alternative to oz

To build with diskimage-builder, do the following in the parent directory of heat-templates::

  git clone https://github.com/stackforge/diskimage-builder.git
  git clone https://github.com/stackforge/tripleo-image-elements.git
  mkdir $HOME/tmp
  export ELEMENTS_PATH=tripleo-image-elements/elements:heat-templates/openshift-origin/elements
  TMP_DIR=$HOME/tmp DIB_IMAGE_SIZE=5 diskimage-builder/bin/disk-image-create --no-tmpfs -a amd64 vm fedora openshift-origin-broker -o F18-x86_64-openshift-origin-broker-cfntools
  TMP_DIR=$HOME/tmp DIB_IMAGE_SIZE=20 diskimage-builder/bin/disk-image-create --no-tmpfs -a amd64 vm fedora openshift-origin-node -o F18-x86_64-openshift-origin-node-cfntools

