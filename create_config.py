#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import time
import platform
import re
from collections import OrderedDict

unumber = os.getuid()
pnumber = os.getpid()
where = os.getcwd()
what = os.uname()
used = os.times()
now = time.time()
means = time.ctime(now)

print ("User number",unumber)
print ("Process ID",pnumber)
print ("Current Directory",where)
print ("System information",what)
print ("System information",used)
print ("\nTime is now",now)
print ("Which interprets as",means)


def cpu_number():

    with open('/proc/cpuinfo') as f:
        # display all
        #for line in f:
        #    print(line.rstrip('\n'))
        nbcpu = 0
        for line in f:
        # Ignore the blank line separating the information between
        # details about two processing units
            if line.strip():
                if line.rstrip('\n').startswith('cpu MHz'):
                    nbcpu += 1
                    #cpu_freq = line.rstrip('\n').split(':')[1]
                    #print(cpu_freq)
    return nbcpu

def route_interface():
    ''' Return the network interface used for routing
    '''
    gwinterface = "no_gateway_interface"
    with open('/proc/net/route') as f:
        for line in f:
            routeinfo = line.split('\t')
            if routeinfo[1] == "00000000":
                gwinterface = routeinfo[0]
    """ Check if the gateway interface is wifi
    as we'll need to know about that for config
    """
    iswifi = False
    with open('/proc/net/wireless') as f:
        for line in f:
            wifi = line.split(':')
            if len(wifi) > 1:
                print('wifi interface: {0}'.format(wifi[0].strip()))
                if wifi[0].strip() == gwinterface:
                    iswifi = True

    return [gwinterface, iswifi]


def disk_select():
    ''' Return the mount point to monitor
    '''
    disks = []
    with open('/proc/mounts') as f:
        for line in f:
            diskinfo = line.split(' ')
            match1 = re.search(r'^/[a-zA-Z-_]+.', diskinfo[0], re.M | re.I)
            match2 = re.search(r'^(fuse|bind|nfs|tmpfs)', diskinfo[2], re.M | re.I)
            if match1 and not match2:
                #print(diskinfo[1])
                disks.append(diskinfo[1])
        disks.sort()
    return disks


def meminfo():
    ''' Return the information in /proc/meminfo
    as a dictionary '''
    meminfo=OrderedDict()

    with open('/proc/meminfo') as f:
        for line in f:
            meminfo[line.split(':')[0]] = line.split(':')[1].strip()
    return meminfo

def display_netconf(interface):
    """ Prepare conky config for network interface
    """
    netconf = []
    if interface[1] is True:
        print('Setting up Wifi as main interface')
        with open('./wificonf') as f:
            for line in f:
                netconf.append(re.sub(r'INTERFACE', interface[0], line))
        print('netconf: {0}'.format(netconf))


    else:
        print('Setting up NIC as main interface')
        with open('./ethconf') as f:
            for line in f:
                netconf.append(re.sub(r'INTERFACE', interface[0], line))
        print('netconf: {0}'.format(netconf))



# main
if __name__ == "__main__":
    print ("called directly")

    cpunb = cpu_number()
    print('Number of CPU(s): {0}'.format(cpunb))

    meminfo = meminfo()
    print('Total memory: {0}'.format(meminfo['MemTotal']))
    print('Free memory: {0}'.format(meminfo['MemFree']))

    interface = route_interface()
    print('Primary interface: {0}'.format(interface))
    display_netconf(interface)

    disks = disk_select()
    print('Locally mounted filesystem identified: {0}'.format(disks))
    threefs = disks[:3]
    print('Keeping 3 first locally mounted filesystem identified: {0}'.format(threefs))






