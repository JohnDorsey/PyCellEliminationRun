"""

PyGenTools.py by John Dorsey.

PyGenTools.py contains tools that work on python generators without handling their items (comparing items, etc.).

"""



def isGen(thing):
  return type(thing) == type((i for i in range(1)))

def makeGen(thing):
  if isGen(thing):
    return thing
  return (item for item in thing)

def makeArr(thing):
  if type(thing) == list:
    return thing
  return [item for item in thing]



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

def arrTakeOnly(inputGen,count):
  return [item for item in genTakeOnly(inputGen,count)]


def zipGens(inputGenArr):
  gensRunning = [True for i in range(len(inputGenArr))] #this map prevents needing to catch the same StopIteration many times for each generator that stops sooner than the last one to stop.
  workingGenArr = [makeGen(item) for item in inputGenArr] #in case the inputGenArr contains things that aren't generators.
  while not all(not genIsRunning for genIsRunning in gensRunning):
    for genIndex in range(len(workingGenArr)):
      if gensRunning[genIndex]:
        try:
          yield workingGenArr[genIndex].next()
        except StopIteration:
          gensRunning[genIndex] = False








assert len([item for item in genTakeOnly(range(256),10)]) == 10
assert arrTakeOnly(range(10),5) == [0,1,2,3,4]
assert arrTakeOnly(range(5),10) == [0,1,2,3,4]
