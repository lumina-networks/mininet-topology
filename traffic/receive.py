"""Traffic generator utility

Usage:
  mnrecv <filter> [--count=COUNT] [--iface=IFACE] [--timeout=TIMEOUT] [--percentage=PERCENTAGE] [--seq] [--timestamp]
  mnrecv (-h | --help)

Options:
  -h --help                     Show this screen.
  -i <iface>, --iface <iface>   Interface name
  -c <count>, --count <count>   Number of packets to be sent. Default 1.
  -p <percentage>, --percentage <percentage> Percentage of packets that can be lost.
  -t <time>, --timeout <time>   Timeout in seconds. Default 30
  -s --seq                      Ensure packets are in sequence (Requires TCP seq field to be set)
  -e --timestamp                Checks packets contain timestamp
  --version                     Show version.

"""

import os
import sys
from docopt.docopt import docopt
from scapy.all import *


class Shell(object):

    def __init__(self):
        arguments = docopt(__doc__, version='Mininet Topology Utility 2.0')
        pkt_callback = None

        count = 1
        if arguments['--count']:
            count = int(arguments['--count'])

        percentage = 0
        if arguments['--percentage']:
            percentage = int(arguments['--percentage'])

        if count > 0 and percentage > 0 and percentage <= 100:
            count = count - ((percentage * count) / 100)
            if count <= 0:
                count = 1

        iface = None
        if arguments['--iface']:
            iface = arguments['--iface']

        timeout = 60
        if arguments['--timeout']:
            timeout = int(arguments['--timeout'])

        if arguments['--seq']:
            if arguments['<filter>'].lower().find('tcp') < 0:
                print "ERROR: tcp must be provided in the filter"
                sys.exit(1)
            self.sequence = []
            pkt_callback = self.pkt_seq_callback

        if  arguments['--timestamp']:
            self.timestamp = []
            pkt_callback = self.check_packet_timestamp

        wait_packets = count
        if count <= 0:
            wait_packets = 1

        recv_packets = len(sniff(count=wait_packets, iface=iface, filter=arguments['<filter>'], timeout=timeout, prn=pkt_callback))

        if (count == 0 and recv_packets > 0) or recv_packets < count:
            print "ERROR: received packets '{}' is different from expected '{}'".format(recv_packets, count)
            sys.exit(1)

        print "SUCCESS: received '{}' packets successfully. Expected '{}'".format(recv_packets, count)

    def pkt_seq_callback(self, pkt):
        seq = int(pkt.sprintf("{TCP:%TCP.seq%}"))
        if len(self.sequence) > 0:
            if self.sequence[-1] + 1 != seq:
                print "ERROR: Recieved packet sequence %s is incorrect, packet should have sequence of %s" %(seq, self.sequence[-1]+1)
                sys.exit(1)
        self.sequence.append(seq)

    def check_packet_timestamp(self,pkt):
        if pkt.haslayer(Padding):
            conv_timestamp = ''
            total_timestamp = 0
            pkt_timestamp = map(ord,str(pkt.getlayer(Padding).load))
            # reversing the array as bytes are read from right to left
            pkt_timestamp.reverse()
            # Reading only 4 bytes as 1G ports only have nano sec of length 4 bytes
            for byte in range(4):
                conv_timestamp += str(pkt_timestamp[byte])
                total_timestamp += pkt_timestamp[byte]
            conv_timestamp += ' NanoSeconds'
            self.timestamp.append(conv_timestamp)
            if ( total_timestamp <=0 ):
                print "ERROR: Recieved packet don't contain timestamp"
                sys.exit(1)
        else:
            print "ERROR: Recieved packet don't contain timestamp"
            sys.exit(1)

def main():
    Shell()

if __name__ == "__main__":
    Shell()
