"""

IntSeqMath.py by John Dorsey.

IntSeqMath.py contains tools for transforming integer sequences into other integer sequences.

"""

from collections import namedtuple

import PyGenTools


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


def _check_if_local_minimum(places):
  return places[0].value > places[1].value and places[2].value > places[1].value
  
def _check_if_local_maximum(places):
  return places[0].value < places[1].value and places[2].value < places[1].value
"""
def genLocalExtrema(inputNumSeq):
  for placeTriplet
"""
"""
def genLocalExtrema(
    inputNumSeq,
    includeSideTag=True, includeDirectionTag=True, includeRunLength=False, signRunLength=False, includeIndex=True, includeValue=True,
    includeLeftMin=True, includeRightMin=False, includeLeftMax=True, includeRightMax=False,
    includeLeftEnd=False, includeRightEnd=False):

  #if includeLeftEnd:
  #  raise NotImplementedError("includeLeftEnd=True not supported yet.")
  #if includeRightEnd:
  #  raise NotImplementedError("includeRightEnd=True not supported yet.")
    
  Place = namedtuple("Place", ["relativePosition", "index", "value"])
  
  trackedPlaceM0 = None
  trackedPlaceM1 = Place(None, None, None)
  trackedPlaceM2 = Place(None, None, None)
  
  leftSideTagItemToUse = ("left",) if includeSideTag else ()
  rightSideTagItemToUse = ("right",) if includeSideTag else ()
  
  
  def genOutputItemsFromPlaces(places, leftInclusionMode="analysis", rightInclusionMode="analysis"):
    assert len(places) == 3
    placeM0 = places[-1]
    placeM1 = places[-2]
    placeM2 = places[-3]
    #if len(places) >= 3:
    #  placeM2 = places[-3]
    assert placeM1 is not None
    assert placeM0 is not None
    if placeM2.value is not None:
      isLocalMinimum = checkIfLocalMinimum([placeM2, placeM1, placeM0])
      isLocalMaximum = checkIfLocalMaximum([placeM2, placeM1, placeM0])
    else:
      isLocalMinimum = checkIfLocalMinimum([placeM0, placeM1, placeM0])
      isLocalMaximum = checkIfLocalMaximum([placeM0, placeM1, placeM0])
    #
    #assert isLocalMinimum or isLocalMaximum
    basicDirectionTag = "minimum" if isLocalMinimum else "maximum" if isLocalMaximum else "unknown"
    #assert basicDirectionTag is not None
    directionTagItemToUse = ((basicDirectionTag,) if includeDirectionTag else ())
    #
    runLength = placeM0.index - placeM1.index
    leftRunLengthItemToUse = (runLength,) if includeRunLength else ()
    rightRunLengthItemToUse = ((-runLength,) if signRunLength else (runLength,)) if includeRunLength else ()
    valueItemToUse = ((placeM1.value,) if includeValue else ())
    #
    basicOutputTuple = directionTagItemToUse
    #
    if leftInclusionMode == "analysis":
      isLeftOutputable = includeLeftMin if isLocalMinimum else (includeLeftMax if isLocalMaximum else False)
    else:
      raise NotImplementedError()
    if rightInclusionMode == "analysis":
      #isRightOutputable = isLocalMinimum if includeRightMin else isLocalMaximim if includeRightMax else False
      isRightOutputable = includeRightMin if isLocalMinimum else (includeRightMax if isLocalMaximum else False)
    else:
      raise NotImplementedError()
    #
    leftOutputTupleEnd = ((placeM1.index,) if includeIndex else ()) + valueItemToUse
    leftOutputTuple = leftSideTagItemToUse + basicOutputTuple + leftRunLengthItemToUse + leftOutputTupleEnd
    if isLeftOutputable:
      yield leftOutputTuple
    else:
      print("Skipped outputting {} for places {}.".format(leftOutputTuple, places))
    rightOutputTupleEnd = ((placeM0.index-1,) if includeIndex else ()) + valueItemToUse
    rightOutputTuple = rightSideTagItemToUse + basicOutputTuple + rightRunLengthItemToUse + rightOutputTupleEnd
    if isRightOutputable:
      yield rightOutputTuple
    else:
      print("Skipped outputting {} for places {}.".format(rightOutputTuple, places))
    return
  LEFTMOST, MIDDLE, RIGHTMOST, ONLY = "leftmost", "middle", "rightmost", "only"
  placeGen = (Place(relativePosition, index, value) for relativePosition, index, value in PyGenTools.genTrackEnds(enumerate(inputNumSeq), leftTag=LEFTMOST, middleTag=MIDDLE, rightTag=RIGHTMOST, onlyTag=ONLY, tagByExpanding=True))
  arePlacesSimilar = (lambda testPlace0, testPlace1: testPlace0.relativePosition == testPlace1.relativePosition and testPlace0.value == testPlace1.value)
  uniquePlaceGen = PyGenTools.genRunless(placeGen, func=arePlacesSimilar)
  
  for trackedPlaces in PyGenTools.genRollingWindowsAsLists(uniquePlaceGen, n=3, defaultValue=Place(None, None, None), includePartialChunks=True):
  
    if trackedPlaces[-1].relativePosition == LEFTMOST:
      continue
  
    if trackedPlaces[-1].relativePosition == ONLY:
      raise NotImplementedError("the case of only one item is not handled yet.")
      
    if trackedPlaces[-1].relativePosition == RIGHTMOST:
      lastRunEndPlace = Place(trackedPlaces[-1].relativePosition, trackedPlaces[-1].index+1, trackedPlaces[-1].value)
      trackedPlaces[-1] = lastRunEndPlace
      #go on! nothing yielded for this branch.
      
    if trackedPlaces[-2].relativePosition == LEFTMOST and trackedPlaces[-1].relativePosition == RIGHTMOST:
      raise NotImplementedError("case: one run only.")
    
    if trackedPlaces[-2].relativePosition == LEFTMOST:
      if trackedPlaces[-1].relativePosition == MIDDLE:
        if includeLeftEnd:
          for outputItem in genOutputItemsFromPlaces(trackedPlaces):
            yield outputItem
      else:
        assert False
    elif trackedPlaces[-2].relativePosition == MIDDLE:
      if trackedPlaces[-1].relativePosition == RIGHTMOST:
        if includeRightEnd:
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
  
  assert False, trackedPlaces
"""    
        
      

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

