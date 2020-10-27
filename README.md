# reviveMC74 -- root and install an open VOIP app

A VOIP application to revive the MC74 that was withdrawn and abandoned by Cisco/Meraki.
This package contains code and instructions on how to (more or less) automatically root
an MC74 and install the new Android apps to allow the phone to be used on any VOIP
provider.

The install python script, reviveMC74.py assesses the state of the MC74 attached to your
computer updates the phone based on its current state.  If your had previously rooted
phone the update process was stopped before completion, the install script picks up
where it left off and continues.  This allows you to do things like root the phone 
and tinker with the boot image contents and continue on installing.  If the process
fails at some point you can patch things up and continue on.

The install process is intended to work from a Windows or Linux host computer with Python 2.7 or 3.x.  However, development is first being done and tested on Windows with Python
2.7.

### Prerequisites

Aside from an MC74 and a host computer (with Python), you need:

* POE (Power Over Ethernet) power injector or switch port
* Ethernet cable
* USB A to USB A (host connector on both ends)
* 'git clone' this reviveMC74 repository to host computer

The reviveMC74 git repository contains any needed scripts, disk images, applications
or other files -- or will attempt to download them from the internet.  The first thing
reviveMC74.py does is verify that all the needed files are in the repo's 'installFiles'
directory.

Get a copy of the repo. In a command prompt, 'cd' to the directory where you want the 
repo.  This is where all the revival programs and backed-up image files and stuff
will be kept.

    git clone https://github.com/reviveMC74/reviveMC74.git
    cd reviveMC74

### USB-A to USB-A Cable
This cable is used for the ADB (Android Debug Bridge) connection between your computer,
which is a USB Host (ie has a USB-A connector) and the MC74 USB-A host connector on
the right side of the MC74, just lower than the Mute button.  Make it yourself:
[USB-A to USB-A Instructable](https://www.instructables.com/Male-to-Male-A-to-A-USB-Cable/)
Of buy one, such as: 
[this one](https://www.amazon.com/UGREEN-Transfer-Enclosures-Printers-Cameras/dp/B00P0E394U)
or 
[this one](https://www.walmart.com/ip/SF-Cable-3-feet-USB-2-0-A-Male-to-A-Male-Cable-Off-White/987955884).
    

### Reviving

First, (in the directory containing the 'reviveMC74' git repo) execute the command:

    python reviveMC74.py listObjectives

This shows a list of the 'objectives' or steps or phases of the revival in the order
they will be performed.
The default objective is 'revive', which means unlock the MC74 by flashing 
a new recovery image, and patching the boot.img to run in not secure mode, uninstall
the Meraki apps and to install revive.MC74-debug.apk

If at some point you want to revive the MC74 up to the point that the boot file system
image was backuped on your host computer, but before the 'fixed' (updated) boot 
partition is installed, use the 'backupBoot' objective.

### Using the phone

After the phone boots up Android you should see the Android launcher (provided by the
com.teslacoilsw.launcher app.  If you pick up the handset the VOIP app should show the
virtual keypad and you should hear a 'dialtone' on the handset.

The MC74 only has a few physical buttons (Volume Up, Volume Down and Mute).  They work
as you would expect -- EXCEPT that if you do a 'long click' on the Mute button it will
take you back to the Android launcher home screen.  (There is also an ambient light 
sensor hidden in the frame 1cm above the Volume Up button -- eventually this will be
made into a virtual 'button' to do something.)

### Configuring the VOIP SIP address

(TBD)

### Problems with the revival process

If a problem occurs while running reviveMC74.py, look at the 'reviveMC.log' file, it may
have some useful info.

Report problems on the github reviveMC74 issues page.

### The Software
reviveMC74 keeps the original Android (JellyBean api level 17) operating system on the MC74.  A version of the Linphone Soft VOIP application is installed.  A com.teslacoil Android Launcher is included to allow other Android apps to be launched.
