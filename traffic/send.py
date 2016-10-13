"""Traffic generator utility

Usage:
  mnsend <packet>... [--count <count>] [--iface=IFACE] [--topology=FILE]
  mnsend (-h | --help)

Options:
  -h --help                     Show this screen.
  --topology=FILE               Topolofy file name [default: mn-topo.yml].
  --iface=IFACE                 Interface name
  -c <count>, --count <count>   Number of packets to be sent. Default 1.
  --version                     Show version.

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

        iface = None
        if arguments['--iface']:
            iface = arguments['--iface']

        count = 1
        if arguments['--count']:
            count = int(arguments['--count'])

        print arguments
        packets = []
        for packet in arguments['<packet>']:
            packets.append(eval(packet))

        for p in range(0, count):
            sendp(packets, iface=iface)

def main():
    Shell()

if __name__ == "__main__":
    Shell()
