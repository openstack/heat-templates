#!/bin/bash
set -eux

apt-get -y update
apt-get -y install python-pip git gcc python-dev libyaml-dev libssl-dev libffi-dev libxml2-dev libxslt1-dev