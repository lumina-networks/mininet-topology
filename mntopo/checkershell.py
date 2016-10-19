"""Mininet Topology Tester.

Usage:
  mntest [--topology=FILE] [--loops=LOOPS] [--no-loop] [--retries=RETRY] [--interval=SEC] [--force-pings] [--delay=SEC] [--ask-for-retry] [--no-links] [--controller=IP]...
  mntest test [--topology=FILE] [--loops=LOOPS] [--no-loop] [--retries=RETRY] [--interval=SEC] [--force-pings] [--delay=SEC] [--ask-for-retry] [--no-links] [--controller=IP]...
  mntest links [-s] [--topology=FILE] [--retries=RETRY] [--interval=SEC] [--ask-for-retry] [--controller=IP]...
  mntest nodes [-s] [--topology=FILE] [--retries=RETRY] [--interval=SEC] [--ask-for-retry] [--controller=IP]...
  mntest flows [-s] [--topology=FILE] [--retries=RETRY] [--interval=SEC] [--ask-for-retry] [--controller=IP]...
  mntest save-flows [--dir=DIR] [--controller=IP]...
  mntest put-flows [--dir=DIR] [--controller=IP]...
  mntest delete-flows [--controller=IP]...
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
  --ask-for-retry   The utility will prompt a question to confirm if it should retry or ignore in case of errors.
  --no-links        Do not check links.
  -c, --controller=IP   Controller IP address

"""

import os
import sys
import yaml
from docopt.docopt import docopt
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
            sys.exit(1)

        if arguments['--controller']:
            props['controller'] = []
            i = 0
            for ip in arguments['--controller']:
                props['controller'].append(
                    {'name': "c{}".format(i),
                     'ip': ip
                     })
                i = i + 1

        checker = mntopo.checker.Checker(props)

        if arguments['--no-loop']:
            checker.loop = False
        if arguments['--no-links']:
            checker.check_links = False
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
        if arguments['--ask-for-retry']:
            checker.ask_for_retry = True

        if arguments['links'] and arguments['--stopped']:
            result = checker._check_links(False)
        elif arguments['links']:
            result = checker._check_links()
        elif arguments['flows']:
            result = checker._check_flows()
        elif arguments['nodes'] and arguments['--stopped']:
            result = checker._check_nodes(False)
        elif arguments['nodes']:
            result = checker._check_nodes()
        elif arguments['flows']:
            result = checker._check_nodes()
        elif arguments['put-flows']:
            result = checker.put()
        elif arguments['save-flows']:
            result = checker.save()
        elif arguments['delete-flows']:
            result = checker.delete()
        else:
            result = checker.test()

        if not result:
            sys.exit(1)

def main():
    Shell()

if __name__ == "__main__":
    Shell()
