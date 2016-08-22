import sys
import yaml
import os
import argparse


class TopoDataCenter(object):

    def __init__(self):

        parser = argparse.ArgumentParser(
            description='Create a list table of switches for given number of rows and columns')

        parser.add_argument('--file', '-f', action="store", help="File name", type=str, default='mn-topo.yml')
        parser.add_argument('--spines', '-s', action="store", help="Number of spines", type=int, default=4)
        parser.add_argument('--leafs', '-l', action="store", help="Number of leafs", type=int, default=12)
        parser.add_argument('--computes', '-c', action="store", help="Number of leafs", type=int, default=10)
        parser.add_argument('--datacenters', '-d', action="store",
                            help="Links per each pair of switches connected horizontally", type=int, default=1)
        parser.add_argument('--controller', '-co', action="store",
                            help="Controller ip address", type=str, default='172.24.86.211')

        inputs = parser.parse_args()

        data = dict()
        data['controller'] = [{'name': 'c0', 'ip': inputs.controller}]
        data['host'] = []
        data['switch'] = []
        data['link'] = []

        for datacenter in range(0, inputs.datacenters):
            dc_base = (datacenter + 1) * 10000
            for spine in range(0, inputs.spines):
                name = str(dc_base + (spine + 5001))
                switch = 's' + name
                data['switch'].append({'name': switch, 'dpid': format(int(name), 'x'), 'protocols': 'OpenFlow13'})

            for leaf in range(0, inputs.leafs):
                name = str(dc_base + (leaf + 1))
                switch = 'l' + name
                data['switch'].append({'name': switch, 'dpid': format(int(name), 'x'), 'protocols': 'OpenFlow13'})

                for compute in range(0, inputs.computes):
                    compute_name = 'h' + str(dc_base + ((leaf + 1) * 1000) + (compute + 1))
                    data['host'].append({'name': compute_name, 'ip': '10.' + str(datacenter + 1) + "." +
                                         str(leaf + 1) + '.' + str(compute + 1) + '/16', 'gw': '10.' + str(datacenter + 1) + '.0.1'})
                    data['link'].append({'source': compute_name, 'destination': switch})

                for spine in range(0, inputs.spines):
                    spine_name = 's' + str(dc_base + (spine + 5001))
                    data['link'].append({'source': switch, 'destination': spine_name})

        with open(inputs.file, 'w') as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))


def main():
    TopoDataCenter()

if __name__ == "__main__":
    TopoDataCenter()
