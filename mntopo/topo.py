import subprocess
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

        self.hosts_ip = {}
        hosts_ip = self.hosts_ip

        self.switches = {}
        switches = self.switches

        self.switches_openflow_names = {}
        switches_openflow_names = self.switches_openflow_names

        self.interfaces = {}
        interfaces = self.interfaces

        self.portmap = {}
        self.host_connected_switch = {}
        self.number_of_swiches_links = 0
        self.number_of_switches = 0

        #switchClass = UserSwitch
        #switchClass = OVSSwitch
        switchClass = partial(OVSSwitch, datapath='user')

        topo = MNTopo()

        if 'host' not in props or props['host'] is None:
            props['host'] = []

        for host in props['host']:
            hosts[host['name']] = topo.addHost(host['name'], ip=host['ip'], defaultRoute='via ' + host['gw'])
            hosts_ip[host['name']] = host['ip'].split('/')[0]

        if 'switch' not in props or props['switch'] is None:
            props['switch'] = []

        self.number_of_switches = len(props['switch'])
        for switch in props['switch']:
            name = switch['name']
            switches[name] = topo.addSwitch(name, dpid=switch['dpid'], protocols=switch['protocols'])
            switches_openflow_names[name] = "openflow:" + str(int(switch['dpid'], 16))

        if 'link' not in props or props['link'] is None:
            props['link'] = []

        # create mininet connections
        for link in props['link']:
            src_name = link['source']
            dst_name = link['destination']

            source = None
            if src_name in switches:
                source = switches[src_name]
            else:
                source = hosts[src_name]

            destination = None
            if dst_name in switches:
                destination = switches[dst_name]
            else:
                destination = hosts[dst_name]

            topo.addLink(source, destination)

            if src_name in switches and dst_name in switches:
                self.number_of_swiches_links = self.number_of_swiches_links + 2

        # save port mapping
        ports = {}
        for link in props['link']:
            src = link['source']
            if src not in ports:
                ports[src] = 1
            src_port = ports[src]
            ports[src] = ports[src] + 1

            dst = link['destination']
            if dst not in ports:
                ports[dst] = 1
            dst_port = ports[dst]
            ports[dst] = ports[dst] + 1

            if src not in self.portmap:
                self.portmap[src] = {}
            self.portmap[src][dst] = src_port

            if dst not in self.portmap:
                self.portmap[dst] = {}
            self.portmap[dst][src] = dst_port

            # skip connections between hosts
            if src in self.hosts and dst in self.hosts:
                continue

            # save the connected switch by host
            if (src in self.hosts and dst in self.switches):
                self.host_connected_switch[src] = dst
            elif (dst in self.hosts and src in self.switches):
                self.host_connected_switch[dst] = src

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
        for switch in self.switches:
            if exists_bridge(switch):
                print "WARNING: brigde {} is running. going to delete it.".format(switch)
                delete_bridge(switch)
        self.net.start()

    def cli(self):
        CLI(self.net)

    def stop(self):
        self.net.stop()
        for switch in self.switches:
            if exists_bridge(switch):
                print "WARNING: node {} was running after stopping mininet".format(switch)
                delete_bridge(switch)


def exists_bridge(name):
    try:
        grepOut = subprocess.check_output("sudo ovs-vsctl br-exists {}".format(name), shell=True)
        return True
    except subprocess.CalledProcessError as grepexc:
        return False


def delete_bridge(name):
    try:
        grepOut = subprocess.check_output("sudo ovs-vsctl del-br {}".format(name), shell=True)
        return True
    except subprocess.CalledProcessError as grepexc:
        print "ERROR: {} bridge cannot be deleted".format(name)
        return False
