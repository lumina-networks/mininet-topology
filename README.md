# Mininet Topology Utility

This tools provides a mechanism to quickly create a Mininet network based on a yml definition.

## Start a Topology

Execute either `sudo python mn-yml.py [topology-file-name]` or `sudo ./mn-yml.py [topology-file-name]` . If topology file name is not provided then `mn-topo.yml` will be used.

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

**mn-datacenter-topo.py** creates a topology yaml file like a datacenter with spines, leafs and computes.

Following optional parameters can be provided:
* **output file name** (default `mn-topo.yml`)
* number of **datacenters** to be created (default `1`)
* number of **spines** (default `4`)
* number of **leafs** (default `12`)
* number of **computes** connected to each leaf (default `10`)
* **controllers**


Example, a datacenter with 3 spines, 4 leafs and 5 compute per leaf will be created by `python mn-datacenter-topo.py -s 3 -l 4 -c 5`

```
$  ./mn-datacenter-topo.py -h
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



**mn-table-topo.py** creates a topology yaml file like a table for given number of rows and columns. A host will be attached to each switch on the first and last column.

Following optional parameters can be provided:
* **output file name** (default `mn-topo.yml`)
* number of **rows** (default `3`)
* number of **columns** (default `3`)
* number of **links-per-rows** (default `1`) number of links that will connect each pair of switches horizontally
* number of **links-per-columns**  (default `1`) number of links that will connect each pair of switches vertically
* **controllers**

Example, a table with 3 rows, 2 columns will be created by `python mn-table-topo.py -r 3 -c 2`


```
$ ./mn-table-topo.py -h
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
                        Controller ip address```
