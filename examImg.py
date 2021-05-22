#!/usr/bin/env python
'''Unpack an MC74 rmcBoot img file into its own directory and display information about
  its form and files.
'''

import sys, os, time, datetime, shutil, inspect
from ribou import *

def examImg(args):
  # If no args, display comaparison of all img* directories
  if len(args)==0:
    return compareImg()
  
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

  pyFile = inspect.getfile(inspect.currentframe())
  pyFile = pyFile.replace('\\', '/')  # Convert windows directory separators to '/'
  pyFileDir = pyFile[:pyFile.rfind('/')]
  print("  pyFileDir: "+pyFileDir)

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


def compareImg():
  iInfo = bunch()  # Collection of data about an img

  for fn in os.listdir('.'):
    print("--"+fn)
    if os.path.isdir(fn) and fn[:3]=="img":  # If this is a img* directory...
      iInfo[fn] = analyzeDir(fn)
     
  pr(iInfo) 


def analyzeDir(dir):
  inf = bunch(img=bunch(fn=dir), unpack=bunch(), ramdisk=bunch())
  os.chdir(dir)  # Enter the directory with the files
  inf.img = fInfo('', "rmcBoot."+dir)

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


def tc(vv):
  '''Return a 2 character string with leading zero for an integer value'''
  return str(vv).rjust(2, '0')


if __name__ == "__main__":
  try:
    examImg(sys.argv[1:])
  except Exception as xx:
    hndExcept()
