"""Topology Data Center Generator

Usage:
  topodc [--file=FILE] [--spines=SPINES] [--leafs=LEAFS] [--computes=COMPUTES] [--datacenters=DATACENTERS] [--interfaces=INTERFACES]... [--controller=IP]...
  topodc (-h | --help)

Options:
  -h --help     Show this screen.
  -f, --file=FILE   Topolofy file name [default: mn-topo.yml].
  -s, --spines=SPINES   Number of spines [default: 2].
  -l, --leafs=LEAFS   Number of leafs [default: 4].
  -p, --computes=COMPUTES   Number of computes per leaf [default: 1].
  -d, --datacenters=DATACENTERS   Number of datacenters [default: 1].
  -c, --controller=IP   Controller IP address
  -i, --interfaces=INTERFACES   List of interface to switch mappings, colon as delimiter <switch:interface>
  --version     Show version.

"""

import sys
import yaml
import os
from docopt.docopt import docopt


class TopoDataCenter(object):

    def __init__(self):

        arguments = docopt(__doc__, version='Topology Table Generator 1.0')
        file_name = arguments['--file'] if arguments['--file'] else 'mn-topo.yml'
        spines = int(arguments['--spines']) if arguments['--spines'] else 2
        leafs = int(arguments['--leafs']) if arguments['--leafs'] else 4
        computes = int(arguments['--computes']) if arguments['--computes'] else 1
        datacenters = int(arguments['--datacenters']) if arguments['--datacenters'] else 1

        data = dict()
        data['controller'] = []
        if arguments['--controller']:
            index = 0
            for ctrl in arguments['--controller']:
                data['controller'].append({'name': 'c' + str(index), 'ip': ctrl})
                index = index + 1
        else:
            data['controller'].append({'name': 'c0', 'ip': '127.0.0.1'})

        data['host'] = []
        data['switch'] = []
        data['link'] = []

        for datacenter in range(0, datacenters):
            dc_base = (datacenter + 1) * 10000
            for spine in range(0, spines):
                name = str(dc_base + (spine + 5001))
                switch = 's' + name
                data['switch'].append({'name': switch, 'dpid': format(int(name), 'x'), 'protocols': 'OpenFlow13'})

            for leaf in range(0, leafs):
                name = str(dc_base + (leaf + 1))
                switch = 'l' + name
                data['switch'].append({'name': switch, 'dpid': format(int(name), 'x'), 'protocols': 'OpenFlow13'})

                for compute in range(0, computes):
                    compute_name = 'h' + str(dc_base + ((leaf + 1) * 1000) + (compute + 1))
                    data['host'].append({'name': compute_name,
                                         'ip': '10.' + str(datacenter + 1) + "." + str(leaf + 1) + '.' + str(compute + 1) + '/16',
                                         'gw': '10.' + str(datacenter + 1) + '.0.1',
                                         'mac': "00:00:10:{:02d}:{:02d}:{:02d}".format(datacenter + 1, leaf + 1, compute + 1),
                                         })
                    data['link'].append({'source': compute_name, 'destination': switch})

                for spine in range(0, spines):
                    spine_name = 's' + str(dc_base + (spine + 5001))
                    data['link'].append({'source': switch, 'destination': spine_name})

        data['interface'] = []
        if arguments['--interfaces']:
            for inter in arguments['--interfaces']:
                name, switch = inter.split(':')
                data['interface'].append({'name': name, 'switch': switch})

        with open(file_name, 'w') as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))


def main():
    TopoDataCenter()

if __name__ == "__main__":
    TopoDataCenter()
