"""Topology Table Generator

Usage:
  topotb [--file=FILE] [--rows=ROWS] [--columns=COLUMNS] [--links-per-rows=LINKS_PER_ROWS] [--links-per-columns=LINKS_PER_COLUMNS] [--controller=IP]...
  topotb (-h | --help)

Options:
  -h --help     Show this screen.
  -f, --file=FILE   Topolofy file name [default: mn-topo.yml].
  -r, --rows=ROWS   Number of rows [default: 3].
  -c, --columns=COLUMNS   Number of rows [default: 3].
  -x, --links-per-rows=LINKS_PER_ROWS   Number of links connecting per pair horizontal switches [default: 1].
  -z, --links-per-columns=LINKS_PER_COLUMNS   Number of links connecting per pair vertical switches  [default: 1].
  -o, --controller=IP   Controller IP address
  --version     Show version.

"""

import sys
import yaml
import os
from docopt.docopt import docopt


def get_host(row, column):
    return {
        'name': 'h' + get_node_id(row, column),
        'ip': '10.0.' + str(row + 1) + '.' + str(column + 1) + '/16',
        'mac': "00:00:10:00:{:02d}:{:02d}".format(row + 1, column + 1),
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

        arguments = docopt(__doc__, version='Topology Table Generator 1.0')
        file_name = arguments['--file'] if arguments['--file'] else 'mn-topo.yml'
        rows = int(arguments['--rows']) if arguments['--rows'] else 3
        columns = int(arguments['--columns']) if arguments['--columns'] else 3
        links_per_rows = int(arguments['--links-per-rows']) if arguments['--links-per-rows'] else 1
        links_per_columns = int(arguments['--links-per-columns']) if arguments['--links-per-columns'] else 1

        data = dict()
        data['controller'] = []
        if arguments['--controller']:
            index = 0
            for ctrl in arguments['--controller']:
                data['controller'].append({'name': 'c'+ str(index), 'ip': ctrl})
                index = index + 1
        else:
            data['controller'].append({'name': 'c0', 'ip': '127.0.0.1'})
        data['host'] = []
        data['switch'] = []
        data['link'] = []

        # we first calculate the host to ensure they are created in port 1 on all switches
        for row in range(0, rows):
            column = 0
            host = get_host(row, column)
            switch_name = get_switch_name(row, column)
            data['host'].append(get_host(row, column))
            data['link'].append({'source': host['name'], 'destination': switch_name})
            if (columns > 1):
                column = columns - 1
                host = get_host(row, column)
                switch_name = get_switch_name(row, column)
                data['host'].append(get_host(row, column))
                data['link'].append({'source': host['name'], 'destination': switch_name})

        for row in range(0, rows):
            for column in range(0, columns):

                switch = get_switch(row, column)
                right = get_switch_name(row, column + 1)
                bottom = get_switch_name(row + 1, column)

                data['switch'].append(switch)

                if column < columns - 1:
                    for repeat in range(0, links_per_rows):
                        data['link'].append({'source': switch['name'], 'destination': right})

                if row < rows - 1:
                    for repeat in range(0, links_per_columns):
                        data['link'].append({'source': switch['name'], 'destination': bottom})

        with open(file_name, 'w') as outfile:
            outfile.write(yaml.dump(data, default_flow_style=False))


def main():
    TopoTable()

if __name__ == "__main__":
    TopoTable()
