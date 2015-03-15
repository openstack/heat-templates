#cloud-config
merge_how: dict(recurse_array)+list(append)
write_files:
  - path: /opt/container_agent/get_container_agent_image.sh
    owner: "root:root"
    permissions: "0644"
    content: |
      #!/bin/bash
      set -eux
      regex='(https?|http)://[-A-Za-z0-9\+&@#/%?=~_|!:,.;]*[-A-Za-z0-9\+&@#/%=~_|]'
      agent_image="$1"
      if [[ $agent_image =~ $regex ]]
      then
        cd /tmp && { curl $agent_image >  heat_container_image.tar ; cd -; }
        /usr/bin/docker load -i /tmp/heat_container_image.tar
      else
         /usr/bin/docker pull $agent_image
      fi
