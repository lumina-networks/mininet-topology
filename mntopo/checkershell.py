"""Mininet Topology Tester.

Usage:
  mntest [--topology=FILE] [--loops=LOOPS] [--no-loop] [--retries=RETRY] [--interval=SEC] [--force-pings] [--delay=SEC]
  mntest test [--topology=FILE] [--loops=LOOPS] [--no-loop] [--retries=RETRY] [--interval=SEC] [--force-pings] [--delay=SEC]
  mntest links [-s] [--topology=FILE]
  mntest nodes [-s] [--topology=FILE]
  mntest flows [-s] [--topology=FILE]
  mntest save-flows [--dir=DIR]
  mntest put-flows [--dir=DIR]
  mntest delete-flows
  mntest (-h | --help)

Options:
  -h --help         Show this screen.
  --version         Show version.
  -s --stopped      If Mininet is not running.
  --no-loop         No loop in case of test.
  --delay=SEC       Number of seconds after successful test and before stopping services and network.
  --loops=LOOPS     Maximum number of loops.
  --topology=FILE   Topolofy file name [default: mn-topo.yml].
  --dir=DIR         Directory name to read/save flows [default: services].
  --retries=RETRY   Max number of retries.
  --interval=SEC    Interval in seconds between retries.

"""

import os
import sys
import yaml
from mntopo.docopt import docopt
import mntopo.checker
from mininet.log import setLogLevel, info, error


class Shell(object):

    def __init__(self):
        arguments = docopt(__doc__, version='Mininet Topology Tester 1.0')

        setLogLevel('info')
        file = 'mn-topo.yml'
        if arguments['--topology']:
            file = arguments['--topology']

        props = None
        if (os.path.isfile(file)):
            with open(file, 'r') as f:
                props = yaml.load(f)

        if props is None:
            print "ERROR: yml topology file {} not found".format(file)
            sys.exit()

        checker = mntopo.checker.Checker(props)

        if arguments['--no-loop']:
            checker.loop = False
        if arguments['--delay']:
            checker.delay = int(arguments['--delay'])
        if arguments['--loops']:
            checker.loop_max = int(arguments['--loops'])
        if arguments['--dir']:
            checker.servicesdir = arguments['--dir']
        if arguments['--retries']:
            checker.retries = int(arguments['--retries'])
        if arguments['--interval']:
            checker.retry_interval = int(arguments['--interval'])
        if arguments['--force-pings']:
            checker.force_pings = True

        if arguments['links'] and arguments['--stopped']:
            checker._check_links(0)
        elif arguments['links']:
            checker._check_links(checker.topo.number_of_swiches_links)
        elif arguments['flows']:
            checker._check_flows()
        elif arguments['nodes'] and arguments['--stopped']:
            checker._check_nodes(0)
        elif arguments['flows']:
            checker._check_nodes(checker.topo.number_of_switches)
        elif arguments['put-flows']:
            checker.put()
        elif arguments['save-flows']:
            checker.save()
        elif arguments['delete-flows']:
            checker.delete()
        else:
            checker.test()


def main():
    Shell()

if __name__ == "__main__":
    Shell()
