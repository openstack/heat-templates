#!/bin/bash
set -eux

yum -y install os-collect-config os-apply-config os-refresh-config dib-utils
