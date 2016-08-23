"""Flow Manager Tester.

Usage:
  mnfm [topology-file]
  mnfm test [topology-file]
  mnfm links [--stopped] [topology-file]
  mnfm nodes [--stopped] [topology-file]
  mnfm flows [--stopped] [topology-file]
  mnfm (-h | --help)

Options:
  -h --help     Show this screen.
  --version     Show version.
  --stopped     If Mininet is not running.

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
        if arguments['links'] and arguments['--stopped']:
            checker._check_links(0)
        elif arguments['links']:
            checker._check_links(checker.topo.expected_links)
        elif arguments['flows']:
            checker._check_flows()
        elif arguments['nodes'] and arguments['--stopped']:
            checker._check_nodes(0)
        elif arguments['flows']:
            checker._check_nodes(checker.topo.expected_nodes)
        else:
            checker.test()


def main():
    Shell()

if __name__ == "__main__":
    Shell()
