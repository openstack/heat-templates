A hook which uses the `docker` command to deploy containers.

The hook currently supports specifying containers in the `docker-compose v1
format <https://docs.docker.com/compose/compose-file/#/version-1>`_. The
intention is for this hook to also support the kubernetes pod format.

A dedicated os-refresh-config script will remove running containers if a
deployment is removed or changed, then the docker-cmd hook will run any
containers in new or updated deployments.
