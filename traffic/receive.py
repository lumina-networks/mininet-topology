"""Traffic generator utility

Usage:
  mnrecv <filter> [--count=COUNT] [--iface=IFACE] [--timeout=TIMEOUT] [--topology=FILE]
  mnrecv (-h | --help)

Options:
  -h --help                     Show this screen.
  --topology=FILE               Topolofy file name [default: mn-topo.yml].
  --iface=IFACE                 Interface name
  -c <count>, --count <count>   Number of packets to be sent. Default 1.
  --timeout=TIMEOUT             Timeout in seconds. Default 30
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

        count = 1
        if arguments['--count']:
            count = int(arguments['--count'])

        iface = None
        if arguments['--iface']:
            iface = arguments['--iface']

        timeout = 60
        if arguments['--timeout']:
            timeout = int(arguments['--timeout'])

        wait_packets = count
        if count <= 0:
            wait_packets = 1
        recv_packets = len(sniff(count=wait_packets, iface=iface, filter=arguments['<filter>'], timeout=timeout))
        if  recv_packets != count:
            print "ERROR: received packets '{}' is different from expected '{}'".format(recv_packets,count)
            sys.exit(1)
        else:
            print "received '{}' packets successfully".format(count)


def main():
    Shell()

if __name__ == "__main__":
    Shell()
