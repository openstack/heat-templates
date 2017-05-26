#!/bin/bash
set -eux

# os-apply-config templates directory
oac_templates=/usr/libexec/os-apply-config/templates
mkdir -p $oac_templates/etc

# initial /etc/os-collect-config.conf
cat <<EOF >/etc/os-collect-config.conf
[DEFAULT]
command = os-refresh-config
EOF

# template for building os-collect-config.conf for polling heat
cat <<EOF >$oac_templates/etc/os-collect-config.conf
[DEFAULT]
{{^os-collect-config.command}}
command = os-refresh-config
{{/os-collect-config.command}}
{{#os-collect-config}}
{{#command}}
command = {{command}}
{{/command}}
{{#polling_interval}}
polling_interval = {{polling_interval}}
{{/polling_interval}}
{{#cachedir}}
cachedir = {{cachedir}}
{{/cachedir}}
{{#collectors}}
collectors = {{.}}
{{/collectors}}

{{#cfn}}
[cfn]
{{#metadata_url}}
metadata_url = {{metadata_url}}
{{/metadata_url}}
stack_name = {{stack_name}}
secret_access_key = {{secret_access_key}}
access_key_id = {{access_key_id}}
path = {{path}}
{{/cfn}}

{{#heat}}
[heat]
auth_url = {{auth_url}}
user_id = {{user_id}}
password = {{password}}
project_id = {{project_id}}
stack_id = {{stack_id}}
resource_name = {{resource_name}}
{{/heat}}

{{#zaqar}}
[zaqar]
auth_url = {{auth_url}}
user_id = {{user_id}}
password = {{password}}
project_id = {{project_id}}
queue_id = {{queue_id}}
{{/zaqar}}

{{#request}}
[request]
{{#metadata_url}}
metadata_url = {{metadata_url}}
{{/metadata_url}}
{{/request}}

{{/os-collect-config}}
EOF
mkdir -p $oac_templates/var/run/heat-config

# template for writing heat deployments data to a file
echo "{{deployments}}" > $oac_templates/var/run/heat-config/heat-config

# os-refresh-config scripts directory
# This moves to /usr/libexec/os-refresh-config in later releases
orc_scripts=/opt/stack/os-config-refresh
for d in pre-configure.d configure.d migration.d post-configure.d; do
    install -m 0755 -o root -g root -d $orc_scripts/$d
done

# os-refresh-config script for running os-apply-config
cat <<EOF >$orc_scripts/configure.d/20-os-apply-config
#!/bin/bash
set -ue

exec os-apply-config
EOF
chmod 700 $orc_scripts/configure.d/20-os-apply-config

chmod 700 /opt/stack/os-config-refresh/configure.d/55-heat-config
chmod 700 /opt/stack/os-config-refresh/configure.d/50-heat-config-docker-compose

chmod 755 /var/lib/heat-config/hooks/atomic
chmod 755 /var/lib/heat-config/hooks/docker-compose
chmod 755 /var/lib/heat-config/hooks/script

chmod 755 /usr/bin/heat-config-notify
