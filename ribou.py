"""Ribo's Utility functions

Object types:
  __class__
    <type type>
    <type object>  -- new style classes

    <type 'classobj'>
    <type 'module'>

    <type 'instance'>
    <type 'function'>
    <type 'list'>
    
  see __bases__ to see inheritence

Structure of objects:

bd              -- An instance of bod
  __class__     -- Class object for bod
    assess      -- A method of class bod
      __func__   
        __code__   -- Describes the code for the func
          co_argcount  int:      4
          co_firstlineno int:      230
          ...
"""
# comment
import sys, code, inspect

# List of all known special names (from grepping CPython source)
_pyidNames = ['__IOBase_closed', '__abstractmethods__', '__adapt__',
  '__aenter__', '__aexit__', '__aiter__', '__all__', '__anext__',
  '__annotations__', '__asyncio_running_event_loop__', '__await__', '__bases__',
  '__bool__', '__build_class__', '__builtins__', '__bytes__', '__call__',
  '__ceil__', '__class__', '__class_getitem__', '__classcell__', '__complex__',
  '__conform__', '__contains__', '__copy__', '__ctypes_from_outparam__',
  '__del__', '__delattr__', '__delete__', '__delitem__', '__dict__', '__dir__',
  '__doc__', '__enter__', '__eq__', '__exit__', '__file__', '__floor__',
  '__format__', '__fspath__', '__get__', '__getattr__', '__getattribute__',
  '__getinitargs__', '__getitem__', '__getnewargs__', '__getnewargs_ex__',
  '__getstate__', '__hash__', '__import__', '__index__', '__init__',
  '__init_subclass__', '__instancecheck__', '__ipow__', '__isabstractmethod__',
  '__iter__', '__len__', '__length_hint__', '__loader__', '__ltrace__',
  '__main__', '__missing__', '__module__', '__mro_entries__', '__name__',
  '__new__', '__newobj__', '__newobj_ex__', '__next__', '__package__',
  '__path__', '__pow__', '__prepare__', '__qualname__', '__reduce__',
  '__reduce_ex__', '__repr__', '__reversed__', '__round__', '__set__',
  '__set_name__', '__setattr__', '__setitem__', '__setstate__', '__sizeof__',
  '__slotnames__', '__slots__', '__spec__', '__subclasscheck__',
  '__subclasshook__', '__tp_del__', '__trunc__', '__warningregistry__']


def info(obj=locals(), depth=10, extended=False, sortby='t', indent=0, width=90):
  '''info display information about various python objects:
  Obj types:
    module
    class
    instance of class
    stackFrame
    builtin objects
      list
      dict
      tuple
      basic things: int, string bytearray, float
  '''
  print("type: '%s',  id=%x" % (type(obj), id(obj)))
  
  #if type(obj)==dict or type(obj)==bunch:
  #  _showDict(obj, obj.keys(), indent=indent, depth=depth, width=width)
  #  return
  if depth==0:
    return
  else:
    depth -= 1
  
  inDict = []
  try:
    for tok in obj.__dict__:
      inDict.append(tok)
  except: pass

  def tryKey(nm):
    try:
      type(obj)  # ??? this is needed to make this work?
      #print("  tryKey %s, %s, %d" % ("nm", type(obj), len(lst)))
      val = eval("obj."+nm)
      dct = "+" if nm in inDict else " "
      typ = str(type(val))
      if (typ[0:6]=="<type " and typ[-1]=='>'):  # remove <type > from type string
        typ = typ[6:-1]
      if (typ[0]=="'" and typ[-1]=="'"):  # Remove quotes from type name
        typ = typ[1:-1]
      lst.append((nm, typ, val, dct))

    except: pass

  lst = []
  for nm in _pyidNames:
    tryKey(nm)
  # Also check any keys listed in dir(), that were not in pyNames
  for nm in [nm for nm in dir(obj) if nm not in _pyidNames]:
    tryKey(nm)


  #try:
  #  dictKeys = obj.__dict__.keys()
  #  print("  (obj has __dict__, %d keys)" % len(dictKeys))
  #  if len(dictKeys) == 0:
  #    dictKeys = dir(obj)
  #except:
  #  dictKeys = dir(obj)
  if len(lst):
    # Separate methods from other entries
    meth = []
    oth = []
    for tup in lst:
      tok = tup[1].lower()
      if 'method' in tok or 'wrapper_' in tok:
        meth.append(tup)
      else:
        oth.append(tup)

    _showDict(obj, oth, sortby=sortby, indent=indent, depth=depth, width=width)
    print("methods:")
    _showDict(obj, meth, sortby='n', indent=indent, depth=depth, width=width)

  if extended:  # Extended info includes info about class
    print("\nclass: %s:" % obj.__class__)
    info(obj.__class__, sortby=None, indent=indent, depth=depth, width=width)

  print("\nval:")    
  pr(obj, indent=1)
  print("")
      

def _showDict(obj, keys, indent=0, sortby='t', depth=10, width=90):    
  # Is the key arg an already resolved tuple list?
  if len(keys)>0 and type(keys[0])==tuple:
    lst = keys

  else:    
    lst = []
    for key in keys:
      if type(obj) == dict:
        try:
          val = obj[key]  # for dictionaries
        except:
          lst.append((key, "--unk--", ""))
          continue
      else:
        try: 
          val = obj.__getattribute__(key)  # for lists
        except: #AttributeErr, type classobj doesn't have a __getattribute__?
          try:
            val = obj.__getitem__(key)
          except:
            val = "(cant eval '%s')" % key
      typ = str(type(val))
      if (typ[0:6]=="<type " and typ[-1]=='>'):  # remove <type > from type str
        typ = typ[6:-1]
      if (typ[0]=="'" and typ[-1]=="'"):  # Remove quotes from type name
        typ = typ[1:-1]

      lst.append((key, typ, val))

  # Sort the list of other attributes by type
  if sortby:
    # First sort by name
    lst.sort(key=lambda tup: tup[0])
    # sort=='t' then sort by type (so type ordering is final
    if sortby[0]=='t':
      lst.sort(key=lambda tup: tup[1])

  dictFlag = " "
  for tup in lst:
    if len(tup) == 3:
      key, typ, val = tup   
    else:
      key, typ, val, dictFlag = tup   
    
    # Detect duplicate entries (for func_XXX attributes)
    key = str(key)  # Someone used bool True and False as keys
    if key[0:5] == "func_":
      nm = "__"+key[5:]+"__"
      if nm in keys and obj.__getattribute__(nm)==obj.__getattribute__(key):
        print(_ind(indent+1)+key+" (duplicate of "+nm+")")
    if typ in ("dict", "dictproxy"):
      keys = val.keys()
      print("  "+_ind(indent)+key+"  dict: ("+str(len(keys))+" entries), id " \
        +hex(id(val)))
      if len(keys):
        if depth==0:
          print(_ind(indent+4)+"...")
        else:
          _showDict(val, val.keys(), indent+1, sortby=sortby, depth=depth-1,
            width=width)
    else:
      frag = dictFlag+' '+key+' '*(12-len(key))+' '+typ+': '+' '*(8-len(typ))
      space = width-len(frag)-indent*2
      valStr = str(val)
      if typ == "str":
        valStr = '"'+valStr.replace("\n", "\\n")+'"'
      if len(valStr) >= space:
        valStr = valStr[0:space-3]+"..."
      print(_ind(indent)+frag+valStr)
  return lst


def rf(obj, indent=0, name=None, width=90, **kArgs):
  print(rformat(obj, indent=indent, name=name, width=width, **kArgs))
  return
def rformat(obj, indent=0, name=None, width=90, **kArgs):
  """ribo's format, converts an obj (a nesting of lists, tuples and dicts)
    into an indented, multiline string which is more readable
  """
  #print(" kArgs: %s" % kArgs)
  try:
    kArgs['depth'] -= 1
  except:
    kArgs['depth'] = 100
  if kArgs['depth']==0: 
    print(indent*"  "+"...")
    return

  
  ss = repr(obj)
  if len(ss)<width-indent*2:
    #print("%s --%d %s" % (name, len(ss), ss))
    ss = indent*"  "+ss
    
  else:  # expression is too long, break it down
    ss = ""
    objType = type(obj)
    #print("%s ++%s" % (name, str(objType)))
    if objType==list:
      ss = ""
      for it in obj:
        ss += rformat(it, indent+1, width=width, **kArgs)+',\n'
      if ss[-2:] == ",\n":  ss = ss[:-2]+'\n'
      ss = indent*"  "+"[\n"+ ss +indent*"  "+"]"
      
    elif objType==tuple:
      ss += indent*"  "+"(\n"
      for it in obj:
        ss += rformat(it, indent+1, width=width, **kArgs)+',\n'
      if ss[-2:] == ",\n":  ss = ss[:-2]+'\n'
      ss += indent*"  "+")"
      
    elif objType==dict or objType==bunch: # or objType==bun:
      if objType==dict:
        startTag = "{";  sep = ":";  endTag = "}"
      else:
        startTag = "bunch(";  sep = "=";  endTag = ")"
        
      ss += indent*"  "+startTag+"\n"
      for it in obj:
        ss += indent*"  "+"  "+str(it)+sep+" "+rformat(obj[it],
          indent+1, name=it, width=width, **kArgs).strip()+',\n'
      if ss[-2:] == ",\n":  ss = ss[:-2]+'\n'
      ss += indent*"  "+endTag
    else:    
      ss += indent*"  "+repr(obj)
  return ss


def rformat2(obj, maxDepth=1, indent=0):
  """ribo's format, converts an obj (a nesting of lists, tuples and dicts)
    into an indented, multiline string which is more readable
  """
  ss = ""
  
  if indent<maxDepth:
    objType = type(obj)
    if objType==list:
      ss = ""
      for it in obj:
        ss += rformat(it, maxDepth, indent+1)+',\n'
      ss = indent*"  "+"[ "+ ss[(indent+1)*2:] +indent*"  "+"]"
       
    elif objType==tuple:
      ss += indent*"  ( "
      for it in obj:
        ss += rformat(it, maxDepth, indent+1)+',\n'
      ss += indent*"  "+")"
    elif objType==dict or objType==bunch:
      ss += indent*"  "+"{ "
      for it in obj:
        ss += indent*"  "+"  '"+str(it)+"': "+rformat(obj[it],
          maxDepth, indent+1)+',\n'
      ss += indent*"  "+"}"
    else:    
      ss += indent*"  "+repr(obj)
  else:    
    ss += indent*"  "+repr(obj)
  return ss


def pr(obj, **args): 
  print(rformat(obj, **args))

  
def _ind(len):
  return "  "*len


def writeObj(obj, fid):
  fp = open(fid, 'wb')
  fp.write(rformat(obj))
  fp.close()


def readObj(fid):
  fp = open(fid, 'rb')
  str = fp.read()
  fp.close()
  return eval(str)


def execu(cmd, stdin=None, showErr=True, returnStr=True):
  '''Execute an operating system command, prehaps passing data to stdin'''
  import subprocess
  if type(cmd)==str:
    cmd = cmd.split(' ')
  cmd = [xx for xx in cmd if xx!='']  # Remove ' ' tokens caused by multiple space in str
  proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
  out, err = proc.communicate(stdin)
  if showErr and len(err)>0:
    print("executeErr: %s" % (err))
  if returnStr:
    out = out.encode()
  return out, proc.returncode


def execute(cmd, showErr=True, returnStr=True):
  import subprocess
  if type(cmd)==str:
    cmd = cmd.split(' ')
  cmd = [xx for xx in cmd if xx!='']  # Remove ' ' tokens caused by multiple space in str
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = proc.communicate()
  if showErr and len(err)>0:
    err = err.decode("utf8")
    print("executeErr: %s" % (err))
  if returnStr:
    #out = out.decode("utf-8")
    out = out.encode()  # Convert UNICODE (u'xxx') to string
  return out, proc.returncode


def executeShow(cmd):
  global executeShowPid
  import subprocess
  if type(cmd)==str:  cmd = cmd.split(' ')
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    bufsize=128)
  executeShowPid = proc.pid
  for line in iter(proc.stdout.readline, b''):
    print("eS: "+line)
    sys.stdout.write(line)
    sys.stdout.flush()
  proc.stdout.close()
  rc = proc.wait()
  return proc.returncode


class bunch(dict):  # Object that allows attributes to be added freely
  def __init__(self, **kwds):
    dict.__init__(self, kwds)
    self.__dict__ = self


def readFile(fid):
  data = None
  with open(fid, 'rb') as ff:
    data = ff.read()
  return data


def writeFile(fid, data):
  ff = open(fid, 'wb')
  ff.write(str.encode(data))  # encode added for py3
  ff.close()


def readLines(fid, start=1, end=None, cnt=1):
  if not end:  end = start+cnt  
  return [ln for ii, ln in enumerate(open(fid)) if ii>=start-1 and ii<end-1]


def src(func, ret=False):
  typ = type(func).__name__
  resp = None
  if typ=='function':  # If arg is a <type 'function'>...
    import inspect
    resp = inspect.getsource(func)
  
  elif typ in ['code', 'stk', 'frame', 'instancemethod']:
    hiLite = -1
    if typ=='stk':  # Our stk class, contains a current frame
      func = func.fr
      typ = 'frame'
    if typ=='instancemethod':
      func = func.__func__.__code__
      typ = 'code'  # Re-evaluate now as 'code'
    elif typ=='frame':
      hiLite = func.f_lineno
      func = func.f_code
      typ = 'code'
    
    if typ=='code':
      fid = func.co_filename;  startLn = func.co_firstlineno
    hiLite -= startLn
    print("fid %s, startLn %d, hiLite %d" % (fid, startLn, hiLite))
    
    lns = readLines(fid, startLn, cnt=80)
    initialIndent = 0
    for ch in lns[0]:
      if ch!=' ': break  # Found first nonblank char
      initialIndent += 1

    # Scan source lines until we find one equally or less indented than first ln
    ii = 1; done = False
    while not done and ii<len(lns):
      pref = lns[ii][:-1][:initialIndent+1]
      for ch in pref:
        if ch=='\t':  # tab, remove 7 chars from end of pref??
          pref = pref[:-7]
        elif ch!=' ': 
          done = True
          break
      if ii==hiLite:  # Highlight the current line
        jj = 0
        for ch in lns[ii]:
          if ch==' ' or ch=='\t':
            jj += 1
          else:
            break
        hil = '-'*(jj-1) + '>'
        lns[ii] = hil + lns[ii][jj:]
      if not done: ii += 1
    
    # Remove trailing lines that are all blanks or tabs
    lns = lns[:ii]  # Remove lines that are not part of this funcion
    for ii in range(len(lns)-1, -1, -1):
      deleteIt = True
      for ch in lns[ii]:
        if ch!=' ' and ch!='\t' and ch!='\n':
          deleteIt = False
          break
      if deleteIt: del lns[ii]
    resp = ''.join(lns)
  if ret:
    return resp
  else:
    print(resp)


class stkFr(dict):
  def __init__(self, frArg=None, **kwds):
    dict.__init__(self, kwds)
    self.__dict__ = self
    if frArg==None:
      frArg = inspect.currentframe()
      self.depth = -1
    self.fr = frArg
    self.lineNo = frArg.f_lineno
    co = frArg.f_code
    self.func = co.co_name
    self.fileName = co.co_filename
    self.locals = frArg.f_locals
    self.globals = frArg.f_globals
  
  
  def __repr__(self):
    fr = self.fr
    return "  %d: %s %s:%d %s" % (self.depth, self.func, fr.f_code.co_filename,
     fr.f_lineno, str(fr))
  
  
  def sfFunc(self):
    print("in stkFr.sfFunc function")


def hndExcept():
  print("in hndExcept")
  exType, exValue, tb = sys.exc_info()
  stk = []
  sFr = None
  fr = None
  try:
    co = tb.tb_frame.f_code
    sys.stderr.write("Exception at %s:%d: %s\n" % (co.co_name, tb.tb_lineno, repr(exValue)))
    #traceback.print_tb(exTrace)
    while tb:
      fr = tb.tb_frame
      sFr = stkFr(fr, prev=sFr, depth=len(stk))
      co = fr.f_code
      fn = co.co_filename.split('/')[-1]
      print("%2d  %s %d %s --" % (len(stk), co.co_name, fr.f_lineno, fn))
      stk.append(sFr)
      #print("globals: %s" % (str(fr.f_globals.keys())))
      tb = tb.tb_next

  except:
    fr = inspect.currentframe().f_back
    stk = [stkFr(fr, depth=0)]
    print("(using current frame)")

  print("  Locals: %s" % (', '.join(stk[-1].locals.keys())))
  #print("  Globals: %s" % (', '.join(stk[-1].globals.keys())))
  fr.f_locals["glob"] = stk[-1].globals
  ex = bunch(exType=exType, exValue=exValue, exTrace=tb, fr=fr, stk=stk)
  fr.f_locals["ex"] = ex
  fr.f_locals["stk"] = stk

  try:  # Must use try, If sys.ps1 attr was not set, it cause exception
    oldPS1 = sys.ps1
  except Exception as ex:
    oldPS1 = ">>> "
  sys.ps1 = "ex> "

  lcl = bunch()
  if len(stk)>0:
    lcl.update(stk[-1].globals)
    lcl.update(stk[-1].locals)
  #print("fr.f_locals: "+str(lcl.keys()))
  code.interact("Explore exception stk:", local=lcl)
  sys.ps1 = oldPS1
  print("(hndExcept returns)")


if __name__ == '__main__':  # Is ribou being loaded as the main executable?
  #import sys
  #print(rformat(sys.modules))
  #aa = rformat(sys.modules)
  #print(aa)
    
  try:
    #glob = globals()
    #loc = locals()
    code.interact("Try:", local=locals())
  except exex:
    hndExcept()

  #import uncompyle2
  #info(uncompyle2.uncompyle)
