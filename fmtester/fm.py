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
        self.fmprops = props.get('fm')
        fmprops = self.fmprops
        if self.fmprops is None:
            fmprops = {}

        self.servicesdir = get_property(fmprops,'servicesdir','fmservices')

        contrl = None
        if 'controller' in props and props['controller'] is not None:
            for controller in props['controller']:
                contrl = controller
                break

        self.ip = get_property(contrl,'ip','127.0.0.1')
        self.port = get_property(contrl,'port', 8181)
        self.user = get_property(contrl,'user','admin')
        self.password = get_property(contrl,'password','admin')
        self.timeout = get_property(contrl,'timeout', 60000)

    def test(self):
        loop = get_property(self.fmprops, 'loop', True)
        loop_interval = get_property(self.fmprops, 'loop_interval', 0)
        loop_max = get_property(self.fmprops, 'loop_max', 10)

        retries = get_property(self.fmprops, 'retries', 30)
        retry_interval = get_property(self.fmprops, 'retry_interval', 1)
        check_links = get_property(self.fmprops, 'check_links', True)
        check_nodes = get_property(self.fmprops, 'check_nodes', True)
        check_flows = get_property(self.fmprops, 'check_flows', True)
        recreate_services = get_property(self.fmprops, 'recreate_services', True)
        pings = get_property(self.fmprops, 'ping', [])


        first_iteration = True
        current_loop = loop_max
        while loop_max <= 0 or current_loop > 0:
            if current_loop > 0:
                current_loop = current_loop - 1
            topo = mntopo.topo.Topo(self.props)

            if first_iteration or recreate_services:
                first_iteration = False
                self.create_pings(topo, pings)

            topo.start()

            t = time.time()

            if check_links:
                if not self._check_links(retries, retry_interval, topo.number_of_swiches_links):
                    topo.stop()
                    return

            if check_nodes:
                if not self._check_nodes(retries, retry_interval, topo.number_of_switches):
                    topo.stop()
                    return

            print "links and nodes detected in {} seconds".format(round((time.time() - t),3))

            if not self._test_pings(retries, retry_interval, topo, pings):
                topo.stop()
                return

            print "ping worked after {} seconds".format(round((time.time() - t),3))

            if check_flows:
                if not self._check_flows(retries, retry_interval):
                    topo.stop()
                    return

            self.counter()
            if recreate_services:
                self.delete_pings(topo, pings)



            if not loop:
                topo.stop()
                break
            if loop_interval > 0:
                time.sleep(loop_interval)

            print "stopping mininet"
            topo.stop()
            print "stopped mininet"
            t = time.time()

            if check_links:
                if not self._check_links(retries, retry_interval, 0):
                    return

            if check_nodes:
                if not self._check_nodes(retries, retry_interval, 0):
                    return

            print "links and nodes removed in {} seconds".format(round((time.time() - t),3))

            if check_flows:
                if not self._check_flows(retries, retry_interval):
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
        if not os.path.exists(self.servicesdir):
            os.makedirs(self.servicesdir)

        dirname = self.servicesdir + '/nodes/{}/tables/{}/flows'.format(nodeid, str(tableid))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        filename = dirname + '/' + flowid
        with open(filename, 'w') as outfile:
            print "saving {} ".format(filename)
            json.dump(flow, outfile)

    def _save_group(self, nodeid, groupid, group):
        if not os.path.exists(self.servicesdir):
            os.makedirs(self.servicesdir)

        dirname = self.servicesdir + '/nodes/{}/groups'.format(nodeid)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        filename = dirname + '/' + str(groupid)
        with open(filename, 'w') as outfile:
            print "saving {} ".format(filename)
            json.dump(group, outfile)

    def _get_number_of_nodes_and_links(self):
        nodelist = []
        linklist = []
        resp = self._http_get(self._get_operational_url() + '/network-topology:network-topology/topology/flow:1')
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
                        nodelist.append(node['node-id'])
                links = topology[0].get('link')
                if links is not None:
                    for link in links:
                        if link['source']['source-node'].startswith('host'):
                            continue
                        if link['destination']['dest-node'].startswith('host'):
                            continue
                        linklist.append(link['link-id'])

        print "Flow topology has {} nodes and {} links. {} ".format(len(nodelist), len(linklist), nodelist)
        return len(nodelist), len(linklist)

    def _get_sr_number_of_nodes_and_links(self):
        nodelist = []
        linklist = []
        resp = self._http_get(self._get_operational_url() + '/network-topology:network-topology/topology/flow:1:sr')
        if resp is not None and resp.status_code == 200 and resp.content is not None:
            data = json.loads(resp.content)
            topology = data.get('topology')
            nodes = None
            if topology is not None and len(topology) > 0:
                nodes = topology[0].get('node')
                if nodes is not None:
                    for node in nodes:
                        nodelist.append(node['node-id'])
                links = topology[0].get('link')
                if links is not None:
                    for link in links:
                        if link['source']['source-node'].startswith('host'):
                            continue
                        if link['destination']['dest-node'].startswith('host'):
                            continue
                        linklist.append(link['link-id'])

        print "Sr topology has {} nodes and {} links. {} ".format(len(nodelist), len(linklist), nodelist)
        return len(nodelist), len(linklist)

    def _get_flow_group_sr_errors(self):
        flow_errors = []
        group_errors = []
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
                        nodeid = unicode(node['node-id'])
                        srnodes[nodeid] = {'groups': [], 'table0': [], 'table1': []}
                        brocadesr = node.get('brocade-bsc-sr:sr')
                        groups = None
                        if brocadesr is not None:
                            groups = brocadesr.get('calculated-groups')
                        if groups is not None:
                            cgroups = groups.get('calculated-group')
                            if cgroups is not None:
                                for group in cgroups:
                                    srnodes[nodeid]['groups'].append(unicode(str(group['group-id'])))

                        flows = None
                        if brocadesr is not None:
                            flows = brocadesr.get('calculated-flows')
                        if flows is not None:
                            cflows = flows.get('calculated-flow')
                            if cflows is not None:
                                for flow in cflows:
                                    tableid = 'table' + str(flow['table-id'])
                                    srnodes[nodeid][tableid].append(unicode(str(flow['flow-name'])))

        #print "Checking if all SR flows and groups in both places ..."
        resp = self._http_get(self._get_config_bscopenflow())
        if resp is None or resp.status_code != 200 or resp.content is None:
            print 'data not found while trying to get openflow information'
            return flow_errors, group_errors

        data = json.loads(resp.content)
        if 'nodes' not in data or 'node' not in data['nodes']:
            print 'nodes not found while trying to get openflow information'
            return flow_errors, group_errors

        for node in data['nodes']['node']:
            nodeid = unicode(node['id'])
            groups = node.get('group')
            if groups is not None:
                for group in groups:
                    groupid = group['group-id']
                    if nodeid not in srnodes or unicode(str(groupid)) not in srnodes[nodeid]['groups']:
                        #print "ERROR: /node/{}/group/{} not found".format(nodeid, str(groupid))
                        group_errors.append("/node/{}/group/{}".format(nodeid, str(groupid)))

            tables = node.get('table')
            if tables is not None:
                for table in tables:
                    tableid = 'table' + str(table['id'])
                    flows = table.get('flow')
                    if flows is not None:
                        for flow in flows:
                            flowid = flow['id']
                            if not flowid.startswith('fm-sr'):
                                continue
                            if nodeid not in srnodes or unicode(str(flowid)) not in srnodes[nodeid][tableid]:
                                #print "ERROR: /node/{}/table/{}/flow/{} not found".format(nodeid, str(tableid), flowid)
                                flow_errors.append("/node/{}/table/{}/flow/{}".format(nodeid, str(tableid), flowid))

        print "Sr checking done, with {} flow errors and {} group errors".format(len(flow_errors),len(group_errors))
        return flow_errors, group_errors

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

    def _get_flow_group_errors(self):
        flow_errors = []
        group_errors = []

        #print "Checking if all flows and groups in configuration data store are present in operational data store ..."
        resp = self._http_get(self._get_config_openflow())
        if resp is None or resp.status_code != 200 or resp.content is None:
            print 'no data found while trying to get openflow information'
            return flow_errors, group_errors

        data = json.loads(resp.content)
        if 'nodes' not in data or 'node' not in data['nodes']:
            print 'no nodes found while trying to get openflow information'
            return flow_errors, group_errors

        for node in data['nodes']['node']:
            nodeid = node['id']
            groups = node.get('flow-node-inventory:group')
            if groups is not None:
                for group in groups:
                    groupid = group['group-id']
                    resp = self._http_get(self._get_operational_group_url(nodeid, groupid))
                    if resp is None or resp.status_code != 200:
                        #print "ERROR: /node/{}/group/{} not found".format(nodeid, str(groupid))
                        group_errors.append("/node/{}/group/{}".format(nodeid, str(groupid)))

            tables = node.get('flow-node-inventory:table')
            if tables is not None:
                for table in tables:
                    tableid = table['id']
                    flows = table.get('flow')
                    if flows is not None:
                        for flow in flows:
                            flowid = flow['id']
                            resp = self._http_get(self._get_operational_flow_url(nodeid, tableid, flowid))
                            if resp is None or resp.status_code != 200:
                                #print "ERROR: /node/{}/table/{}/flow/{} not found".format(nodeid, str(tableid), flowid)
                                flow_errors.append("/node/{}/table/{}/flow/{}".format(nodeid, str(tableid), flowid))

        print "Openflow checking done, with {} flow errors and {} group errors".format(len(flow_errors),len(group_errors))
        return flow_errors, group_errors

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

    def create_pings(self, topo, pings):
        for ping in pings:
            src = ping['source']
            srcsw = topo.host_connected_switch[src]
            srcsw_name = topo.switches_openflow_names[srcsw]
            srcport = topo.portmap[srcsw][src]
            dst = ping['destination']
            dstsw = topo.host_connected_switch[dst]
            dstsw_name = topo.switches_openflow_names[dstsw]
            dstport = topo.portmap[dstsw][dst]
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

    def delete_pings(self, topo, pings):
        for ping in pings:
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

    def _test_pings(self, retries, retry_interval, topo, pings):
        current_retries = retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            pingfailed = False
            for ping in pings:
                src = ping['source']
                dst = ping['destination']
                dstip = topo.hosts_ip[dst]

                output = topo.net.get(src).cmd('ping -c 1 {}'.format(dstip))
                #print "executed: {}".format(output)
                if ' 1 received,' not in output:
                    print "ping failed from {} to {} ({})".format(src,dst,dstip)
                    pingfailed = True
                    break
            if not pingfailed:
                return True

            if current_retries == 0:
                if self._ask_retry():
                    current_retries = retries

        return False

    def _check_links(self, retries, retry_interval, expected_links):
        current_retries = retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            nodes, links = self._get_number_of_nodes_and_links()
            srnodes, srlinks = self._get_number_of_nodes_and_links()
            if links == expected_links and srlinks == links:
                return True
            time.sleep(retry_interval)
            if current_retries == 0:
                if self._ask_retry():
                    current_retries = retries
        return False

    def _check_nodes(self, retries, retry_interval, expected_nodes):
        current_retries = retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            nodes, links = self._get_number_of_nodes_and_links()
            srnodes, srlinks = self._get_number_of_nodes_and_links()
            if nodes == expected_nodes and nodes == srnodes:
                return True
            time.sleep(retry_interval)
            if current_retries == 0:
                if self._ask_retry():
                    current_retries = retries
        return False

    def _check_flows(self, retries, retry_interval):
        current_retries = retries
        while (current_retries > 0):
            current_retries = current_retries - 1
            flow_errors, group_errors = self._get_flow_group_errors()
            flowsr_errors, groupsr_errors = self._get_flow_group_sr_errors()
            if len(flow_errors) == 0 and len(group_errors) == 0 and len(flowsr_errors) == 0 and len(groupsr_errors) == 0:
                return True
            time.sleep(retry_interval)
            if current_retries == 0:
                if self._ask_retry():
                    current_retries = retries
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
