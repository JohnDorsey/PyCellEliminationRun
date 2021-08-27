"""

PyGenTools.py by John Dorsey.

PyGenTools.py contains tools that work on python generators without handling their items (comparing items, etc.).

"""

import traceback
import itertools
from collections import deque


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
  
class SynchronicityViolation(Exception):
  """
  SynchronicityViolation is raised when some code expected to perform exactly one operation per execution step of the code around it performs a different number of operations.
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




def handleOnExhaustion(methodName, yieldedCount, targetCount, onExhaustion):
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

def genTakeOnly(inputGen, targetCount, onExhaustion="partial"):
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

def arrTakeOnly(inputGen, targetCount, onExhaustion="partial"):
  #just like genTakeOnly, but bundle the taken items together into an array.
  assert isinstance(onExhaustion,Exception) or onExhaustion in ["fail","ExhaustionError","warn+partial","partial"]
  result = [item for item in genTakeOnly(inputGen,targetCount)]
  if len(result) < targetCount:
    handleOnExhaustion("PyGenTools.arrTakeOnly", len(result), targetCount, onExhaustion)
  return result
  
  
def genSkipFirst(inputGen, count):
  assert isGen(inputGen)
  for i in range(count):
    _ = next(inputGen)
  return inputGen
  
def genTakeUntil(inputGen, stopFun, stopSignalsNeeded=1): #might be used in MarkovTools someday.
  stopSignalCount = 0
  for item in inputGen:
    yield item
    if stopFun(item):
      stopSignalCount += 1
      if stopSignalCount >= stopSignalsNeeded:
        return
  print("PyGenTools.genTakeUntil ran out of items.")
  

def arrTakeLast(inputGen, count):
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
  
def getLast(inputGen):
  if type(inputGen) == list:
    print("PyGenTools.getLast was called on a list. It will treat the list like a generator. This might be a pointless waste of time.")
  storage = None
  loopRan = False
  for item in inputGen:
    loopRan = True
    storage = item
  assert loopRan
  return storage
  
  
def indexOfValueInGen(testValue, testGen): #used in MarkovTools.
  for i,item in enumerate(testGen):
    if item == testValue:
      return i
  return None
  
def valueAtIndexInGen(inputIndex, inputGen): #used in MarkovTools.
  if inputIndex == None:
    raise ValueError("inputIndex can't be None.")
  return arrTakeLast(genTakeOnly(inputGen, inputIndex+1), 1)[0]

  

def sentinelize(inputSeq, sentinel=None, loopSentinel=False, failFun=None):
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

def genAddInt(inputSeq, inputInt): #used in CodecTools.Codec.
  for item in inputSeq:
    yield item+inputInt
    
def arrAddInt(inputArr, inputInt): #used in CodecTools.Codec.
  assert type(inputArr) == list
  return [item+inputInt for item in inputArr] 


def genDeduped(inputSeq):
  if isGen(inputSeq) or type(inputSeq) == list:
    history = set()
    for item in inputSeq:
      if item not in history:
        history.add(item)
        yield item
    #this version uses less memory but isn't as fast. if re-enabling, change first branch's condition.
    """
    elif type(inputSeq) == list:
      for i,item in enumerate(inputSeq):
        if i == 0:
          yield item
          continue
        if item not in inputSeq[:i]:
          yield item
    """
  else:
    raise ValueError("unsupported type: " + str(type(inputSeq)) + ".")

"""
def getAccumulatorFun(thing):
  if type(thing) == str:
    result = eval("(lambda x,y: x{}y)".format(thing))
  elif type(thing) == type((lambda x: x)):
    result = thing
  else:
    raise TypeError("must be string or function.")
  return result
"""


def accumulate(inputSeq, inputFun):
  inputSeq = makeGen(inputSeq)
  #inputFun = getAccumulatorFun(inputFun) #not used anymore now that itertools.accumulate is sometimes used.
  result = next(inputSeq)
  for item in inputSeq:
    result = inputFun(result, item)
  return result
  
    
def product(inputSeq):
  return accumulate(inputSeq, (lambda x,y:x*y))


def genChunksAsLists(inputGen, n=2, partialChunkHandling="warn partial"):
  inputGen = makeGen(inputGen)
  while True:
    chunkAsList = arrTakeOnly(inputGen, n, onExhaustion="partial") #make list.
    if len(chunkAsList) < n:
      if "warn" in partialChunkHandling:
        print("PyGenTools.genChunksAsLists: warning: partial chunk.")
      if "fail" in partialChunkHandling:
        raise IterationFailure("partial chunk.")
      if not "partial" in partialChunkHandling:
        if "discard" in partialChunkHandling:
          return
        else:
          print("PyGenTools.genChunksAsLists: warning: partial chunk encountered, but the partialChunkHandling kwarg does not indicate what should be done (no \"partial\" and no \"discard\"). The chunk will be yielded.")

    if len(chunkAsList) == 0:
      return
    yield chunkAsList
  
  
def genRollingWindowsAsLists(inputGen, n=3, step=1, defaultValue=None, includePartialChunks=True, includeEmptyChunks=False): # @ could be faster by using an index wrapping list.
  if step != 1:
    raise NotImplementedError("step != 1")
  if includeEmptyChunks and not includePartialChunks:
    raise ValueError("can't include empty chunks without including partial chunks.")
    
  currentWindowDeque = deque([defaultValue for i in range(n)])
  registeredCount = 0
  def register(itemToRegister):
    currentWindowDeque.append(itemToRegister)
    currentWindowDeque.popleft()
    
  if includeEmptyChunks:
    yield list(currentWindowDeque)
    
  for index, item in enumerate(inputGen):
    register(item)
    registeredCount += 1
    if registeredCount%step != 0:
      continue
    if (index+1 >= n) or includePartialChunks:
      yield list(currentWindowDeque)
  if includePartialChunks:
    for i in range(n-1):
      register(defaultValue)
      registeredCount += 1
      if registeredCount%step != 0:
        continue
      yield list(currentWindowDeque)
      
  if includeEmptyChunks:
    yield list(currentWindowDeque)
      

def allAreEqual(inputSeq):
  inputSeq = makeGen(inputSeq)
  sharedValue = next(inputSeq)
  for item in inputSeq:
    if item != sharedValue:
      return False
  return True
  
  
def seqsAreEqual(*args):
  return all(allAreEqual(item) for item in itertools.izip_longest(*args))
  
  
def countIn(inputSeq, testValue, includeDenominator=False):
  return countTriggers(inputSeq,(lambda x: x==testValue),includeDenominator=includeDenominator)
  
  
def countTriggers(inputSeq, triggerFun, includeDenominator=False):
  count, denominator = 0, 0
  for item in inputSeq:
    count, denominator = count+triggerFun(item), denominator+1
  return (count, denominator) if includeDenominator else count


def genRunless(inputSeq, func=(lambda compA, compB: compA == compB)):
  #this generator takes an input sequence and yields only the items that aren't the same as the previous item.
  #this generator eats only as much as it yields.
  previousItem = None
  justStarted = True
  for item in inputSeq:
    if justStarted:
      justStarted = False
      previousItem = item
      yield item
    else:
      if not func(item, previousItem):
        previousItem = item
        yield item



#not tested well.
def genTrackEnds(
    inputSeq,
    leftTag="left", middleTag="middle", rightTag="right", onlyTag="only",
    useLookahead=True,
    tagByExpanding=False,
    supressOvereatingWarning=False):
    
  if iter(inputSeq) is iter(inputSeq):
    if useLookahead:
      if not supressOvereatingWarning:
        print("PyGenTools.genTrackEnds: over-eating warning: this function may take more items from inputSeq than it yields with the current args.")
  
  if tagByExpanding:
    def toTagged(workingItem, tagToApply):
      return (type(workingItem))((tagToApply,)) + workingItem
  else:
    def toTagged(workingItem, tagToApply):
      return (tagToApply, workingItem)
  
  inputGen = makeGen(inputSeq)
  
  if useLookahead:
    previousItem = None
    index = None
    for index,currentItem in enumerate(inputGen):
      #assert currentItem is not None, "can't handle Nones in inputSeq yet."
      if index == 0:
        previousItem = currentItem
      elif index == 1:
        yield toTagged(previousItem, leftTag)
      else:
        yield toTagged(previousItem, middleTag)
        previousItem = currentItem
        
    if index is None:
      return
    elif index == 0:
      yield toTagged(currentItem, onlyTag)
    else:
      yield toTagged(currentItem, rightTag)
  else:
    for index,currentItem in enumerate(inputGen):
      if index == 0:
        yield toTagged(currentItem, leftTag)
      else:
        yield toTagged(currentItem, middleTag)

  

def enumerateFlatly(inputSeq, start=0):
  commonLength = None
  isProbablyTupleSeq = None
  isProbablyListSeq = None
  for index,value in enumerate(inputSeq, start=start):
    assert value != None, "can't."
    if commonLength is None:
      isProbablyTupleSeq = isinstance(value, tuple)
      isProbablyListSeq = isinstance(value, list)
      if isTupleSeq or isListSeq:
        commonLength = len(value)
      isExpandableSeq = isProbablyTupleSeq or isProbablyListSeq
      if not isExpandableSeq:
        print("PyGenTools.enumerateFlatly: warning: this input sequence isn't of items that can be expanded to include enumeration (the first item is of type {}). New tuples will be created for each item... This is just like builtin enumerate, but with overhead.".format(repr(type(value))))
    if isExpandableSeq:
      if isinstance(value, tuple):
        assert len(value) == commonLength
        yield (index,) + value
      elif isinstance(value, list):
        assert len(value) == commonLength
        yield [index,] + value
      else:
        assert False
    else:
      yield (index, value)
        
  

def genMonitored(inputSeq, text=""):
  inputGen = makeGen(inputSeq)
  i = 0
  while True:
    try:
      item = next(inputGen)
      print("PyGenTools.genMonitored: " + text + " i={}, item={}.".format(i, item))
      yield item
      i += 1
    except StopIteration as se:
      print("PyGenTools.genMonitored: " + text + " i={}, {}".format(i, repr(se)))
      raise se
  assert False, "Unreachable statement."
  
  
class GenBypass:
  def __init__(self, useHistory=False):
    #print("GenBypass init.")
    self.inputGens = None
    self.lastOutputs = None
    self.modifiedInputGens = None
    self.useHistory = useHistory
    if self.useHistory:
      self.history = deque()
    
  def _create_callback_method(self, indexToWriteTo):
    def callbackMethod(value):
      #print("callback method: value {} into index {}.".format(value, indexToWriteTo))
      if self.latestOutputs[indexToWriteTo] is not None:
        raise SynchronicityViolation("multiple writes to output tracker for generator at index {}.".format(indexToWriteTo))
      self.latestOutputs[indexToWriteTo] = value
      if self.useHistory:
        assert value is not None, "this breaks things."
        if self.latestOutputs.count(None) == 0:
          self._handle_full_outputs()
      #print("self.lastOutputs is now {}.".format(self.lastOutputs))
    return callbackMethod
    
  def _gen_modify(self, genToModify, callbackMethod):
    #print("_gen_modify called on {} with callbackMethod {}.".format(genToModify, callbackMethod))
    for item in genToModify:
      callbackMethod(item)
      yield item
      
  def _handle_full_outputs(self):
    self.history.append([item for item in self.latestOutputs])
    for i in range(len(self.latestOutputs)):
      self.latestOutputs[i] = None
      
  def intercept(self, *inputGens):
    self.capture(inputGens)
    return self.share()
      
  def capture(self, *inputGens):
    genCount = len(inputGens)
    self.inputGens = [item for item in inputGens]
    self.latestOutputs = [None for i in range(genCount)]
    self.callbackMethods = [self._create_callback_method(i) for i in range(genCount)]
    self.modifiedInputGens = [self._gen_modify(genToModify, self.callbackMethods[i]) for i,genToModify in enumerate(self.inputGens)]
      
  def share(self):
    assert len(self.modifiedInputGens) != 0
    return self.modifiedInputGens
  
  def wrap(self, inputGen):
    #"unspecified_at_{}".format(i)
    #result = [None for i in range(len(self.lastOutputs)+1)]
    isLastRun = False
    if self.useHistory:
      sentinel = object() #get unique sentinel. only compare using is.
      for inputGenItem in sentinelize(inputGen, sentinel=sentinel):
        assert self.latestOutputs == [None for i in range(len(self.latestOutputs))]
        while len(self.history) > 1:
          yield [item for item in self.history.popleft()] + [None]
        if inputGenItem is sentinel:
          isLastRun = True
          inputGenItem = None #don't yield sentinel.
          if not len(self.history) >= 1:
            return #don't try.
        yield [item for item in self.history.popleft()] + [inputGenItem]
        if isLastRun:
          return #history dumped after last item, nothing left to do.
    else:
      yield [item for item in self.latestOutputs] + [inputGenItem]
      for i in range(len(self.latestOutputs)):
        self.latestOutputs[i] = None
      #assert i != 0
      #assert self.lastOutputs.count(None) == len(self.lastOutputs)
    
  

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
