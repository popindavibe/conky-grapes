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

src_lua = './conky/rings-v2_tpl'
dest_lua = './conky/rings-v2_gen.lua'

src_conky = './conky_tpl'
dest_conky = './conky_gen.conkyrc'

def read_conf(filename):
    """ Read file
    """
    try:
        with open(filename, 'r') as f:
            filedata = f.read();
    except IOError:
        print("Could not open {}".format(filename))
        return 1

    return filedata


def write_conf(filedata, dest):
    """ Write new config file
    """
    try:
        with open(dest, 'w') as f:
            f.write(filedata);
    except IOError:
        print("Could not open {}".format(dest))
        return 1



def write_conf_blank(src, dest):
    """ Reload new config file template
    """
    try:
        with open(src, 'r') as f:
            filedata = f.read()
            
    except IOError:
        print("Could not open {}".format(src))
        return 1

    try:
        with open(dest, 'w') as f:
            f.write(filedata);
            
    except IOError:
        print("Could not open {}".format(src))
        return 1


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
    if len(disks) > 3:
        diskKeep = disks[:3]
        print('Keeping 3 first locally mounted filesystem identified: {0}'.format(diskKeep))
    else:
        diskKeep = disks

    return diskKeep


def meminfo():
    ''' Return the information in /proc/meminfo
    as a dictionary '''
    meminfo=OrderedDict()

    with open('/proc/meminfo') as f:
        for line in f:
            meminfo[line.split(':')[0]] = line.split(':')[1].strip()
    return meminfo

def write_batconf_lua():
    """ Prepare lua config for BATTERY if detected
    """

    BAT = None
    for i in range(2):
        try:
            open('/sys/class/power_supply/BAT{}/uevent'.format(i))
            BAT = i

        except IOError:
            print("Could not check battery via /sys/class/power_suplly")

        try:
            open('/proc/acpi/battery/BAT{}/state'.format(i))
            BAT = i

        except IOError:
            print("Could not check battery via acpi")
    
    if BAT is not None:
        batconf_lua = []
        alpha = 0.6
        radius = 18
        thickness = 10
        data = { 'arg': 'BAT{}'.format(BAT), 'bg_alpha': alpha, 'radius': radius, 'thickness': thickness} 

        new_block = "{{\n name='battery_percent',\n arg='{arg}',\n max=100,\n bg_colour=0x3b3b3b,\n bg_alpha={bg_alpha},\n fg_colour=0x34cdff,\n fg_alpha=0.8,\n x=274, y=464,\n radius={radius},\n thickness={thickness},\n start_angle=180,\n end_angle=420\n}},\n".format(**data)
        batconf_lua.append(new_block)

        print('Writing BATTERY LUA config in template file')

        filedata = read_conf(dest_lua)

        #with open('./conky/rings-v2_tpl', 'r') as f:
        #    filedata = f.read()
        filedata = filedata.replace('--{{ BATTERY }}', ''.join(batconf_lua))
        filedata = filedata.replace('--{{ BATTERY_WATCH }}', 'battery=tonumber(conky_parse("${{battery_percent {arg} }}"))'.format(**data))

        write_conf(filedata, dest_lua)
        #with open('./conky/rings-v2_tpl', 'w') as f:
        #    f.write(filedata)


def write_fsconf_lua(disk):
    """ Prepare lua config for FILESYSTEM
    """
    fsconf_lua = []
    alpha = 0.8
    radius = 40
    # we will spread alpha over 0.4 gradient
    alpha_scale = 0.2
    thickness = 10

    for cpt in range (len(disk)): 
        
        data = { 'arg': disk[cpt], 'bg_alpha': alpha, 'radius': radius, 'thickness': thickness} 

#        print("data of bg_alpha is {bg_alpha} ".format(**data))
        new_block = "{{\n name='fs_used_perc',\n arg='{arg}',\n max=100,\n bg_colour=0x3b3b3b,\n bg_alpha={bg_alpha},\n fg_colour=0x34cdff,\n fg_alpha=0.8,\n x=220, y=280,\n radius={radius},\n thickness={thickness},\n start_angle=0,\n end_angle=240\n}},\n".format(**data)

        fsconf_lua.append(new_block)

        alpha -= alpha_scale
        radius -= (thickness +1)
        thickness -= 1

    #print("cpuconf_lua is {} ".format(cpuconf_lua))
    print('Writing FILESYSTEM LUA config in template file')
    #regex = re.compile(r"^\{\{ CPU \}\}$", re.MULTILINE)

    filedata = read_conf(dest_lua)
    #with open('./conky/rings-v2_tpl', 'r') as f:
    #    filedata = f.read()
        
    filedata = filedata.replace('--{{ FILESYSTEM }}', ''.join(fsconf_lua))
    #print("filedata = {}".format(filedata))
    
    write_conf(filedata, dest_lua)
    #with open('./conky/rings-v2_tpl', 'w') as f:
    #    f.write(filedata)


def write_cpuconf_lua(cpunb):
    """ Prepare lua config for CPU
    """
    # Testing
    #cpunb = 8 
    
    cpuconf_lua = []
    radius = 86
    max_cpu_display = 8
    thickness_max = 13
    alpha = 0.7
    # we will spread alpha over 0.6 gradient
    alpha_scale = 0.4 / cpunb 

    print('We have {} CPUs'.format(cpunb))
    if cpunb >= max_cpu_display:
        cpunb = max_cpu_display

    
    if cpunb > 4:
        thickness_max -= (cpunb - 3)
        radius = 88

    thickness = thickness_max 

    for cpt in range (cpunb): 
        
        data = { 'arg': "cpu{}".format(cpt+1), 'bg_alpha': alpha, 'radius': radius, 'thickness': thickness} 

#        print("data of bg_alpha is {bg_alpha} ".format(**data))
        new_block = "{{\n name='cpu',\n arg='{arg}',\n max=100,\n bg_colour=0x3b3b3b,\n bg_alpha={bg_alpha},\n fg_colour=0x34cdff,\n fg_alpha=0.8,\n x=200, y=120,\n radius={radius},\n thickness={thickness},\n start_angle=0,\n end_angle=240\n}},\n".format(**data)

        cpuconf_lua.append(new_block)

        alpha -= alpha_scale
        radius -= (thickness +1)

        thickness -= 0.5 

    #print("cpuconf_lua is {} ".format(cpuconf_lua))
    print('Writing CPU LUA config in template file')
    #regex = re.compile(r"^\{\{ CPU \}\}$", re.MULTILINE)

    filedata = read_conf(dest_lua)
    #with open('./conky/rings-v2_tpl', 'r') as f:
    #    filedata = f.read()
        
    filedata = filedata.replace('--{{ CPU }}', ''.join(cpuconf_lua))
    #print("filedata = {}".format(filedata))
    
    write_conf(filedata, dest_lua)
    #with open('./conky/rings-v2_tpl', 'w') as f:
    #    f.write(filedata)

    #for line in f:
    #    if regex.search(line) is not None:
    #        line = regex.sub(format(print(''.join(cpuconf_lua))), line)

def write_netconf(interface):
    """ Prepare lua config for NETWORK
    """
    netconf_lua = []
    alpha = 0.8
    radius = 30
    # we will spread alpha over 0.4 gradient
    alpha_scale = 0.2
    thickness = 12

    for speed in  ['downspeedf', 'upspeedf']:
        
        data = { 'name': speed, 'bg_alpha': alpha, 'radius': radius, 'thickness': thickness} 
        new_block = "{{\n name='{name}',\n arg='',\n max=125000,\n bg_colour=0x3b3b3b,\n bg_alpha={bg_alpha},\n fg_colour=0x34cdff,\n fg_alpha=0.8,\n x=290, y=345,\n radius={radius},\n thickness={thickness},\n start_angle=180,\n end_angle=420\n}},\n".format(**data)

        netconf_lua.append(new_block)

        alpha -= alpha_scale
        radius -= (thickness +1)
        thickness -= 2

    print('Writing NETWORK LUA config in template file')

    filedata = read_conf(dest_lua)
    #with open('./conky/rings-v2_tpl', 'r') as f:
    #    filedata = f.read()
    filedata = filedata.replace('--{{ NETWORK }}', ''.join(netconf_lua))
    
    write_conf(filedata, dest_lua)
    #with open('./conky/rings-v2_tpl', 'w') as f:
    #    f.write(filedata)


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


    # init file
    write_conf_blank(src_lua, dest_lua)
    write_conf_blank(src_conky, dest_conky)

    write_cpuconf_lua(cpunb)
    write_fsconf_lua(disks)
    write_netconf(interface)
    write_batconf_lua()

    
#    with open('./conky/rings-v2_tpl', 'r') as f:
#        filedata = f.read()
#    
#    with open('./conky/rings-v2_gen.lua', 'w') as f:
#        f.write(filedata)




