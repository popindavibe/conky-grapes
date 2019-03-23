# conky-grapes

**The Github repository is only a mirror, only for visibility purppose.** I use GitLab CE for my own projects (which now has mirroring feature on Community Edition).

You can authenticate on [my gitlab server](https://gitlab.nomagic.uk/popi/conky-grapes) using your Github or Gitlab account to submit issues or merge requests.

### Updates
- 2018-07-22: changed option `--arch` to `--old` with reverse meaning, so that by default we create config for freetype >= 2.8.
- 2018-04-04: tagging first stable as reference.
- 2018-01-28: Activating mirror between gitlab and github for this project. Also latest updates should allow the script to work on gnome-shell (though there might still be shome issues).
- 2017-08-13: New io_wait ring! Due to the nature of io_wait monitoring in conky, I reversed display for this one. In the middle you will see average values for reads and writes and the rigns will show the 3 processes using most IO.
It's not perfect, but it can point out which process is creating a bottleneck.

## What is it
This repository aims at providing you everything you need to be able to **very quickly** build a fantastic grape-shaped lua/ conky adapted to your machine including:
* Metrics on temperature, cpu (maximum fixed to 8 cpu to display), disks (maximum 3 filesystem), memory (ram and swap), networking (we select the interface used as default gateway),
and battery when relevant.
* Visual monitoring for high temperature, low disk space and low battery charge (orange is warning, red is critical)
* A set of pre-defined colours that allows to easily adapt your settings to different backgrounds (colors can be added/ changed in the python file fairly easily).
* Possibility to select different colors for the rings, the section titles, and the text.

_note: the limits on cpu and filesystems are for display reason._

![](https://pic.nomagic.uk/W9MjLPJF)

## Why use it
To tune up your desktop of course! It is under [GPLv3 License](gpl-3.0.txt), so feel free to use, study, improve and share as you please.


## How to use it
* If you already know your way around, all you need is:
  - install conky-full
  - clone this repo to ~/conky/conky-grapes
  - install the fonts
  - use `create_config.py` to generate your configuration (use `-h` to display help)
  - enjoy color combinations and spend a fairly big amount of time looking at those magic rings

```
 -----------------------------
< ALL GLORY TO THE HYPNOTOAD! >
 -----------------------------
        \   ^__^
         \  (@@)\_______
            (__)\       )\/\
             U ||----w |
                ||     ||
```

* If you haven't used or set up any conky before, please go to the [Wiki](https://gitlab.nomagic.fr/popi/conky-grapes/wikis/home) page (that you can also edit with your inputs!)
