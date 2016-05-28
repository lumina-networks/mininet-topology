#!/usr/bin/python

import re
import sys
import yaml
import os

from functools import partial

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node , Controller, RemoteController, UserSwitch, OVSSwitch
from mininet.log import setLogLevel, info, error
from mininet.cli import CLI
from mininet.util import irange
from mininet.link import Intf,Link,TCLink
from mininet.util import quietRun, irange
from mininet.topolib import TreeTopo


def run(file):

    default_controllers=[]
    hosts={}
    switches={}
    interfaces={}

    #switchClass = UserSwitch
    #switchClass = OVSSwitch
    switchClass = partial( OVSSwitch, datapath='user' )

    if (os.path.isfile(file)):
        with open(file, 'r') as f:
            props = yaml.load(f)


    topo = Topo()

    for host in props['host']:
        hosts[host['name']]=topo.addHost( host['name'], ip=host['ip'], defaultRoute='via ' + host['gw'] )


    for switch in props['switch']:        
        switches[switch['name']]=topo.addSwitch( switch['name'], dpid=switch['dpid'],protocols=switch['protocols'] )

    for link in props['link']:
        source = None
        if link['source'] in switches:
            source = switches[link['source']]
        else:
            source = hosts[link['source']]

        destination = None
        if link['destination'] in switches:
            destination = switches[link['destination']]
        else:
            destination = hosts[link['destination']]

        topo.addLink(source,destination)


    for controller in props['controller']:
        default_controllers.append(RemoteController( controller['name'], ip=controller['ip'] ))

    net = Mininet( topo=topo, switch=switchClass,controller=default_controllers[0])

    if 'interface' in props and props['interface'] is not None:
        for interface in props['interface']:
            Intf( interface['name'], node=net.nameToNode[interface['switch']] )



    net.start()
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    file = 'mn-topo.yml'
    if len(sys.argv) > 1:
        file = sys.argv[1]
    run(file)
