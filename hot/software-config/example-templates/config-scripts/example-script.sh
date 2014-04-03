#!/bin/sh -x
echo "Writing to /tmp/$bar"
echo $foo > /tmp/$bar
echo -n "The file /tmp/$bar contains `cat /tmp/$bar` for server $deploy_server_id during $deploy_action" > $heat_outputs_path.result
echo "Written to /tmp/$bar"
echo "Output to stderr" 1>&2