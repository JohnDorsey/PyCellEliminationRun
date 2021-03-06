"""

MarkovTools.py by John Dorsey.

MarkovTools.py contains tools for transforming sequences using markov models.

"""

import itertools

from PyGenTools import genTakeOnly, arrTakeOnly, makeGen, genDeduped, ExhaustionError, indexOfValueInGen, valueAtIndexInGen, genSkipFirst
from PyArrTools import insort
from HistTools import OrderlyHist
import HuffmanMath
import CodecTools
from CodecTools import remapToValueArrCodec, remapToValueArrTranscode
import Codes


def getStartingIndicesOfSubSequence(inputArr,subSequence):
  #search an entire input array and output a list of all indices where matches with a specified subSequence start.
  #the output could be streamable.
  #this method could be much faster. The faster version _is_ MarkovTools.getEndingIndicesOfGrowingSubSequences.
  assert len(subSequence) > 0
  result = []
  for i in range(len(inputArr)-len(subSequence)+1):
    if inputArr[i:i+len(subSequence)] == subSequence:
      result.append(i)
  return result


def getEndingIndicesOfGrowingSubSequences(inputArr, searchTerm, keepOnlyLongest=True):
  #search an entire input array, and output all ending indices of matches with any portion of searchTerm which ends at the end of searchTerm. So searching for [2,3,4,5] is the same as searching for [5], and then searching among those matches for places that also match [4,5], and so on. The time complexity is O(total number of matches). This makes it superior to using getStartingIndicesOfSubSequence repeatedly.
  #the keepOnlyLongest option is useful for avoiding double-counting. With it enabled, a search for "34567" in "1234567" finds only one match of length 5 instead of one match for each length in [1,2,3,4,5].
  #the output of this could be made streamable. But there is little use - most of the ways it is used require reversing the order of the items of its output.
  if len(searchTerm) == 0:
    return [(0,[])]
  result = [(0,[]),(1,[])]
  
  for location in range(len(inputArr)): #populate list of matches with LENGTH OF ONE!
    if inputArr[location] == searchTerm[-1]:
      result[-1][1].append(location)
      
  for currentLength in range(2,len(searchTerm)+1):
    result.append((currentLength,[]))
    i = 0
    while i < len(result[-2][1]):
      location = result[-2][1][i]
      if location+1-currentLength < 0: #This test prevents wrapping around to the other end of the inputArr and general chaos. Without this test, the method finds nonexistant matches.
        i += 1
        continue
      if searchTerm[-currentLength] == inputArr[location+1-currentLength]:
        result[-1][1].append(location)
        if keepOnlyLongest:
          del result[-2][1][i]
          continue #skip incrementing i, because the items have shifted.
      i += 1
    #this is probably slower:
    """
    if keepOnlyLongest:
      ii = 0
      while ii < len(result[-2][1]):
        if result[-2][1][ii] in result[-1][1]:
          assert False, "this loop should have nothing to do!"
          del result[-2][1][ii]
        else:
          ii += 1
    """
    if len(result[-1][1]) == 0:
      break
  return result

def getEndingIndicesOfShrinkingSubSequences(inputArr, searchTerm, keepOnlyLongest=True):
  return getEndingIndicesOfGrowingSubSequences(inputArr, searchTerm, keepOnlyLongest=keepOnlyLongest)[::-1]



def ordify(inputStr):
  return [ord(char) for char in inputStr]


def genBleedSortedArr(inputArr,noNegatives=False):
  #this generator will help in using a markov model with values the model has not seen before, by mapping them to smaller numbers when they are closer to a value that has been seen before.
  return genBleedSortedArrWithoutSearches(inputArr,noNegatives=noNegatives)


def validateSeedArrNoNegatives(seedArr, noNegatives):
  if noNegatives:
    if seedArr[0] < 0:
      raise ValueError("called with noNegatives=True and an seedArr starting with a negative value.")

def genBleedSortedArrWithSearches(inputArr,noNegatives=False):
  """
  This is the original version of genBleedSortedArr. It involves lots of list searches. A much faster version involving no list searches exists and should usually be used instead.
  """
  validateSeedArrNoNegatives(inputArr, noNegatives)
  for item in inputArr:
    yield item
  lowerSpots = [item for item in inputArr] #these move down.
  upperSpots = [item for item in inputArr] #these move up.
  collisionSpots = None #these only appear when a lowerSpot and an upperSpot collide, and this list exists to make it easier to track where it happened but then delete it at the end of a sweep of all spots in order.
  while True:
    collisionSpots = []
    #print("inputArr-based dedupe phase...")
    #print("lowerSpots start as " + str(lowerSpots))
    i = 0
    while i < len(lowerSpots):
      while lowerSpots[i]-1 in inputArr:
        #print("deleting from lowerSpots at " + str(i))
        del lowerSpots[i]
        if i >= len(lowerSpots):
          #print("breaking delete loop.")
          break
      if i >= len(lowerSpots):
        break
      lowerSpots[i] -= 1
      i += 1
    #print("lowerSpots end up as " + str(lowerSpots))
    #print("upperSpots start as " + str(upperSpots))
    i = 0
    while i < len(upperSpots):
      while upperSpots[i]+1 in inputArr:
        #print("deleting from upperSpots at " + str(i))
        del upperSpots[i]
        if i >= len(lowerSpots):
          #print("breaking delete loop.")
          break
      if i >= len(upperSpots):
        break
      upperSpots[i] += 1
      i += 1
    #print("upperSpots end up as " + str(upperSpots))
    #print("cleanup phase...")
    #print("lowerSpots start as " + str(lowerSpots))
    #print("upperSpots start as " + str(upperSpots))
    i = 0
    while i < len(lowerSpots): #cleanup.
      if lowerSpots[i] in upperSpots: #simple dedupe branch.
        collisionSpots.append(lowerSpots[i]) #track until this value is shown once, then forget it after the largest loop continues.
        del upperSpots[upperSpots.index(lowerSpots[i])]
        del lowerSpots[i]
        continue
      if lowerSpots[i]+1 in upperSpots: #if an overlap just happened...
        #then these spots should both be eliminated.
        del upperSpots[upperSpots.index(lowerSpots[i]+1)]
        del lowerSpots[i]
      else:
        i += 1
    if noNegatives:
      while len(lowerSpots) > 0:
        if lowerSpots[0] < 0: #this works because lowerSpots is sorted.
          del lowerSpots[0]
          continue
        else:
          break
    #print("lowerSpots end up as " + str(lowerSpots))
    #print("upperSpots end up as " + str(upperSpots))
    currentArr = sorted(lowerSpots+upperSpots+collisionSpots)
    #print("iterating through " + str(currentArr))
    for item in currentArr:
      yield item
      
      
      
class ListInternalTranscriptionHelperPipe:
  def __init__(self, iSrc, iDest, dataRef):
    self.iSrc, self.iDest, self.data = iSrc, iDest, dataRef
    
  def reset(self):
    self.iSrc, self.iDest = 0, 0
    
  def writeIncD(self, valueToPut):
    self.data[self.iDest] = valueToPut
    self.iDest += 1
    
  def writeIncDS(self, valueToPut):
    self.data[self.iDest] = valueToPut
    self.iDest += 1
    self.iSrc += 1
    
  def writeIncS(self, valueToPut):
    self.data[self.iDest] = valueToPut
    self.iSrc += 1
    
  def peek(self):
    return self.data[self.iSrc]
    
  def read(self):
    result = self.data[self.iSrc]
    self.iSrc += 1
    return result
  
  def trim(self):
    del self.data[self.iDest:]
    
  def skip(self):
    self.iSrc += 1
    
  def canRead(self):
    return self.iSrc < len(self.data)

 
class Spot:
  def __init__(self, motion, position):
    self.motion, self.position = motion, position
  
  def isMovingLeft(testSpot):
    return testSpot.motion == -1
    
  def isMovingRight(testSpot):
    return testSpot.motion == 1
    
  def isStationary(testSpot):
    return testSpot.motion == 0
    
  def overlaps(self, other):
    return self.position == other.position
    
  def moved(inputSpot):
    return Spot(inputSpot.motion, inputSpot.motion + inputSpot.position)
    
  def stopped(inputSpot):
    return Spot(0, inputSpot.position)
    

def _get_gen_bleed_sorted_arr_starting_spots(seedArr, noNegatives):
  primitiveNeighborsOfInt = (lambda calcSpot: [[-1,calcSpot-1],[1,calcSpot+1]])
  genNoneless = (lambda genToEdit: (item for item in genToEdit if item != None))
  
  genLocalNeighborsWithMutualErasure = (lambda calcSpotIndex,calcSpot,calcArr: (localNeighbor for localNeighbor in primitiveNeighborsOfInt(calcSpot) if localNeighbor[1] != calcArr[(calcSpotIndex+localNeighbor[0])%len(calcArr)]))
  
  genLocalNeighborsWithCollisionsAndNones = (lambda calcSpotIndex,calcSpot,calcArr: ((localNeighbor if sum(localNeighbor) != calcArr[(calcSpotIndex+localNeighbor[0])%len(calcArr)] else ([0,localNeighbor[1]] if localNeighbor[0]>0 else None)) for localNeighbor in genLocalNeighborsWithMutualErasure(calcSpotIndex,calcSpot,calcArr)))
  
  movingSpotArgs = (neighbor for spotIndex,spot in enumerate(seedArr) for neighbor in genNoneless(genLocalNeighborsWithCollisionsAndNones(spotIndex,spot,seedArr)))
  
  return [Spot(pair[0], pair[1]) for pair in movingSpotArgs]
  

def genBleedSortedArrWithoutSearches(seedArr, noNegatives=False, stopSingleRisingSeedTail=False):
  #futher optimization is possible, but not necessary. movingSpots beyond all others and moving outwards could be removed from collision detection.
  validateSeedArrNoNegatives(seedArr, noNegatives)
  if stopSingleRisingSeedTail and not noNegatives:
    print("MarkovTools.genBleedSortedArrWithoutSearches: stopSingleTail=True policy won't be used because with noNegatives=False a single seed tail can't exist.")
  
  for item in seedArr:
    yield item
  
  movingSpots = _get_gen_bleed_sorted_arr_starting_spots(seedArr, noNegatives)
    
  pipe = ListInternalTranscriptionHelperPipe(None, None, movingSpots)
  
  def isInBounds(testSpot):
    if not noNegatives:
      return True
    return testSpot[1] >= 0
    
  while True:
    for currentSpot in movingSpots:
      yield currentSpot.position
    pipe.reset()
    
    while pipe.canRead():
      oldSpot = pipe.peek()
      if oldSpot.isStationary(): #if it's a collision spot:
        pipe.skip() #nothing will be done with the spot, so it will be overwritten at some point, and not yielded more than once.
        continue
      newSpot = oldSpot.moved() #what oldSpot wants to be. This is never stationary.
      if not isInBounds(newSpot):
        pipe.skip()
        continue
      if oldSpot.isMovingLeft():
        if pipe.iDest == 0: #if there's nothing to the left of this spot, so no collision can happen:
          pipe.writeIncDS(newSpot)
        else: # a collision should be tested for.
          assert pipe.iSrc > 0
          iLeftOfDest = pipe.iDest - 1
          assert iLeftOfDest >= 0
          spotLeftOfIDest = movingSpots[iLeftOfDest]
          if spotLeftOfIDest.isMovingRight(): #if left spot is collidable (or slippable) because it is moving in the opposite direction:
            if spotLeftOfIDest.overlaps(newSpot): #if collision:
              movingSpots[iLeftOfDest] = spotLeftOfIDest.stopped() #merge
              pipe.skip()
            elif spotLeftOfIDest.overlaps(oldSpot): #if slip (needs mutual erasure):
              pipe.iDest = iLeftOfDest #iDest is now index of spotLeftOfDest, allowing it to be rewritten too. same as -= 1
              pipe.skip()
            else: #no collision or skip. This point is fine.
              pipe.writeIncDS(newSpot)
          else:
            assert spotLeftOfIDest.isMovingLeft()
      else: #spot is moving right.
        #don't check for anything. checks are only done by points moving left.
        pipe.writeIncDS(newSpot)
      
    pipe.trim()
    if all(testSpot.isMovingRight() for testSpot in movingSpots):
      break
  
  #after the above loop breaks, there are only movingSpots with directions equal to 1, so no more testing needs to be done.
  assert all(spot[0] == 1 for spot in movingSpots)
  uniformlyMovingSpots = [spot[1] for spot in movingSpots]
  assert len(uniformlyMovingSpots) == 1
  if stopSingleRisingSeedTail:
    return
  for offset in itertools.count(0):
    for value in uniformlyMovingSpots:
      yield value+offset
      
      
def genBleedSortedArrDownOnly(seedArr, noNegatives=False):
  if not len(seedArr) > 0:
    raise ValueError("seedArr can't be empty.")
  validateSeedArrNoNegatives(seedArr, noNegatives)
  
  activeSeedEntries = [(None, seedArr[0])] + [(seedArr[i-1], seedArr[i]) for i in range(1,len(seedArr))]
  for seedEntry in activeSeedEntries:
    yield seedEntry[1]
  for offset in itertools.count(1): #don't yield seeds again - start at 1.
    currentSeedEntry = activeSeedEntries[0] #yield lowest item now instead of processing it along with the others and testing for a collision where one is impossible.
    currentValue = currentSeedEntry[1] - offset
    if noNegatives:
      if currentValue < 0:
        del activeSeedEntries[0]
        if len(activeSeedEntries) == 0:
          return
        continue
    yield currentValue
    i = 1 #don't yield lowest item again - start at 1.
    while i < len(activeSeedEntries):
      currentSeedEntry = activeSeedEntries[i]
      currentValue = currentSeedEntry[1] - offset
      if currentValue == currentSeedEntry[0]:
        del activeSeedEntries[i]
      else:
        yield currentValue
        i += 1
  #finished.


def remapToReorderedPositiveIntsTranscode(mainItem, opMode, inputSeq, startIndex=0):
  if mainItem == None:
    print("MarkovTools.remapToReorderedPositiveIntsTranscode: decode: warning: can't use None as an index. Will return None immediately.")
    return None
  assert mainItem >= 0
  assert startIndex >= 0
  if startIndex != 0:
    raise NotImplementedError("nonzero startIndex")
  
  #attempt shortcut:
  if opMode == "decode":
    if hasattr(inputSeq, "__getitem__") and not isinstance(inputSeq, dict):
      if hasattr(inputSeq, "__len__"):
        if mainItem + startIndex < len(inputSeq):
          return inputSeq[mainItem + startIndex]
        else:
          return mainItem
      else:
        try:
          return inputSeq[mainItem + startIndex]
        except IndexError:
          print("MarkovTools.remapToReorderedPositiveIntsTranscode: slow: shortcut failed due to index error. Falling back to linear search, which is slow and might have no chance of succeeding depending on the inputSeq type ({}).".format(repr(type(inputSeq))))
          pass
    
  workingGen = genSkipFirst(inputSeq, startIndex)
  if opMode == "encode":
    result = indexOfValueInGen(mainItem, workingGen)
  elif opMode == "decode":
    result = valueAtIndexInGen(mainItem, workingGen)
  else:
    raise ValueError("invalid opMode.")
  if result is None:
    if startIndex != 0:
      raise NotImplementedError("passing through the mainItem with a nonzero startIndex is not yet allowed because startIndex might not be correctly applied to this returned value.")
    return mainItem + startIndex
  else:
    assert result >= 0
    return result
      

def remapToGeneratedValuesTranscode(mainItem, opMode, inputGen, startIndex=0, timeout=2**20):
  workingGen = genTakeOnly(genSkipFirst(inputGen, startIndex), timeout, onExhaustion="warn")
  if opMode == "encode":
    foundIndex = indexOfValueInGen(mainItem, workingGen)
    if foundIndex == None:
      print("MarkovTools.remapToGeneratedValuesTranscode: encode: warning: couldn't find it. returning None.")
    return foundIndex
  elif opMode == "decode":
    if mainItem == None:
      print("MarkovTools.remapToGeneratedValuesTranscode: decode: warning: can't use None as an index. Will return None immediately.")
      return None
    foundValue = valueAtIndexInGen(mainItem, workingGen)
    if foundValue == None:
      print("MarkovTools.remapToGeneratedValuesTranscode: decode: warning: foundValue is None. returning None.")
    return foundValue
  else:
    raise ValueError("invalid opMode.")
    
    
def remapToBleedingSortedArrTranscode(mainItem, opMode, seedArr, noNegatives=True, skipSeedArr=False, timeout=2**20):
  assert type(seedArr) in [list,set]
  if type(seedArr) == set:
    print("MarkovTools.remapToBleedingSortedArrTranscode: warning: converting set to list is slow!")
    seedArr = sorted(seedArr)
  assert opMode in ["encode","decode"]
  if len(seedArr) == 0: #happens when this codec is used by genfunctionalDynamicMarkovTranscode when it shouldn't be, like when the history is empty except for items that are filtered out like an escapeValue.
    return mainItem
  startIndex = len(seedArr) if skipSeedArr else 0
  if skipSeedArr:
    if opMode == "encode":
      if mainItem in seedArr:
        print("MarkovTools.remapToBleedingSortedArrTranscode: warning: mainItem is present in seedArr, but skipSeedArr is True, so mainItem is not representable, and None will be returned.")
        return None
  valueMapGen = genBleedSortedArr(seedArr,noNegatives=noNegatives)
  #the following is disabled for being too complicated, but could provide a large speedup.
  #if noNegatives:
  #  #add early end to switch to more efficient mapping.
  #  earlyStoppingValueMapGen = (pairA[1] for pairA in genTakeUntil(enumerate(valueMapGen),(lambda pairB: pairB[0]==pairB[1]+startIndex),stopSignalsNeeded=len(seedArr)*3))
  #  #this generator will run until its items are equal to their indices (with an offset provided by startIndex), and then for a little while longer, and then it will stop. During this time it will only eat from valueMapGen what it yields.
  result = remapToGeneratedValuesTranscode(mainItem,opMode,valueMapGen,startIndex=startIndex,timeout=max([timeout,max(seedArr)*2]))
  if result == None:
    if noNegatives:
      #the following is not really necessary.
      #lowestValueNotVisited = None
      #try:
      #  lowestValueNotVisited = next(valueMapGen)
      #except StopIteration:
      #  assert False, "impossible error."
      return mainItem
    else:
      print("MarkovTools.remapToBleedingSortedArrTranscode: warning: can't attempt to resolve None when noNegatives is not True. returning None.")
  return result
    
bleedingSortedArrRemapCodec = CodecTools.Codec(None,None,transcodeFun=remapToBleedingSortedArrTranscode)
  


def extendWithoutDupes(arrToExtend,extensionSrc):
  arrToExtend.extend(item for item in extensionSrc if not item in arrToExtend)


def getPredictedValuesFromHistory(history,singleUsageHist,maxContextLength,scoreMode):
  predictedValues = []
  if scoreMode == "(max(l),f(max(l)),max(x(max(l))),-y)":
    #the following code really is incompatible with the idea of merging the single analyzed item into the search term, because it needs to add things to predictedItems in strictly descending match length order.
    currentLengthContextHist = None
    for currentLength,matchesOfCurrentLength in getEndingIndicesOfShrinkingSubSequences(history[:-1],history[-maxContextLength:]):
      currentLengthContextHist = OrderlyHist()
      for matchEndLocation in matchesOfCurrentLength:
        if history[matchEndLocation+1] not in predictedValues:
          currentLengthContextHist.register(history[matchEndLocation+1])
      extendWithoutDupes(predictedValues,currentLengthContextHist.keysInDescendingRelevanceOrder())
    #print("predictedItems without general history = " + str(predictedItems))
    #print("general history = " + str(singleUsageHist.data))
    extendWithoutDupes(predictedValues,singleUsageHist.keysInDescendingRelevanceOrder())
  elif scoreMode == "(max(l)*f(max(l)),max(x(max(l))),-y)":
    #the following code is a change towards including the search item in the search term, and it avoids needing to apply a singleUsageHist at the end, because the main search includes these items when its match length is 1.
    raise NotImplementedError("Not finished!")
    allLengthSearchItemHist = OrderlyHist()
    for searchItem in singleUsageHist.keysInDescendingRelevanceOrder():
      for currentLength,matchesOfCurrentLength in getEndingIndicesOfShrinkingSubSequences(history,history[-maxContextLength:]+[searchItem]):
        for matchEndLocation in matchesOfCurrentLength:
          assert history[matchEndLocation] == searchItem
          if history[matchEndLocation] not in predictedValues:
            allLengthSearchItemHist.registerMany(history[matchEndLocation],currentLength) #this currentLength is the "l" in "l*f", and the "f" is the result of repeatedly running this line.
        extendWithoutDupes(predictedValues,contextualHist.keysInDescendingRelevanceOrder()) # @ what is contextualHist? where is it supposed to come from? The old fixed-function markov tools should just be deleted.
  else:
    assert False, "invalid scoreMode."
  return predictedValues
  

def getValueChancesFromHistory(history,chanceFun,maxContextLength,searchValueSrc=None):
  valueChanceDict = dict()
  searchValueSrcSeq = None #searchItemGen may be built in different ways and give different item orders, but it doesn't really matter since in this method, the probability given to each item doesn't depend on when it is processed or what the unfinished output looks like so far.
  if type(searchValueSrc) in [set,list]:
    searchValueSrcSeq = searchValueSrc
  elif searchValueSrc != None:
    try:
      searchValueSrcSeq = searchValueSrc.keysInDescendingRelevanceOrder()
    except AttributeError: #it's probably of type dict and not a histogram class.
      searchValueSrcSeq= searchValueSrc.keys()
  else:
    searchValueSrcSeq = genDeduped(history)
  for searchValue in searchValueSrcSeq:
    searchTerm = history[-maxContextLength:] + [searchValue]
    matchEndIndices = getEndingIndicesOfGrowingSubSequences(history,searchTerm)
    valueChanceDict[searchValue] = chanceFun(matchEndIndices,len(history))
  if all(value == 0 for value in valueChanceDict.values()):
    print("MarkovTools.getValueChancesFromHistory: warning: returning a dict with a value sum of 0.")
  return valueChanceDict
  




def findMax(inputSeq,keyFun=None):
  if keyFun == None:
    keyFun = (lambda x: x)
  recordHigh = None
  recordHighIndex = None
  justStarted = True
  for i,item in enumerate(inputSeq):
    if justStarted:
      recordHigh = keyFun(item)
      recordHighIndex = i
      justStarted = False
      continue
    if keyFun(item) > recordHigh:
      recordHigh = keyFun(item)
      recordHighIndex = i
  return (recordHighIndex,recordHigh)
  

def basicMatchIndexArrArrScoreFun(inputMatchIndexArrArr,currentHistoryLength): #this is the demo/default scoreFun for genDynamicMarkovTranscode.
  #this function does not assume that the inputMatchIndexArrArr is sorted by the first item of each tuple. It also does NOT assume that the second item of each tuple is sorted, so it uses max() in a slow way.
  #this function assumes the matches are for searches involving an item being investigated, and including that item in the search term. it is correct to use currentHistoryLength when scaling using locationOfLatestLongestMatch because no match location can be higher than that.
  #print("MarkovTools.basicMatchIndexArrArrScoreFun: called with args: " + str([inputMatchIndexArrArr,currentHistoryLength]) + ".")
  result = None
  #thereAreMatches = sum(len(pair[1]) for pair in inputMatchIndexArrArr) > 0
  #if thereAreMatches:
  maxMatchLengthIndex, maxMatchLength = findMax(inputMatchIndexArrArr,keyFun=(lambda pairB: pairB[0] if (len(pairB[1])>0) else -100)) #the filtering to exclude empty match lists should be unecessary, and can be fixed if it doesn't break genDynamicMarkovTranscodeNonFunctional.
  #print("MarkovTools.basicMatchIndexArrArrScoreFun: (maxMatchLengthIndex, maxMatchLength)="+str((maxMatchLengthIndex, maxMatchLength))+".")
  if maxMatchLengthIndex != None and len(inputMatchIndexArrArr[maxMatchLengthIndex][1]) > 0:
    #print("took complex branch.")
    #direction = inputMatchIndexArrArr[-1][0] > inputMatchIndexArrArr[0][0]
    #maxMatchLengthIndex = -1 if direction else 0
    
    locationOfLatestLongestMatch = float(max(inputMatchIndexArrArr[maxMatchLengthIndex][1]))
    assert 0 <= locationOfLatestLongestMatch <= currentHistoryLength
    result = 0
    for x,matchesOfLengthX in inputMatchIndexArrArr:
      #result = min(result,result.bit_length()) #don't let even a huge amount of very short matches overpower any very long matches.
      result = len(matchesOfLengthX)**x
    #the following scaling operation avoids the need for floats and ensures that every scored value will have a unique integer score.
    result = (result * currentHistoryLength) + locationOfLatestLongestMatch
  else:
    #print("took simple branch.")
    result = 0
  return result


class Escape:
  """
  This class is for use inside genDynamicMarkovTranscode. This class indicates that the huffman codec _will not_ know what to do with the following value because it has never been encountered before. This class will probably only be used when a huffman codec is being used and the probabilityMode is "explicit". This class is a temporary solution to be used until there is something in place to give huffman coding codecs (either within this method or in general) an escape code that is always present in their database.
  """
  def __init__(self):
    pass





def genFunctionalDynamicMarkovTranscode(inputSeq, opMode, maxContextLength=16, noveltyCodec=None, noveltyIndexRemapCodec="linear", scoreFun=None, redundantEscapesInHistory=False, addDbgChars=False, addDbgWords=False):
  """
  inputSeq is the source, which may be a generator.
  maxContextLength is the maximum length of a match that will be recognized. Larger values should give better compression without significant performance impact, see performance notes on getEndingIndicesOfGrowingSubSequence.
  noveltyCodec is used to transcode the values of novel symbols after an escape symbol. Right now it only applies to explicit probability mode.
  scoreFun is the scoring function used to score a possible new value based on its arguments, which are (1) a collection of known matches for that value and various context lengths before it and (2) the length of recorded history.
  """
  inputSeq = makeGen(inputSeq)
  assert opMode in ["encode","decode"]
  if scoreFun == None: #if the scoreFun still needs to be initialized to its default value...
    scoreFun = basicMatchIndexArrArrScoreFun
  if noveltyCodec == None:
    #noveltyCodec = CodecTools.makePlainDataNumOffsetClone(Codes.codecs["fibonacci"],1)
    noveltyCodec = Codes.codecs["fibonacci"]
  if type(noveltyIndexRemapCodec) == str:
    if noveltyIndexRemapCodec == "linear":
      noveltyIndexRemapCodec = remapToValueArrCodec
    elif noveltyIndexRemapCodec == "bleed":
      noveltyIndexRemapCodec = bleedingSortedArrRemapCodec.clone(extraKwargs={"noNegatives":True,"skipSeedArr":True})
    else:
      raise KeyError("unknown noveltyIndexRemapCodec string ID {}.".format(repr(noveltyIndexRemapCodec)))
  
  escapeValue = Escape() #just keep one instance of this for use inside here.
  history = []
  encounteredValues = set()
  #encounteredIntValues = set()
  ascendingEncounteredIntValues = []
  #encounteredIntValues are not sorted, so when using bleed remapping, a sort is performed for every call to remap.
  def register(valueToRegister):
    if (valueToRegister != escapeValue) or redundantEscapesInHistory:
      history.append(valueToRegister)
    elif escapeValue not in history: #slow, but simple.
      history.append(escapeValue)
    if not valueToRegister in encounteredValues:
      if type(valueToRegister) == int:
        #encounteredIntValues.add(valueToRegister)
        insort(ascendingEncounteredIntValues,valueToRegister)
      encounteredValues.add(valueToRegister)
  
  valueChanceDict = None
  valueHuffmanCodec = None
    
  #noveltyCodecWithMixedContext = CodecTools.Codec((lambda encArg0,encValueListArg: noveltyCodec.zeroSafeEncode(noveltyIndexRemapCodec.encode(encArg0,[itemA for itemA in encValueListArg if type(itemA)==int]))),(lambda decArg0,decValueListArg: noveltyIndexRemapCodec.decode(noveltyCodec.zeroSafeDecode(decArg0),[itemB for itemB in decValueListArg if type(itemB)==int]))) #non-integer items can't be included in the context because they (usually???) can't be mapped around by the noveltyIndexRemapCodec. MIGHT NEED SORTING.
  noveltyCodecWithIntOnlyContext = CodecTools.Codec((lambda encArg0,encValueListArg: noveltyCodec.zeroSafeEncode(noveltyIndexRemapCodec.encode(encArg0,encValueListArg))),(lambda decArg0,decValueListArg: noveltyIndexRemapCodec.decode(noveltyCodec.zeroSafeDecode(decArg0),decValueListArg))) #a shortcut to avoid the need for filtering a list.


  getNewValueChanceDict = (lambda: getValueChancesFromHistory([escapeValue] if len(history) == 0 else history, scoreFun, maxContextLength, searchValueSrc=([escapeValue] if len(history) == 0 else encounteredValues)))
  # ^ this exists as a function just so that it can easily be repeated in the attempt loop. When history length is 0, escapeValue is prepended to history so that encoding escapeValue should be immediately possible for the huffman coding codec created from the returned dict to represent it. But when history is longer than 0 items, escapeValue isn't prepended, because history must already contain escapeValue just as many times as it has been used.
  
  getNewValueHuffmanCodec = (lambda: HuffmanMath.makeHuffmanCodecFromDictHist(valueChanceDict)) #this exists as a function just so that it can easily be repeated in the attempt loop.
  
  breakAll = False
  while True:
    inputValue = None #to be initialized later.
    resultValue = None #to be initialized later.
    
    if opMode == "encode":
      
      valueChanceDict = getNewValueChanceDict()
      valueHuffmanCodec = getNewValueHuffmanCodec()
    
      #the attempt loop.
      while True:
        try:
          try:
            inputValue = next(inputSeq)
          except StopIteration:
            breakAll = True
            break
          resultValue = valueHuffmanCodec.encode(inputValue)
          break
        except HuffmanMath.AlienError: #if the item is not representable by valueHuffmanCodec because it has never been seen before...
          
          if addDbgWords:
            yield "(fail in attempt loop; huffman-coded escapeValue and noveltyCodec-coded inputValue to follow.)"
            
          for outputElement in valueHuffmanCodec.encode(escapeValue): #it should be able to do this.
            yield outputElement
          if addDbgChars:
            yield ","
          register(escapeValue)
          #it isn't necessary to update valueHuffmanCodec at this time because it won't be used before the next time it is updated.
          
          #for outputComponent in noveltyCodec.encode(inputValue):
          for outputElement in noveltyCodecWithIntOnlyContext.encode(inputValue,ascendingEncounteredIntValues):
            yield outputElement
          if addDbgChars:
            yield ","
          register(inputValue)
          
          valueChanceDict = getNewValueChanceDict()
          valueHuffmanCodec = getNewValueHuffmanCodec()
      if breakAll:
        break
      
      if addDbgWords:
        yield "(" + str(inputValue) + " became:)"
      for outputElement in resultValue:
        yield outputElement
      if addDbgChars:
        yield ","
      register(inputValue)
          
    elif opMode == "decode":
    
      valueChanceDict = getNewValueChanceDict()
      valueHuffmanCodec = getNewValueHuffmanCodec()
    
      try:
        resultValue = valueHuffmanCodec.decode(inputSeq)
      except ExhaustionError:
        print("MarkovTools.genFunctionalDynamicMarkovTranscode: ending due to ExhaustionError from valueHuffmanCodec.")
        break
      register(resultValue)
      #it isn't necessary to update valueHuffmanCodec at this time because it won't be used before the next time it is updated.
      if resultValue == escapeValue:
        #no version of the escapeValue will be yielded. Anyone reading the plaindata does not need to know!.
        #resultValue = noveltyCodec.decode(inputSeq)
        resultValue = noveltyCodecWithIntOnlyContext.decode(inputSeq,ascendingEncounteredIntValues)
        register(resultValue)
        
      if addDbgWords:
        yield "(dec out:)"      
      yield resultValue
      if addDbgChars:
        yield ","
    else:
      assert False, "invalid opMode."
  if addDbgWords:
    print("MarkovTools.genFunctionalDynamicMarkovTranscode: end: history started out like {} and had length {}.".format(history[:1024],len(history)))
    print("MarkovTools.genFunctionalDynamicMarkovTranscode: end: The final huffman codec extraDataDict was {}.".format(valueHuffmanCodec.extraDataDict))

functionalDynamicMarkovCodec = CodecTools.Codec(None,None,transcodeFun=genFunctionalDynamicMarkovTranscode)











def genNonFunctionalDynamicMarkovTranscode(inputSeq, opMode, maxContextLength=16, scoreMode="(max(l),f(max(l)),max(x(max(l))),-y)", addDbgChars=False, addDbgWords=False):
  """
  deprecated. Anything this function can do, the functional version can do better.
  """
  inputSeq = makeGen(inputSeq)
  assert opMode in ["encode","decode"]
  #in a scoreMode definition, l is the set of all unique lengths of all matches (to what? it varies), the function f gives the frequency of matches of a length, the function x gives all positions of all matches of a length, and y is just the value of the item being analyzed.
  assert scoreMode in ["(max(l),f(max(l)),max(x(max(l))),-y)","(max(l)*f(max(l)),max(x(max(l))),-y)"]
        
  history = []
  singleUsageHist = OrderlyHist()

  while True:
    inputValue = None #to be initialized later.
    
    #parse phase.
    try:
      inputValue = next(inputSeq)
    except StopIteration:
      #print("MarkovTools.genNonFunctionalDynamicMarkovTranscode: stopping because inputSeq is now empty.")
      #return
      break
    #analyze phase:
    #all known history, but NOT the current plainData or pressData item, is used to create a map that can be used to convert between a plainData value and a pressData value. This map will LATER be used to transcode whatever the current value is, in whichever direction it must be transcoded.
    predictedValues = getPredictedValuesFromHistory(history,singleUsageHist,maxContextLength,scoreMode)
    
    #transcode phase.
    resultValue = None
    if scoreMode.endswith(",-y)"):
      resultValue = remapToValueArrTranscode(inputValue,opMode,predictedValues)
    else:
      assert False, "unfinished."
      
    #yield phase.
    if addDbgWords:
      yield "(norm out:)"
    yield resultValue
    if addDbgChars:
      yield ","
    
    #update phase.
    if opMode == "encode":
      history.append(inputValue)
      singleUsageHist.register(inputValue)
    elif opMode == "decode":
      history.append(resultValue)
      singleUsageHist.register(resultValue)
    else:
      assert False
  #end of generator items.











sampleTexts = ["hello, world!","123456789 123456789 123456789 123456789 123456789 3456789 3456789 3456789 3456789 56789 56789 56789 789 789 9"]




assert arrTakeOnly(genBleedSortedArr([5,8,10,11,15,16,17]),30) == [5,8,10,11,15,16,17,4,6,7,9,12,14,18,3,13,19,2,20,1,21,0,22,-1,23,-2,24,-3,25,-4]

for test in [(sampleTexts[0],"rld"),(sampleTexts[1],"678")]:
  assert [item+len(test[1])-1 for item in getStartingIndicesOfSubSequence(test[0],test[1])] == getEndingIndicesOfGrowingSubSequences(test[0],test[1])[-1][1]
  continue

assert [item for item in genNonFunctionalDynamicMarkovTranscode([5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100], "encode")] == [5, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
assert [item for item in genNonFunctionalDynamicMarkovTranscode([5, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],"decode")] == [5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100]

