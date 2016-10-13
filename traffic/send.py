"""Traffic generator utility

Usage:
  mnsend [--topology=FILE] <packets> [--vlan=VLAN] [--iface=IFACE]
  mnsend (-h | --help)

Options:
  -h --help         Show this screen.
  --topology=FILE   Topolofy file name [default: mn-topo.yml].
  --vlan=VLAN       Vlan id
  --iface=IFACE     Interface name
  --version         Show version.

"""

import os
import sys
import yaml
from mntopo.docopt import docopt
import mntopo.topo
from mininet.log import setLogLevel, info, error
from scapy.all import *


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

        topo = mntopo.topo.Topo(props)

        vlan = None
        if arguments['--vlan']:
            vlan = arguments['--vlan']
        iface = None
        if arguments['--iface']:
            iface = arguments['--iface']

        for count in range(0, int(arguments['<packets>'])):
            if vlan is None:
                sendp(Ether() / IP() / ICMP(), iface=iface)
            else:
                sendp(Ether() / Dot1Q(vlan=int(vlan)) / IP() / ICMP(), iface=iface)


def main():
    Shell()

if __name__ == "__main__":
    Shell()
