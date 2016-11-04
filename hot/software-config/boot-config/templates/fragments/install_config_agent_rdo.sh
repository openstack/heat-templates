#!/bin/bash
set -eux

yum -y install https://www.rdoproject.org/repos/rdo-release.rpm
yum -y install python2-oslo-log python-psutil python-zaqarclient os-collect-config os-apply-config os-refresh-config dib-utils
