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
filesPresentFid = "filesPresent.flag"  # If this file exists, we checked that needed files are here

neededProgs = bunch(  # These are commands that demonstrate that needed programs are in the
  # PATH and that they execute (ie not just the filename of the program
  adb = ["adb version", "adbNeeded"],   
  fastboot = ["fastboot", "adbNeeded"],
  unpackbootimg = ["unpackbootimg", "unpNeeded"],
  mkbootimg = ["mkbootimg", "unpNeeded"]
)

neededFiles = bunch(
  recoveryClockImg = "recovery-clockwork-touch-6.0.4.7-mc74v2.img",
  packBootPy = "packBoot.py",
)

installApps = bunch(
  audTest = "audTest.apk",
  launcher = "com.teslacoilsw.launcher-4.1.0-41000-minAPI16.apk",
  ssm = "revive.SSMService-debug.apk",
  reviveMC74 = "revive.MC74-debug.apk"
)


options = bunch(
  #sendOid=[None, 'o:', 'Name of object to send as body of command'],
  #sessionMode = [False, 's', 'Loop reading commands from stdin'],
  #debug = [False, 'd', 'Pause for debug after cmdeply returns'],
  help = [False, '?', 'Print help info']
)

arg = bunch(  # Place to store args for objective funcs to use
  part = "boot",  # Target partition to backup or fix/install, ie 'boot' or 'boot2'
)

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
        print("\nUNPACKBOOTIMG/MKBOOTIMG programs needed.  To download, see:\n"
          +"  https://forum.xda-developers.com/showthread.php?t=2073775\n"
          +"  or: https://github.com/huaixzk/android_win_tool   for precompiled"
          +" windows version\n"
          +"  or: https://github.com/osm0sis/mkbootimg   for the source code.\n"
          +"  If you have unpackbootimg and mkbootimg, make sure they are in"
          +" the 'path'"
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


def executeLog(cmd, showErr=False):
  '''Execute an operating system command and log the command and response'''
  print("  Executing: '"+cmd+"'")
  ret = execute(cmd, showErr)
  logp("  '"+cmd+"'  (rc="+str(ret[1])+")\n"+prefix('    |', ret[0]))
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


# FUNCTIONS FOR CARRYING OUT OBJECTIVES ----------------------------------------
def reviveFunc():
  logp("--(reviveFunc)") 
  if fixPartFunc()==False:
    print("fixPartFunc failed")  
    return False

  if installAppsFunc()==False:
    print("installAppsFunc failed")  
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
  resp, rc = executeLog("adb shell grep secure default.prop", False)
  
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
  if replaceRecoveryFunc()==False:
    return False
  if "backupBoot" in state and state.backupBoot and target!="backupPart":
    # If target is explicitly backupBoot, continue on
    return True  # backupBoot was already done, no need to backup boot

  partName = arg.part  # Get name of partition to backup, defaults to 'boot'
  partFid = "/dev/block/platform/sdhci.1/by-name/"+partName
  imgFn = 'rmc'+partName[:1].upper()+partName[1:]

  logp("\n--backupPart "+partName+" partition: "+partFid)
  resp, rc = executeLog("adb shell dd if="+partFid+" of=/cache/"+imgFn+".img ibs=4096")
  resp, rc = executeLog("adb pull /cache/"+imgFn+".img .")
  resp, rc = executeLog("adb shell rm /cache/"+imgFn+".img")

  if os.path.isfile(imgFn+".img")==False:
    logp("!!Can't find "+imgFn+".img after pulling it")
    return False
  biSize = os.path.getsize(imgFn+".img")
  if biSize!=8192*1024 and partName[:4]!='boot':
    print("--"+imgFn+".img file size is "+str(biSize)+", should be 8388608")
    return False
    
  print("    -- unpack "+imgFn+".img and unpack the ramdisk")
  resp, rc = executeLog("python "+installFilesDir+"/packBoot.py unpack "+imgFn+".img")

  try:
    os.remove(imgFn+".imgOrig")
  except:  pass
  os.rename(imgFn+".img", imgFn+".imgOrig")

  if partName[:4]=='boot':
    state.backupBoot = True
    return True
  else: 
    return False


def fixPartFunc():
  if backupPartFunc()==False:
    return False

  partName = arg.part  # Get name of partition to backup, defaults to 'boot'
  partFid = "/dev/block/platform/sdhci.1/by-name/"+partName
  imgFn = 'rmc'+partName[:1].upper()+partName[1:]

  if partName=='boot' and state.fixBootPart and target!=fixPartFunc:
    print("  --skipping fixPart for boot partition, already done")
    return True  # For normal revive, if boot is fixed, skip it
    # If this is an explicit request to fixPart, do it

  logp("\n--fixPartFunc "+imgFn+".img to "+partFid)
  try:
    os.remove(imgFn+'.img')
  except:  pass

  if partName[:4]=='boot':
    # Edit default.props, change 'ro.secure=1' to 'ro.secure=0'
    # and: persist.meraki.usb_debug=0 to ...=1
    logp("  -- edit default.prop to change ro.secure to = 0")
    try:
      fn = imgFn+"Ramdisk/default.prop"
      prop = readFile(fn)
      log("  default.prop:\n"+prefix('   |', prop))

      try:
        ii = prop.index('secure=')+7
        prop = prop[:ii]+'0'+prop[ii+1:] # Change '1' to '0'
      except:  print("  --failed to find/replace 'secure=1'")
      try:
        ii = prop.index('usb_debug=')+10
        prop = prop[:ii]+'1'+prop[ii+1:] # Change '0' to '1'
      except:  print("  --failed to find/replace 'secure=1'")
      log("itermediate default.prop:\n"+prop)

      # other fixes (not implemented yet)
      print("  (UIF create sym link from /ssm to /sdcard/ssm)");
      print("  (UIF change prompt to be '\\n# ' (shorten it))");

      # Remove \r from \r\n on windows systems
      pp = []
      for ln in prop.split('\n'):
        if ln[-1:]=='\r':  ln = ln[:-1]
        if len(ln)>0:
          print("      .."+ln)
          pp.append(ln)
      writeFile(imgFn+"Ramdisk/default.prop", '\n'.join(pp))
      log("    fixed "+partName+" default.prop:\n"+'\n'.join(pp))
    except IOError as err:
      logp("  !! Can't find: "+fn+" in "+os.getcwd())

  logp("  -- repack ramdisk, repack "+imgFn+".img")
  resp, rc = executeLog("python "+installFilesDir+"/packBoot.py pack "+imgFn+".img")
  if os.path.isfile(imgFn+".img"):
    hndExcept()
  # Rename the new file, rmcBoot.img20xxxxxxxxxx (20... is the date/time stamp)
  for fid in os.listdir('.'):
    if fid[:len(imgFn)+6] == imgFn+'.img20':
      os.rename(fid, imgFn+'.img')
      break

  logp("  -- write new "+imgFn+".img to "+partName+" parition")
  resp, rc = executeLog("adb push "+imgFn+".img /cache/"+imgFn+".img")
  resp, rc = executeLog("adb shell dd if=/cache/"+imgFn+".img of="+partFid
    +" ibs=4096")
  resp, rc = executeLog("adb shell rm /cache/"+imgFn+".img")

  if partName[:4]=='boot':
    state.fixBootPart = True
    return True
  else:
    return false
  

def installAppsFunc():
  if adbModeFunc("normal")==False:  # Get into normal operation
    return False

  logp("\n--installAppsFunc, uinstall dialer2, droidNode, droidNodeSystemSvc")

  # Uninstall apps
  resp, rc = executeLog("adb rm /system/app/DroidNode.apk")
  resp, rc = executeLog("adb rm /systemls/app/DroidNodeSystemSvcs.apk")
  resp, rc = executeLog("adb uninstall package:com.meraki.dialer2")
  # Perhaps run: ps |grep meraki and kill process?  perhaps reboot 

  # Install new apps
  for id in installApps:
    print("  --installing app: "+id)
    resp, rc = executeLog("adb install -t "+installFilesDir+"/"+installApps[id])
  
  state.installApps = True
  return True


def checkFilesFunc():
  succeeded = True 

  for id in neededProgs:
    succeeded &= chkProg(neededProgs[id]) # Execute cmds to verify programs installed

  for id in neededFiles:
    succeeded &= chkFile(neededFiles[id]) # Verify files exist in installFiles dir

  for id in installApps:
    succeeded &= chkFile(installApps[id]) # (Apps are also in installFiles dir)

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

  resp, rc = executeLog("adb devices", False)

  # Figure out what mode we are currently in
  currentMode = "unknown"
  if findLine(resp, "\trecovery"):
    currentMode = "adb"
    isAdb = True
  if findLine(resp, "\tdevice"):
    currentMode = "normal"
    isNormal = True
    isAdb = True  # Normal mode (after fixing) should also adb enabled.
  else:
    resp, rc = executeLog("fastboot devices", False)
    ln = findLine(resp, "\tfastboot")
    if ln:
      currentMode = "fastboot"
      state.serialNo = ln.split('\t')[0]
      if targetMode=="fastboot":  # We are in fastboot, and that is the target mode
        state.adbMode = "fastboot"
        return True
      isFastboot = True

  print("\n  --adbModeFunc, currentMode: "+currentMode+", targetMode: "+targetMode)

  if currentMode == targetMode:
    pass  # Nothing to change

  elif isAdb and targetMode=="fastboot":
    print("    --Changing from adb mode to fastboot mode")
    resp, rc = executeLog("adb reboot bootloader")

  elif isAdb and targetMode=="adb":
    currentMode = targetMode  # normal mode should be eqivalent to adb after fixing
    
  elif isAdb==False and targetMode=="adb":
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
    print("    --Changing from adb mode to normal device mode")
    resp, rc = executeLog("adb reboot")

  else:
    print("adbMode request to go from '"+currentMode+"' mode to '"+targetMode+"'.")
    print("  Don't know how to change to that mode.")
    return false
    
  if currentMode!=targetMode:
    cmd = "fastboot" if targetMode=="fastboot" else "adb"
    print("    --loop running '"+cmd+" devices' until we see a device")
    searchStr = "\trecovery" if targetMode=='adb' else "\tfastboot"
    if targetMode == "normal":   searchStr = "device"

    for ii in range(0, 12):
      resp, rc = executeLog(cmd+" devices")
      ln = findLine(resp, searchStr)
      if ln:
        state.serialNo = ln.split('\t')[0]
        print("      found device with serial number: "+state.serialNo)
        state.adbMode = targetMode
        return True

      print("    --Waiting for reboot "+str(12-ii)+"/12: "+resp.replace('\n', ' '))
      time.sleep(5)
    state.adbMode = "unknown"
    return False

  state.adbMode = targetMode
  return True


def resetBFFFunc():
  logp("\n--resetBFFFunc")
  if os.path.isfile(filesPresentFid):
    os.remove(filePresentFid)
  if os.path.isfile(bootFixedFid):
    os.remove(bootFixedFid)
    print("reviveMC74 no longer thinks the boot partition has been updated.")
    print("  (Meaning that normal restart of MC74 is not expected to have a useful 'adb' server)")
  else:
    print("There was no 'boot partition has been fixed' state file")


def manualFunc():
  logp("\n--manualFunc Enter commands on console...")
  aa = arg
  hndExcept()


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
  ['fixPart', "Rewrites the boot partition image with a 'fixed'(unlocked) ramdisk"],
  ['installApps', "Install VOIP phone app, uninstall old Meraki phone apps"],
  ['revive', "<--Install reviveMC74 apps --this is the principal objective--"],
  ['resetBFF', "(manual step) Reset the 'Boot partion Fixed Flag'"],
] # end of objectives




if __name__ == "__main__":
  try:
    reviveMain(sys.argv[1:])
  except: hndExcept()
