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

def write_cpuconf_lua(cpunb):
    """ Prepare lua config for CPU
    """
    cpt = 1
    cpuconf_lua = []
    max_cpu_display = 8
    print('We have {} CPUs'.format(cpunb))
    if cpunb >= max_cpu_display:
        cpunb = max_cpu_display

    alpha = 0.7
    radius = 86
    # we will spread alpha over 0.4 gradient
    alpha_scale = 0.4 / cpunb 
    thickness_max = 13
    
    if cpunb > 4:
        thickness_max = 13 - (cpunb - 4)

    thickness = thickness_max 

    for cpt in range (cpunb): 
        
        data = { 'arg': "cpu{}".format(cpt+1), 'bg_alpha': alpha, 'radius': radius, 'thickness': thickness} 

#        print("data of bg_alpha is {bg_alpha} ".format(**data))
        new_block = "{{\n name='cpu',\n args='{arg}',\n max=100,\n bg_colour=0x3b3b3b,\n bg_alpha={bg_alpha},\n fg_colour=0x34cdff,\n fg_alpha=0.8,\n x=200, y=120,\n radius={radius},\n thickness={thickness},\n start_angle=0,\n end_angle=240\n}},\n".format(**data)

        cpuconf_lua.append(new_block)

        alpha -= alpha_scale
        radius -= (thickness + 2)
        thickness -= 1

    #print("cpuconf_lua is {} ".format(cpuconf_lua))
    print('Writing CPU LUA config in template file')
    #regex = re.compile(r"^\{\{ CPU \}\}$", re.MULTILINE)

    with open('./conky/rings-v2_tpl', 'r') as f:
        filedata = f.read()
        
    filedata = filedata.replace('{{ CPU }}', ''.join(cpuconf_lua))
    print("filedata = {}".format(filedata))
    
    with open('./conky/rings-v2_tpl', 'w') as f:
        f.write(filedata)

    #for line in f:
    #    if regex.search(line) is not None:
    #        line = regex.sub(format(print(''.join(cpuconf_lua))), line)


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
    write_cpuconf_lua(cpunb)

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






