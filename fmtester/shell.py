import os
import sys
import yaml
import fmtester.fm
from mininet.log import setLogLevel, info, error


class Shell(object):

    def __init__(self):
        setLogLevel('info')
        file = 'mn-topo.yml'
        if len(sys.argv) > 1:
            file = sys.argv[1]

        props = None
        if (os.path.isfile(file)):
            with open(file, 'r') as f:
                props = yaml.load(f)

        if props is None:
            print "ERROR: yml topology file not found"
        else:
            checker = fmtester.fm.Checker(props)
            checker.test()


def main():
    Shell()

if __name__ == "__main__":
    Shell()
