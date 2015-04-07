This hook uses the kubelet agent from the kubernetes project to provision
containers. The StructuredConfig resource data represents a pod of containers
to be provisioned.

The files have the following purpose:

- extra-data.d/50-docker-images allows an archive file of docker images to
  be included in the dib image

- install.d/50-heat-config-kubelet installs kubernetes for redhat based
  distros during dib image build, along with the required systemd and config
  files required to enable a working kubelet service on the host

- install.d/hook-kubelet.py polls docker images and containers until the
  expected kubelet-provisioned containers are running (or a timeout occurs)

- os-refresh-config/configure.d/50-heat-config-kubelet runs before
  55-heat-config (and the kubelet hook it triggers). This orc script writes
  out all pod definition files for the pods that should currently be running.
  Kubelet is configured to monitor the directory containing these files, so
  the current running containers will change when kubelet acts on these
  config changes