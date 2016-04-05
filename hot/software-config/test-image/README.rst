=======================================
Elements for building a heat test image
=======================================

The heat functional test job needs to boot full images containing the
heat agent code (os-collect-config etc) so that it can test the
interaction between heat and the agent.

Images built with these elements contain the necessary
distro packages so that only pip packages need to be installed on
server boot.

The script build-heat-test-image.sh will trigger an image build
defaulting to fedora. Ubuntu and CentOS7 are also fully supported by
these elements. Run the following to build all supported images:


::

  DISTRO=fedora ./build-heat-test-image.sh
  DISTRO=ubuntu ./build-heat-test-image.sh
  DISTRO=centos7-rdo ./build-heat-test-image.sh
