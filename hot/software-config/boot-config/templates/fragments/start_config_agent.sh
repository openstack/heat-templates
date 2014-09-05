#!/bin/bash
set -eux

if [[ `systemctl` =~ -\.mount ]]; then

    # if there is no system unit file, install a local unit
    if [ ! -f /usr/lib/systemd/system/os-collect-config.service ]; then

        cat <<EOF >/etc/systemd/system/os-collect-config.service
[Unit]
Description=Collect metadata and run hook commands.

[Service]
ExecStart=/usr/bin/os-collect-config
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF >/etc/os-collect-config.conf
[DEFAULT]
command=os-refresh-config
EOF
    fi

    # enable and start service to poll for deployment changes
    systemctl enable os-collect-config
    systemctl start --no-block os-collect-config
elif [[ `/sbin/init --version` =~ upstart ]]; then
    if [ ! -f /etc/init/os-collect-config.conf ]; then

        cat <<EOF >/etc/init/os-collect-config.conf
start on runlevel [2345]
stop on runlevel [016]
respawn

# We're logging to syslog
console none

exec os-collect-config  2>&1 | logger -t os-collect-config
EOF
    fi
    initctl reload-configuration
    service os-collect-config start
else
    echo "ERROR: only systemd or upstart supported" 1>&2
    exit 1
fi




