#!/usr/bin/env python
''''packBoot -- unpack an Android boot.img to a kernel file and unpacked ramdisk --
repack the ramdisk directory back into a ramdisk and pack with kernel
@author: ribo
'''
import sys, os, time, subprocess, shutil
from ribou import *
from datetime import datetime


def unpack(biFn):
  '''Unpack a boot image file
  '''
  fn, ext = biFn.split('.')
  unDir = fn+"Unpack"
  try:
    shutil.rmtree(unDir)
  except:
    pass  # Directory may exist
  os.mkdir(unDir)
  os.chdir(unDir)
  print("cwd "+os.getcwd())

  resp, rc = execute("unpackbootimg -i ../"+biFn)
  print("unpackbootimg "+biFn+": "+str(rc)+"\n"+resp)
  
  resp, rc = execute("ls -l")
  print("ls "+os.getcwd()+": "+str(rc)+"\n"+resp)

  resp, rc = execute("gunzip "+biFn+"-ramdisk.gz")
  print("gunzip "+biFn+"-ramdisk.gz: "+str(rc)+"\n"+resp)
  rd = readFile(biFn+"-ramdisk")
  print("ramdisk "+str(len(rd))+" bytes")
  lsRdOrig, rc = execu("cpio -i -tv", rd)
  writeFile("../"+fn+"LsRdOrig", lsRdOrig)

  os.chdir("..")
  rdDir = fn+"Ramdisk"
  try:
    shutil.rmtree(rdDir)
  except:
    pass
  os.mkdir(rdDir)
  os.chdir(rdDir)
  print("cwd rd "+os.getcwd())
  
  resp, rc = execu("cpio -i -m", rd)
    # -m is preservce file modification time
  print("cpio -i <"+biFn+"-ramdisk: "+str(rc)+"\n"+resp)
  

def pack(biFn):
  '''Pack a bootRamdisk dir back into a ramdisk, and build an image file
     from booUnpack dir
  '''
  print("pack: "+biFn)
  fn, ext = biFn.split('.')
  unDir = fn+"Unpack"
  rdDir = fn+"Ramdisk"

  # In bootRamdisk dir, recreate the cpio archive
  os.chdir(rdDir)
  print("    cwd rd "+os.getcwd())

  fl = listDir('.')
  fl.sort()   # Sort filenames alphabetically
  fList = ""
  for ff in fl:
    if len(ff)>2:  # Remove blank lines and './'
      fList += ff[2:]+"\n"
  
  pr(fList)

  outFid = "../"+unDir+"/"+biFn+"-ramdisk"
  rd, rc = execu("cpio -o -H newc -R 0.0 -F "+outFid, fList, showErr=False,
    returnStr=False)
  print("cpio -o  rc="+str(rc)+", "+str(os.path.getsize(outFid))+" bytes")

  # In the bootUnpack directory, write the ramdisk file and gzip it
  os.chdir("../"+unDir)
  #try:
  #  os.remove(biFn+"-ramdisk")
  #except: pass
  #writeFile(biFn+"-ramdisk", rd)
  lsRdNew, rc = execute("cpio -tv -I "+biFn+"-ramdisk")


  # Compress ramdisk
  #resp, rc = execute("ls -l")
  #print("pre-gzip "+os.getcwd()+": "+str(rc)+"\n"+resp)
  try:
    os.remove(biFn+"-ramdisk.gz")
  except: pass
  resp, rc = execute("gzip "+biFn+"-ramdisk")
  print(" ramdisk gzipped "+str(rc))


  # Build file system image file
  cmdline = readFile(biFn+"-cmdline")[:-1]
  base = readFile(biFn+"-base")[:-1]
  pagesize = readFile(biFn+"-pagesize")[:-1]
  ts = datetime.now().strftime("%y%m%d%H%M")
  cmd = "mkbootimg --kernel "+biFn+"-zImage --ramdisk "+biFn+"-ramdisk.gz" \
    +" --cmdline '"+cmdline+"' --base "+base+" --pagesize "+pagesize \
    +" --output ../"+biFn+ts
  print("cmd: '"+cmd+"'")
  #resp, rc = execute("ls -l")
  #print("pre-mkbootimg "+os.getcwd()+": "+str(rc)+"\n"+resp)
  resp, rc = execute(cmd, True)

  os.chdir("..")
  writeFile(fn+"LsRdNew", lsRdNew)


def listDir(dir):  # Replacement for 'find . -print' on Windows
  lst = []
  for fn in os.listdir(dir):
    subdir = dir+'/'+fn
    lst.append(subdir)
    if os.path.isdir(subdir):
      lst.extend(listDir(subdir))
  return lst


if __name__ == '__main__':
  try:
    # Set defaults (which may be changed by name=value arguments)
    op = 'unpack'

    if len(sys.argv)<2:
      print("packBoot needs arg 'pack' or 'unpack <filename>'")

    else:
      op = sys.argv[1]
      args = []
      argList = sys.argv[2:]  # Remove the program name and pack/unpack mode token
      for arg in argList:
	if '=' in arg:
	  args.remove(arg)
	  arg = arg.split('=')  # Handle name=val arguments
	  locals()[arg[0]] = arg[1]  # Add name to locals
	else:
	  args.append(arg)

      biFn = args[0] if len(args)>0 else "boot.img"
      if op == 'pack':
	pack(biFn)
      else:
	unpack(biFn)
  except Exception as ex:
    hndExcept()
