A hook which uses `docker-compose` to deploy containers.

A special input 'env_files' can be used with SoftwareConfig and
StructuredConfig for docker-compose `env_file` key(s).

if env_file keys specified in the `docker-compose.yml`, do not
exist in input_values supplied, docker-compose will throw an
error, as it can't find these files.

Also, `-Pf` option can be used to pass env files from client.

Example:

$ heat stack-create test_stack -f example-docker-compose-template.yaml \
    -Pf env_file_0=./common.env -Pf env_file_1=./apps/web.env \
    -Pf env_file_2=./test.env -Pf env_file_3=./busybox.env