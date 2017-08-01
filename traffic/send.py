"""Traffic generator utility

Usage:
  mnsend <packet>... [--count <count>] [--iface=IFACE]
  mnsend (-h | --help)

Options:
  -h --help                     Show this screen.
  -i <iface>, --iface <iface>   Interface name
  -c <count>, --count <count>   Number of packets to be sent. Default 1.
  --version                     Show version.

"""

import os
import sys
from docopt.docopt import docopt
from scapy.all import *


class Shell(object):

    def __init__(self):
        arguments = docopt(__doc__, version='Mininet Topology Utility 1.0')

        iface = None
        if arguments['--iface']:
            iface = arguments['--iface']

        count = 1
        if arguments['--count']:
            count = int(arguments['--count'])

        packets = []
        for packet in arguments['<packet>']:
            packets.append(eval(packet))

        sendp(packets, iface=iface, count=count)


def main():
    Shell()

if __name__ == "__main__":
    Shell()
