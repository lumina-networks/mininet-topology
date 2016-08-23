import re
import subprocess
from functools import partial

from mininet.clean import cleanup
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
        self.switchClass = partial(OVSSwitch, datapath='user')

        topo = MNTopo()
        self.topo = topo

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

    def start(self):
        cleanup()

        self.net = Mininet(topo=self.topo, switch=self.switchClass, controller=self.controllers[0])

        if 'interface' not in self.props or self.props['interface'] is None:
            self.props['interface'] = []

        for interface in self.props['interface']:
            name = interface['name']
            interfaces[name] = Intf(name, node=net.nameToNode[interface['switch']])

        self.net.start()

    def cli(self):
        CLI(self.net)

    def stop(self):
        self.net.stop()
        cleanup()

    def get_nodes_flows_groups(self, prefix=None):
        nodes = {}
        for name in self.switches_openflow_names:
            if not exists_bridge(name):
                continue
            oname = self.switches_openflow_names[name]
            nodes[oname] = {'cookies': [], 'groups': [],'bscids':{}}
            output = subprocess.check_output(
                "sudo ovs-ofctl dump-groups {} --protocol=Openflow13".format(name), shell=True)
            pattern = r'group_id=(\d+)'
            regex = re.compile(pattern, re.IGNORECASE)
            for match in regex.finditer(output):
                nodes[oname]['groups'].append(int(match.group(1)))

            output = subprocess.check_output(
                "sudo ovs-ofctl dump-flows {} --protocol=Openflow13".format(name), shell=True)
            pattern = r'cookie=(0[xX][0-9a-fA-F]+)'
            regex = re.compile(pattern, re.IGNORECASE)
            for match in regex.finditer(output):
                number = int(match.group(1), 16)
                nodes[oname]['cookies'].append(number)
                if prefix is None:
                    continue
                if number >> 56 == prefix:
                    bscid = (number & 0x00FFFFFF00000000) >> 32
                    nodes[oname]['bscids'][bscid]= {
                        'cookie': number,
                        'version': (number & 0x00000000FF000000) >> 24
                    }

        return nodes


def exists_bridge(name):
    try:
        grepOut = subprocess.check_output("sudo ovs-vsctl br-exists {}".format(name), shell=True)
        return True
    except subprocess.CalledProcessError as grepexc:
        return False
