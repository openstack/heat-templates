==========================
OpenShift Enterprise templates
==========================

This directory contains files for deploying OpenShift Enterprise to an OpenStack environment via heat.

It includes the following files:

* `OpenShift.yaml` - heat template for launching OpenShift Enterprise with a single broker server and a single node server
* `openshift-enterprise` - diskimage-builder elements to build images
To build with diskimage-builder, do the following in the parent directory of heat-templates::

  git clone https://github.com/openstack/diskimage-builder.git
  mkdir $HOME/tmp
  export ELEMENTS_PATH=heat-templates/elements:heat-templates/openshift-enterprise/elements
  export DIB_CLOUD_IMAGES=url rhel-server-x86_64-kvm-6.4_20130130.0-4.qcow2 image can be found (download this from rhn)

  # Either set the following variables if you have the packages in a yum repo or specify an OpenShift Enterprise subscription pool id.
  export DIB_CONF_JBOSS_REPO_BASE=<location of JBoss repo>
  export DIB_CONF_REPO_BASE=<location of OpenShift Enteprise repo>
  export DIB_RHSM_OSE_POOL=<OpenShift Enterprise subscription pool id>

  export DIB_RHSM_USER=your_rhel_subscription_username
  export DIB_RHSM_PASSWORD=your_rhel_subscription_password
  TMP_DIR=$HOME/tmp DIB_IMAGE_SIZE=5 diskimage-builder/bin/disk-image-create --no-tmpfs -a amd64 vm rhel openshift-enterprise-broker -o RHEL64-x86_64-broker
  TMP_DIR=$HOME/tmp DIB_IMAGE_SIZE=20 diskimage-builder/bin/disk-image-create --no-tmpfs -a amd64 vm rhel openshift-enterprise-node -o RHEL64-x86_64-node
  
Register the RHEL64-x86_64-broker and RHEL64-x86_64-node with OpenStack Glance::

  glance add name=RHEL64-x86_64-broker is_public=true disk_format=qcow2 container_format=bare < RHEL64-x86_64-broker.qcow2
  glance add name=RHEL64-x86_64-node is_public=true disk_format=qcow2 container_format=bare < RHEL64-x86_64-node.qcow2

Invoke Heat
-----------

Once you have the required disk images registered with glance, you can use OpenStack Heat to provision instances of your images and configure them to work together as an OpenShift infrastructure::

  heat create openshift --template-file=./heat-templates/openshift-enterprise/OpenShift.yaml --parameters="InstanceType=m1.xlarge;KeyName=${USER}_key;Prefix=novalocal;BrokerHostname=openshift.brokerinstance.novalocal;NodeHostname=openshift.nodeinstance.novalocal;ConfRHELRepoBase=example.com/rhel/server/6/6Server/x86_64/os;ConfJBossRepoBase=http://example.com/rhel/server/6/6Server/x86_64;ConfRepoBase=http://example.com/OpenShiftEnterprise/1.2/latest"

Using Custom Yum repos (default)
-------------------------------

By default, the Heat Orchestration Template assumes you're using the Yum installation method, which means it also expects you to pass parameters to heat for yum repositories. As an example, you can add the following to your list of parameters::

  ConfRHELRepoBase=http://example.com/rhel/server/6/6Server/x86_64/os;ConfJBossRepoBase=http://example.com/rhel/server/6/6Server/x86_64;ConfRepoBase=http://example.com/OpenShiftEnterprise/1.2/latest 

Using Subscription Manager
--------------------------

You can switch from the default installation method by passing in the parameter ConfInstallMethod. The allowed values, other than yum are rhsm and rhn. If you set the installation method to rhsm, you'll want to also pass in the following parameters ConfSMRegName and ConfSMRegPass for the username and password respectively. Additionally, you'll need to set the ConfSMRegPool parameter with the value of the subscription pool id that corresponds to your OpenShift Enterprise subscription. When setting the ConfInstallMethod to something other than yum it is not necessary to pass the Conf*RepoBase parameters::

  ConfInstallMethod=rhsm;ConfSMRegName=myuser;ConfSMRegPass=mypass;ConfSMRegPool=XYZ01234567

Using RHN
---------

You can switch from the default installation method by passing in the parameter ConfInstallMethod. The allowed values, other than yum are rhsm and rhn. If you set the installation method to rhn, you'll want to also pass in the following parameters ConfRHNRegName and ConfRHNRegPass for the username and password respectively. Additionally, you'll need to set the ConfRHNRegAK parameter with the value of the subscription activation key that corresponds to your OpenShift Enterprise subscription. When setting the ConfInstallMethod to something other than yum it is not necessary to pass the Conf*RepoBase parameters::

  ConfInstallMethod=rhn;ConfRHNRegName=myuser;ConfRHNRegPass=mypass;ConfRHNRegAK=7202f3b7d218cf59b764f9f6e9fa281b

