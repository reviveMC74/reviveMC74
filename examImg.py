#!/usr/bin/env python
'''Unpack an MC74 rmcBoot img file into its own directory and display information about
  its form and files.
'''

import sys, os, time, datetime, shutil, inspect
from ribou import *

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


if __name__ == "__main__":
  pyFile = inspect.getfile(inspect.currentframe())
  pyFile = pyFile.replace('\\', '/')  # Convert windows directory separators to '/'
  pyFileDir = pyFile[:pyFile.rfind('/')]
  
  try:
    examImg(sys.argv[1:])
  except Exception as xx:
    hndExcept()
