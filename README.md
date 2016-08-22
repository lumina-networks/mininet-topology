# Mininet Topology Utility

This tools provides a mechanism to quickly create a Mininet network based on a yml definition. It also provide a testing tool for Flow Manager and a couple of topology generators based.

- [Install](#install)
- [Usage](#usage)
- [Topology YAML](#topology-yaml)

## Install

### From source

```
git clone ssh://git@swnstash.brocade.com:7999/skyn/mininet-topology.git
cd mininet-topology
sudo python setup.py install
```

### Dependencies

The dependencies to run this tools are

- [Mininet](https://github.com/mininet)


## Usage

### Mininet topology

Execute either `sudo mnyml [topology-file-name]` to create a topology based on given topology file. This scripts command just starts a Mininet topology using OVS switches.

### Flow Manager tester

Flow Manager tester test if the flows and services runs properly on the given topology. It makes following tasks:

* starts given Mininet topology
* configure an eline/path sr services for each given pair of hosts
* checks SDN controller discover all nodes and links properly
* checks if flows are generated properly
* check if the pings works between each pair of hosts for given services
* checks if SR calculcated flows and groups are consistent
* stops Mininet and check if all flows are removed
* repeats previous steps as a loop

Execute either `sudo mnfm [topology-file-name]`

Following are the attributes that can be added to the topology yaml file to include Flow Manager testing capabilities.

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
fm:
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
  servicesdir: 'fmservices'
```

### Topology generators

This utility provides a couple of commands to quickly create topologies. Two examples are given, `Table Topology` for given rows and columns and `DataCenter topology` for given number of spines and leafs.

See following sections for further information.

- [Table Topology Generator](#table-topology-generator)
- [Datacenter Topology Generator](#datacenter-topology-generator)

## Mininet YAML description

The YAML file is composed on 4 main ArgumentParser

* **Controller**: a list of controllers identified by name and ip address

```
controller:
  - name : c0
    ip : 172.24.86.214
```


* **host**: a list of host identified by name. It must also contain a network and gateway

```
host:
- name: h101
  ip: 10.0.1.1/16
  gw: 10.0.0.1
- name: h102
  ip: 10.0.1.2/16
  gw: 10.0.0.1
```


* **switch**: a list of switches identified by name. It must also contain a dpip and protocol version. Dpid is in hexadecimal format without the `0x` prefix.

```
switch:
  - name: s11
    dpid: B
    protocols: OpenFlow13
  - name: s12
    dpid: C
    protocols: OpenFlow13
```

* **link**: a list of links that can connect either a host with a switch or a switch with a switch. It is possible to define multiple links between two nodes just repeating the value. In the following example, h11 is connected to s11. Also, two links connects s11 and s12

```
link:
  - source: h11
    destination: s11
  - source: s11
    destination: s12
  - source: s11
    destination: s12    
```


* **interface**: a list of interfaces on the host connected to the Mininet switches. This is typically empty unless we want to connect Mininet to an external network.

```
interface:
  - name: eth1
    switch: s11   
```


## Datacenter Topology Generator

**topodc** creates a topology yaml file like a datacenter with spines, leafs and computes.

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
usage: mn-datacenter-topo.py [-h] [--file FILE] [--spines SPINES]
                             [--leafs LEAFS] [--computes COMPUTES]
                             [--datacenters DATACENTERS]
                             [--controller CONTROLLER]

Create a list table of switches for given number of rows and columns

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  File name
  --spines SPINES, -s SPINES
                        Number of spines
  --leafs LEAFS, -l LEAFS
                        Number of leafs
  --computes COMPUTES, -c COMPUTES
                        Number of leafs
  --datacenters DATACENTERS, -d DATACENTERS
                        Links per each pair of switches connected horizontally
  --controller CONTROLLER, -co CONTROLLER
                        Controller ip address
```

## Table Topology Generator



**topotb** creates a topology yaml file like a table for given number of rows and columns. A host will be attached to each switch on the first and last column.

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
usage: mn-table-topo.py [-h] [--file FILE] [--rows ROWS] [--columns COLUMNS]
                        [--links-per-rows LINKS_PER_ROWS]
                        [--links-per-columns LINKS_PER_COLUMNS]
                        [--controller CONTROLLER]

Create a list table of switches for given number of rows and columns

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  File name
  --rows ROWS, -r ROWS  Number of rows
  --columns COLUMNS, -c COLUMNS
                        Number of columns
  --links-per-rows LINKS_PER_ROWS, -lr LINKS_PER_ROWS
                        Links per each pair of switches connected horizontally
  --links-per-columns LINKS_PER_COLUMNS, -lc LINKS_PER_COLUMNS
                        Links per each pair of switches connected vertically
  --controller CONTROLLER, -co CONTROLLER
                        Controller ip address
```
