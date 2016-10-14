import mntopo.topo
import mntopo.checker
import os
import json
import requests
import time
from requests.auth import HTTPBasicAuth


class Checker(mntopo.checker.Checker):
    """ Openflow Flow ManagerChecker """

    def __init__(self, props):
        super(Checker, self).__init__(props)
        self.check_bsc = get_property(self.testprops, 'check_bsc', True)
        self.recreate_services = get_property(self.testprops, 'recreate_services', True)

        # if pings not provided let's just create ours
        if self.pings is None and self.check_bsc:
            self.pings = []
            current = None
            for name in sorted(self.topo.hosts):
                if current is None:
                    current = {}
                    current['source'] = name
                else:
                    current['destination'] = name
                    self.pings.append(current)
                    current = None

    def test(self):

        first_iteration = True
        current_loop = self.loop_max
        while self.loop_max <= 0 or current_loop > 0:
            if current_loop > 0:
                current_loop = current_loop - 1

            if first_iteration or self.recreate_services:
                first_iteration = False
                self.create_pings()

            self.topo.start()

            t = time.time()

            if self.check_links:
                if not self._check_links():
                    self.topo.stop()
                    return False

            if self.check_nodes:
                if not self._check_nodes():
                    self.topo.stop()
                    return False

            print "links and nodes detected in {} seconds".format(round((time.time() - t), 3))

            if not self._test_pings():
                self.topo.stop()
                return False

            print "ping worked after {} seconds".format(round((time.time() - t), 3))

            if self.check_flows:
                if not self._check_flows():
                    self.topo.stop()
                    return False

            self.counter()

            if self.delay > 0:
                time.sleep(self.delay)

            if self.recreate_services:
                self.delete_pings()

            if not self.loop:
                self.topo.stop()
                break
            if self.loop_interval > 0:
                time.sleep(self.loop_interval)

            print "stopping mininet"
            self.topo.stop()
            print "stopped mininet"
            t = time.time()

            if self.check_links:
                if not self._check_links(False):
                    return False

            if self.check_nodes:
                if not self._check_nodes(False):
                    return False

            print "links and nodes removed in {} seconds".format(round((time.time() - t), 3))

            if self.check_flows:
                if not self._check_flows():
                    return False

            self.counter()
        return True

    def _get_config_eline_url(self, name):
        return self._get_config_url() + '/brocade-bsc-eline:elines/eline/{}'.format(name)

    def _get_config_path_url(self, name):
        return self._get_config_url() + '/brocade-bsc-path:paths/path/{}'.format(name)

    def _get_calculated_flows_groups(self):
        srnodes = {}
        resp = self._http_get(self._get_operational_url() + '/network-topology:network-topology/topology/flow:1:sr')
        if resp is not None and resp.status_code == 200 and resp.content is not None:
            data = json.loads(resp.content)
            topology = data.get('topology')
            nodes = None
            if topology is not None and len(topology) > 0:
                nodes = topology[0].get('node')
                if nodes is not None:
                    for node in nodes:
                        nodeid = node['node-id']
                        srnodes[nodeid] = {'groups': [], 'flows': []}
                        brocadesr = node.get('brocade-bsc-sr:sr')
                        groups = None
                        if brocadesr is not None:
                            groups = brocadesr.get('calculated-groups')
                        if groups is not None:
                            cgroups = groups.get('calculated-group')
                            if cgroups is not None:
                                for group in cgroups:
                                    srnodes[nodeid]['groups'].append(group['group-id'])

                        flows = None
                        if brocadesr is not None:
                            append_calculated_flows(srnodes, brocadesr.get('calculated-flows'))

        resp = self._http_get(self._get_operational_url() + '/brocade-bsc-path:paths')
        if resp is not None and resp.status_code == 200 and resp.content is not None:
            data = json.loads(resp.content)
            if data.get('paths') is not None:
                paths = data.get('paths')
                if paths.get('path') is not None:
                    for path in paths.get('path'):
                        append_calculated_flows(srnodes, path.get('calculated-flows'))

                if paths.get('mpls-nodes') is not None:
                    append_calculated_flow_nodes(srnodes, paths.get('mpls-nodes').get('calculated-flow-nodes'))

        resp = self._http_get(self._get_operational_url() + '/brocade-bsc-eline:elines')
        if resp is not None and resp.status_code == 200 and resp.content is not None:
            data = json.loads(resp.content)
            if data.get('elines') is not None:
                elines = data.get('elines')
                if elines.get('eline') is not None:
                    for eline in elines.get('eline'):
                        append_calculated_flows(srnodes, eline.get('calculated-flows'))

        resp = self._http_get(self._get_operational_url() + '/brocade-bsc-path-mpls:mpls-nodes')
        if resp is not None and resp.status_code == 200 and resp.content is not None:
            data = json.loads(resp.content)
            mpls_nodes = data.get('mpls-nodes')
            if mpls_nodes is not None:
                append_calculated_flow_nodes(srnodes, mpls_nodes.get('calculated-flow-nodes'))

        resp = self._http_get(self._get_operational_url() + '/brocade-bsc-eline-mpls:eline-nodes')
        if resp is not None and resp.status_code == 200 and resp.content is not None:
            data = json.loads(resp.content)
            mpls_nodes = data.get('eline-nodes')
            if mpls_nodes is not None:
                append_calculated_flow_nodes(srnodes, mpls_nodes.get('calculated-flow-nodes'))

        return srnodes

    def _get_flow_group(self, url, prefix=None):
        nodes = super(Checker, self)._get_flow_group(url, prefix)
        if nodes is None:
            return {}

        for nodeid in nodes:
            flowsbscids = {}
            nodes[nodeid]['flowsbscids'] = flowsbscids

            for flowid, flow in nodes[nodeid]['flows'].iteritems():
                cookie = flow.get('cookie')
                if cookie is not None and cookie >> 56 == prefix:
                    flow['bscversion'] = (cookie & 0x00000000FF000000) >> 24
                    flow['bscid'] = (cookie & 0x00FFFFFF00000000) >> 32
                    flowsbscids[flow['bscid']] = flowid
                else:
                    flow['bscid'] = cookie
                    flowsbscids[flow['bscid']] = flowid

        return nodes

    def create_pings(self):
        for ping in self.pings:
            src = ping['source']
            srcsw = self.topo.host_connected_switch[src]
            srcsw_name = self.topo.switches_openflow_names[srcsw]
            srcport = self.topo.portmap[srcsw][src]
            dst = ping['destination']
            dstsw = self.topo.host_connected_switch[dst]
            dstsw_name = self.topo.switches_openflow_names[dstsw]
            dstport = self.topo.portmap[dstsw][dst]
            name = src + dst

            pathurl = self._get_config_path_url(name)
            self._http_put(pathurl, json.dumps({
                "path": [
                    {
                        "name": name,
                        "provider": "sr",
                        "endpoint1": {
                            "node": srcsw_name
                        },
                        "endpoint2": {
                            "node": dstsw_name
                        }
                    }
                ]

            }))

            elinename = name + '-arp'
            elineurl = self._get_config_eline_url(elinename)
            self._http_put(elineurl, json.dumps({
                "eline": [{
                    "name": elinename,
                    "path-name": name,
                    "endpoint1": {
                        "match": {
                            "in-port": srcport,
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 2054
                                }
                            }
                        },
                        "egress": {
                            "action": [
                                {
                                    "order": 3,
                                    "output-action": {
                                        "output-node-connector": srcport
                                    }
                                }
                            ]
                        }
                    },
                    "endpoint2": {
                        "match": {
                            "in-port": dstport,
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 2054
                                }
                            }
                        },
                        "egress": {
                            "action": [
                                {
                                    "order": 3,
                                    "output-action": {
                                        "output-node-connector": dstport
                                    }
                                }
                            ]
                        }
                    },
                    "provider": "mpls"
                }]
            }))

            elinename = name + '-ip'
            elineurl = self._get_config_eline_url(elinename)
            self._http_put(elineurl, json.dumps({
                "eline": [{
                    "name": elinename,
                    "path-name": name,
                    "endpoint1": {
                        "match": {
                            "in-port": srcport,
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 2048
                                }
                            }
                        },
                        "egress": {
                            "action": [
                                {
                                    "order": 3,
                                    "output-action": {
                                        "output-node-connector": srcport
                                    }
                                }
                            ]
                        }
                    },
                    "endpoint2": {
                        "match": {
                            "in-port": dstport,
                            "ethernet-match": {
                                "ethernet-type": {
                                    "type": 2048
                                }
                            }
                        },
                        "egress": {
                            "action": [
                                {
                                    "order": 3,
                                    "output-action": {
                                        "output-node-connector": dstport
                                    }
                                }
                            ]
                        }
                    },
                    "provider": "mpls"
                }]
            }))

    def delete_pings(self):
        for ping in self.pings:
            src = ping['source']
            dst = ping['destination']
            name = src + dst

            pathurl = self._get_config_path_url(name)
            self._http_delete(pathurl)

            elinename = name + '-arp'
            elineurl = self._get_config_eline_url(elinename)
            self._http_delete(elineurl)

            elinename = name + '-ip'
            elineurl = self._get_config_eline_url(elinename)
            self._http_delete(elineurl)

    def _check_links(self, running=True):
        print "checking for links while network is running={}".format(running)
        current_retries = self.retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            if self._is_valid_topology_links(running, 'flow:1') and self._is_valid_topology_links(running, 'flow:1:sr'):
                return True

            time.sleep(self.retry_interval)
            if current_retries == 0:
                retry, ignore = self._ask_retry()
                if ignore:
                    return True
                if retry:
                    current_retries = self.retries

        return False

    def _check_nodes(self, running=True):
        print "checking for nodes while network is running={}".format(running)
        current_retries = self.retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            if self._is_valid_topology_nodes(running, 'flow:1') and self._is_valid_topology_nodes(running, 'flow:1:sr'):
                return True
            if current_retries > 0:
                time.sleep(self.retry_interval)
            if current_retries == 0:
                retry, ignore = self._ask_retry()
                if ignore:
                    return True
                if retry:
                    current_retries = self.retries

        return False

    def _check_flows(self):
        current_retries = self.retries
        while (current_retries > 0):
            error_found = False
            current_retries = current_retries - 1
            ovs_flows_groups = self.topo.get_nodes_flows_groups(0x1f)
            calculated_nodes = self._get_calculated_flows_groups()
            config_nodes = self._get_flow_group(self._get_config_openflow(), 0x1f)
            operational_nodes = self._get_flow_group(self._get_operational_openflow(), 0x1f)
            if self.check_bsc:
                for nodeid in calculated_nodes:
                    node = calculated_nodes[nodeid]
                    if 'flows' in node:
                        for flowid in node['flows']:
                            if nodeid not in config_nodes or flowid not in config_nodes[nodeid]['flows']:
                                print "ERROR: node {} calculated flow {} not configured".format(nodeid, flowid)
                                error_found = True

                    if 'groups' in node:
                        for groupid in node['groups']:
                            if nodeid not in config_nodes or groupid not in config_nodes[nodeid]['groups']:
                                print "ERROR: node {} calculate group {} not configured".format(nodeid, groupid)
                                error_found = True

            for nodeid in config_nodes:
                node = config_nodes[nodeid]
                if 'flows' in node:
                    for flowid in node['flows']:
                        bscid = node['flows'][flowid]['bscid']
                        if nodeid not in operational_nodes or bscid not in operational_nodes[nodeid]['flowsbscids']:
                            print "ERROR: node {} flow {} not running".format(nodeid, flowid)
                            error_found = True
                        if nodeid not in calculated_nodes or flowid not in calculated_nodes[nodeid]['flows']:
                            print "ERROR: node {} flow {} not present in calculated nodes".format(nodeid, flowid)
                            error_found = True
                        if nodeid not in ovs_flows_groups or bscid not in ovs_flows_groups[nodeid]['bscids']:
                            print "ERROR: node {} flow {} configured but not in OVS switch".format(nodeid, flowid)
                            error_found = True
                        elif node['flows'][flowid]['cookie'] not in ovs_flows_groups[nodeid]['cookies']:
                            print "WARNING: node {} flow {} configured in OVS but not running same version".format(nodeid, flowid)

                if 'groups' in node:
                    for groupid in node['groups']:
                        if nodeid not in operational_nodes or 'groups' not in operational_nodes[nodeid] or groupid not in operational_nodes[nodeid]['groups']:
                            print "ERROR: node {} group {} not running".format(nodeid, groupid)
                            error_found = True
                        if nodeid not in calculated_nodes or groupid not in calculated_nodes[nodeid]['groups']:
                            print "ERROR: node {} group {} group not present in calculated groups".format(nodeid, flowid)
                            error_found = True
                        if nodeid not in ovs_flows_groups or groupid not in ovs_flows_groups[nodeid]['groups']:
                            print "ERROR: node {} group {} configured but not in OVS".format(nodeid, groupid)
                            error_found = True

            for nodeid in operational_nodes:
                node = operational_nodes[nodeid]
                if 'flows' in node:
                    for flowid in node['flows']:
                        bscid = node['flows'][flowid]['bscid']
                        if nodeid not in config_nodes or bscid not in config_nodes[nodeid]['flowsbscids']:
                            print "ERROR: node {} flow {} running but not configured".format(nodeid, flowid)
                            error_found = True

                if 'groups' in node:
                    for groupid in node['groups']:
                        if nodeid not in config_nodes or 'groups' not in config_nodes[nodeid] or groupid not in config_nodes[nodeid]['groups']:
                            print "ERROR: node {} group {} running but not configured".format(nodeid, groupid)
                            error_found = True

            for nodeid in ovs_flows_groups:
                node = ovs_flows_groups[nodeid]
                if 'bscids' in node:
                    for bscid in node['bscids']:
                        if nodeid not in config_nodes or bscid not in config_nodes[nodeid]['flowsbscids']:
                            print "ERROR: node {} flow {} running in OVS but not configured".format(nodeid, flowid)
                            error_found = True

                if 'groups' in node:
                    for groupid in node['groups']:
                        if nodeid not in config_nodes or 'groups' not in config_nodes[nodeid] or groupid not in config_nodes[nodeid]['groups']:
                            print "ERROR: node {} group {} running in OVS but not configured".format(nodeid, groupid)
                            error_found = True

            if not error_found:
                return True
            if current_retries > 0:
                time.sleep(self.retry_interval)
            if current_retries == 0:
                retry, ignore = self._ask_retry()
                if ignore:
                    return True
                if retry:
                    current_retries = self.retries

        return False


def get_property(props, name, default_value=None):
    if props is not None:
        value = props.get(name)
        if value is not None:
            return value
    return default_value


def append_calculated_flow_nodes(nodes, cnodes):
    if cnodes is not None:
        cnodes = cnodes.get('calculated-flow-node')
        if cnodes is not None:
            for cnode in cnodes:
                append_calculated_flows(nodes, cnode.get('calculated-flows'))


def append_calculated_flows(nodes, flows):
    if flows is not None:
        cflows = flows.get('calculated-flow')
        if cflows is not None:
            for flow in cflows:
                flowid = 'table/{}/flow/{}'.format(flow['table-id'], flow['flow-name'])
                nodeid = flow['node-id']
                if nodeid not in nodes:
                    nodes[nodeid] = {'groups': [], 'flows': []}
                nodes[nodeid]['flows'].append(flowid)
