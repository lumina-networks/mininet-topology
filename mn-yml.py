#!/usr/bin/python

import os
import sys
import yaml
import mntopo
from mininet.log import setLogLevel, info, error

if __name__ == '__main__':
    setLogLevel( 'info' )
    file = 'mn-topo.yml'
    if len(sys.argv) > 1:
        file = sys.argv[1]

    props = None
    if (os.path.isfile(file)):
        with open(file, 'r') as f:
            props = yaml.load(f)

    if props is None:
        print "ERROR: yml topology file not found"
    else:
        topo = mntopo.Topo(props)
        topo.start()
        topo.cli()
        topo.stop()
