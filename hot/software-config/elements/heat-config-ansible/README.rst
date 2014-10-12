A hook which invokes ``ansible-playbook -i "localhost,"`` on the provided
configuration. Config inputs are written to a 'variables.json' file and
then passed to ansible via the '--extra-vars @json_file' parameter.
Config output values are read from written-out files.
