=====================
Simple Cirros example
=====================

This directory contains a very simple proof-of-concept hook script and
template which shows how you can use SoftwareDeployment resources with
a cirros image (which doesn't contain cloud-init or python), which may
be useful for testing.

Since cirros images don't currently support multi-part mime user-data,
it's necessary to inject the hook script to the image and upload the
modified image to glance:

1. wget http://download.cirros-cloud.net/0.3.2/cirros-0.3.2-x86_64-disk.img
2. virt-copy-in -a cirros-0.3.2-x86_64-disk.img init.d/heat-deploy-hook /etc/init.d
3. virt-copy-in -a cirros-0.3.2-x86_64-disk.img rc3.d/S99-heat-deploy-hook /etc/rc3.d
4. openstack image create cirros-0.3.2-sc --disk-format=qcow2 --container-format=bare < cirros-0.3.2-x86_64-disk.img
5. openstack stack create sc1 -t cirros-hello-world.yaml --parameter "image=cirros-0.3.2-sc"

*NOTE*: The hook script is very basic and has a number of TODO items related to
security and functionality - please don't use it for "real" deployments, it's
intended to enable easier testing and for developer experimentation only.
