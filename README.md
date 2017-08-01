# Mininet Topology Utility

This tool provides a mechanism to quickly create a Mininet network based on a YAML definition. It also provides testing tools focusing on Openflow validation, packet generator and a couple of topology generators.

- [Install](#install)
- [Usage](#usage)
  - [Mininet topology](#mininet-topology)
  - [Test utilities](#test-utilities)
  - [Topology generators](#topology-generators)
- [Packet Generator](packet-generator)
- [Mininet YAML description](#Mininet-yaml-description)

## Install

### From source

```
git clone https://github.com/lumina-networks/mininet-topology
cd mininet-topology
sudo python setup.py install
```

### Dependencies

The dependencies to run this tool are

- [Mininet](https://github.com/mininet)
- [Scapy](http://www.secdev.org/projects/scapy/)

**Scapy** is installed automatically when this project is installed.

**Mininet** is not installed by this project. Following commands shows how to installed from command line.

```
git clone https://github.com/mininet/mininet.git

cd mininet
git checkout tags/2.2.1
cd ..
sed -i 's/git:\/\/openflowswitch.org\/openflow.git/https:\/\/github.com\/mininet\/openflow.git/g' mininet/util/install.sh
sed -i 's/git:\/\/gitosis.stanford.edu\/oflops.git/https:\/\/github.com\/mininet\/oflops.git/g' mininet/util/install.sh
mininet/util/install.sh -n3fv
```

Mininet currently only supports up to 3 mpls label in a packet. If you plan to use MPLS heavily and more than 3 mpls label depth is required then following lines will update Mininet with the given number of labels (`10` in following example commands).

```
## execute as root
sudo su

MPLS_MAX=10
OVS_FILE=http://openvswitch.org/releases/openvswitch-2.7.0.tar.gz


# remove current OVS
apt-get remove openvswitch-common openvswitch-datapath-dkms openvswitch-controller openvswitch-pki openvswitch-switch -y


cd /root
rm -rf ../openvswitch*deb
rm -rf openvswitch*


wget $OVS_FILE
tar zxvf openvswitch-*.tar.gz
cd openvswitch-*

if [ "MPLS_MAX" != "" ]
then
  for file in `find . -type f -name flow.h`
  do
    sed -i "s/define FLOW_MAX_MPLS_LABELS .*/define FLOW_MAX_MPLS_LABELS $MPLS_MAX/g" $file
    sed -i "s/sizeof(struct flow_tnl) + 248/sizeof(struct flow_tnl) + 232 + (4 * ROUND_UP(FLOW_MAX_MPLS_LABELS, 2))/g" $file
  done
fi


apt-get update
apt-get install build-essential fakeroot dh-make dh-autoreconf graphviz libssl-dev python-all python-qt4 python-twisted-conch -y
apt-get install debhelper autoconf automake libssl-dev pkg-config bzip2 openssl python-all procps python-qt4 python-zopeinterface python-twisted-conch -y
DEB_BUILD_OPTIONS='parallel=8'
fakeroot debian/rules binary
cd ..
dpkg -i openvswitch-common*.deb openvswitch-datapath-dkms*.deb openvswitch-controller*.deb openvswitch-pki*.deb openvswitch-switch*.deb
/etc/init.d/openvswitch-controller stop
update-rc.d openvswitch-controller disable
```

## Usage

### Mininet topology

Execute `sudo mnyml` to create a topology based on given topology defined in `mn-topo.yml` file. If topology YAML file is named differently then execute `sudo mnyml -t <topology-file-name.yml>`. This script command starts a Mininet topology using OVS switches.

### Test utilities

This tool provides a tester utility command `mntest`.

`mntest` checks if flows, groups and services runs properly on the given topology executing following tasks:

* cleanup any previous Mininet network using Mininet `cleanup` method
* starts a Mininet network based on give YAML topology
* checks if SDN controller has discovered all nodes and links properly
* checks if flows are installed in all switches properly.
* checks if pings works between each pair of hosts for given services
* stops Mininet and executes Mininet `cleanup` method
* check if all nodes and links are removed
* check if all flows are removed properly from Openflow and FlowManager model.
* repeats previous steps as a loop

Execute either `sudo mntest [topology-file-name]`

Following are the attributes that can be added to the topology YAML file to include Flow Manager testing capabilities.

* **ping**: a list of `source` and `destination` hosts to configure a eline/path service. `fmmn` will test the ping between the two hosts. If not provided and `check_bsc` is True, then a ping service for each couple of hosts will be created.
* **loop**: True if it should loop the whole testing process. Default `True`.
* **loop_max**: maximum loops. Default `20`.
* **retries**: maximum of retries in case of detected error. Default `60`.
* **retry_interval**: retry interval in seconds. Default `5`.
* **check_links**: `True` if links are discovered or removed properly when Mininet start/stop. Default `True`.
* **check_nodes**: `True` if nodes are discovered or removed properly when Mininet start/stop. Default `True`.
* **check_flows**: `True` if flows are installed or removed properly when Mininet start/stop. Default `True`.
* **check_bsc**: `True` if flows in brocade-bsc-openflow model has to be checked. Default `True`.
* **recreate_services**: `True` if services should be removed/create every time thata Miniet stop/start. Default `False`.
* **servicesdir**: a directory where this solution can save and recover flows and groups configuration

```
test:
  ping:
    - source: h101
      destination: h104
  loop: True
  loop_max: 10
  loop_interval: 0
  retries: 12
  retry_interval: 5
  check_links: True
  check_nodes: True
  check_flows: True
  recreate_services: False
  servicesdir: 'services'
```

### Topology generators

This utility provides a couple of commands to quickly create topologies. Two examples are given, `Table Topology` for given rows and columns and `DataCenter topology` for given number of spines and leafs.

See following sections for further information.

- [Table Topology Generator](#table-topology-generator)
- [Datacenter Topology Generator](#datacenter-topology-generator)


## Packet Generator

`mnsend` and `mnrecv` commands create packets based on **Scapy** format and validate these packets has been received on the egress side.

### Sending packets

`mnsend` requires to be executed in a host or switch inside of Mininet network. Note that `mnsend` requires to be executed from inside mininet session if traffic is generated from a host inside mininet.

The main argument required by `mnsend` is a packet. For example, sending an ICMP packet with a vlan can be achieved by `mnsend 'Ether() / Dot1Q(vlan=100) / IP() / ICMP()'`

Please, refer to [Scapy documentation](http://scapy.readthedocs.io/en/latest/) to understand how packets can be created.

This command also provides options such `count` to define the number of packets to be sent or `iface` which defines the interface to be used.

Refer to `mnsend -h` for further information.


### Validating if packet has been received

`mnrecv` counts if given number of packets has been received for a period of time. The main parameter is to be provided is `filter` in [BPF](http://biot.com/capstats/bpf.html) format.

For example, `mnrecv "vlan 100" -c 10 -t 60` checks if 10 packets has been received with vlan 100 for a maximum of 60 seconds time.



## Mininet YAML description

The YAML file is composed on 4 main ArgumentParser

* **Controller**: a list of controllers identified by name and ip address

```
controller:
  - name : c0
    ip : 172.24.86.214
```


* **host**: a list of host identified by name. It must contain a network ip/mask and gateway.

```
host:
- name: h101
  ip: 10.0.1.1/16
  gw: 10.0.0.1
- name: h102
  ip: 10.0.1.2/16
  gw: 10.0.0.1
```


* **switch**: a list of switches identified by name. It must contain a dpip and protocol version. Dpid is in hexadecimal format without the `0x` prefix.

```
switch:
  - name: s11
    dpid: B
    protocols: OpenFlow13
  - name: s12
    dpid: C
    protocols: OpenFlow13
```

* **link**: a list of links that can connect either a host with a switch or a switch with a switch. It is possible to define multiple links between two nodes just repeating the value. In the following example, h11 is connected to s11 and two links connects s11 and s12

```
link:
  - source: h11
    destination: s11
  - source: s11
    destination: s12
  - source: s11
    destination: s12    
```


* **interface**: a list of interfaces on the machine running Mininet to the switches. This is typically empty unless we want to connect Mininet to an external network.

```
interface:
  - name: eth1
    switch: s11   
```


## Datacenter Topology Generator

**topodc** creates a topology YAML file like a datacenter with spines, leafs and computes.

Following optional parameters can be provided:
* **output file name** (default `mn-topo.yml`)
* number of **datacenters** to be created (default `1`)
* number of **spines** (default `4`)
* number of **leafs** (default `12`)
* number of **computes** connected to each leaf (default `10`)
* **controllers**


Example, a datacenter with 3 spines, 4 leafs and 5 compute per leaf will be created by `topodc -s 3 -l 4 -c 5`

```
$  topodc -h
Topology Data Center Generator

Usage:
  topodc [--file=FILE] [--spines=SPINES] [--leafs=LEAFS] [--computes=COMPUTES] [--datacenters=DATACENTERS] [--controller=IP]...
  topodc (-h | --help)

Options:
  -h --help     Show this screen.
  -f, --file=FILE   Topolofy file name [default: mn-topo.yml].
  -s, --spines=SPINES   Number of spines [default: 2].
  -l, --leafs=LEAFS   Number of leafs [default: 4].
  -p, --computes=COMPUTES   Number of computes per leaf [default: 1].
  -d, --datacenters=DATACENTERS   Number of datacenters [default: 1].
  -c, --controller=IP   Controller IP address
  --version     Show version.
```

## Table Topology Generator



**topotb** creates a topology YAML file like a table for given number of rows and columns. A host will be attached to each switch on the first and last column.

Following optional parameters can be provided:
* **output file name** (default `mn-topo.yml`)
* number of **rows** (default `3`)
* number of **columns** (default `3`)
* number of **links-per-rows** (default `1`) number of links that will connect each pair of switches horizontally
* number of **links-per-columns**  (default `1`) number of links that will connect each pair of switches vertically
* **controllers**

Example, a table with 3 rows, 2 columns will be created by `topotb -r 3 -c 2`


```
$ topotb -h
Topology Table Generator

Usage:
  topotb [--file=FILE] [--rows=ROWS] [--columns=COLUMNS] [--links-per-rows=LINKS_PER_ROWS] [--links-per-columns=LINKS_PER_COLUMNS] [--controller=IP]...
  topotb (-h | --help)

Options:
  -h --help     Show this screen.
  -f, --file=FILE   Topolofy file name [default: mn-topo.yml].
  -r, --rows=ROWS   Number of rows [default: 3].
  -c, --columns=COLUMNS   Number of rows [default: 3].
  -x, --links-per-rows=LINKS_PER_ROWS   Number of links connecting per pair horizontal switches [default: 1].
  -z, --links-per-columns=LINKS_PER_COLUMNS   Number of links connecting per pair vertical switches  [default: 1].
  -o, --controller=IP   Controller IP address
  --version     Show version.
```
