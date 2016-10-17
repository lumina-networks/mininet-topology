"""Mininet Topology Utility

Usage:
  mnyml [--topology=FILE] [--controller=IP]...
  mnyml (-h | --help)

Options:
  -h --help     Show this screen.
  -t, --topology=FILE   Topolofy file name [default: mn-topo.yml].
  -c, --controller=IP   Controller IP address
  --version     Show version.

"""

import os
import sys
import yaml
from mntopo.docopt import docopt
import mntopo.topo
from mininet.log import setLogLevel, info, error


class Shell(object):

    def __init__(self):
        arguments = docopt(__doc__, version='Mininet Topology Utility 1.0')

        setLogLevel('info')
        file = 'mn-topo.yml'
        if arguments['--topology']:
            file = arguments['--topology']

        props = None
        if (os.path.isfile(file)):
            with open(file, 'r') as f:
                props = yaml.load(f)

        if props is None:
            print "ERROR: yml topology file not found"
            sys.exit()

        if arguments['--controller']:
            props['controller'] = []
            i = 0
            for ip in arguments['--controller']:
                props['controller'].append(
                    {'name': "c{}".format(i),
                     'ip': ip
                     })
                i = i + 1

        topo = mntopo.topo.Topo(props)
        topo.start()
        topo.cli()
        topo.stop()


def main():
    Shell()

if __name__ == "__main__":
    Shell()
