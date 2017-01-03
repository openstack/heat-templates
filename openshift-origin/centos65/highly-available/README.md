# OpenShift Origin Highly Available Environment
This nested heat stack deploys a highly-available OpenShift Origin environment.

## Resources Deployed
* 6 instances
  * Highly available OpenShift broker set (3)
  * OpenShift nodes (3)
* 7 floating IPs (includes one for LBaaS VIP)
* LBaaS, consisting of health monitor (HTTPS), pool, virtual IP (VIP)
* Integrated BIND server on broker 1 for dynamic DNS updates

### Deployment



       zone transferred to
        upstream DNS (IT)
                  \          ----------------------
                   \        /   mongo replica set  \
                    \      /      ActiveMQ pool     \
                   --\---------   ------------   ------------
                   | BIND |   |   |          |   |          |
                   --------   |---| broker 2 |---| broker 3 |
                   | broker 1 |   |          |   |          |
                   ------------   ------------   ------------
                               \       |          /
                                \      |         /
                                LBaaS agent (API) ---------------- developers
                                /      |       \
                               /       |        \
                   ------------   ------------   ------------
                   |          |   |          |   |          |
                   |  node 1  |---|  node 2  |---|  node  3 | ---- application
                   |          |   |          |   |          |         users
                   ------------   ------------   ------------



## Requirements
* Neutron networking: one private and one public network
* Compute quota for six VM instances
* Pool of seven available floating IP addresses. Addresses will be created and assigned at deployment.
* Load Balancer as a Server (LBaaS) configured. See neutron [lbaas agent configuration section](http://openstack.redhat.com/LBaaS).
* IP address of upstream (IT) DNS server for zone transfers

## Files
These templates are [Heat Orchestration Templates (HOT)](http://docs.openstack.org/developer/heat/template_guide/environment.html). Environment files are used to reduce CLI parameters and provide a way to reuse resources.

* Templates
  * oso_ha_stack.yaml
  * oso_node_stack.yaml
* Environments
  * oso_ha_env.yaml
  * oso_node_env.yaml

## How to Deploy
1. `git clone https://github.com/openstack/heat-templates.git` this repository
2. Change to this directory

        cd heat-templates/openshift-origin/centos65/highly-available/

3. Edit heat environment file `oso_ha_env.yaml` according to your environment.
4. Launch highly available OpenShift stack

        openstack stack create openshift-ha-stack -t oso_ha_stack.yaml -e oso_ha_env.yaml

5. Monitor progress. Options include:
  * `tail -f /var/log/heat/heat-engine.log`
  * `tail -f /tmp/openshift.out`
  * `openstack stack list`
  * `openstack stack resource list openshift-ha-stack`

## Scaling: Adding Nodes

OpenShift nodes may be manually added as needed using the OpenShift node heat template.

1. From directory `heat-templates/openshift-origin/centos65/highly-available/` edit the heat environment file `oso_node_env.yaml`
2. Launch node stack. This will deploy a single node server with attached cinder volume and floating IP address. Be sure to pass in the node hostname parameter to override the default.

        openstack stack create openshift-node -t oso_node_stack.yaml -e oso_node_env.yaml --parameter "node_hostname=node4"

3. On broker1 add a DNS record for the new node server in `/var/named/dynamic/<my_domain>.db`. To force a zone transfer to the upstream DNS increment the serial number by 1 and run `rndc freeze ; rndc thaw`.

## Additional configuration Steps

1. Add brokers to LBaaS pool. On OpenStack:

        neutron lb-member-create --address <broker1_fixed_ip> --protocol-port 443 oso_broker_lb_pool
        neutron lb-member-create --address <broker2_fixed_ip> --protocol-port 443 oso_broker_lb_pool
        neutron lb-member-create --address <broker3_fixed_ip> --protocol-port 443 oso_broker_lb_pool

2. Add session persistence to LBaaS virtual IP (VIP):

        neutron lb-vip-update oso_broker_vip --session-persistence type=dict type='SOURCE_IP'

3. Update upstream DNS server to accept zone transfers from the OpenShift dynamic DNS. An example configuration would be to add a slave zone to /var/named.conf


        zone "<openshift_domain_name>" {
            type slave;
            file "slaves/<openshift_domain_name>.db";
            masters { <broker1_ip_address>; };
        };


    * If the upstream DNS configuration is not available a test client machine may be pointed to the broker 1 IP address (e.g. edit /etc/resolv.conf).

4. Create districts. The following creates a small district and adds two nodes to the district.

        oo-admin-ctl-district -c create -n small_district -p small
        oo-admin-ctl-district -c add-node -n small_district -i <node1_hostname>
        oo-admin-ctl-district -c add-node -n small_district -i <node2_hostname>

## Troubleshooting
* `oo-mco ping` on a broker to verify nodes are registered
* `oo-diagnostics -v` on a broker to run a comprehensive set of tests
* `oo-accept-node -v` on a node
* If LBaaS is not set up any broker hostname can be used temporarily as the developer and node API target. Be sure to edit `/etc/openshift/node.conf`.
