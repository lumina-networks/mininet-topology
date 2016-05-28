#!/usr/bin/python

import sys
import yaml
import os
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Create a list table of switches for given number of rows and columns')

    parser.add_argument('--file', '-f', action="store", help="File name", type=str, default='mn-topo.yml')
    parser.add_argument('--rows', '-r', action="store", help="Number of rows", type=int, default=3)
    parser.add_argument('--columns', '-c', action="store", help="Number of columns", type=int, default=3)
    parser.add_argument('--links-per-rows', '-lr', action="store",help="Links per each pair of switches connected horizontally", type=int, default=1)
    parser.add_argument('--links-per-columns', '-lc', action="store", help="Links per each pair of switches connected vertically", type=int, default=1)
    parser.add_argument('--controller', '-co', action="store", help="Controller ip address", type=str, default='172.24.86.231')

    inputs =  parser.parse_args()

    data=dict()
    data['controller']=[{'name':'c0','ip':inputs.controller}]
    data['host']=[]
    data['switch']=[]
    data['link']=[]
    for row in range(0,inputs.rows):
        for column in range(0,inputs.columns):
            name=str(((row+1) * 100) + (column+1))
            switch='s'+name
            host='h'+name
            right='s'+str(((row+1) * 100) + (column+2))
            bottom='s'+str(((row+2) * 100) + (column+1))

            data['switch'].append({'name':switch,'dpid':format(int(name),'x'),'protocols':'OpenFlow13'})

            if column == 0 or column == inputs.columns-1:
                data['host'].append({'name':host,'ip':'10.0.'+str(row+1)+'.'+str(column+1)+'/16','gw':'10.0.0.1'})
                data['link'].append({'source':host,'destination':switch})

            if column < inputs.columns - 1:
                for repeat in range(0,inputs.links_per_rows):
                    data['link'].append({'source':switch,'destination':right})

            if row < inputs.rows - 1:
                for repeat in range(0,inputs.links_per_columns):
                    data['link'].append({'source':switch,'destination':bottom})


    with open(inputs.file, 'w') as outfile:
        outfile.write( yaml.dump(data, default_flow_style=False) )
