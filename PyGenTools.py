"""

PyGenTools.py by John Dorsey.

PyGenTools.py contains tools that work on python generators without handling their items (comparing items, etc.).

"""

import traceback


class ExhaustionError(Exception):
  """
  ExhaustionError is raised when a function that eats items from an input generator runs out of items in that generator, but did not have a strict target count of items to eat.
  """
  pass
  
class IterationFailure(Exception):
  """
  IterationFailure is raised when an iterable runs out of items, in a situation where it never should have run out of items.
  """
  pass


def isGen(thing):
  #test whether something is a generator. Compatible with python2 and python3.
  return type(thing) == type((i for i in range(1)))

def makeGen(thing):
  #make anything iterable into a generator. This is useful for when certain functions are supposed to take only as many items as they need from the beginning of some data and leave the rest in a way that further iteration will begin where the first function stopped iterating, such as in parsing universal codes in Codes.py.
  if isGen(thing):
    return thing
  return (item for item in thing)

def makeArr(thing):
  if type(thing) == list:
    return thing
  try:
    result = [item for item in thing]
  except KeyboardInterrupt:
    raise KeyboardInterrupt("PyGenTools.makeArr was stuck on " + str(thing) + ".")
  return result




def handleOnExhaustion(methodName,yieldedCount,targetCount,onExhaustion):
  if isinstance(onExhaustion,Exception):
    raise onExhaustion
  elif onExhaustion == "fail":
    raise IterationFailure(methodName + " ran out of items, and its onExhaustion action is \"fail\".")
  if onExhaustion == "ExhaustionError":
    raise ExhaustionError(methodName + " ran out of items, and its onExhaustion action is \"ExhaustionError\".")
  if "warn" in onExhaustion:
    print("...\n" + "".join(traceback.format_list(traceback.extract_stack())) + ": " + methodName + " ran out of items. (yieldedCount,targetCount,onExhaustion)=" + str((yieldedCount, targetCount, onExhaustion)) + ".")
  if "partial" in onExhaustion:
    return
  if "None" in onExhaustion:
    raise ValueError(methodName + ": the onExhaustion action \"None\" is no longer supported.")
  raise ValueError(methodName + ": the value of onExhaustion is invalid. (yieldedCount,targetCount,onExhaustion)=" + str((yieldedCount, targetCount, onExhaustion)) + ".")

def genTakeOnly(inputGen,targetCount,onExhaustion="partial"):
  #take ONLY _count_ items from a generator _inputGen_ and yield them, so that if other functions call .next on the generator that was shared with this function, they will pick up exactly where this function's output left off (no missing items).
  assert onExhaustion in ["fail","ExhaustionError","partial","warn"]
  assert targetCount >= 0
  if targetCount == 0:
    return
  i = 0
  for item in inputGen:
    if i < targetCount:
      yield item
      i += 1
    if not i < targetCount:
      return
  handleOnExhaustion("PyGenTools.genTakeOnly", i, targetCount, onExhaustion)

def arrTakeOnly(inputGen,targetCount,onExhaustion="partial"):
  #just like genTakeOnly, but bundle the taken items together into an array.
  assert isinstance(onExhaustion,Exception) or onExhaustion in ["fail","ExhaustionError","warn+partial","partial"]
  result = [item for item in genTakeOnly(inputGen,targetCount)]
  if len(result) < targetCount:
    handleOnExhaustion("PyGenTools.arrTakeOnly", len(result), targetCount, onExhaustion)
  return result
  
  
def genSkipFirst(inputGen,count):
  assert isGen(inputGen)
  for i in range(count):
    forget = next(inputGen)
  return inputGen
  
def genTakeUntil(inputGen,stopFun,stopSignalsNeeded=1): #might be used in MarkovTools someday.
  stopSignalCount = 0
  for item in inputGen:
    yield item
    if stopFun(item):
      stopSignalCount += 1
      if stopSignalCount >= stopSignalsNeeded:
        return
  print("PyGenTools.genTakeUntil ran out of items.")
  

def arrTakeLast(inputGen,count):
  if count == None:
    raise ValueError("count can't be None.")
  if type(inputGen) == list:
    print("PyGenTools.arrTakeLast was called on a list. It will treat the list like a generator. This might be a waste of time.")
  storage = [None for ii in range(count)]
  i = -1
  for item in inputGen:
    i = (i+1)%count
    storage[i] = item
  splitPoint = i+1
  return storage[splitPoint:]+storage[:splitPoint]
  
  
def indexOfValueInGen(testValue,testGen): #used in MarkovTools.
  for i,item in enumerate(testGen):
    if item == testValue:
      return i
  return None
  
def valueAtIndexInGen(inputIndex,inputGen): #used in MarkovTools.
  if inputIndex == None:
    raise ValueError("inputIndex can't be None.")
  return arrTakeLast(genTakeOnly(inputGen,inputIndex+1),1)[0]
  

def sentinelize(inputSeq,sentinel=None,loopSentinel=False,failFun=None):
  """
  Signals the end of a generator by yielding an additional item after its end. Note that sentinelize(x) makes a generator from any type of input, so combining it with makeGen is redundant.
  """
  for item in inputSeq:
    yield item
  yield sentinel
  while loopSentinel:
    yield loopSentinel
  if failFun:
    failFun()


def zipGens(inputGens):
  """
  This function gives a generator whose items are taken one at a time from each generator provided in a circular order. It runs until all the provided generators are empty. Technically, it can be given arrays instead of generators and it will correct for this. The array of generators may also be a generator instead of an array.
  """
  gensRunning = [True for i in range(len(inputGens))] #this map prevents needing to catch the same StopIteration many times for each generator that stops sooner than the last one to stop.
  workingGenArr = [makeGen(item) for item in inputGens] #in case the inputGens contains things that aren't generators _or_ inputGens itself is a generator, this fixes that.
  while not all(not genIsRunning for genIsRunning in gensRunning):
    for genIndex in range(len(workingGenArr)):
      if gensRunning[genIndex]:
        try:
          yield next(workingGenArr[genIndex])
        except StopIteration:
          gensRunning[genIndex] = False #don't check this generator for items again.

def genAddInt(inputSeq,inputInt): #used in CodecTools.Codec.
  for item in inputSeq:
    yield item+inputInt
    
def arrAddInt(inputArr,inputInt): #used in CodecTools.Codec.
  assert type(inputArr) == list
  return [item+inputInt for item in inputArr] 

def genFilter(inputSeq,filterFun): #might be added to Testing.PressNumsAnalysis.
  for item in inputSeq:
    if filterFun(item):
      yield item

def genDeduped(inputSeq):
  if isGen(inputSeq):
    history = []
    for item in inputSeq:
      if item not in history:
        history.append(item)
        yield item
  elif type(inputSeq) == list:
    for i,item in enumerate(inputSeq):
      if i == 0:
        yield item
        continue
      if item not in inputSeq[:i]:
        yield item
  else:
    raise ValueError("unsupported type: " + str(type(inputSeq)) + ".")



class CC:
  """
  CC stands for ConverterClass.
  An instance of CC can convert an iterable object to a python list by right multiplication (<iterable> * <CC instance> is equivalent to PyGenTools.makeArr(<iterable>)) or convert a list (or other iterable object) to a generator by right division (<iterable> / <CC instance> is equivalent to PyGenTools.makeGen(<iterable>)).
  """
  def __init__(self,*args):
    self.count = None
    if len(args) > 0:
      self.count = args[0]
      if not self.count > 0:
        raise ValueError("Zero or negative CC counts are not allowed.")
    print("PyGenTools.ConverterClass.__init__: initialized with " + ("count " + str(self.count) if self.count != None else "indefinite count") + ".")
  def __rmul__(self,other):
    if self.count != None:
      return arrTakeOnly(other,self.count)
    else:
      return makeArr(other)
  def __rdiv__(self,other):
    if self.count != None:
      return genTakeOnly(other,self.count)
    else:
      return makeGen(other)
  def __rtruediv__(self,other):
    #python3 compatibility.
    return self.__rdiv__(other)

cc = CC()




#tests:

assert len([item for item in genTakeOnly(range(256),10)]) == 10
assert arrTakeOnly(range(10),5) == [0,1,2,3,4]
assert arrTakeOnly(range(5),10) == [0,1,2,3,4]

assert "".join(zipGens(["hello","123456789","ABC"])) == "h1Ae2Bl3Cl4o56789"

assert range(10) * cc == [0,1,2,3,4,5,6,7,8,9]
assert isGen([0,1,2,3,4] / cc)
