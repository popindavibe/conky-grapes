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


with open('/proc/cpuinfo') as f:
    # display all
    #for line in f:
    #    print(line.rstrip('\n'))

    for line in f:
    # Ignore the blank line separating the information between
    # details about two processing units
        if line.strip():
            if line.rstrip('\n').startswith('model name'):
                model_name = line.rstrip('\n').split(':')[1]
                print(model_name)

def route_interface():
    ''' Return the network interface used for routing
    '''

    with open('/proc/net/route') as f:
        for line in f:
            routeinfo = line.split('\t')
            if routeinfo[1] == "00000000":
                interface = routeinfo[0]
    return interface


def disk_select():
    ''' Return the mount point to monitor
    '''
    with open('/proc/mounts') as f:
        for line in f:
            diskinfo = line.split(' ')
            match1 = re.search(r'^/[a-zA-Z-_]+.', diskinfo[0], re.M | re.I)
            match2 = re.search(r'^(fuse|bind|nfs|tmpfs)', diskinfo[2], re.M | re.I)
            if match1 and not match2:
                print(diskinfo[1])
                disks = diskinfo[1]
    return disks


def meminfo():
    ''' Return the information in /proc/meminfo
    as a dictionary '''
    meminfo=OrderedDict()

    with open('/proc/meminfo') as f:
        for line in f:
            meminfo[line.split(':')[0]] = line.split(':')[1].strip()
    return meminfo


# main
if __name__ == "__main__":
    print ("called directly")

    meminfo = meminfo()
    print('Total memory: {0}'.format(meminfo['MemTotal']))
    print('Free memory: {0}'.format(meminfo['MemFree']))
    interface = route_interface()
    print('Primary interface: {0}'.format(interface))
    disks = disk_select()

