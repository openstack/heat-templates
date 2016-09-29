A hook which helps write hiera files to disk and creates
the hiera.yaml to order them. This is typically used alongside
of the puppet hook to generate Hiera in a more composable manner.

Example:

  ComputeConfig:
    type: OS::Heat::StructuredConfig
    properties:
      group: hiera
      config:
        hierarchy:
          - compute
        datafiles:
          compute:
            debug: true
            db_connection: foo:/bar
            # customized hiera goes here...

This would write out:

 1) An /etc/hiera.yaml config file with compute in the hierarchy.

 2) An /etc/puppet/hieradata/compute.json file loaded with the
    custom hiera data.
