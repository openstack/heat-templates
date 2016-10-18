A hook which invokes ``puppet apply`` on the provided configuration.

Config inputs are passed in as facts and/or using hiera, and output values
are read from written-out files.

Hook Options:
-------------
  use_facter: default True. Set to True to pass puppet inputs via Facter
  use_hiera: default False. Set to True to pass puppet inputs via Hiera
  modulepath: If set, puppet will use this filesystem path to load modules
  tags: If set, puppet will use the specified value(s) to apply only a
        subset of the catalog for a given manifest.
  enable_debug: default False. Set to True to run puppet apply in debug mode
                and have it captured on the node to /var/log/puppet/heat-debug.log
  enable_verbose: default False. Set to True to run puppet apply in verbose mode
                and have it captured on the node to /var/log/puppet/heat-verbose.log
