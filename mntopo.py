from functools import partial

from mininet.topo import Topo as MNTopo
from mininet.net import Mininet
from mininet.node import Node, Controller, RemoteController, UserSwitch, OVSSwitch
from mininet.cli import CLI
from mininet.util import irange
from mininet.link import Intf, Link, TCLink
from mininet.util import quietRun, irange
from mininet.topolib import TreeTopo


class Topo(object):

    def __init__(self, props):
        self.props = props

        self.controllers = []
        controllers = self.controllers

        self.hosts = {}
        hosts = self.hosts

        self.switches = {}
        switches = self.switches

        self.interfaces = {}
        interfaces = self.interfaces

        #switchClass = UserSwitch
        #switchClass = OVSSwitch
        switchClass = partial(OVSSwitch, datapath='user')

        topo = MNTopo()

        if 'host' not in props or props['host'] is None:
            props['host'] = []

        for host in props['host']:
            hosts[host['name']] = topo.addHost(host['name'], ip=host['ip'], defaultRoute='via ' + host['gw'])

        if 'switch' not in props or props['switch'] is None:
            props['switch'] = []

        for switch in props['switch']:
            switches[switch['name']] = topo.addSwitch(
                switch['name'], dpid=switch['dpid'], protocols=switch['protocols'])

        if 'link' not in props or props['link'] is None:
            props['link'] = []

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

            topo.addLink(source, destination)

        if 'controller' not in props or props['controller'] is None:
            props['controller'] = []

        for controller in props['controller']:
            controllers.append(RemoteController(controller['name'], ip=controller['ip']))

        self.net = Mininet(topo=topo, switch=switchClass, controller=controllers[0])

        if 'interface' not in props or props['interface'] is None:
            props['interface'] = []

        for interface in props['interface']:
            name = interface['name']
            interfaces[name] = Intf(name, node=net.nameToNode[interface['switch']])

    def start(self):
        self.net.start()

    def cli(self):
        CLI(self.net)

    def stop(self):
        self.net.stop()
