#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import time
import platform
import re
from collections import OrderedDict
import sys

src_lua = './rings-v2_tpl'
dest_lua = './rings-v2_gen.lua'

src_conky = './conky_tpl'
dest_conky = './conky_gen.conkyrc'

# Defaults is blue metrics and white font
## blue     | 34cdff
## white    | efefef

# for LUA config, this should not be changed.
default_fg_color = '0x34cdff'

couleurs = {
        'yellow': 'fffd1d',
        'orange': 'ff8523',
        'red': 'ff1d2b',
        'green': '1dff22',
        'pink': 'd70751',
        'skyblue': '008cff',
        'brown': 'd7bd4c',
        'blue': '34cdff',
        'white': 'efefef',
        'grey': '323232',
        'black': '000000',
        'violet': 'bb07d7',
        'ASSE': '006a32'
        }
#cpunb = 8  # For testing only


def init(rings, title, text):
    """Initialisation of colors
    """
    # for lua
    crings = '0x'+couleurs[rings]
    # for conky
    ctitle = '#'+couleurs[title]
    ctext = '#'+couleurs[text]
    return crings, ctitle, ctext

def read_conf(filename):
    """ Read file in variable and returns it
    """
    try:
        with open(filename, 'r') as f:
            filedata = f.read();
    except IOError:
        print("[Error] Could not open {}".format(filename))
        return 1
    return filedata

def write_conf(filedata, dest):
    """ Write new config file
    """
    try:
        with open(dest, 'w') as f:
            f.write(filedata);
    except IOError:
        print("[Error] Could not open {}".format(dest))
        return 1

def write_color_lua():
    """ Last function called
    """
    datain = read_conf(dest_lua)
    filedata = datain.replace(default_fg_color, crings)
    write_conf(filedata, dest_lua)

def write_conf_blank(src, dest):
    """ Reload new config file template
    """
    filedata = read_conf(src)
    print('Overwriting config template file')
    filedata = filedata.replace('--{{ COLOR0 }}', "    color0 = '{}',".format(ctitle))
    filedata = filedata.replace('--{{ COLOR1 }}', "    color1 = '{}',".format(ctext))
    write_conf(filedata, dest)

def cpu_number():
    """ Looks for number of CPU threads
    """
    with open('/proc/cpuinfo') as f:
        nbcpu = 0
        for line in f:
        # Ignore the blank line separating the information between
        # details about two processing units
            if line.strip():
                if line.rstrip('\n').startswith('cpu MHz'):
                    nbcpu += 1
    return nbcpu

def route_interface():
    """ Returns the network interface used for routing
    """
    gwinterface = "no_gateway_interface"
    with open('/proc/net/route') as f:
        for line in f:
            routeinfo = line.split('\t')
            if routeinfo[1] == "00000000":
                gwinterface = routeinfo[0]
    print('Gateway interface: {0}'.format(gwinterface))

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
    """ Return the mount point to monitor
    """
    disks = []
    with open('/proc/mounts') as f:
        for line in f:
            diskinfo = line.split(' ')
            match1 = re.search(r'^/[a-zA-Z-_]+.', diskinfo[0], re.M | re.I)
            match2 = re.search(r'^(fuse|bind|nfs|tmpfs)', diskinfo[2], re.M | re.I)
            if match1 and not match2:
                disks.append(diskinfo[1])
    disks.sort()

    if len(disks) > 3:
        diskKeep = disks[:3]
        print('Keeping 3 first locally mounted filesystem identified: {0}'
            .format(diskKeep))
    else:
        diskKeep = disks
    return diskKeep

def meminfo():
    """ Return the information in /proc/meminfo as a dictionary
    """
    meminfo=OrderedDict()

    with open('/proc/meminfo') as f:
        for line in f:
            meminfo[line.split(':')[0]] = line.split(':')[1].strip()
    return meminfo

def write_batconf():
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
        batconf_conky = []
        alpha = 0.6
        radius = 18
        thickness = 10
        data = {
            'arg': 'BAT{}'.format(BAT),
            'bg_alpha': alpha,
            'radius': radius,
            'thickness': thickness
            }

        print('Writing lua BATTERY config in template file')
        new_block = """    {{
        name='battery_percent',
        arg='{arg}', max=100,
        bg_colour=0x3b3b3b,
        bg_alpha={bg_alpha},
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=274, y=464,
        radius={radius},
        thickness={thickness},
        start_angle=180,
        end_angle=420
    }},""".format(**data)

        batconf_lua.append(new_block)
        filedata = read_conf(dest_lua)
        filedata = filedata.replace('--{{ BATTERY }}', ''.join(batconf_lua))
        filedata = filedata.replace('--{{ BATTERY_WATCH }}', 'battery=tonumber(conky_parse("${{battery_percent {arg} }}"))'.format(**data))
        write_conf(filedata, dest_lua)

        print('Writing conky BATTERY config in template file')
        new_block = "${{font}}${{color0}}${{goto 280}}${{voffset 1}}${{color1}}${{battery_percent {arg}}}%".format(**data)
        batconf_conky.append(new_block)
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ BATTERY }}', ''.join(batconf_conky))
        write_conf(filedata, dest_conky)

def write_fsconf_lua(disk, cpunb):
    """ Prepare lua config for FILESYSTEM
    """
    fsconf_lua = []
    fsconf_watch = []
    alpha = 0.8
    radius = 40
    # we will decrease alpha value for each FS
    alpha_scale = 0.2
    thickness = 10
    # for disk monitoring in disk_watch
    index_start = cpunb + 4
    print('index_start is {}'.format(index_start))

    for cpt in range (len(disk)):
        data = {
                'arg': disk[cpt],
                'bg_alpha': alpha,
                'radius': radius,
                'thickness': thickness
                }

        new_block = """\n    {{
        name='fs_used_perc',
        arg='{arg}',
        max=100,
        bg_colour=0x3b3b3b,
        bg_alpha={bg_alpha},
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=220, y=280,
        radius={radius},
        thickness={thickness},
        start_angle=0,
        end_angle=240
    }},""".format(**data)

        fsconf_lua.append(new_block)
        # for DISK_WATCH section
        index = index_start + cpt
        with open('./fs_watch') as f:
            for line in f:
                test = re.sub(r'FILESYS', data['arg'], line)
                fsconf_watch.append(re.sub(r'INDEX', format(index), test))

        alpha -= alpha_scale
        radius -= (thickness +1)
        thickness -= 1

    print('Writing FILESYSTEM LUA config in template file')
    filedata = read_conf(dest_lua)
    filedata = filedata.replace('--{{ FILESYSTEM }}', ''.join(fsconf_lua))
    write_conf(filedata, dest_lua)

    print('Writing DISK_WATCH lua config in template file')
    filedata = read_conf(dest_lua)
    filedata = filedata.replace('--{{ DISK_WATCH }}', ''.join(fsconf_watch))
    write_conf(filedata, dest_lua)

def write_fsconf_conky(fs):
    """ Prepare conky config for CPU
    """
    conf = []
    voffset = -65
    fs_max = 3

    for cpt in range (len(fs)):
        if cpt > 0:
            voffset = 0
        data = {
                'voffset': voffset,
                'filesys': "{}"
                .format(fs[cpt])
                }

        new_block = "${{goto 70}}${{voffset {voffset}}}{filesys}${{color1}}${{alignr 310}}${{fs_used {filesys}}} / ${{fs_size {filesys}}}\n".format(**data)
        conf.append(new_block)

    print('adjusting voffset for FS...')
    adjust = 12 + ((fs_max - len(fs)) *10)
    new_block = "${{font Michroma:size=10}}${{color0}}${{goto 68}}${{voffset {0}}}FILESYSTEM".format(adjust)
    conf.append(new_block)

    print('Writing FS conky config in template file')
    filedata = read_conf(dest_conky)
    filedata = filedata.replace('#{{ FILESYSTEM }}', ''.join(conf))
    write_conf(filedata, dest_conky)

def write_cpuconf_lua(cpunb):
    """ Prepare lua config for CPU
    """
    cpuconf_lua = []
    radius = 86
    max_cpu_display = 8
    thickness_max = 13
    alpha = 0.7
    # we will spread alpha over 0.4 gradient
    alpha_scale = 0.4 / cpunb
    print('We have {} CPUs'.format(cpunb))
    if cpunb >= max_cpu_display:
        cpunb = max_cpu_display
    print('We keep {} CPUs'.format(cpunb))

    if cpunb > 4:
        thickness_max -= (cpunb - 3)
        radius = 88
    thickness = thickness_max

    for cpt in range (cpunb):
        data = {
            'arg': "cpu{}".format(cpt+1),
            'bg_alpha': alpha,
            'radius': radius,
            'thickness': thickness
            }

        new_block = """\n    {{
        name='cpu',
        arg='{arg}',
        max=100,
        bg_colour=0x3b3b3b,
        bg_alpha={bg_alpha},
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=200, y=120,
        radius={radius},
        thickness={thickness},
        start_angle=0,
        end_angle=240
    }},""".format(**data)

        cpuconf_lua.append(new_block)
        alpha -= alpha_scale
        radius -= (thickness +1)
        thickness -= 0.5

    print('Writing CPU LUA config in template file')
    filedata = read_conf(dest_lua)
    filedata = filedata.replace('--{{ CPU }}', ''.join(cpuconf_lua))
    write_conf(filedata, dest_lua)

def write_cpuconf_conky(cpunb):
    """ Prepare conky config for CPU
    """
    cpuconf = []
    voffset = 3
    max_cpu_display = 8

    # bring lines closer if many cpus
    if cpunb > 4:
        if cpunb > 6:
            voffset = 0.5
        else:
            voffset = 1.5

    print('We have {} CPUs'.format(cpunb))
    if cpunb >= max_cpu_display:
        cpunb = max_cpu_display
    print('We keep {} CPUs'.format(cpunb))

    if cpunb > 4:
        voffset -= 1

    for cpt in range (cpunb):
        data = { 'voffset': voffset, 'cpu': "{}".format(cpt+1)}

        new_block = "${{voffset {voffset}}}${{goto 120}}${{color1}}CPU {cpu}${{alignr 330}}${{color1}}${{cpu cpu{cpu}}}%\n".format(**data)
        cpuconf.append(new_block)

    print('adjusting voffset for top cpu processes...')
    adjust = 34 - (voffset * cpunb)
    new_block = "${{goto 50}}${{voffset {0}}}${{color1}}${{top name 1}}${{alignr 306}}${{top cpu 1}}%".format(adjust)
    cpuconf.append(new_block)

    print('Writing CPU conky config in template file')
    filedata = read_conf(dest_conky)
    filedata = filedata.replace('#{{ CPU }}', ''.join(cpuconf))
    write_conf(filedata, dest_conky)

def write_netconf_lua(interface):
    """ Prepare lua config for NETWORK
    """
    netconf_lua = []
    alpha = 0.8
    radius = 30
    # we will spread alpha over 0.4 gradient
    alpha_scale = 0.2
    thickness = 12

    for speed in  ['downspeedf', 'upspeedf']:
        data = {
            'name': speed,
            'arg': interface[0],
            'bg_alpha': alpha,
            'radius': radius,
            'thickness': thickness
            }

        new_block = """\n    {{
        name='{name}',
        arg='{arg}',
        max=125000,
        bg_colour=0x3b3b3b,
        bg_alpha={bg_alpha},
        fg_colour=0x34cdff,
        fg_alpha=0.8,
        x=290, y=345,
        radius={radius},
        thickness={thickness},
        start_angle=180,
        end_angle=420
    }},""".format(**data)

        netconf_lua.append(new_block)
        alpha -= alpha_scale
        radius -= (thickness +1)
        thickness -= 1

    print('Writing NETWORK LUA config in template file')
    filedata = read_conf(dest_lua)
    filedata = filedata.replace('--{{ NETWORK }}', ''.join(netconf_lua))
    write_conf(filedata, dest_lua)

def write_netconf_conky(interface):
    """ Prepare conky config for network interface
    """
    netconf = []
    if interface[0] == "no_gateway_interface":
        print('No default route on the system! Tachikoma, what is happening?!')

        with open('./nonetconf') as f:
            for line in f:
                netconf.append(line)
        #print('netconf: {0}'.format(netconf))
        print('Writing NETWORK conky config in template file')
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ NETWORK }}', ''.join(netconf))
        write_conf(filedata, dest_conky)

    elif interface[1] is True:
        print('Setting up Wifi as main interface')
        with open('./wificonf') as f:
            for line in f:
                netconf.append(re.sub(r'INTERFACE', interface[0], line))
        #print('netconf: {0}'.format(netconf))
        print('Writing NETWORK conky config in template file')
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ NETWORK }}', ''.join(netconf))
        write_conf(filedata, dest_conky)
    else:
        print('Setting up NIC as main interface')
        with open('./ethconf') as f:
            for line in f:
                netconf.append(re.sub(r'INTERFACE', interface[0], line))
        #print('netconf: {0}'.format(netconf))
        print('Writing NETWORK conky config in template file')
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ NETWORK }}', ''.join(netconf))
        write_conf(filedata, dest_conky)


# main
if __name__ == "__main__":
#    print ("called directly")

    parser = argparse.ArgumentParser(description='Creates/overwrites conky and lua configuration for conky-grappes adjustments to your system.')
    parser.add_argument('-r', '--color_rings', dest='rings', metavar='COLOR_RINGS', default='blue', choices=couleurs,
                        help='the textual color for the rings and titles, among: {0}'.format(' '.join(couleurs.keys())))
    parser.add_argument('-ti', '--color_title', dest='title', metavar='COLOR_TITLE', default='blue', choices=couleurs,
                        help='the textual color for the title display, see COLOR_RINGS for accepted values.')
    parser.add_argument('-te', '--color_text', dest='text', metavar='COLOR_TEXT', default='grey', choices=couleurs,
                        help='the textual color for the text display, see COLOR_RINGS for accepted values.')

    args = parser.parse_args()
    print('Arguments received: {}'.format(args))

    # init file
    crings, ctitle, ctext = init(args.rings, args.title, args.text)
    print('colors: {} {} {}'.format(crings, ctitle, ctext))

    write_conf_blank(src_lua, dest_lua)
    write_conf_blank(src_conky, dest_conky)

    cpunb = cpu_number()
    print('Number of CPU(s): {0}'.format(cpunb))
    meminfo = meminfo()
    print('Total memory: {0}'.format(meminfo['MemTotal']))
    print('Free memory: {0}'.format(meminfo['MemFree']))
    interface = route_interface()
    disks = disk_select()


    # LUA
    write_cpuconf_lua(cpunb)
    write_fsconf_lua(disks,cpunb)
    write_netconf_lua(interface)

    write_cpuconf_conky(cpunb)
    write_fsconf_conky(disks)
    write_netconf_conky(interface)

    write_batconf()
    write_color_lua()


