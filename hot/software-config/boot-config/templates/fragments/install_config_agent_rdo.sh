#!/bin/bash
set -eux

yum -y install https://www.rdoproject.org/repos/rdo-release.rpm
yum -y install python-zaqarclient os-collect-config os-apply-config os-refresh-config dib-utils
