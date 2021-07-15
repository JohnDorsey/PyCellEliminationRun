"""

PyGenTools.py by John Dorsey.

PyGenTools.py contains tools that work on python generators without handling their items (comparing items, etc.).

"""

class ExhaustionError(Exception):
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



def genTakeOnly(inputGen,count):
  #take ONLY _count_ items from a generator _inputGen_ and yield them, so that if other functions call .next on the generator that was shared with this function, they will pick up exactly where this function's output left off (no missing items).
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


def zipGens(inputGens):
  #This function gives a generator whose items are taken one at a time from each generator provided in a circular order. It runs until all the provided generators are empty. Technically, it can be given arrays instead of generators and it will correct for this. The array of generators may also be a generator instead of an array.
  gensRunning = [True for i in range(len(inputGens))] #this map prevents needing to catch the same StopIteration many times for each generator that stops sooner than the last one to stop.
  workingGenArr = [makeGen(item) for item in inputGens] #in case the inputGens contains things that aren't generators _or_ inputGens itself is a generator, this fixes that.
  while not all(not genIsRunning for genIsRunning in gensRunning):
    for genIndex in range(len(workingGenArr)):
      if gensRunning[genIndex]:
        try:
          yield next(workingGenArr[genIndex])
        except StopIteration:
          gensRunning[genIndex] = False #don't check this generator for items again.






#tests:

assert len([item for item in genTakeOnly(range(256),10)]) == 10
assert arrTakeOnly(range(10),5) == [0,1,2,3,4]
assert arrTakeOnly(range(5),10) == [0,1,2,3,4]

assert "".join(zipGens(["hello","123456789","ABC"])) == "h1Ae2Bl3Cl4o56789"
