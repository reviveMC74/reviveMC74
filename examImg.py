#!/usr/bin/env python
'''Unpack an MC74 rmcBoot img file into its own directory and display information about
  its form and files.
'''

import sys, os, time, datetime, shutil, inspect
from ribou import *

logFid = "reviveMC74.log"

def examImg(args):
  # If no args, display comaparison of all img* directories
  if len(args)==0 or args[0][:4]=="comp":
    return compareImg(args[1:])
  if args[0][:4]=="pack":
    return pack(args[1:])
  
  imgFn = args[0]
  ii = imgFn.find('.')
  if ii<=0:
    imgFn = "rmcBoot."+imgFn[ii+1:]
  imgDir = args[1] if len(args)>1 else imgFn.split('.')[1]

  # Move the .img file to a directory with the name equal to the img file name extension
  # Create the directory for unpacking the files
  if os.path.isdir(imgDir):
    shutil.rmtree(imgDir)
  os.mkdir(imgDir)
  shutil.copyfile(imgFn, imgDir+'/'+imgFn)
  os.chdir(os.getcwd()+'/'+imgDir)

  resp, rc = execute(sys.executable+' '+pyFileDir+"/installFiles/packBoot.py unpack "+imgFn)
  #print("unpack: %d -- %s" % (rc, resp))

  print(fileInfo('', imgFn))

  print(imgDir+" -- ramdisk:")
  for fn in os.listdir("./rmcBootRamdisk"):
    print(fileInfo("./rmcBootRamdisk/", fn))

  print(imgDir+" -- unpack:")
  for fn in os.listdir("./rmcBootUnpack"):
    print(fileInfo("./rmcBootUnpack/", fn))

  os.chdir('..')  # Go back from imgDir to the original directory


def compareImg(args):
  '''Make a signature of all files in an unpacked image and display/compare them'''
  iInfo = bunch()  # Collection of data about an img

  for fn in os.listdir('.'):
    if os.path.isdir(fn) and fn[:3]=="img":  # If this is a img* directory...
      print("  (%s)" % (fn))
      iInfo[fn] = analyzeDir(fn)
     
  # For each .img, prepare a column of signature information
  imgNmList = args if len(args)>0 else iInfo.keys()
  ref = iInfo[imgNmList[0]]  # Reference img to compare to
  sig = bunch()
  for imgNm in iInfo:
    sig[imgNm] = makeSignature(ref, iInfo[imgNm])

  # Combine the requested signature columns, line by line
  res = []
  for lnNo in range(0, len(sig[imgNmList[0]])):
    for imgNm in imgNmList:
      try:
        res.append(sig[imgNm][lnNo])
      except:
        res.append('?'.ljust(len(sig[imgNm][0])))  # If not enough lines, append junk line
    res.append('\n')  
    
  res = ''.join(res)
  print(res)


def makeSignature(ref, iInf):
  resp = [fileSig(None, iInf.img.name, iInf, ref)]

  resp.append("         UNPACK".ljust(len(resp[0])))  # Make all lines the same length
  sortedFns = iInf.unpack.keys(); sortedFns.sort()
  for fn in sortedFns:
    resp.append(fileSig("unpack", fn, iInf, ref))
    
  resp.append("        RAMDISK".ljust(len(resp[0])))
  sortedFns = iInf.ramdisk.keys(); sortedFns.sort()
  for fn in sortedFns:
    resp.append(fileSig("ramdisk", fn, iInf, ref))
  return resp  


def fileSig(group, fn, iInf, ref):
  # If group is None, then this refers to the img file itself, in iInf.img
  iIn = iInf[group] if group else iInf.img
  refG = ref[group] if group else ref.img
  ff = iIn[fn] if group else iInf.img
  if "md5" in ff:
    md5 = ff.md5[:8]
    try:
      refMd5 = refG[fn].md5[:8]
    except:
      try:
        refMd5 = refG[fn+".gz"].md5[:8]
      except:
        try:
          refMd5 = refG.md5[:8] 
        except:
          refMd5 = "??"
    md5 = (' ' if md5==refMd5 else '*')+md5
  else: 
    md5 = ""
  return "  %s %s %8d%9s" % (fn.ljust(12)[:12], ff.date, ff.size, md5)


def analyzeDir(dir):
  inf = bunch(img=bunch(fn=dir), unpack=bunch(), ramdisk=bunch())
  os.chdir(dir)  # Enter the directory with the files
  inf.img = fInfo('', "rmcBoot."+dir)
  inf.img.name = dir

  for fn in os.listdir("./rmcBootRamdisk"):
    inf.ramdisk[fn] = fInfo("./rmcBootRamdisk/", fn)

  for fn in os.listdir("./rmcBootUnpack"):
    inf.unpack[fn] = fInfo("./rmcBootUnpack/", fn)

  os.chdir('..')  # Go back from imgDir to the original directory
  return inf


def fInfo(dir, fn):
  tm = os.path.getmtime(dir+fn)
  tm = time.localtime(tm)  # Convert tm to time.struct_time format
  ts = tc(tm.tm_year%100)+'/'+tc(tm.tm_mon)+'/'+tc(tm.tm_mday)+'-' \
    +tc(tm.tm_hour)+':'+tc(tm.tm_min)+':'+tc(tm.tm_sec)
  sz = os.path.getsize(dir+fn)
  finf = bunch(
    size = sz,
    date = ts
  )

  if sz<80 and os.path.isfile(dir+fn): finf.cont = readFile(dir+fn)

  if os.path.isfile(dir+fn):
    md5, rc = execute('md5 '+dir+fn)
    finf.md5 = md5.split()[0]
  return finf


def fileInfo(dir, fn):
  if os.path.isfile(dir+fn):
    md5, rc = execute('md5 '+dir+fn)
  else:
    md5 = "        "
  resp = "  "+md5[0:4]+" "+md5[4:8]+" "+str(os.path.getsize(dir+fn)).rjust(8)
  resp += ' '+fn
  return resp


def pack(args):
  imgFn = args[0]
  ii = imgFn.find('.')
  if ii==-1: imgFn = 'rmcBoot.'+imgFn
  if ii==0:  imgFn = 'rmcBoot'+imgFn
  print("Pack this dir into %s" % (imgFn))

  resp, rc = execute(sys.executable+' '+pyFileDir+'/installFiles/packBoot.py pack '+imgFn)
  print("%d %s" % (rc, resp))


def tc(vv):
  '''Return a 2 character string with leading zero for an integer value'''
  return str(vv).rjust(2, '0')


# Utilities used by reviveMC74.py
def editFile(fid, find="<editMe>", replace=None, insert=None, delete=None, adb=False):
  '''Simple edit of a file.  Find first line containing 'find' string, then 'insert' a line
    lines, and/or 'replace' the line we found, or delete the line found, then write back to
    disk.  

    By default, the file is on this computer's file system, if adb=True, the file is read
    and written (pulled and pushed) to the remove Android device using adb.
  '''
  logp("  -- editFile "+fid+" find '"+find+"'")
  try:
    if adb:
      localTmpFid = "examImgEditFile.tmp"
      resp, rc = executeAdbLog("pull "+fid+" "+localTmpFid)
      body = readFile(localTmpFid)
    else:
      body = readFile(fid)
    
    lines = body.split('\n')
    pp = []
    for lnNo in range(0, len(lines)):
      ln = lines[lnNo]  # Get lines by index number so we can inspect/insert/delete future lines
      if ln[-1:]=='\r':  ln = ln[:-1]  # Remove \r from \r\n on windows systems
      if find and ln.find(find)!=-1:  # Does this line contain the content we need to find?
        find = None  # Remove the 'find' string now that we found it
        if replace:  # If the line is to be replaced, replace it, otherwise add it
          pp.append(replace)
        elif not delete:
          pp.append(ln)  # Keep this line, others may be inserted next
        
        if insert:  # Insert a list of lines, or just one line
          # Avoid creating duplicate inserts if fixPart is run multiple times
          firstInsert = insert if type(insert)==str else insert[0]
          print("    firstInsert '"+firstInsert+"'")
          print("    next line   '"+lines[lnNo+1]+"' ("+str(len(lines)>lnNo+1)
            +" "+str(len(lines)>lnNo+1 and lines[lnNo+1]!=firstInsert)+")")
          if len(lines)>lnNo+1 and lines[lnNo+1]!=firstInsert:
            if type(insert)==list:
              for il in insert:
                pp.append(il)
            else:
              pp.append(insert)
          else:
            logp("  (ignoring duplicate insertion edit request for: '"+firstInsert+"'")
      else:
        pp.append(ln)  # This is not the line you are looking for, just copy the file
        
    if find:
      logp("  !! Failed to find '"+find+"' in "+fid)

    pp = '\n'.join(pp)
    if adb:
      writeFile(localTmpFid, pp)
      resp, rc = executeAdbLog("push "+localTmpFid+" "+fid)
    else :
      writeFile(fid, pp)
    
  except IOError as err:
    logp("  !! Can't find: "+fid+" in "+os.getcwd())
    return False


def getDateTime(iList, fn):
  resp, rc = executeAdbLog("shell ls -l "+fn)
  if rc==0:
    lines = linesToList(resp)
    for ln in lines:
      if len(ln)>2 and ln[0:2]=='__':  # Ignore '__bionic_open_tzdata...' error lines
        continue
      iList.append(fn+":\t"+ln)
    

def fileDtTm(fid):
  try:
    dt = os.path.getmtime(fid)
    ts = datetime.datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M:%S')
    sz = os.path.getsize(fid)
    dt, tm = ts.split(' ')
    return [dt, tm, sz]
  except Exception as ex:
    logp("    ("+ex.strerror+", local file: "+fid+")")
  return ["(noDate)", "(noTime)", 0]


def remoteFileDtTm(fid, tag=None):
  if tag == None: tag = fid
  remDtTm = ["(noDate)", "(noTime)", 0]
  resp, rc = executeAdb("shell ls -l "+fid)
  if rc==0:
    for ln in resp.split('\n'):
      if ln.find(tag)>0:  # If this line of ls -l is the one for this file...
        if ln.find("No such") != -1:
          logp("    (remoteFile"+fid+" present ("+tag+"))")
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


def findLine(data, searchStr):
  for line in data.split('\n'):
    if searchStr in line:
      return line


def executeAdbLog(cmd, showErr=True, ignore=None):
  return executeAdb(cmd, showErr, ignore, log=True)


def executeAdb(cmd, showErr=True, returnStr=True, log=False):
  '''Execute a command through ADB on android device, optionally specifying the TCP 
  host name (and optional port number).  Either do it with logging or without
  '''
  if 'arg' in sys.__dict__ and "host" in sys.arg:
    host = sys.arg.host  # Was an explicity host device specified?
    if host.find(':') == -1:
      host += ":5555"
  else:
    host = ""
  if type(cmd) == list:
    cmd.insert(0, "adb")
    if host:
      cmd.insert(1, '-s')
      cmd.insert(2, host)
  else:
    hostOpt = "-s "+host+" " if host else ""
    cmd = "adb "+hostOpt+cmd 
  
  if log:
    return executeLog(cmd, showErr, returnStr);
  else:
    return execute(cmd, showErr, returnStr);


def executeLog(cmd, showErr=True, ignore=None):
  '''Execute an operating system command and log the command and response'''
  print("    Executing: '"+str(cmd)+"'")
  ret = execute(cmd, showErr)
  resp = "    '"+str(cmd)+"'  (rc="+str(ret[1])+")\n"+prefix('      |', ret[0])
  if ignore and ret[0].find(ignore)!=-1:  # Does the response contain the string to ignore
    log(resp)  # This error response is okay, don't print to console
    # Usually done with a command which is okay to fail, like erasing a file that is not there.
  else :
    logp(resp)
  return ret


def log(msg, prefix=""):
  fp = open(logFid, 'ab')
  if prefix:
    fp.write(str.encode(prefix))  # Usually used to prefix line with a \n LF
  ts = datetime.datetime.now().strftime("%y/%m/%d-%H:%M:%S")
  fp.write(str.encode(ts+" "+msg+'\n'))
  fp.close()


def logp(msg, prefix=""):
  print(prefix+msg)
  log(msg, prefix=prefix)


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


def dbCmd(dbFile, sqlCmd):
  '''Execute an SQL command on an android database
  ie: dbCmd(ldb, "select _id, title, componentName from allapps")
  '''
  print("-- "+sqlCmd+"; --")
  try:
    resp, rc = executeAdb(["shell", "sqlite3", dbFile, '"'+sqlCmd+'"'])
    #print("%d %s" % (rc, resp))
  
  except:
    hndExcept()
  return resp


def dbGetRow(dbFile, tblName, colName, colVal):
  '''Retrieve an SQL DB row, given a 'where' clause matching a column value.
  Returns a bunch/dict object with the column values
  ie: dbGetRow(ldb, "allapps", "title", "wPhone")
  '''
  if type(colVal) == str:
    colVal = "'"+colVal+"'"  # sqlCmd will be wrapped in double quotes
  sqlCmd = "select * from %s where %s=%s" % (tblName, colName, colVal)
  print("-- "+sqlCmd+"; --")
  try:
    resp, rc = executeAdb(["shell", "sqlite3", "-line", dbFile, '"'+sqlCmd+'"'])
    #print("%d %s" % (rc, resp))

    # Convert the resp lines:  colName = colValue     into a bunch
    row = bunch()
    for ln in resp.split("\n"):
      ln = ln.split(" = ", 1)
      #print(ln)
      if len(ln) > 1:  # If the line was split on a '='
        row[ln[0].strip()] = ln[1].split('\r')[0]

  except:
    hndExcept()
  return row


def dbSetCell(dbFile, tblName, selColName, selColVal, colName, colVal):
  '''Update one column in one row of an SQL DB table.
  ie: dbSetCell(ldb, "allapps", "title", "wPhone", "title", "MC74")
  '''
  if type(selColVal) == str:
    selColVal = "'"+selColVal+"'"  # sqlCmd will be wrapped in double quotes
  if type(colVal) == str:
    colVal = "'"+colVal+"'"  # sqlCmd will be wrapped in double quotes
  sqlCmd = "update %s set %s=%s where %s=%s" % (tblName, colName, colVal,
    selColName, selColVal)
  print("-- "+sqlCmd+"; --")
  resp, rc = executeAdb(["shell", "sqlite3", dbFile, '"'+sqlCmd+'"'])
  return resp


def dbAddRow(dbFile, tblName, vals):
  '''Add a row to an SQL DB table, where the values for the row are in a bunch/dict
  ie: dbAddRow(ldb, "allapps", bunch(_id=1, title="Clock", cellX=2, cellY=1))
  '''
  
  names = ", ".join(vals.keys())
  values = []
  for nm in vals.keys():
    vv = vals[nm]
    vv = "'"+str(vv)+"'"
    values.append(vv)
  values = ", ".join(values)
  
  sqlCmd = "insert into %s (%s) values (%s)" % (tblName, names, values)
  print("-- "+sqlCmd+"; --")
  
  resp, rc = executeAdb(["shell", "sqlite3", dbFile, '"'+sqlCmd+'"'])
  return resp


ldb = "/data/data/com.teslacoilsw.launcher/databases/launcher.db"  # for testing
def initLauncher():
  ldb = "/data/data/com.teslacoilsw.launcher/databases/launcher.db"
  mcComp = "revive.MC74/org.linphone.activities.LinphoneLauncherActivity"
  favInt = "#Intent;action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;launchFlags=0x10200000;component=%s;end"
  # Switch the Phone favorite in the upper right (dock position 0) to reviveMC74
  print("\nSwitch Phone favorite to reviveMC74")
  resp = dbSetCell(ldb, "favorites", "title", "Phone", "intent", favInt % mcComp)
  print(resp)
  print("\nMove Show Apps icon to lower right")
  resp = dbSetCell(ldb, "favorites", "_id", 1, "hotSeatRank", 0)
  print(resp)

  favRow = dbGetRow(ldb, "favorites", "title", "Phone")
  favRow.update(container=-100, cellY=5.0, screen=1)
  
  print("\nAdd dolphin Browser favorite:")
  dolphComp = "mobi.mgeek.TunnyBrowser/.SplashActivity"
  favRow.update(_id=12, cellX=0.0, title='Browser', intent=favInt % dolphComp)
  resp = dbAddRow(ldb, "favorites", favRow)
  print(resp)
  
  print("\nAdd magicEarth/Map favorite:")
  earthComp = "com.generalmagic.magicearth/com.generalmagic.android.map.MapActivity;l.profile=0"
  favRow.update(_id=13, cellX=1.0, title='Maps', intent=favInt % earthComp)
  resp = dbAddRow(ldb, "favorites", favRow)
  print(resp)
  
  print("\nAdd riboVideo favorite:")
  VPComp = "ribo.vp/.VPcontrol"
  favRow.update(_id=14, cellX=2.0, title='riboVideo', intent=favInt % VPComp)
  resp = dbAddRow(ldb, "favorites", favRow)
  print(resp)
  
  # Remove the 'Google' and 'Create' folder icons, and the side Google search bar
  resp = dbCmd(ldb, "delete from favorites where title='Google'")
  print(resp)
  resp = dbCmd(ldb, "delete from favorites where title='Create'")
  print(resp)
  resp = dbCmd(ldb, "delete from favorites where spanX=5.0")  # The Google search bar, no title
  print(resp)

  # Restart the Nova Launcher so it reads the updated database
  logp("  Killing com.teslacoilsw.launcher... to restart it")
  executeAdb("shell am force-stop com.teslacoilsw.launcher")
  logp("Restarting com.teslacoilsw.launcher")
  executeAdb("shell am start com.teslacoilsw.launcher")
 

def btest():
  try:
    linRc = "/data/data/revive.MC74/files/.linphonerc"
    editFile(linRc, find="reg_expires=3600", replace="reg_expires=600", adb=True)
  except:
    hndExcept()








if __name__ == "__main__":
  pyFile = inspect.getfile(inspect.currentframe())
  pyFile = pyFile.replace('\\', '/')  # Convert windows directory separators to '/'
  pyFileDir = pyFile[:pyFile.rfind('/')]
  
  try:
    examImg(sys.argv[1:])
  except Exception as xx:
    hndExcept()
