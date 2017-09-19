#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    This script creates configuration files for conky and lua based on
#    your machines's current resources.
#    Copyright (C) 2017  popi
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see ihttp://www.gnu.org/licenses/gpl.html.

from __future__ import print_function
import argparse
import time
import platform
import re
from collections import OrderedDict
import sys
from os.path import expanduser
import logging as log

home = expanduser("~")
working_dir = home+'/conky/conky-grapes/'

src_lua = working_dir+'rings-v2_tpl'
dest_lua = working_dir+'rings-v2_gen.lua'
src_conky = working_dir+'conky_tpl'
dest_conky = working_dir+'conky_gen.conkyrc'

# Defaults is blue metrics and white font
## blue     | 34cdff
## white    | efefef

# for LUA config, this should not be changed.
default_fg_color = '0x34cdff'

couleurs = {
        'yellow': 'fffd1d',
        'lightyellow': 'e7dc64',
        'orange': 'ff8523',
        'lightorange': 'e79064',
        'red': 'ff1d2b',
        'lightred': 'e7646a',
        'green': '1dff22',
        'lightgreen': '64e766',
        'pink': 'd70751',
        'lightpink': 'e78cb7',
        'brown': 'b57131',
        'lightbrown': 'ceab8a',
        'blue': '165cc4',
        'iceblue': '43d2e5',
        'skyblue': '8fd3ff',
        'white': 'efefef',
        'grey': '323232',
        'lightgrey': '323232',
        'black': '000000',
        'violet': 'bb07d7',
        'lightviolet': 'a992e6',
        'ASSE': '006a32'
        }

def init(rings, title, text, arch, reload):
    """Initialisation of colors
    """
    # Keeping previous colors?
    if reload:
        with open(dest_conky, 'r') as f:
            filedata = f.read() 
            matchconky = re.findall('^ +color[01] = \'#([0-9a-f]{6})', filedata, re.M)
            print('colors were: {}'.format(matchconky))

        with open(dest_lua, 'r') as f:
            filedata = f.read() 
            matchlua = re.findall('^normal="0x([0-9a-f]{6})"', filedata, re.M)
            print('colors were: {}'.format(matchlua))
            crings = '0x'+matchlua[0]
            # for conky
            ctitle = '#'+matchconky[0]
            ctext = '#'+matchconky[1]
    else:
        # for lua
        crings = '0x'+couleurs[rings]
        # for conky
        ctitle = '#'+couleurs[title]
        ctext = '#'+couleurs[text]
    if arch:
        ctextsize = '8'
    else:
        ctextsize = '8'

    return crings, ctitle, ctext, ctextsize, arch

def read_conf(filename):
    """ Read file in variable and returns it
    """
    try:
        with open(filename, 'r') as f:
            filedata = f.read();
    except IOError:
        log.error("[Error] Could not open {}".format(filename))
        return 1
    return filedata

def write_conf(filedata, dest):
    """ Write new config file
    """
    try:
        with open(dest, 'w') as f:
            f.write(filedata);
    except IOError:
        log.error("[Error] Could not open {}".format(dest))
        return 1

def write_color_lua():
    """ Last function called
    """
    datain = read_conf(dest_lua)
    filedata = datain.replace(default_fg_color, crings)
    write_conf(filedata, dest_lua)

def write_conf_blank(src, dest):
    """ Reload new config file from template
    """
    filedata = read_conf(src)
    log.info('Overwriting config file {}'.format(dest))
    filedata = filedata.replace('--{{ COLOR0 }}', "    color0 = '{}',".format(ctitle))
    filedata = filedata.replace('--{{ COLOR1 }}', "    color1 = '{}',".format(ctext))
    filedata = filedata.replace('--{{ FONTTEXT }}', "    font = 'Play:normal:size={}',".format(ctextsize))
	
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
    
    log.info('Gateway interface: {0}'.format(gwinterface))

    """ Check if the gateway interface is wifi
        as we'll need to know about that for config
    """
    iswifi = False
    with open('/proc/net/wireless') as f:
        for line in f:
            wifi = line.split(':')
            if len(wifi) > 1:
                log.info('wifi interface: {0}'.format(wifi[0].strip()))
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
        log.info('Keeping 3 first locally mounted filesystem identified: {0}'
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
    log.info('Looking for battery info')
    for i in range(2):
        try:
            open('/sys/class/power_supply/BAT{}/uevent'.format(i))
            BAT = i
        except IOError:
            log.warning("Could not check battery {} via /sys/class/power_suplly".format(i))

        try:
            open('/proc/acpi/battery/BAT{}/state'.format(i))
            BAT = i
        except IOError:
            log.warning("Could not check battery {} via acpi".format(i))

    if BAT is not None:
        print('Found battery info!')
        batconf_lua = []
        batconf_conky = []
        alpha = 0.6
        radius = 18
        thickness = 10
        log.info('- Calculating index for battery in lua watch_battery')
        # 9 => lua starts at 0 | 2 for mem, 2 for network, 1 for temp, 3 for time
        index = cpunb+len(disks)+9
        log.info('  Battery index = {}'.format(index))
        data = {
            'arg': 'BAT{}'.format(BAT),
            'bg_alpha': alpha,
            'radius': radius,
            'thickness': thickness
            }

        log.info('Writing lua BATTERY config in config file')
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
        filedata = filedata.replace('--{{ BATTERY_WATCH }}', 'index={}\n    battery=tonumber(conky_parse("${{battery_percent {arg} }}"))'.format(index,**data))
        filedata = filedata.replace('--{{ BATTERY_ACTIVATE }}', 'battery_watch()')
        write_conf(filedata, dest_lua)

        print('Writing conky BATTERY config in config file')
        new_block = "${font Michroma:size=10}${color0}${goto 296}${voffset 22}BATTERY"
        if arch:
            new_block += "\n${{font}}${{color0}}${{goto 280}}${{voffset -2}}${{color1}}${{battery_percent {arg}}}%".format(**data)
        else:
            new_block += "\n${{font}}${{color0}}${{goto 280}}${{voffset 1}}${{color1}}${{battery_percent {arg}}}%".format(**data)

        batconf_conky.append(new_block)
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ BATTERY }}', ''.join(batconf_conky))
        filedata = filedata.replace('#{{ OS }}', "${font Michroma:bold:size=11}${color0}${voffset 50}${alignc}${execi 3600 awk -F '=' '/PRETTY_NAME/ { print $2 }' /etc/os-release | tr -d '\"'}")
        write_conf(filedata, dest_conky)
    else:
        # adjusting if no battery
        new_block = "${font Michroma:bold:size=11}${color0}${voffset 90}${alignc}${execi 3600 awk -F '=' '/PRETTY_NAME/ { print $2 }' /etc/os-release | tr -d '\"'}"
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ OS }}', new_block)
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
    log.info('index_start is {}'.format(index_start))

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
        with open(working_dir+'fs_watch') as f:
            for line in f:
                test = re.sub(r'FILESYS', data['arg'], line)
                fsconf_watch.append(re.sub(r'INDEX', format(index), test))

        alpha -= alpha_scale
        radius -= (thickness +1)
        thickness -= 1

    print('Writing FILESYSTEM LUA config in config file')
    filedata = read_conf(dest_lua)
    filedata = filedata.replace('--{{ FILESYSTEM }}', ''.join(fsconf_lua))
    write_conf(filedata, dest_lua)

    print('Writing DISK_WATCH lua config in config file')
    filedata = read_conf(dest_lua)
    filedata = filedata.replace('--{{ DISK_WATCH }}', ''.join(fsconf_watch))
    write_conf(filedata, dest_lua)

def write_fsconf_conky(fs):
    """ Prepare conky config for CPU
    """
    conf = []
    if arch:
        voffset = -70
    else:
        voffset = -68
    fs_max = 3

    for cpt in range (len(fs)):
        if cpt > 0:
                 voffset = -1
        data = {
                'voffset': voffset,
                'filesys': "{}"
                .format(fs[cpt])
                }

        new_block = "${{goto 70}}${{voffset {voffset}}}{filesys}${{color1}}${{alignr 310}}${{fs_used {filesys}}} / ${{fs_size {filesys}}}\n".format(**data)
        conf.append(new_block)

    log.info('adjusting voffset for FS...')
    adjust = 12 + ((fs_max - len(fs)) *10)
    new_block = "${{font Michroma:size=10}}${{color0}}${{goto 68}}${{voffset {0}}}FILESYSTEM".format(adjust)
    conf.append(new_block)

    print('Writing FS conky config in config file')
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
    log.info('We have {} CPUs'.format(cpunb))
    if cpunb >= max_cpu_display:
        cpunb = max_cpu_display
    log.info('We keep {} CPUs'.format(cpunb))

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

    print('Writing CPU LUA config in config file')
    filedata = read_conf(dest_lua)
    filedata = filedata.replace('--{{ CPU }}', ''.join(cpuconf_lua))
    write_conf(filedata, dest_lua)

def write_cpuconf_conky(cpunb):
    """ Prepare conky config for CPU
    """
    cpuconf = []
    voffset = 2
    max_cpu_display = 8

    # bring lines closer if many cpus
    if cpunb > 4:
        if cpunb > 6:
            voffset = -0.5
        else:
            if arch:
                voffset = -1
            else:
                voffset = 0.5

    log.info('We have {} CPUs'.format(cpunb))
    log.info('voffest is set to {}'.format(voffset))
    if cpunb >= max_cpu_display:
        cpunb = max_cpu_display
    log.info('We keep {} CPUs'.format(cpunb))

#    if cpunb > 4:
#        voffset -= 1

    for cpt in range (cpunb):
        data = { 'voffset': voffset, 'cpu': "{}".format(cpt+1)}

        new_block = "${{voffset {voffset}}}${{goto 120}}${{color1}}CPU {cpu}${{alignr 330}}${{color1}}${{cpu cpu{cpu}}}%\n".format(**data)
        cpuconf.append(new_block)

    log.info('adjusting voffset for top cpu processes...')
    if cpunb > 4:
        adjust = 12 - (voffset * cpunb)
    else:
        adjust = 28 - (voffset * cpunb)
    new_block = "${{goto 50}}${{voffset {0}}}${{color1}}${{top name 1}}${{alignr 306}}${{top cpu 1}}%".format(adjust)
    cpuconf.append(new_block)

    print('Writing CPU conky config in config file')
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

    print('Writing NETWORK LUA config in config file')
    filedata = read_conf(dest_lua)
    filedata = filedata.replace('--{{ NETWORK }}', ''.join(netconf_lua))
    write_conf(filedata, dest_lua)

def write_netconf_conky(interface):
    """ Prepare conky config for network interface
    """
    netconf = []
    if interface[0] == "no_gateway_interface":
        log.warning('No default route on the system! Tachikoma, what is happening?!')

        with open(working_dir+'nonetconf') as f:
            for line in f:
                netconf.append(line)
        #print('netconf: {0}'.format(netconf))
        print('Writing NETWORK conky config in config file')
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ NETWORK }}', ''.join(netconf))
        write_conf(filedata, dest_conky)

    elif interface[1] is True:
        print('Setting up Wifi as main interface')
        with open(working_dir+'wificonf') as f:
            for line in f:
                netconf.append(re.sub(r'INTERFACE', interface[0], line))
        #print('netconf: {0}'.format(netconf))
        print('Writing NETWORK conky config in config file')
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ NETWORK }}', ''.join(netconf))
        write_conf(filedata, dest_conky)
    else:
        print('Setting up NIC as main interface')
        with open(working_dir+'ethconf') as f:
            for line in f:
                netconf.append(re.sub(r'INTERFACE', interface[0], line))
        #print('netconf: {0}'.format(netconf))
        print('Writing NETWORK conky config in config file')
        filedata = read_conf(dest_conky)
        filedata = filedata.replace('#{{ NETWORK }}', ''.join(netconf))
        write_conf(filedata, dest_conky)


# main
if __name__ == "__main__":
#    print ("called directly")
    print ("Digging in the system to gather info...\n")

    parser = argparse.ArgumentParser(description='Creates/overwrites conky and lua configuration for conky-grapes adjustments to your system.')
    parser.add_argument('-ri', '--color_rings', dest='rings', metavar='COLOR_RINGS',
                        default='blue', choices=couleurs,
                        help='the textual color for the rings and titles, among: {0}'
                        .format(' '.join(couleurs.keys()))
                        )
    parser.add_argument('-ti', '--color_title', dest='title', metavar='COLOR_TITLE',
                        default='blue', choices=couleurs,
                        help='the textual color for the title display, see COLOR_RINGS \
                            for accepted values.'''
                        )
    parser.add_argument('-te', '--color_text', dest='text', metavar='COLOR_TEXT',
                        default='grey', choices=couleurs,
                        help='the textual color for the text display, see COLOR_RINGS \
                            for accepted values.'
                       )
    parser.add_argument('--archlinux', '--arch', dest='arch', action="store_true",
                        help='small adjustments for archlinux, most notable the font size decimal delimiter is changed from "." to ",". This is worth a try if you notice bad alignment of bad font display.'
                       )
    parser.add_argument('-v', '--verbose', dest='verbose', action="store_true",
                        help='verbose mode, displays gathered info as we found it.'
                       )
    parser.add_argument('-r', '--reload', dest='reload', action="store_true",
                        help='Only refresh configuration resource-wise. Colors will stay the same as previously.'
                       )

    args = parser.parse_args()
    # Log Level
    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    log.info('Arguments received: {}'.format(args))

    # init file
    crings, ctitle, ctext, ctextsize, arch = init(args.rings, args.title, args.text, args.arch, args.reload)
    write_conf_blank(src_lua, dest_lua)
    write_conf_blank(src_conky, dest_conky)

    cpunb = cpu_number()
    #cpunb = 6  # For testing only

    log.info('Number of CPU(s): {0}'.format(cpunb))
    meminfo = meminfo()
    log.info('Total memory: {0}'.format(meminfo['MemTotal']))
    log.info('Free memory: {0}'.format(meminfo['MemFree']))
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

    print ("""\nSuccess!\nNew config files have been created:\n- {}\n- {} \n\nIf you \
add a preivous conky-grapes running, the update should be instantaneous. \
If conky-grapes is not running, you can activate it with following command:\n 
conky -q -d -c ~/conky/conky-grapes/conky_gen.conkyrc\n\n 
** If it runs but text is not aligned or font is horribly wrong (and you \
installed required fonts), chances are you are using a \
recent version of freetype2 (2.8 onwardsi, see \
https://bbs.archlinux.org/viewtopic.php?id=226380), which breaks vertical \
alignment with conky.\nIf you are on Archlinux, install AUR package \
https://aur.archlinux.org/packages/freetype2-ttmetrics to fix the vertical \
alignment (you might need to restart your session / machine for the change \
to take effect. \nThen call that script again using the --arch option."""
         .format(dest_conky, dest_lua)
         )

