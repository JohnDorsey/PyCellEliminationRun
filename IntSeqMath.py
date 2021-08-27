"""

IntSeqMath.py by John Dorsey.

IntSeqMath.py contains tools for transforming integer sequences into other integer sequences.

"""

from collections import namedtuple

import PyGenTools
from PyGenTools import genSkipFirst


def genDelayFirstTupleItem(inputSeq,startValue): #used by genTrackDelayedSum.
  previousA = startValue
  a = None
  b = None
  for item in inputSeq:
    a, b = item
    yield (previousA, b)
    previousA = a

def genTrackInstantMean(inputNumSeq):
  currentSum = 0
  for i,item in enumerate(inputNumSeq):
    currentSum += item
    yield (currentSum/float(i+1),item)

def genTrackInstantMin(inputNumSeq):
  currentMin = None
  for i,item in enumerate(inputNumSeq):
    if i == 0:
      currentMin = item
    else:
      currentMin = min(currentMin,item)
    yield (currentMin,item)

def genTrackInstantSum(inputNumSeq):
  currentSum = 0
  for item in inputNumSeq:
    currentSum += item
    yield (currentSum,item)

def genTrackDelayedSum(inputNumSeq):
  return genDelayFirstTupleItem(genTrackInstantSum(inputNumSeq),0)


def genDeltaEncode(inputNumSeq):
  previousItem = 0
  for item in inputNumSeq:
    yield item - previousItem
    previousItem = item

def genDeltaDecode(inputNumSeq):
  previousItem = 0
  for item in inputNumSeq:
    yield item + previousItem
    previousItem += item




def genRecordLows(inputNumSeq):
  recordLow = None
  justStarted = True
  for item in inputNumSeq:
    if justStarted:
      recordLow = item
      yield item
      justStarted = False
      continue
    if item < recordLow:
      recordLow = item
      yield item


def genTrackLocalExtrema(inputNumSeq, **kwargs):
  gb = PyGenTools.GenBypass(useHistory=True)
  gb.capture(inputNumSeq)
  gbWrapped = gb.wrap(genLocalExtrema(*gb.share(), **kwargs))
  for actualIndex, gbPair in enumerate(gbWrapped):
    inputNum, outputPair = gbPair
    if outputPair is not None:
      raise NotImplementedError()
  raise NotImplementedError()
    
  #gbTupled = (tuple(item) for item in gbWrapped)
  #return gbTupled
  #raise NotImplementedError()
  #return genSkipFirst(genDelayFirstTupleItem(gbTupled, None), 1)
  
  
  

def genLocalExtrema(
    inputNumSeq,
    includeDirection=True,
    includeIndex=True, includeValue=True,
  ):
    
  def _check_if_local_minimum(places):
    return places[0].value > places[1].value and places[2].value > places[1].value
    
  def _check_if_local_maximum(places):
    return places[0].value < places[1].value and places[2].value < places[1].value
    
  Place = namedtuple("Place", ["relativePosition", "index", "value"])
  
  LEFTMOST, MIDDLE, RIGHTMOST, ONLY = "leftmost", "middle", "rightmost", "only"
  
  
  placeGen = (Place(relativePosition, index, value) for relativePosition, index, value in PyGenTools.genTrackEnds(enumerate(inputNumSeq), leftTag=LEFTMOST, middleTag=MIDDLE, rightTag=RIGHTMOST, onlyTag=ONLY, useLookahead=False, tagByExpanding=True)) #to transition to more advanced version, REMEMBER TO ALLOW LOOKAHEAD AGAIN.
  
  arePlacesSimilar = (lambda testPlace0, testPlace1: testPlace0.relativePosition == testPlace1.relativePosition and testPlace0.value == testPlace1.value)

  uniquePlaceGen = PyGenTools.genRunless(placeGen, func=arePlacesSimilar)
  
  arePlaceValuesSimilar = (lambda testPlace0, testPlace1: testPlace0.value == testPlace1.value)
  uniquePlaceGenByValuesOnly = PyGenTools.genRunless(placeGen, func=arePlaceValuesSimilar) #don't include ends!
  
  def optTuplePart(part, shouldExist):
    return (part,) if shouldExist else ()
  def completePlaces(places):
    assert len(places) == 3
    for i in range(len(places)):
      if places[i] is None:
        places[i] = Place(None, None, None)
    if places[0].value == None:
      places[0] = places[2]
    if places[2].value == None:
      places[2] = places[0]
    assert places[0].value is not None, places
    assert places[2].value is not None, places
  def getExtremeDirection(places):
    assert len(places) == 3
    completePlaces(places)
    isMin = _check_if_local_minimum(places)
    isMax = _check_if_local_maximum(places)
    if isMin:
      return "minimum"
    if isMax:
      return "maximum"
    return False
  def genOutputItemsFromPlaces(places):
    extremeDirection = getExtremeDirection(places)
    if not extremeDirection:
      return
    result = optTuplePart(extremeDirection, includeDirection) + optTuplePart(places[-2].index, includeIndex) + optTuplePart(places[-2].value, includeValue)
    if result[-2:] == (None, None):
      return
    yield result
    return
    
  placeGenToUse = uniquePlaceGenByValuesOnly
  
  for trackedPlaces in PyGenTools.genRollingWindowsAsLists(placeGenToUse, n=3, defaultValue=None, includePartialChunks=True):
    """
    if trackedPlaces[-1].relativePosition == LEFTMOST:
      continue
    if trackedPlaces[-1].relativePosition == ONLY:
      raise NotImplementedError("the case of only one item is not handled yet.")
      
    if trackedPlaces[-1].relativePosition == RIGHTMOST:
      placeAfterLastRun = Place(trackedPlaces[-1].relativePosition, trackedPlaces[-1].index+1, trackedPlaces[-1].value)
      trackedPlaces[-1] = placeAfterLastRun
      #go on! nothing yielded for this branch.
    
      
    if trackedPlaces[-2].relativePosition == LEFTMOST and trackedPlaces[-1].relativePosition == RIGHTMOST:
      raise NotImplementedError("case: one run only.")
    
    if trackedPlaces[-2].relativePosition == LEFTMOST:
      if trackedPlaces[-1].relativePosition == MIDDLE:
        if False and includeLeftEnd:
          for outputItem in genOutputItemsFromPlaces(trackedPlaces):
            yield outputItem
      else:
        assert False
    elif trackedPlaces[-2].relativePosition == MIDDLE:
      if trackedPlaces[-1].relativePosition == RIGHTMOST:
        if False and includeRightEnd:
          for outputItem in genOutputItemsFromPlaces(trackedPlaces):
            yield outputItem
        return
      elif trackedPlaces[-1].relativePosition == MIDDLE:
        for outputItem in genOutputItemsFromPlaces(trackedPlaces):
          yield outputItem
      else:
        assert False, trackedPlaces
    else:
      assert False, trackedPlaces
    """
    if trackedPlaces[-2] is None:
      continue
    if trackedPlaces.count(None) == 2:
      continue
    for outputItem in genOutputItemsFromPlaces(trackedPlaces):
      yield outputItem
  
        
      

"""
def findBasicColumnInfo(inputSeq,delimiter):
  #in tattered data (lines of different lengths), for each index counting from the left, collect info on all values that exist at that index.
  i = 0
  columnMinimums = []
  columnMaximums = []
  columnSizes = []
  columnSums = []
  columnProducts = []
  for item in inputSeq:
    if item == delimiter:
      i = 0
      continue
    if i == len(columnMinimums):
      columnMinimums.append(item)
      assert i == len(columnMaximums)
      columnMaximums.append(item)
      assert i == len(columnSizes)
      columnSizes.append(1)
      assert i == len(columnSums)
      columnSums.append(item)
      assert i == len(columnProducts)
      columnProducts.append(item)
    else:
      columnMinimums[i] = min(columnMinimums[i],item)
      columnMaximums[i] = max(columnMaximums[i],item)
      columnSizes[i] += 1
      columnSums[i] += item
      columnProducts[i] *= item
    i += 1
  return {"columnMinimums":columnMinimums, "columnMaximums":columnMaximums, "columnSizes":columnSizes, "columnSums":columnSums, "columnProducts":columnProducts}
"""
def columnSetStatReporterFun(i,item,report):
  if report == None:
    return {"size":1,"min":item,"max":item,"sum":item,"product":item}
  else:
    return {"size":report["size"]+1,"min":min(item,report["min"]),"max":max(item,report["max"]),"sum":report["sum"]+item,"product":report["product"]*item}

def findColumnInfo(inputSeq,delimiter,reporterFun):
  #in tattered data (lines of different lengths), for each index counting from the left, collect info on all values that exist at that index.
  i = 0
  columnReports = []
  for item in inputSeq:
    if item == delimiter:
      i = 0
      continue
    if i == len(columnReports):
      columnReports.append(reporterFun(i,item,None))
    else:
      columnReports[i] = reporterFun(i,item,columnReports[i])
    i += 1
  return columnReports

def applyColumnAwareFun(inputSeq,transformerFun,columnInfoArr=None):
  i = 0
  for item in inputSeq:
    if type(columnInfoArr) == list:
      modifiedItem = transformerFun(i,item,columnInfoArr[i])
    else:
      modifiedItem = transformerFun(i,item)
    reset = yield modifiedItem
    if reset:
      i = 0
      continue



assert findColumnInfo([1,5,0,6,2,4,7,0,8,8,8,8,8,8,8,8,0,999],0,(lambda i,x,r: min(x,r) if r!=None else x)) == [1,2,4,7,8,8,8,8]



assert [item for item in genDeltaDecode(genDeltaEncode([5,5,6,5,3,0,10,0]))] == [5,5,6,5,3,0,10,0]

