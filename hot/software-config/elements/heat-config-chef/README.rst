A hook which invokes ``chef-client`` in local mode (chef zero) on the
provided configuration.

Inputs:
-------
Inputs are attribute overrides. In order to format them correctly for
consumption, you need to explicitly declare each top-level section as an
input of type ``Json`` in your config resource.

Additionally, there is a special input named ``environment`` of type
``String`` that you can use to specify which environment to use when
applying the config. You do not have to explicitly declare this input in
the config resource.

Outputs:
--------
If you need to capture specific outputs from your chef run, you should
specify the output name(s) as normal in your config. Then, your recipes
should write files to the directory specified by the ``heat_outputs_path``
environment variable. The file name should match the name of the output
you are trying to capture.

Options:
-------------

kitchen : optional
    A URL for a Git repository containing the desired recipes, roles,
    environments and other configuration.

    This will be cloned into ``kitchen_path`` for use by chef.

kitchen_path : default ``/var/lib/heat-config/heat-config-chef/kitchen``
    Instance-local path for the recipes, roles, environments, etc.

    If ``kitchen`` is not specified, this directory must be populated via
    user-data, another software config, or other "manual" method.
