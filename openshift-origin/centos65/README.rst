==========================
OpenShift Origin templates
==========================

.. note::

   These templates have only been tested with OpenShift V2 and are now
   deprecated. For up to date templates for deploying OpenShift V3 and beyond
   on OpenStack refer to the `OpenShift-on-OpenStack
   <https://github.com/redhat-openstack/openshift-on-openstack/>`_ github
   project.

This directory contains files for deploying OpenShift Origin to an OpenStack environment via Heat.

It includes the following template files:

* `OpenShift.yaml` - deploys OpenShift Origin in an all-in-one setup (broker+console+node)
* `OpenShift-1B1N.yaml` - deploys OpenShift Origin with separate instances for broker and node

And the following directory:

* `highly-available` - deploys OpenShift Origin in a highly available setup as further described in its README.md
