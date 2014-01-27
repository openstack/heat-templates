==========================
OpenShift Enterprise templates
==========================

This directory contains files for deploying OpenShift Enterprise to an OpenStack environment via heat.

It includes the following files:

* `OpenShift.yaml` - heat template for launching OpenShift Enterprise with a single broker server and a single node server
* `openshift-enterprise` - diskimage-builder elements to build images

OpenShift Enteprise now requires that you use Red Hat Enterprise Linux 6.5, which can be downloaded from:
https://rhn.redhat.com/rhn/software/channel/downloads/Download.do?cid=16952

To build with diskimage-builder, do the following in the parent directory of heat-templates::

  git clone https://github.com/openstack/diskimage-builder.git
  mkdir $HOME/tmp
  export ELEMENTS_PATH=heat-templates/openshift-enterprise/dib/elements
  export DIB_CLOUD_IMAGES=url rhel-guest-image-6-6.5-20131220.3-1.qcow2 image can be found (download this from rhn)

  # Either set the following variables if you have the packages in a yum repo
  # or specify an OpenShift Enterprise subscription pool id.

  # Use yum repos for package installation
  export DIB_CONF_JBOSS_REPO_BASE=<location of JBoss repo>
  export DIB_CONF_REPO_BASE=<location of OpenShift Enteprise repo>

  # Or, use Red Hat subscriptions for package installation
  export DIB_RHSM_OSE_POOL=<OpenShift Enterprise subscription pool id>
  export DIB_RHSM_POOL=<Red Hat Enterprise Linux Server subscription pool id (if not setting a custom repo url for it)>

  # You will need to provide credentials for the Red Hat Enterprise Linux
  # Server packages. If you don't provide a pool id with DIB_RHSM_POOL, a
  # matching subscription on your user account will be automatically attached to
  the system.
  export DIB_RHSM_USER=your_rhel_subscription_username
  export DIB_RHSM_PASSWORD=your_rhel_subscription_password

  # Add the following to the disk image bulding command:

  export DIB_OSE_VERSION=2.0
  export DIB_YUM_VALIDATOR_VERSION=2.0

  export TMP_DIR=$HOME/tmp
  export DIB_IMAGE_SIZE=5
  diskimage-builder/bin/disk-image-create --no-tmpfs -a amd64 vm rhel openshift-enterprise-broker -o RHEL65-x86_64-broker

  export TMP_DIR=$HOME/tmp
  export DIB_IMAGE_SIZE=20
  diskimage-builder/bin/disk-image-create --no-tmpfs -a amd64 vm rhel openshift-enterprise-node -o RHEL65-x86_64-node

  # Register the RHEL65-x86_64-broker and RHEL65-x86_64-node with OpenStack Glance::
  glance add name=RHEL65-x86_64-broker is_public=true disk_format=qcow2 container_format=bare < RHEL65-x86_64-broker.qcow2
  glance add name=RHEL65-x86_64-node is_public=true disk_format=qcow2 container_format=bare < RHEL65-x86_64-node.qcow2

Invoke Heat
-----------

Once you have the required disk images registered with glance, you can use OpenStack Heat to provision instances of your images and configure them to work together as an OpenShift infrastructure::

For OSE 1.2:

heat create openshift --template-file=./heat-templates/openshift-enterprise/heat/neutron/OpenShift-1B1N-neutron.yaml --parameters="key_name=${USER}_key;prefix=novalocal;BrokerHostname=openshift.brokerinstance.novalocal;NodeHostname=openshift.nodeinstance.novalocal;ConfInstallMethod=rhsm;ConfSMRegName=username;ConfSMRegPass=password;ConfSMRegPool=OSE_1.2_pool_id;private_net_id=neturon_private_net_id;public_net_id=neutron_public_net_id;private_subnet_id=neutron_private_subnet_id;yum_validator_version=1.2;ose_version=1.2"

For OSE 2.0 (Only available via beta subscription for now):

heat create openshift --template-file=./heat-templates/openshift-enterprise/heat/neutron/OpenShift-1B1N-neutron.yaml --parameters="key_name=${USER}_key;prefix=novalocal;BrokerHostname=openshift.brokerinstance.novalocal;NodeHostname=openshift.nodeinstance.novalocal;ConfInstallMethod=rhsm;ConfSMRegName=username;ConfSMRegPass=password;ConfSMRegPool=OSE_2.0_pool_id;private_net_id=neturon_private_net_id;public_net_id=neutron_public_net_id;private_subnet_id=neutron_private_subnet_id;yum_validator_version=2.0;ose_version=2.0"

Using Custom Yum repos
----------------------

By default, the Heat Orchestration Template assumes you're using the Yum installation method, which means it also expects you to pass parameters to heat for yum repositories. As an example, you can add the following to your list of parameters::

  ConfRHELRepoBase=http://example.com/rhel/server/6/6Server/x86_64/os;ConfJBossRepoBase=http://example.com/rhel/server/6/6Server/x86_64;ConfRepoBase=http://example.com/OpenShiftEnterprise/1.2/latest

Using Subscription Manager
--------------------------

You can switch from the default installation method by passing in the parameter ConfInstallMethod, as demonstrated above. The allowed values, other than yum are rhsm and rhn. If you set the installation method to rhsm, you'll want to also pass in the following parameters ConfSMRegName and ConfSMRegPass for the username and password respectively. Additionally, you'll need to set the ConfSMRegPool parameter with the value of the subscription pool id that corresponds to your OpenShift Enterprise subscription. When setting the ConfInstallMethod to something other than yum it is not necessary to pass the Conf*RepoBase parameters::

  ConfInstallMethod=rhsm;ConfSMRegName=myuser;ConfSMRegPass=mypass;ConfSMRegPool=XYZ01234567

Using RHN
---------

You can switch from the default installation method by passing in the parameter ConfInstallMethod. The allowed values, other than yum are rhsm and rhn. If you set the installation method to rhn, you'll want to also pass in the following parameters ConfRHNRegName and ConfRHNRegPass for the username and password respectively. Additionally, you'll need to set the ConfRHNRegAK parameter with the value of the subscription activation key that corresponds to your OpenShift Enterprise subscription. When setting the ConfInstallMethod to something other than yum it is not necessary to pass the Conf*RepoBase parameters::

  ConfInstallMethod=rhn;ConfRHNRegName=myuser;ConfRHNRegPass=mypass;ConfRHNRegAK=activationkey

