import mntopo.topo
import os
import json
import requests
import time
from requests.auth import HTTPBasicAuth


_DEFAULT_HEADERS = {
    'content-type': 'application/json',
    'accept': 'application/json'
}


class Checker(object):
    """ Openflow Checker """

    def __init__(self, props):
        self.props = props
        self.topo = mntopo.topo.Topo(self.props)

        self.fmprops = props.get('fm')
        fmprops = self.fmprops
        if self.fmprops is None:
            fmprops = {}

        self.servicesdir = get_property(fmprops, 'servicesdir', 'fmservices')
        self.servicesdirExists = False

        contrl = None
        if 'controller' in props and props['controller'] is not None:
            for controller in props['controller']:
                contrl = controller
                break

        self.ip = get_property(contrl, 'ip', '127.0.0.1')
        self.port = get_property(contrl, 'port', 8181)
        self.user = get_property(contrl, 'user', 'admin')
        self.password = get_property(contrl, 'password', 'admin')
        self.timeout = get_property(contrl, 'timeout', 60000)

        self.loop = get_property(self.fmprops, 'loop', True)
        self.loop_interval = get_property(self.fmprops, 'loop_interval', 0)
        self.loop_max = get_property(self.fmprops, 'loop_max', 2)

        self.retries = get_property(self.fmprops, 'retries', 60)
        self.retry_interval = get_property(self.fmprops, 'retry_interval', 5)
        self.check_links = get_property(self.fmprops, 'check_links', True)
        self.check_nodes = get_property(self.fmprops, 'check_nodes', True)
        self.check_flows = get_property(self.fmprops, 'check_flows', True)
        self.check_bsc = get_property(self.fmprops, 'check_bsc', True)
        self.recreate_services = get_property(self.fmprops, 'recreate_services', True)
        self.pings = get_property(self.fmprops, 'ping', None)

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
                if not self._check_links(self.topo.number_of_swiches_links):
                    self.topo.stop()
                    return

            if self.check_nodes:
                if not self._check_nodes(self.topo.number_of_switches):
                    self.topo.stop()
                    return

            print "links and nodes detected in {} seconds".format(round((time.time() - t), 3))

            if not self._test_pings():
                self.topo.stop()
                return

            print "ping worked after {} seconds".format(round((time.time() - t), 3))

            if self.check_flows:
                if not self._check_flows():
                    self.topo.stop()
                    return

            self.counter()
            if self.recreate_services:
                self.delete_pings()

            if not self.loop:
                self.topo.stop()
                break
            if self.loop_interval > 0:
                time.sleep(loop_interval)

            print "stopping mininet"
            self.topo.stop()
            print "stopped mininet"
            t = time.time()

            if self.check_links:
                if not self._check_links(0):
                    return

            if self.check_nodes:
                if not self._check_nodes(0):
                    return

            print "links and nodes removed in {} seconds".format(round((time.time() - t), 3))

            if self.check_flows:
                if not self._check_flows():
                    return

            self.counter()

    def _get_base_url(self):
        return 'http://' + self.ip + ':' + str(self.port) + '/restconf'

    def _get_config_url(self):
        return self._get_base_url() + '/config'

    def _get_operational_url(self):
        return self._get_base_url() + '/operational'

    def _get_config_bscopenflow(self):
        return self._get_config_url() + '/brocade-bsc-openflow:nodes'

    def _get_operational_bscopenflow(self):
        return self._get_operational_url() + '/brocade-bsc-openflow:nodes'

    def _get_config_openflow(self):
        return self._get_config_url() + '/opendaylight-inventory:nodes'

    def _get_operational_openflow(self):
        return self._get_operational_url() + '/opendaylight-inventory:nodes'

    def _get_config_flow_url(self, node, table, flow):
        return self._get_config_openflow() + '/node/{}/table/{}/flow/{}'.format(node, str(table), flow)

    def _get_operational_flow_url(self, node, table, flow):
        return self._get_operational_openflow() + '/node/{}/table/{}/flow/{}'.format(node, str(table), flow)

    def _get_config_group_url(self, node, group):
        return self._get_config_openflow() + '/node/{}/group/{}'.format(node, str(group))

    def _get_operational_group_url(self, node, group):
        return self._get_operational_openflow() + '/node/{}/group/{}'.format(node, str(group))

    def _get_config_bscflow_url(self, node, table, flow):
        return self._get_config_bscopenflow() + '/node/{}/table/{}/flow/{}'.format(node, str(table), flow)

    def _get_operational_bscflow_url(self, node, table, flow):
        return self._get_operational_bscopenflow() + '/node/{}/table/{}/flow/{}'.format(node, str(table), flow)

    def _get_config_bscgroup_url(self, node, group):
        return self._get_config_bscopenflow() + '/node/{}/group/{}'.format(node, str(group))

    def _get_operational_bscgroup_url(self, node, group):
        return self._get_operational_bscopenflow() + '/node/{}/group/{}'.format(node, str(group))

    def _get_config_eline_url(self, name):
        return self._get_config_url() + '/brocade-bsc-eline:elines/eline/{}'.format(name)

    def _get_config_path_url(self, name):
        return self._get_config_url() + '/brocade-bsc-path:paths/path/{}'.format(name)

    def _http_get(self, url):
        return requests.get(url,
                            auth=HTTPBasicAuth(self.user,
                                               self.password),
                            headers=_DEFAULT_HEADERS,
                            timeout=self.timeout)

    def _http_post(self, url, data):
        return requests.post(url,
                             auth=HTTPBasicAuth(self.user,
                                                self.password),
                             data=data, headers=_DEFAULT_HEADERS,
                             timeout=self.timeout)

    def _http_put(self, url, data):
        return requests.put(url,
                            auth=HTTPBasicAuth(self.user,
                                               self.password),
                            data=data, headers=_DEFAULT_HEADERS,
                            timeout=self.timeout)

    def _http_delete(self, url):
        return requests.delete(url,
                               auth=HTTPBasicAuth(self.user,
                                                  self.password),
                               headers=_DEFAULT_HEADERS,
                               timeout=self.timeout)

    def _save_flow(self, nodeid, tableid, flowid, flow):
        if not self.servicesdirExists:
            os.makedirs(self.servicesdir)
            self.servicesdirExists = os.path.exists(self.servicesdir)

        dirname = self.servicesdir + '/nodes/{}/tables/{}/flows'.format(nodeid, str(tableid))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        filename = dirname + '/' + flowid
        with open(filename, 'w') as outfile:
            print "saving {} ".format(filename)
            json.dump(flow, outfile)

    def _save_group(self, nodeid, groupid, group):
        if not self.servicesdirExists:
            os.makedirs(self.servicesdir)
            self.servicesdirExists = os.path.exists(self.servicesdir)

        dirname = self.servicesdir + '/nodes/{}/groups'.format(nodeid)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        filename = dirname + '/' + str(groupid)
        with open(filename, 'w') as outfile:
            print "saving {} ".format(filename)
            json.dump(group, outfile)

    def _get_nodes_and_links(self, topology_name):
        nodelist = {}
        linklist = {}
        resp = self._http_get(self._get_operational_url() +
                              '/network-topology:network-topology/topology/{}'.format(topology_name))
        if resp is not None and resp.status_code == 200 and resp.content is not None:
            data = json.loads(resp.content)
            topology = data.get('topology')
            nodes = None
            if topology is not None and len(topology) > 0:
                nodes = topology[0].get('node')
                if nodes is not None:
                    for node in nodes:
                        if unicode(node['node-id']).startswith(unicode('host')):
                            continue
                        nodelist[node['node-id']] = node
                links = topology[0].get('link')
                if links is not None:
                    for link in links:
                        if link['source']['source-node'].startswith('host'):
                            continue
                        if link['destination']['dest-node'].startswith('host'):
                            continue
                        linklist[link['link-id']] = link

        print "Topology {} has {} nodes and {} links. {} ".format(topology_name, len(nodelist), len(linklist), nodelist.keys())
        return nodelist, linklist

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

    def counter(self):
        nodecounter = {}
        print "Couting all flows and groups ..."
        resp = self._http_get(self._get_config_openflow())
        if resp is None or resp.status_code != 200 or resp.content is None:
            print 'no data found'
            return

        data = json.loads(resp.content)
        if 'nodes' not in data or 'node' not in data['nodes']:
            print 'no nodes found'
            return
        for node in data['nodes']['node']:
            nodeid = unicode(node['id'])
            if unicode('controller-config') == nodeid:
                continue
            nodecounter[nodeid] = {'groups': 0, 'flows': 0, 'table0': 0, 'table1': 0}
            groups = node.get('flow-node-inventory:group')
            if groups is not None:
                nodecounter[nodeid]['groups'] = len(groups)

            tables = node.get('flow-node-inventory:table')
            if tables is not None:
                for table in tables:
                    tableid = 'table' + str(table['id'])
                    flows = table.get('flow')
                    if flows is not None:
                        nodecounter[nodeid][tableid] = len(flows)

            print "Node {} groups {} table 0 {} table 1 {}".format(nodeid,
                                                                   nodecounter[nodeid]['groups'],
                                                                   nodecounter[nodeid]['table0'],
                                                                   nodecounter[nodeid]['table1'])
        print "Counting done"

    def _get_flow_group(self, url, prefix=None):
        nodes = {}

        # print "Checking if all flows and groups in configuration data store are present in operational data store ..."
        resp = self._http_get(url)
        if resp is None or resp.status_code != 200 or resp.content is None:
            print 'no data found while trying to get openflow information'
            return flow_errors, group_errors

        data = json.loads(resp.content)
        if 'nodes' not in data or 'node' not in data['nodes']:
            print 'no nodes found while trying to get openflow information'
            return flows, groups, cookies

        for node in data['nodes']['node']:
            nodeid = node['id']
            flows = {}
            flowsbscids = {}
            cookies = {}
            groups = {}
            nodes[nodeid] = {
                'flows': flows,
                'flowsbscids': flowsbscids,
                'groups': groups,
                'cookies': cookies
            }

            thegroups = node.get('flow-node-inventory:group')
            if thegroups is None:
                thegroups = node.get('group')

            if thegroups is not None:
                for group in thegroups:
                    groups[group['group-id']] = group

            tables = node.get('flow-node-inventory:table')
            if tables is None:
                tables = node.get('table')

            if tables is not None:
                for table in tables:
                    tableid = table['id']
                    theflows = table.get('flow')
                    if theflows is not None:
                        for flow in theflows:
                            flowid = 'table/{}/flow/{}'.format(tableid, flow['id'])
                            if prefix is None:
                                flows[flowid] = flow
                            elif 'cookie' in flow:
                                cookie = flow.get('cookie')
                                if cookie >> 56 == prefix:
                                    flow['bscversion'] = (cookie & 0x00000000FF000000) >> 24
                                    flow['bscid'] = (cookie & 0x00FFFFFF00000000) >> 32
                                    flowsbscids[flow['bscid']] = flowid
                                    flows[flowid] = flow

        return nodes

    def save(self):
        resp = self._http_get(self._get_config_openflow())
        if resp is None or resp.status_code != 200 or resp.content is None:
            print 'no data found'
            return

        data = json.loads(resp.content)
        if 'nodes' not in data or 'node' not in data['nodes']:
            print 'no nodes found'
            return
        for node in data['nodes']['node']:
            nodeid = node['id']
            groups = node.get('flow-node-inventory:group')
            if groups is not None:
                for group in groups:
                    groupid = group['group-id']
                    self._save_group(nodeid, groupid, group)

            tables = node.get('flow-node-inventory:table')
            if tables is not None:
                for table in tables:
                    tableid = table['id']
                    flows = table.get('flow')
                    if flows is not None:
                        for flow in flows:
                            flowid = flow['id']
                            self._save_flow(nodeid, tableid, flowid, flow)

    def put(self):
        nodesdir = self.servicesdir + '/nodes'
        if not os.path.exists(nodesdir):
            print "ERROR: dir {} does exits".format(nodesdir)
            return False
        print "configuring groups for {}".format(os.listdir(nodesdir))
        for nodeid in os.listdir(nodesdir):
            nodedir = nodesdir + '/' + nodeid
            groupsdir = nodedir + '/groups'
            for groupid in os.listdir(groupsdir):
                groupfile = groupsdir + '/' + groupid
                with open(groupfile) as data_file:
                    data = json.dumps({
                        "flow-node-inventory:group": [json.load(data_file)]
                    })
                    resp = self._http_put(self._get_config_group_url(nodeid, groupid), data)
                    if resp is None or resp.status_code != 200:
                        print "ERROR putting {}".format(groupfile)
                        print data
                        print resp.content

        print "sleeping 10 seconds to let the controler configure all groups before sending flows"
        time.sleep(10)
        nodesdir = self.servicesdir + '/nodes'
        print "configuring flows for {}".format(os.listdir(nodesdir))
        for nodeid in os.listdir(nodesdir):
            nodedir = nodesdir + '/' + nodeid
            tablesdir = nodedir + '/tables'
            for tableid in os.listdir(tablesdir):
                tabledir = tablesdir + '/' + tableid
                flowsdir = tabledir + '/flows'
                for flowid in os.listdir(flowsdir):
                    flowfile = flowsdir + '/' + flowid
                    with open(flowfile) as data_file:
                        data = json.dumps({
                            "flow-node-inventory:flow": [json.load(data_file)]
                        })
                        self._http_put(self._get_config_flow_url(nodeid, tableid, flowid), data)
                        if resp is None or resp.status_code != 200:
                            print "ERROR putting {}".format(flowfile)
                            print self._get_config_flow_url(nodeid, tableid, flowid)
                            print data

    def delete(self):
        resp = self._http_delete(self._get_config_openflow())
        resp = self._http_get(self._get_config_openflow())
        if resp is not None and resp.status_code != 404:
            print "ERROR configuration has not been deleted"

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

    def _test_pings(self):
        current_retries = self.retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            pingfailed = False
            for ping in self.pings:
                src = ping['source']
                dst = ping['destination']
                dstip = self.topo.hosts_ip[dst]

                output = self.topo.net.get(src).cmd('ping -c 1 {}'.format(dstip))
                # print "executed: {}".format(output)
                if ' 1 received,' not in output:
                    print "ping failed from {} to {} ({})".format(src, dst, dstip)
                    pingfailed = True
                    break
                else:
                    print 'successful ping from {} to {}'.format(src, dst)
            if not pingfailed:
                return True

            if current_retries > 0:
                time.sleep(self.retry_interval)
            if current_retries == 0:
                if self._ask_retry():
                    current_retries = self.retries

        return False

    def _check_links(self, expected_links):
        print "checking for expected number of links {}".format(expected_links)
        current_retries = self.retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            nodes, links = self._get_nodes_and_links('flow:1')
            srnodes, srlinks = self._get_nodes_and_links('flow:1:sr')
            if len(links) == expected_links and len(srlinks) == len(links):
                return True
            time.sleep(self.retry_interval)
            if current_retries == 0:
                if self._ask_retry():
                    current_retries = self.retries
        return False

    def _check_nodes(self, expected_nodes):
        print "checking for expected number of nodes {}".format(expected_nodes)
        current_retries = self.retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            nodes, links = self._get_nodes_and_links('flow:1')
            srnodes, srlinks = self._get_nodes_and_links('flow:1:sr')
            if len(nodes) == expected_nodes and len(nodes) == len(srnodes):
                return True
            if current_retries > 0:
                time.sleep(self.retry_interval)
            if current_retries == 0:
                if self._ask_retry():
                    current_retries = self.retries
        return False

    def _check_flows(self):
        current_retries = self.retries
        while (current_retries > 0):
            error_found = False
            current_retries = current_retries - 1
            ovs_flows_groups = self.topo.get_nodes_flows_groups(0x1f)
            calculated_nodes = self._get_calculated_flows_groups()
            sr_nodes = self._get_flow_group(self._get_config_bscopenflow())
            config_nodes = self._get_flow_group(self._get_config_openflow(), 0x1f)
            operational_nodes = self._get_flow_group(self._get_operational_openflow(), 0x1f)
            if self.check_bsc:
                for nodeid in sr_nodes:
                    node = sr_nodes[nodeid]
                    if 'flows' in node:
                        for flowid in node['flows']:
                            if nodeid not in config_nodes or flowid not in config_nodes[nodeid]['flows']:
                                print "ERROR: node {} flow {} not configured".format(nodeid, flowid)
                                error_found = True
                            elif nodeid not in calculated_nodes or flowid not in calculated_nodes[nodeid]['flows']:
                                print "ERROR: node {} flow {} not in calculated flows".format(nodeid, flowid)
                                error_found = True

                if 'groups' in node:
                    for groupid in node['groups']:
                        if nodeid not in config_nodes or groupid not in config_nodes[nodeid]['groups']:
                            print "ERROR: node {} group {} not configured".format(nodeid, groupid)
                            error_found = True

            for nodeid in config_nodes:
                node = config_nodes[nodeid]
                if 'flows' in node:
                    for flowid in node['flows']:
                        bscid = node['flows'][flowid]['bscid']
                        if nodeid not in operational_nodes or bscid not in operational_nodes[nodeid]['flowsbscids']:
                            print "ERROR: node {} flow {} not running".format(nodeid, flowid)
                            error_found = True
                        elif self.check_bsc and (nodeid not in sr_nodes or flowid not in sr_nodes[nodeid]['flows']):
                            print "ERROR: node {} flow {} configured but not by fm".format(nodeid, flowid)
                            error_found = True
                        elif nodeid not in ovs_flows_groups or bscid not in ovs_flows_groups[nodeid]['bscids']:
                            print "ERROR: node {} flow {} configured but not in OVS switch".format(nodeid, flowid)
                            error_found = True
                        elif node['flows'][flowid]['cookie'] not in ovs_flows_groups[nodeid]['cookies']:
                            print "WARNING: node {} flow {} configured in OVS but not running same version".format(nodeid, flowid)


                if 'groups' in node:
                    for groupid in node['groups']:
                        if nodeid not in operational_nodes or 'groups' not in operational_nodes[nodeid] or groupid not in operational_nodes[nodeid]['groups']:
                            print "ERROR: node {} group {} not running".format(nodeid, groupid)
                            error_found = True
                        elif self.check_bsc and (nodeid not in sr_nodes or groupid not in sr_nodes[nodeid]['groups']):
                            print "ERROR: node {} group {} configured but not by fm".format(nodeid, groupid)
                            error_found = True
                        elif nodeid not in ovs_flows_groups or groupid not in ovs_flows_groups[nodeid]['groups']:
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
                        elif self.check_bsc and (nodeid not in sr_nodes or config_nodes[nodeid]['flowsbscids'][bscid] not in sr_nodes[nodeid]['flows']):
                            print "ERROR: node {} flow {} running but not configured fm".format(nodeid, flowid)
                            error_found = True

                if 'groups' in node:
                    for groupid in node['groups']:
                        if nodeid not in config_nodes or 'groups' not in config_nodes[nodeid] or groupid not in config_nodes[nodeid]['groups']:
                            print "ERROR: node {} group {} running but not configured".format(nodeid, groupid)
                            error_found = True
                        elif self.check_bsc and (nodeid not in sr_nodes or groupid not in sr_nodes[nodeid]['groups']):
                            print "ERROR: node {} group {} running but not configured in fm".format(nodeid, groupid)
                            error_found = True

            for nodeid in ovs_flows_groups:
                node = ovs_flows_groups[nodeid]
                if 'bscids' in node:
                    for bscid in node['bscids']:
                        if nodeid not in config_nodes or bscid not in config_nodes[nodeid]['flowsbscids']:
                            print "ERROR: node {} flow {} running in OVS but not configured".format(nodeid, flowid)
                            error_found = True
                        elif self.check_bsc and (nodeid not in sr_nodes or config_nodes[nodeid]['flowsbscids'][bscid] not in sr_nodes[nodeid]['flows']):
                            print "ERROR: node {} flow {} running in OVS but not configured in fm".format(nodeid, flowid)
                            error_found = True

                if 'groups' in node:
                    for groupid in node['groups']:
                        if nodeid not in config_nodes or 'groups' not in config_nodes[nodeid] or groupid not in config_nodes[nodeid]['groups']:
                            print "ERROR: node {} group {} running in OVS but not configured".format(nodeid, groupid)
                            error_found = True
                        elif self.check_bsc and (nodeid not in sr_nodes or groupid not in sr_nodes[nodeid]['groups']):
                            print "ERROR: node {} group {} running in OVS but not in fm".format(nodeid, groupid)
                            error_found = True

            if not error_found:
                return True
            if current_retries > 0:
                time.sleep(self.retry_interval)
            if current_retries == 0:
                if self._ask_retry():
                    current_retries = self.retries
        return False

    def _ask_retry(self):
        var = raw_input("Do you want to retry? yes/no:")
        print "you entered", var
        if 'yes' == var:
            return True
        else:
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
