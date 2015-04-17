=======================================================
Steps to build container image with all container hooks
=======================================================

Docker build does not work with soft links. Therefore, convert all
soft links to hardlinks.

 $ find -type l -exec bash -c 'ln -f "$(readlink -m "$0")" "$0"' {} \;

Build docker image with container hooks.

  $docker build -t xxxx/heat-container-agent ./

Push the image to docker hub.

  $docker push xxxx/heat-container-agent