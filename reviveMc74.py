#!/usr/bin/env python
'''reviveMC74 -- Semiautomatic program to recover/revive/reflash a stock Meraki MC74,
  incrementally and restartably.

reviveMC74.py <options> <objectiveName>

Options:'''  # See options bunch below for list of options

helpTail = '''\nEach time reviveMC74 is called, it reassess the state conversion of the device
and resumes the update process from that point.  The first positional argument is the name of
the update objective to be done.  Use the objective 'listObjectives' to get a list of 
defined objectives.  The default objective is 'revive', which means unlock the MC74 by flashing 
a new recovery image, and patching the boot.img to run in not secure mode, uninstall
the Meraki apps and to install reviveMC74.apk
'''

import sys, os, time, datetime, shutil
from ribou import *

logFid = "reviveMC74.log"
installFilesDir = "installFiles"
filesPresentFid = "filesPresent.flag"
  # If this file exists, we checked that needed files are here

neededProgs = bunch(  # These are commands that demonstrate that needed programs are in the
  # PATH and that they execute (ie not just the filename of the program
  adb = ["adb version", "adbNeeded"],   
  fastboot = ["fastboot", "adbNeeded"],
  unpackbootimg = ["unpackbootimg", "unpNeeded"],
  mkbootimg = ["mkbootimg", "unpNeeded"],
  chmod = ["chmod", "unpNeeded"], 
  cpio = ["cpio", "unpNeeded"], 
  gzip = ["gzip -V", "gzipNeeded"], 
  gunzip = ["gunzip -V", "gzipNeeded"], 
)

neededFiles = bunch(
  recoveryClockImg = "recovery-clockwork-touch-6.0.4.7-mc74v2.img",
  packBootPy = "packBoot.py"
)

installFiles = bunch(
  lights = ["lights", "/system/bin", "chmod 755"],
  sockSvr = ["sockSvr", "/system/bin", "chmod 755"],
  hex = ["hex", "/system/bin", "chmod 755"],
  pp = ["pp", "/system/bin", "chmod 755"]
)

installApps = bunch(
  launcher = ["com.teslacoilsw.launcher-4.1.0-41000-minAPI16.apk", "com.teslacoilsw.launcher"],
  ssm = ["revive.SSMService-debug.apk", "ribo.ssm"],
  reviveMC74 = ["revive.MC74-debug.apk", "revive.MC74"]
)

updateFiles = '''
copy /y \andrStud\SSMservice\app\build\outputs\apk\debug\revive.SSMService-debug.apk \git\reviveMC74\installFiles
copy /y \git\MC74\app\build\outputs\apk\debug\revive.MC74-debug.apk \git\reviveMC74\installFiles

copy /y \andrStud\hex\app\.cxx\cmake\debug\armeabi-v7a\hex \git\reviveMC74\installFiles
copy /y \andrStud\hex\app\.cxx\cmake\debug\armeabi-v7a\lights \git\reviveMC74\installFiles
copy /y \andrStud\hex\app\.cxx\cmake\debug\armeabi-v7a\sockSvr \git\reviveMC74\installFiles
copy /y \andrStud\hex\app\.cxx\cmake\debug\armeabi-v7a\sendevent \git\reviveMC74\installFiles
''' 


options = bunch(
  #sendOid=[None, 'o:', 'Name of object to send as body of command'],
  #sessionMode = [False, 's', 'Loop reading commands from stdin'],
  #debug = [False, 'd', 'Pause for debug after cmdeply returns'],
  help = [False, '?', 'Print help info']
)

arg = bunch(  # Place to store args for objective funcs to use
  part = "both",  # Target partition to backup or fix/install, ie 'boot', 'both' or 'boot2'
)
# Options:
#   part  -- specify which parition to read or write(flash) data to
#   img   -- full filename of disk image to write/flash in flashPart objective


def reviveMain(args):
  global target, arg

  if type(args)==str:
    args = args.split(' ')
  while len(args)>0:
    if args[0][0]!='-':  # Is this an option?
      break;  # Not an option, remaining tokens are args
    tok = args.pop(0)[1:]  # Get the first token, remove the leading '-'
    while len(tok)>0:
      for nn, vv in options.items():
        if vv[1][0]==tok[0]:  # Does this option def match this option letter?
          if len(vv[1])>1 and vv[1][1]==':':  # Is an value token expected?
            # Set the value of this option (vv[0]) to the rest of tok,
            # or the next token
            vv[0] = tok[1:] if len(tok)>1 else args.pop(0)
            tok = ""  # Token has been consumed
          else:  # No value expected, just the option letter
            tok = tok[1:]  # Consume this option letter
            vv[0] = True
          break

  if options.help[0]:  # If the -? option was given, display help info
    print(__doc__)
    for nn, vv in options.items():
      print("  -%s %s # %s" % (vv[1][0],
        nn.ljust(8) if len(vv[1])>1 and  vv[1][1]==':' else "        ", vv[2]))
    print(helpTail)
    return

  #print(""+str(len(args))+" args: '"+str(args)+"'")

  if len(args)==0:
    target = "revive"
  else:
    target = args.pop(0)  # Take first token (after the options) as final objective
  log("\nreviveMC74 "+target+"-"+','.join(args)  \
    +" --------------------------------------------------------------")

  # Parse args, set them as variables in global 'arg' var
  for tok in args:
    tok = tok.split('=')
    arg[tok[0]] = tok[1] if len(tok)==2 else True
  
  if target=='listObjectives':
    listObjectivesFunc()
    return

  # Verify that the needed programs and files are/were present
  if os.path.isfile(filesPresentFid)==False:
    if checkFilesFunc():
      writeFile(filesPresentFid, "ok")
    else:
      print("Not all needed programs are in the 'PATH' or not all files are"
        +" present in this directory:")
      for line in state.error:
        print("  --"+line)

      if "adbNeeded" in state.needed:
        print("\nADB/FASTBOOT programs needed.  See:\n"
          +"  https://www.xda-developers.com/install-adb-windows-macos-linux/\n"
          +"  for instructions.  If you have adb and fastboot, make sure they"
          +" are in the 'path'"
          +"\n  (For experts, see: reviveMC74.py  neededProgs.adb[0] for the"
          +" command we use to test.)"
        )
        
      if "unpNeeded" in state.needed:
        print("\nUNPACKBOOTIMG/MKBOOTIMG/CPIO/CHMOD programs needed.  To download, see:\n"
          +"  https://forum.xda-developers.com/showthread.php?t=2073775\n"
          +"  or: https://github.com/huaixzk/android_win_tool   for precompiled"
          +" windows version\n"
          +"  or: https://github.com/osm0sis/mkbootimg   for the source code.\n"
          +"  Make sure that 'unpackbootimg', 'mkbootimg', 'chmod' and 'cpio' are in"
          +" the 'path'."
        )
        
      if "gzipNeeded" in state.needed:
        print("\nGZIP/GUNZIP programs needed.  To for windows, see:\n"
          +"  https://sourceforge.net/projects/unxutils/files/unxutils/current/UnxUtils.zip/download"
          +"To get 'UnxUtil.zip.  From that file extract: 'usr/local/wbin/gunzip.exe' "
          +"and 'usr/local/wbin/gzip.exe' to a directory that is in your PATH." 
        )
        
      return

  # Execute the target objective's 'func', it will call it's prerequisites
  try:
    func = eval(target+"Func")
  except: 
    # Objective not found, show list of objectives
    listObjectivesFunc()
    return

  if type(func).__name__ != 'function':
    print("Can't find function for objective '"+target+"'")
    return

  print("  "+target+" Function:")  
  if func():
    print("Acheived objective '"+target+"'")
  else:
    print(target+" failed:")
    for line in state.error:
      print("  --"+line)

  log(rformat(state))  # Log the state of the operation on completion



# VARIOUS UTILITY FUNCTIONS --------------------------------------------------
def chkProg(pg):
  try:
    resp, rc = execute(pg[0], False)
  except:
    progName = pg[0].split(' ')[0]
    #print("Can't find '"+progName+"' program in path")
    state.error.append("checkProgs: Can't find '"+progName+"' program")
    state.needed.append(pg[1])
    return False
  return True


def chkFile(fid):
  if os.path.isfile(installFilesDir+"/"+fid):
    return True
  else:
    state.error.append("checkFiles: Can't find file '"+fid+"'")
    return False


def findLine(data, searchStr):
  for line in data.split('\n'):
    if searchStr in line:
      return line


def executeLog(cmd, showErr=True):
  '''Execute an operating system command and log the command and response'''
  print("    Executing: '"+str(cmd)+"'")
  ret = execute(cmd, showErr)
  logp("  '"+str(cmd)+"'  (rc="+str(ret[1])+")\n"+prefix('      |', ret[0]))
  return ret


def log(msg):
  fp = open(logFid, 'ab')
  ts = datetime.datetime.now().strftime("%y/%m/%d-%H:%M:%S")
  fp.write(str.encode(ts+" "+msg+'\n'))
  fp.close()


def logp(msg):
  print(msg)
  log(msg)


def prefix(prefix, msg):
  if len(msg)==0:  return msg
  msg = msg[:-1] if msg[-1]=='\n' else msg
  return prefix+('\n'+prefix).join(msg.split('\n'))


def listDir(dir, recursive=True, search=''):
  # Replacement for 'find . -print' on Windows
  lst = []
  for fn in os.listdir(dir):
    subdir = dir+'/'+fn
    if search in subdir: 
      lst.append(subdir)
    if recursive and os.path.isdir(subdir):
      lst.extend(listDir(subdir))
  return lst


# FUNCTIONS FOR CARRYING OUT OBJECTIVES ----------------------------------------
def reviveFunc():
  logp("--(reviveFunc)") 
  #if adbModeFunc("normal") == False:
  if flashPartFunc()==False:
    print("flashPartFunc failed")  
    return False

  if installAppsFunc()==False:
    print("installAppsFunc failed")  
    return False

  if startPhoneFunc()==False:
    print("startPhoneFunc failed")  
    return False
  return True


def replaceRecoveryFunc():
  ''' Use fastboot to flash the CWM recovery image, recoveryClock.img to the recovery 
  partition, then reboot into 'adb' mode with the new unrestricted recovery mode

  The CWM interface should show on the phone's display.
  '''

  if state.adbMode != 'adb':
    if adbModeFunc("adb")==False: 
      return False

  # Has the recovery partition already been replaced?
  isReplaced = False
  resp, rc = executeLog("adb shell grep secure default.prop")
  
  if findLine(resp, "ro.secure=0"):
    # This phone already has had the recovery replaced (ie shell cmd worked)
    # ro.secure has already been changed to '0', boot partition already fixed
    state.fixBootPart = True
    if os.path.isfile("rmcBoot.img"):
      state.backupBoot = True  # No need to backup, boot partition already fixed

  elif findLine(resp, "failed: No such file"):
    # The recovery partition has not been replaced, do it now
    # Switch to fastboot mode
    if state.adbMode != 'fastboot':
      if adbModeFunc("fastboot")==False: 
        return False

    logp("\n--replaceRecovery partition")
    logp("  --Writng revovery partition image:  "+neededFiles.recoveryClockImg)
    resp, rc = executeLog("fastboot flash recovery "+installFilesDir+"/"+neededFiles.recoveryClockImg)

    print('''
    The recovery partition has been updated; the MC74 is going to reboot now.

    --Hold the 'mute' button down.
    --Press enter on this computer.
    --When the cisco/meraki logo appears and the vibrator grunts, release the 'mute' button
    --(The ClockworkRecovery UI should appear on the display.  You need not do anything on
      that display.)

    ''')
    try: 
      resp = input()  # Wait for the user to hold mute down and press enter
    except: 
      pass

    print("    --Rebooting")
    resp, rc = executeLog("fastboot reboot")

  state.replaceRecovery = True
  return True


def backupPartFunc():
  '''Backup a disk partition from the MC74, defaults to the 'boot' partition.  If it is the boot or boot2
  partition, it is then unpacked into the rmcBoot[2]Unpack and the ramdisk from that boot image is 
  unpacked into the rmcBoot[2]Ramdisk directory.
  '''

  if replaceRecoveryFunc()==False:
    return False
  if "backupBoot" in state and state.backupBoot and target!="backupPart":
    # If target is explicitly backupBoot, continue on
    return True  # backupBoot was already done, no need to backup boot

  partName = arg.part  # Get name of partition to backup, defaults to 'boot'
  if partName=="both":
    partName = "boot"
  partFid = "/dev/block/platform/sdhci.1/by-name/"+partName
  if 'img' in arg:
    imgFn = arg.img
    makeOrig = False
  else:
    imgFn = 'rmc'+partName[:1].upper()+partName[1:]+".img"
    makeOrig = True


  logp("\nbackupPart "+partName+" partition: "+partFid)
  resp, rc = executeLog("adb shell dd if="+partFid+" of=/cache/"+imgFn+" ibs=4096")
  resp, rc = execute("adb pull /cache/"+imgFn+" .")
  resp, rc = executeLog("adb shell rm /cache/"+imgFn)

  if os.path.isfile(imgFn)==False:
    logp("!!Can't find "+imgFn+" after pulling it")
    return False
  biSize = os.path.getsize(imgFn)
  if biSize!=8192*1024 and partName[:4]=='boot':
    print("--"+imgFn+" file size is "+str(biSize)+", should be 8388608")
    return False
    
  print("  --unpack "+imgFn+" and unpack the ramdisk")
  resp, rc = executeLog(sys.executable+' '+installFilesDir+"/packBoot.py unpack "+imgFn)
  # sys.executable is the name of the python interpreter we are running

  if makeOrig: # If img fn was NOT explicitly specified, rename to ...Orig
    try:
      os.remove(imgFn+"Orig")
    except:  pass
    os.rename(imgFn, imgFn+"Orig")

  if partName[:4]=='boot':
    state.backupBoot = True
    state.fixBootPart = False  # Newly backuped up boot.img needs to be packed
      # and written out / flashed
  return True


def fixPartFunc():
  ''' Edit default.prop file (and perhaps other) from rmcBootRamdisk directory, then pack the 
      ramdisk back into a rmcBoot.img file
  '''
  if backupPartFunc()==False:
    return False

  partName = arg.part  # Get name of partition to backup, defaults to 'boot'
  if partName=="both":
    partName = "boot"
  imgId = 'rmc'+partName[:1].upper()+partName[1:]

  if partName=='boot' and 'fixBootPart' in state and state.fixBootPart \
    and target!="fixPart":
    print("  --skipping fixPart for boot partition, already done")
    return True  # For normal revive, if boot is fixed, skip it
    # If this is an explicit request to fixPart, do it

  logp("\nfixPartFunc "+imgId+".img to make it rooted.")
  try:
    os.remove(imgId+'.img')
  except:  pass

  if partName[:4]=='boot':
    # Edit default.props, change 'ro.secure=1' to 'ro.secure=0'
    # and: persist.meraki.usb_debug=0 to ...=1
    logp("  -- edit default.prop to change ro.secure to = 0")
    try:
      fn = imgId+"Ramdisk/default.prop"
      prop = readFile(fn)
      log("  default.prop:\n"+prefix('__', prop))

      try:
        ii = prop.index('secure=')+7
        prop = prop[:ii]+'0'+prop[ii+1:] # Change '1' to '0'
      except:  print("  --failed to find/replace 'secure=1'")
      try:
        ii = prop.index('usb_debug=')+10
        prop = prop[:ii]+'1'+prop[ii+1:] # Change '0' to '1'
      except:  print("  --failed to find/replace 'secure=1'")
      #log("itermediate default.prop:\n"++prefix('--', prop))

      # other fixes (not implemented yet)
      print("  (UIF create sym link from /ssm to /sdcard/ssm)");
      print("  (UIF change prompt to be '\\n# ' (shorten it))");

      # Remove \r from \r\n on windows systems
      pp = []
      for ln in prop.split('\n'):
        if ln[-1:]=='\r':  ln = ln[:-1]
        if len(ln)>0:
          #print("      .."+ln)
          pp.append(ln)
      writeFile(imgId+"Ramdisk/default.prop", '\n'.join(pp))
      # /default.prop will be ignored by system/core/init/init.c if writable by
      # group/other
      resp, rc = executeLog("chmod go-w "+imgId+"Ramdisk/default.prop")
      log("    fixed "+partName+" default.prop:\n"+prefix('__', '\n'.join(pp)))
    except IOError as err:
      logp("  !! Can't find: "+fn+" in "+os.getcwd())
      return False

    # Add symlink to /ssm
    # in /init.rc after 'symlink /system/etc /etc' insert symlink /storage/emulated/legacy/ssm /ssm
    # in init.bcm911130_me1.rc after symlink.../sdcard  symlink /storage/emulated/legacy/ssm /ssm2
    editFile(imgId+"Ramdisk/init.rc", "symlink /system/etc",
      insert="symlink /storage/emulated/legacy/ssm /ssm\n")
    editFile(imgId+"Ramdisk/init.bcm911130_me1.rc", "symlink /storage/emulated/legacy /sdcard",
      insert="symlink /storage/emulated/legacy/ssm /ssm\n")


  logp("  -- repack ramdisk, repack "+imgId+".img")
  resp, rc = executeLog(sys.executable+' '+installFilesDir+"/packBoot.py pack "+imgId+".img")
  # sys.executable is the name of the python interpreter we are running
  logp(prefix("__|", '\n'.join(listDir(os.getcwd(), False, 'rmcBoot.img'))))
  if os.path.isfile(imgId+".img"):  # Make sure no .img file, we will rename
    hndExcept()
  

  # Rename the new file, rmcBoot.img2xxxxxxxxxxx (2... is the first digit in decade timestamp)
  for fid in os.listdir('.'):
    if fid[:len(imgId)+5] == imgId+'.img2':
      os.rename(fid, imgId+'.img')
      break
  logp(prefix("..|", '\n'.join(listDir(os.getcwd(), False, 'rmcBoot.img'))))

  if os.path.isfile(imgId+".img"):  # Did packBoot succeed in creating .img file?
    return True
  else:
    state.error.append("fixPart: Can't find file '"+imgId+".img' after packBoot returned.")
    return False


def flashPartFunc():
  '''Write a parition image to the device then copy it to the specified partition
  By default this 'flashes' 'rmcBoot.img' to the 'boot' partition, but by
  specifiying 'part=???' and/or 'img=???' options, any image can be written
  to any partition.
  ''' 
  doBoth = False
  partName = arg.part  # Get name of partition to backup, defaults to 'boot'
  if partName == "both":
    partName = "boot"
    doBoth = True
  partFid = "/dev/block/platform/sdhci.1/by-name/"+partName
  if 'img' in arg:
    imgFn = arg.img
  else:
    imgFn = 'rmc'+partName[:1].upper()+partName[1:]+".img"

  # If flashPart was not explicitly called, test to see if it has been done
  if target != "flashPart":
    # Check timestamp of rmcBoot.img with copy stored in /cache/boot.versionDate
    imgDt, imgTm, imgSz = fileDtTm(imgFn)
    print("    "+imgFn+" timestamp: "+imgDt+' '+imgTm)
    # if upToDate, return True

  # If the partition image file doesn't exist, run the fixPartFunc
  if os.path.isfile(imgFn)==False and arg.part[:4]=='boot':
    if fixPartFunc()==False:
      return False

  logp("\nflashPartFunc, writing "+imgFn+" to "+partFid)
  resp, rc = executeLog("adb push "+imgFn+" /cache/"+imgFn)
  if rc!=0:
    state.error.append("Writing "+imgFn+" on device failed")
    return False

  resp, rc = executeLog("adb shell dd if=/cache/"+imgFn+" of="+partFid
    +" ibs=4096")
  if rc!=0:
    state.error.append("Copying "+imgFn+" on device, to "+partName+" failed")
    return False
  if doBoth:
    resp, rc = executeLog("adb shell dd if=/cache/"+imgFn+" of="+partFid+'2'
      +" ibs=4096")
    if rc!=0:
      state.error.append("Copying "+imgFn+" on device, to "+partName+"2 failed")
      return False

  resp, rc = executeLog("adb shell rm /cache/"+imgFn)

  if partName[:4]=='boot':
    state.fixBootPart = True
  return True
  

def installAppsFunc():
  if adbModeFunc("normal")==False:  # Get into normal operation
    return False

  # TTD: add /ssm symlink, disable tunnel, change telsacoilsw launcher DB


  logp("\ninstallAppsFunc, uninstall dialer2, droidNode, droidNodeSystemSvc, if not already done")

  # Uninstall apps
  resp, rc = executeLog("adb shell rm /system/app/DroidNode.apk")
  resp, rc = executeLog("adb shell rm /systemls/app/DroidNodeSystemSvcs.apk")
  resp, rc = executeLog("adb uninstall ribo.audtest")
  resp, rc = executeLog("adb uninstall package:com.meraki.dialer2")
  resp, rc = executeLog("adb shell rm /data/app/com.meraki.dialer2-2.apk")

  # Install programs
  for id in installFiles:
    print("--install file/program: "+id)
    instFl = installFiles[id]
    resp, rc = executeLog("adb push "+installFilesDir+"/"+instFl[0] 
      +" "+instFl[1]+'/'+instFl[0]) 
    if len(instFl)>2:  # If there is a fixup cmd, do it (usually chmod)
      resp, rc = executeLog("adb shell "+instFl[2]+" "+instFl[1]+'/'+instFl[0])

  # Install/update new apps
  for id in installApps:
    fid = installApps[id][0]
    appTag = installApps[id][1]
    newDt, newTm, newSz = fileDtTm(installFilesDir+"/"+fid)

    # If app is already installed see if we have a newer version
    doInstall = True
    instDt, instTm, instSz = remoteFileDtTm("/data/app/"+appTag+"*", appTag)
    if instDt == None:
      logp("    no "+id+" present")
    else:
      logp("    installed copy of "+id+": "+instDt+" "+instTm+"  size: "+str(instSz))
      # Is the installed apk, instDt the same or new?
      if newDt<=instDt and newSz==instSz:
        logp("    (Installed version of "+id+" is good, skipping install. (new "
          +newDt+' '+str(newSz)+")")
        doInstall = False
     
    if doInstall:
      logp("--installing app: "+id+"     ("+newDt+' '+newTm+' '+str(newSz)+")")
      resp, rc = executeLog("adb install -t -r "+installFilesDir+"/"+fid)
  
  # Make the shell prompt something short
  resp, rc = execute("adb shell rm /sdcard/SHELL_PROMPT")  # File is used by /system/etc/mkshrc
  resp, rc = execute("adb shell touch /sdcard/SHELL_PROMPT")

  
  state.installApps = True
  return True


def checkFilesFunc():
  succeeded = True 

  for id in neededProgs:
    succeeded &= chkProg(neededProgs[id]) # Execute cmds to verify programs installed

  for id in neededFiles:
    succeeded &= chkFile(neededFiles[id]) # Verify files exist in installFiles dir

  for id in installFiles:
    succeeded &= chkFile(installFiles[id][0]) # (Programs/Files to be installed)

  for id in installApps:
    succeeded &= chkFile(installApps[id][0]) # (Apps are also in installFiles dir)

  state.checkFiles = succeeded
  return succeeded
 

def adbModeFunc(targetMode="adb"):
  '''Instruct user how to get MC74 in adb mode.
  
  Note: The factory recovery mode does not have the 'sh' command available, therefore
  adb functionality is limited.
  '''
  isAdb = False
  isFastboot = False
  isNormal = False  # Normal is: booted into normal dev operation, not recovery mode
  
 
  # Figure out what mode we are currently in
  currentMode = "unknown"
  resp, rc = executeLog("adb devices")
  if findLine(resp, "\trecovery"):
    currentMode = "recovery"
    isAdb = True
  if findLine(resp, "\tdevice"):
    currentMode = "normal"
    isNormal = True
    isAdb = True  # Normal mode (after fixing) should also adb enabled.
  else:
    resp, rc = executeLog("fastboot devices")
    ln = findLine(resp, "\tfastboot")
    if ln:
      currentMode = "fastboot"
      state.serialNo = ln.split('\t')[0]
      if targetMode=="fastboot":  # We are in fastboot, and that is the target mode
        state.adbMode = "fastboot"
        return True
      isFastboot = True
  
  logp("\n  --adbModeFunc, currentMode: "+currentMode+", targetMode: "+targetMode
    +(" adb" if isAdb else "")+(" normal" if isNormal else "")+(" fastboot" if isFastboot else ""))
  
  if currentMode == targetMode:
    pass  # Nothing to change
  
  elif isAdb and targetMode=="fastboot":
    print("    --Changing from adb mode to fastboot mode")
    resp, rc = executeLog("adb reboot bootloader")
  
  elif isAdb and targetMode=="adb":
    currentMode = targetMode  # normal mode should be eqivalent to adb after fixing
  
  elif targetMode=="adb" or targetMode=="recovery":
    # Reboot the MC74 into Recovery mode
    print('''
    Prepare to reboot the MC74.
      -- Remove the USB cable from the side of the MC74 (if connected)
      -- Remove the Ethernet/POE cable from the back of the MC74
      -- Reconnect the USB cable to the right side(not back) connector of the MC74
        (and the other end to the development computer)
    
    Then, be ready to do this after you press enter:
      -- Apply power with POE ethernet cable to WAN port (the ethernet port closest to the round
        socket on the back of the MC74.)
      -- quickly, press and hold mute button, before backlight flashes
      -- keep mute button down until cisco/meraki logo appears and vibrator grunts.
      -- release mute
      -- (in about 15 sec, Windows should make the  'usb device attached' sound.)
    
    Press enter when ready to power up the MC74.
    ''')
    try:
      resp = input()
    except:
      pass
    
  elif isNormal==False and targetMode=="normal":
    print("    --Changing from "+currentMode+" mode to normal device mode")
    if isFastboot:
      resp, rc = executeLog("fastboot reboot")
      
    else:
      #resp, rc = executeLog("adb reboot")  --This seems to hang in clockwork recovery mode
      # Per https://opensource.com/article/19/7/reboot-linux  reboot can be forced with:
      #   echo b > /proc/sysrq-trigger
      # (if /proc/sys/kernel/sysrq is set to '1', which seems to be the case in clockwork recovery)
      resp, rc = executeLog(['adb', 'shell', "echo b >/proc/sysrq-trigger"])
      log("reboot by sysrq, rc="+str(rc)+": "+resp)
    
  else:
    print("adbMode request to go from '"+currentMode+"' mode to '"+targetMode+"'.")
    print("  Don't know how to change to that mode.")
    return False
    
  if currentMode!=targetMode:
    cmd = "fastboot" if targetMode=="fastboot" else "adb"
    print("  --loop running '"+cmd+" devices' until we see a device")
    searchStr = "\trecovery" if targetMode=='adb' else "\tfastboot"
    if targetMode == "normal":   searchStr = "\tdevice"
    
    for ii in range(0, 12):
      resp, rc = executeLog(cmd+" devices")
      ln = findLine(resp, searchStr)
      if ln:
        state.serialNo = ln.split('\t')[0]
        print("      found device with serial number: "+state.serialNo)
        state.adbMode = targetMode
        return True
        
      print("--Waiting for reboot "+str(12-ii)+"/12: "+resp.replace('\n', ' '))
      time.sleep(5)
    state.adbMode = "unknown"
    return False
    
  state.adbMode = targetMode
  return True


def resetBFFFunc():
  logp("\nresetBFFFunc")
  if os.path.isfile(filesPresentFid):
    os.remove(filePresentFid)
    print("The filesPresent.flag file was removed, next time you run"
      +" reviveMC74, it will recheck that you have all the needed files"
      +" and programs.")
  else:
    print("(There was no 'filesPresent.flag file.)")
  return True


def startPhoneFunc():
  logp("\nstartPhoneFunc")
  resp, rc = executeLog("adb shell am startservice ribo.ssm/.SSMservice")
  resp, rc = executeLog("adb shell am start revive.MC74/org.linphone.dialer.DialerActivity")
  resp, rc = executeLog("adb shell am force-stop com.meraki.droidnode")
  resp, rc = executeLog("adb shell am force-stop com.meraki.dialer2")
  resp, rc = executeLog("adb shell am force-stop com.meraki.dialer2:pjsip")
  return True


def manualFunc():
  logp("\nmanualFunc Enter commands on console...")
  try:
    hndExcept()
    return True
  except: hndExcept()


def versionFunc():
  logp("\nversionFunc --Gathers information about the software version on the MC74")
  if state.adbMode != 'adb':
    if adbModeFunc("adb")==False: 
      print("Sorry, the MC74 needs to have ADB working in recovery or normal "
        +"device mode to work.")
      return False

  if state.adbMode == "recovery":
    # Mount /system, and /data  if in recovery mode
    resp, rc = executeLog("mount /dev/block/platform/sdhci.1/by-name/system /system")
    resp, rc = executeLog("mount /dev/block/platform/sdhci.1/by-name/userdata /data")
  
  iList = []

  # Get the device serial number from u-boot-env partition
  resp, rc = executeLog("adb shell dd if=/dev/block/platform/sdhci.1/by-name/u-boot-env " \
    "of=/cache/uBootEnv bs=640 count=1")
  if rc==0:
    resp, rc = executeLog("adb pull /cache/uBootEnv uBootEnv.tmp")
    resp, rc = executeLog("adb shell rm /cache/uBootEnv")
    ube = readFile("uBootEnv.tmp")
    if len(ube)>5:  # Remove mysterious leading 5 bytes
      ube = ube[5:]

    for ii in reversed(range(0, len(ube))):  # Remove trail nulls from u-boot-env file
      if ube[ii]!='\0':
        ube = ube[:ii+1]
        break

    ube = ube.split('\0')
    log("u-boot-env:\n"+rformat(ube))
    for ln in ube:
      if len(ln)>3 and ln[:3]=='sn=':
        iList.append("devSN:\t"+ln[3:])
    try:
      os.remove("uBootEnv.tmp")
    except:  pass


  # Get ro.build.version.release, ro.build.id, ro.build.date
  propNames = ["ro.build.id", "ro.build.version.release", "ro.build.date"]
  resp, rc = execute("adb shell cat /system/build.prop")
  prop = bunch()
  if rc == 0:
    lines = linesToList(resp)
    for ln in lines:
      nameVal = ln.split('=')  
      if len(nameVal)>1:  # If line doesn't contain an '=', it may be a comment
        prop[nameVal[0].strip()] = nameVal[1].strip()
  
  for pn in propNames:
    if pn in prop:
      iList.append(pn+":\t"+prop[pn])
    
  # Get date and size of various interesting files
  getDateTime(iList, "/init")
  getDateTime(iList, "/system/build.prop")
  getDateTime(iList, "/system/framework/am.jar")
  getDateTime(iList, "/cache/downloads/update.tar.gz")
  getDateTime(iList, "/cache/downloads/images/boot.img")
  getDateTime(iList, "/cache/downloads/images/system.img")

  # Read /proc/version (in normal mode)
  resp, rc = executeLog("adb shell cat /proc/version")
  if rc==0:
    iList.append("/procVersion:\t"+resp)
  else:
    iList.append("/procVersion:\t(unknown, in recovery mode)")

  infoStr = ""
  for ln in iList:
    infoStr += "  "+ln+"\n"
  print("\nVersion Info:\n"+infoStr)
  writeFile("version.info", infoStr)
  return True


def editFile(fid, find="<editMe>", replace=None, insert=None, delete=None):
  '''Simple edit of a file.  Find first line containing 'find' string, then 'insert' a line
    lines, and/or 'replace' the line we found, or delete the line found, then write back to
    (local) disk.
  '''
  logp("  -- editFile "+fid+" find '"+find+"'")
  try:
    body = readFile(fid)
    
    # other fixes (not implemented yet)
    #print("  (UIF create sym link from /ssm to /sdcard/ssm)");
    
    pp = []
    for ln in body.split('\n'):
      if ln[-1:]=='\r':  ln = ln[:-1]  # Remove \r from \r\n on windows systems
      if find and ln.find(find)!=-1:  # Does this line contain the content we need to find?
        find = None  # Remove the 'find' string now that we found it
        if replace:  # If the line is to be replaced, replace it, otherwise add it
          pp.append(replace)
        elif not delete:
          pp.append(ln)
        
        if insert:  # Insert a list of lines, or just one line
          if type(insert)==list:
            for il in insert:
              pp.append(il)
          else:
            pp.append(insert)
      else:
        pp.append(ln)  # This is not the line you are looking for, just copy the file
        
    if find:
      logp("  !! Failed to find '"+find+"' in "+fid)
    writeFile(fid, '\n'.join(pp))
    
  except IOError as err:
    logp("  !! Can't find: "+fid+" in "+os.getcwd())
    return False


def getDateTime(iList, fn):
  resp, rc = executeLog("adb shell ls -l "+fn)
  if rc==0:
    lines = linesToList(resp)
    for ln in lines:
      if len(ln)>2 and ln[0:2]=='__':  # Ignore '__bionic_open_tzdata...' error lines
        continue
      iList.append(fn+":\t"+ln)
    

def fileDtTm(fid):
  dt = os.path.getmtime(fid)
  ts = datetime.datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M:%S')
  sz = os.path.getsize(fid)
  dt, tm = ts.split(' ')
  return [dt, tm, sz]

def remoteFileDtTm(fid, tag=None):
  if tag == None: tag = fid
  remDtTm = [None, None, 0]
  resp, rc = execute("adb shell ls -l "+fid)
  if rc==0:
    for ln in resp.split('\n'):
      if ln.find(tag)>0:  # If this line of ls -l is the one for this file...
        if ln.find("No such") != -1:
          logp("    no "+tag+" present")
          break
        sz, dt, tm, fn = ln.split(' ')[-4:]
        remDtTm = [dt, tm, int(sz)]
  return remDtTm


def linesToList(resp):
  lines = []
  for ln in resp.split('\n'):
    while len(ln)>0 and ln[-1]=='\r':  # Lines through adb/shell have 2 \r's before the \n
      ln = ln[:-1]
    ln = ln.strip()
    if len(ln)==0 or ln[0]=='#':
      continue  # Skip comments
    lines.append(ln)
  return lines


def listObjectivesFunc():
  print("\nList of objectives (phases or operations needed for revival) Case sensitive:")
  for ob in objectives:
    objName = ob[0]
    desc = ob[1]
    if desc[0]!='!':
      print("  "+objName+"\t"+desc)
  print("\n\nThe objectives are listed in the order they are normally preformed.\n")


state = bunch( # Attributes are added here to indicate state or progress in objective
  adbMode = None,
  error = [],   # A place to return a list of errors
  needed = []   # A list of messages that need to be displayed
)

# Collection of all defined objectives
#  Note: If 'func' attribute is missing, the function is:  <objectiveName>Func
objectives = [
  ['listObjectives', "(optional) Lists all objectives"],
  ['checkFiles', "Verifies that you have the needed files, apps, images, and programs."],
  ['adbMode', "Gets device into 'adb' mode, or 'fastboot' or 'normal' operation."],
  ['replaceRecovery', "Replace the recovery partition with a full featured recovery program"], 
  ['backupPart', "Backs up boot (or other specified partition)."],
  ['fixPart', "Changes default.prop file on the ramdisk to allow rooting."],
  ['flashPart', "Rewrites the (boot) partition image "],
  ['installApps', "Install VOIP phone app, uninstall old Meraki phone apps"],
  ['revive', "<--Install reviveMC74 apps --this is the principal objective--"],
  ['version', "Find and record some software version info"],
  ['manual', "Place to manually invoke reviveMC74 functions (advanced users)"],
  ['resetBFF', "(manual step) Reset the 'Boot partion Fixed Flag'"],
] # end of objectives




if __name__ == "__main__":
  try:
    reviveMain(sys.argv[1:])
  except: hndExcept()
