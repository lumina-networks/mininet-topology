"""Traffic generator utility

Usage:
  mnrecv <filter> [--count=COUNT] [--iface=IFACE] [--timeout=TIMEOUT] [--percentage=PERCENTAGE]
  mnrecv (-h | --help)

Options:
  -h --help                     Show this screen.
  --iface=IFACE                 Interface name
  -c <count>, --count <count>   Number of packets to be sent. Default 1.
  -p <percentage>, --percentage <percentage> Percentage of packets that can be lost.
  --timeout=TIMEOUT             Timeout in seconds. Default 30
  --version                     Show version.

"""

import os
import sys
import yaml
from docopt.docopt import docopt
import mntopo.topo
from mininet.log import setLogLevel, info, error
from scapy.all import *


class Shell(object):

    def __init__(self):
        arguments = docopt(__doc__, version='Mininet Topology Utility 2.0')


        count = 1
        if arguments['--count']:
            count = int(arguments['--count'])

        percentage = 0
        if arguments['--percentage']:
            percentage = int(arguments['--percentage'])

        if count > 0 and percentage > 0 and percentage <= 100:
            count = count - ((percentage * count)/100)
            if count <= 0:
                count = 1

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

        if (count == 0 and recv_packets > 0) or recv_packets < count:
            print "ERROR: received packets '{}' is different from expected '{}'".format(recv_packets,count)
            sys.exit(1)

        print "received packets '{}' successfully. Expected '{}'".format(recv_packets,count)



def main():
    Shell()

if __name__ == "__main__":
    Shell()
