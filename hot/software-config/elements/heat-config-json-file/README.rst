A hook which helps write JSON files to disk for configuration or use
with ad-hoc scripts. The data files are written to the named file
location for each section listed under 'config'.

Multiple JSON files can be written out in this manner.

Example:

  JsonConfig:
    type: OS::Heat::StructuredConfig
    properties:
      group: json-file
      config:
         /tmp/foo:
           - bar
           - bar2

This would write out a JSON files at
 /tmp/foo containing a JSON representation of ['bar', 'bar2'].
