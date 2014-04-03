#!/usr/bin/env python
from heat_cfntools.cfntools import cfn_helper
import json
import sys


def main(argv=sys.argv):
    c = json.load(sys.stdin)

    config = c.get('config', {})
    if not isinstance(config, dict):
        config = json.loads(config)
    meta = {'AWS::CloudFormation::Init': config}

    metadata = cfn_helper.Metadata(None, None)
    metadata.retrieve(meta_str=json.dumps(meta))
    metadata.cfn_init()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
