#!/bin/bash
set -eux

pip install os-collect-config os-apply-config os-refresh-config heat-cfntools

cfn-create-aws-symlinks
