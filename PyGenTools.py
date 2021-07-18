"""

PyGenTools.py by John Dorsey.

PyGenTools.py contains tools that work on python generators without handling their items (comparing items, etc.).

"""

class ExhaustionError(Exception):
  """
  ExhaustionError is raised when a function that eats items from an input generator runs out of items in that generator, but did not have a strict target count of items to eat.
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





def genTakeOnly(inputGen,count,onExhaustion="partial"):
  #take ONLY _count_ items from a generator _inputGen_ and yield them, so that if other functions call .next on the generator that was shared with this function, they will pick up exactly where this function's output left off (no missing items).
  assert onExhaustion in ["partial","ExhaustionError","warn"]
  assert count >= 0
  if count == 0:
    return
  i = 0
  for item in inputGen:
    if i < count:
      yield item
      i += 1
    if not i < count:
      return
  if onExhaustion == "partial":
    return
  elif onExhaustion == "ExhaustionError":
    raise ExhaustionError("PyGenTools.genTakeOnly ran out of items, and its onExhaustion action is \"ExhaustionError\".")
  elif onExhaustion == "warn":
    print("PyGenTools.genTakeOnly: count argument was " + str(count) + ", but inputGen ran out after just " + str(i) + " items.")
  else:
    raise ValueError("PyGenTools.genTakeOnly: the value of keyword argument onExhaustion is invalid.")

def genSkipFirst(inputGen,count):
  assert isGen(inputGen)
  for i in range(count):
    forget = next(inputGen)
  return inputGen

def arrTakeOnly(inputGen,count,onExhaustion="partial"):
  #just like genTakeOnly, but bundle the taken items together into an array.
  assert onExhaustion in ["fail","warn+partial","partial","warn+None","None"]
  result = [item for item in genTakeOnly(inputGen,count)]
  if len(result) < count:
    if onExhaustion == "fail":
      raise ExhaustionError("PyGenTools.arrTakeOnly ran out of items, and its onExhaustion action is \"fail\".")
    elif "warn" in onExhaustion:
      print("PyGenTools.arrTakeOnly ran out of items, and will return only part of the requested array.")
    if "partial" in onExhaustion:
      return result
    elif "None" in onExhaustion:
      return None
    else:
      raise ValueError("PyGenTools.arrTakeOnly: the value of keyword argument onExhaustion is invalid.")
  return result


def arrTakeLast(inputGen,count):
  if type(inputGen) == list:
    print("PyGenTools.arrTakeLast was called on a list. It will treat the list like a generator. This might be a waste of time.")
  storage = [None for i in range(count)]
  i = -1
  for item in inputGen:
    i = (i+1)%count
    storage[i] = item
  return storage[i+1:]+storage[:i+1]

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
