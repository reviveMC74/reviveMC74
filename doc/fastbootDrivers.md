# Fastboot Devices Drivers

Particularly on Windows, a 'bad' device driver gets loaded that causes 'fastboot' to fail.  The symptom is that reviveMC74.py fails to 
be able to install the clockwork recovery image, the 'adbModeFunc' function in reviveMC74.py loops 12 times unsuccessfully getting a 
proper response from 'fastboot devices'.  In addition to the correct 'fastboot' device driver, reviveMC74.py may need to be run as 
'administrator' on Windows 10 for the 'replaceRecovery' objective.

On Linux the solution is usually to do the reviveMC74.py 'replaceRecovery' objective as super user. (The script prompts you to retry that
objective after 'sudo'ing.

On Windows, the solution is to install an device driver that works for the 'fastboot' 'device'.  As a USB device, the MC74 sends a hardware id
string to identify what sort of device is it. 

    USB\VID_18D1&PID_D001  - 'adb' device, when MC74 is in 'recovery' mode
    USB\VID_18D1&PID_0D02  - 'fastboot' device when MC74 is in 'bootloader' or 'fastboot' mode
    
The device driver (which may have been 'updated' in a recent (May 2021) Windows 10 update) works correctly, with 'adb', when the MC74 identifies itself 
in recovery mode, but when in 'bootloader' (aka 'fastboot') mode, it identifies itself as a different device -- for which the device driver doesn't
seem to work.

### Replacing the 'fastboot' device driver

This: https://forum.xda-developers.com/t/official-tool-windows-adb-fastboot-and-drivers-15-seconds-adb-installer-v1-4-3.2588979/
acticle describes how to use **'15 second adb installer'** to install a device driver that works.
This video: https://www.youtube.com/watch?v=nQjg6ePnGAc shows the process.  
[adb-setup-1.4.3.exe](https://forum.xda-developers.com/attachment.php?attachmentid=4623157&d=1540039037) is a the installer software. 
The version I used is: 

    9614711 May 03 2017 15:59:44 adb-setup-1.4.3.exe

Install that device driver, and run reviveMC74.py as 'administrator' and rerun the 'replaceRecovery' objective.
