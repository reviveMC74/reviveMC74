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

First, to see the steps the script will take, (in the directory containing the 'reviveMC74' git repo) execute the command:

    python reviveMC74.py listObjectives

This shows a list of the 'objectives' or steps or phases of the revival in the order
they will be performed.
The default objective is 'revive', which means unlock the MC74 by flashing 
a new recovery image, and patching the boot.img to run in not secure mode, uninstall
the Meraki apps and to install revive.MC74-debug.apk

If for some reason you only want to revive the MC74 up to the point that the boot file system
image was backuped on your host computer, but before the 'fixed' (updated) boot 
partition is installed, use the 'backupBoot' objective.

To start the revival, start the reviveMC74.py script with no arguments (implying the top level 'revive' objective):

    python reviveMC74.py
    
The script will check that all the needed programs and files are avaialble.  It then checks the state of the MC74 to see what
state it is in and how much of the revival process has already been done.  Follow the instructions in the script -- as there
are some manual steps, like holding down the 'Mute' button and connecting and disconnecting cables.

### Revival Process

The revival process is done in steps, called 'objectives'.  Most objectives have 
perequiste objectives.  If a perequiste objective has already been completed, it is 
not skipped (unless it is explicity requested by the user).  This objectively run
in the following order:

* checkFiles    Verifies that you have the needed files, apps, images, and programs.
* replaceRecovery       Replace the recovery partition with a full featured recovery program
* backupBoot    Backs up boot partitions and extracts the files from it.
* fixBootPartition      Rewrites the boot partition image with a 'fixed'(unlocked) ramdisk
* installApps   Install VOIP phone app, uninstall old Meraki phone apps
* revive        The Prime Objective -- causes the perequisites to be run

* listObjectives        (optional) Lists all objectives
* adbMode       Gets device into 'adb' mode.
* resetBFF      (manual step) Reset the 'Boot partion Fixed Flag' to force this fixBootParation to be rerun on a subsequent call.

If you look in reviveMC74.py, each 'objective' is in its own function, for example,  
'backupBootFunc' if the function that imlements the 'backupBoot' objective.  The first
thing 'backupBootFunc' does is to call 'replaceRecoveryFunc' to see if the recovery 
partition has had 'clockwork recovery' installed.  If it hasn't it proceeds do that.

### Uploaded Data

In the 'backupBoot' objective of reviving the MC74, the contents of the stock /boot partition is
uploaded to the host, and extracted.  It is then modified and reassembled.  This data is 
left on the host computer for advanced users to look at and and modify.  After modification
the user can repeat the reviveMC74.py 'fixBootPartition' objective to install those
modifications to the MC74.

The data on the host includes:
*rmcBoot.imgOrig  -- the original boot partition image uploaded from phone
*rmcBootUnpack    -- boot.img unpacked
*rmcBootRamdisk   -- ramdisk.gz from rmcBootUnpack, expanded into individual files

### Problems with the revival process

If a problem occurs while running reviveMC74.py, look at the 'reviveMC.log' file, it may
have some useful info.

Report problems on the github reviveMC74 issues page.

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

When the phone app starts up, if no VOIP account address is saved, the 'VOIP Settings'
page will be displayed to allow you to enter the SIP address for the phone.  The SIP
can be changed later by swiping 'in' from the the left of the screen (while in the phone 
app), to pull out the 'side menu'.  Click on the 'SIP Address' menu item.  For more complicated
SIP addresses use the 'Settings' side menu item.

### Phone Software
reviveMC74 keeps the original Android 4.2.3 (JellyBean api level 17) operating system on the MC74.  A version of the Linphone Soft VOIP application is installed.  A com.teslacoil Android Launcher is included to allow other Android apps to be launched.

### Other Information

Here's some more information about how to use and program the MC74:
* [doc/config.md](reviveMC74 configuration files}
* [doc/hardware.md]{Hardware and supporting software documentation)  

### Further Questions

If you have any further questions, please talk with our community at https://reddit.com/r/ReviveMC74.
Further findings, information, and troubleshooting are available from our community via our subreddit!
