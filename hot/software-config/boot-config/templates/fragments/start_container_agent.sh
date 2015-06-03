#!/bin/bash
set -eux

# heat-docker-agent service
cat <<EOF > /etc/systemd/system/heat-container-agent.service

[Unit]
Description=Heat Container Agent
After=docker.service
Requires=docker.service

[Service]
User=root
Restart=on-failure
ExecStartPre=-/usr/bin/docker kill heat-container-agent
ExecStartPre=-/usr/bin/docker rm heat-container-agent
ExecStartPre=/opt/container_agent/get_container_agent_image.sh $agent_image
ExecStart=/usr/bin/docker run --name heat-container-agent --privileged --net=host -v /usr/bin/atomic:/usr/bin/atomic -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/atomic:/usr/bin/atomic -v /var/lib/cloud:/var/lib/cloud -v /var/lib/heat-cfntools:/var/lib/heat-cfntools $agent_image
ExecStop=/usr/bin/docker stop heat-container-agent

[Install]
WantedBy=multi-user.target

EOF

# enable and start docker
/usr/bin/systemctl enable docker.service
/usr/bin/systemctl start --no-block docker.service

# enable and start heat-container-agent
chmod 0640 /etc/systemd/system/heat-container-agent.service
chmod 0755 /opt/container_agent/get_container_agent_image.sh
/usr/bin/systemctl enable heat-container-agent.service
/usr/bin/systemctl start --no-block heat-container-agent.service