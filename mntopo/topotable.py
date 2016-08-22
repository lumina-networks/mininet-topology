#!/usr/bin/python

import sys
import yaml
import os
import argparse


def get_host(row, column):
    return {
        'name': 'h' + get_node_id(row, column),
        'ip': '10.0.' + str(row + 1) + '.' + str(column + 1) + '/16',
        'gw': '10.0.0.1'
    }


def get_switch(row, column):
    return {
        'name': get_switch_name(row, column), 'dpid': format(int(get_node_id(row, column)), 'x'), 'protocols': 'OpenFlow13'}


def get_switch_name(row, column):
    return 's' + get_node_id(row, column)


def get_node_id(row, column):
    return str(((row + 1) * 100) + (column + 1))


class TopoTable(object):

    def __init__(self):

        parser = argparse.ArgumentParser(
            description='Create a list table of switches for given number of rows and columns')

        parser.add_argument('--file', '-f', action="store", help="File name", type=str, default='mn-topo.yml')
        parser.add_argument('--rows', '-r', action="store", help="Number of rows", type=int, default=3)
        parser.add_argument('--columns', '-c', action="store", help="Number of columns", type=int, default=3)
        parser.add_argument('--links-per-rows', '-lr', action="store",
                            help="Links per each pair of switches connected horizontally", type=int, default=1)
        parser.add_argument('--links-per-columns', '-lc', action="store",
                            help="Links per each pair of switches connected vertically", type=int, default=1)
        parser.add_argument('--controller', '-co', action="store",
                            help="Controller ip address", type=str, default='172.24.86.211')

        inputs = parser.parse_args()

        data = dict()
        data['controller'] = [{'name': 'c0', 'ip': inputs.controller}]
        data['host'] = []
        data['switch'] = []
        data['link'] = []

        # we first calculate the host to ensure they are created in port 1 on all switches
        for row in range(0, inputs.rows):
            column = 0
            host = get_host(row, column)
            switch_name = get_switch_name(row, column)
            data['host'].append(get_host(row, column))
            data['link'].append({'source': host['name'], 'destination': switch_name})
            if (inputs.columns > 1):
                column = inputs.columns - 1
                host = get_host(row, column)
                switch_name = get_switch_name(row, column)
                data['host'].append(get_host(row, column))
                data['link'].append({'source': host['name'], 'destination': switch_name})

        for row in range(0, inputs.rows):
            for column in range(0, inputs.columns):

                switch = get_switch(row, column)
                right = get_switch_name(row, column + 1)
                bottom = get_switch_name(row + 1, column)

                data['switch'].append(switch)

                if column < inputs.columns - 1:
                    for repeat in range(0, inputs.links_per_rows):
                        data['link'].append({'source': switch['name'], 'destination': right})

                if row < inputs.rows - 1:
                    for repeat in range(0, inputs.links_per_columns):
                        data['link'].append({'source': switch['name'], 'destination': bottom})

        with open(inputs.file, 'w') as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))


def main():
    TopoTable()

if __name__ == "__main__":
    TopoTable()
