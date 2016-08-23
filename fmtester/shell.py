"""Flow Manager Tester.

Usage:
  mnfm [topology-file] [--loops=LOOPS] [--no-loop]
  mnfm test [topology-file] [--loops=LOOPS] [--no-loop]
  mnfm links [-s] [topology-file]
  mnfm nodes [-s] [topology-file]
  mnfm flows [-s] [topology-file]
  mnfm (-h | --help)

Options:
  -h --help             Show this screen.
  --version             Show version.
  -s --stopped          If Mininet is not running.
  --no-loop             No loop in case of test.
  --loops=LOOPS     Maximum number of loops.

"""

import os
import sys
import yaml
from mntopo.docopt import docopt
import fmtester.fm
from mininet.log import setLogLevel, info, error


class Shell(object):

    def __init__(self):
        arguments = docopt(__doc__, version='Flow Manager Tester 1.0')

        setLogLevel('info')
        file = 'mn-topo.yml'
        if arguments['topology-file']:
            file = arguments['topology-file']

        props = None
        if (os.path.isfile(file)):
            with open(file, 'r') as f:
                props = yaml.load(f)

        if props is None:
            print "ERROR: yml topology file not found"
            sys.exit()

        checker = fmtester.fm.Checker(props)

        if arguments['--no-loop']:
            checker.loop = False
        if arguments['--loops']:
            checker.loop_max = int(arguments['--loops'])

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
        else:
            checker.test()


def main():
    Shell()

if __name__ == "__main__":
    Shell()
