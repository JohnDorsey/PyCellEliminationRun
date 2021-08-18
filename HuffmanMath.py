
import CodecTools
import math

from PyGenTools import ExhaustionError
from Codes import ParseError
from PyArrTools import bubbleSortSingleItemRight,insort

import StatCurveTools




class AlienError(KeyError):
  """
  This error is thrown by methods (especially of CodecTools.Codec instances configured for huffman coding) which respond to input based on a search of an internal database. This error is thrown to indicate that the database does not include anything that can be used to determine the proper response. It is used in MarkovTools.py.
  """
  pass



  

def morphAscendingEntriesIntoHuffmanTree(entries,includeTreeTotalChance=False):
  #modifies the input array and returns a tree.
  #input must be in the same format as is specified in HuffmanMath.makeHuffmanTreeFromAscendingEntries.
  #The tree ends up in last item of the input array as (sum of the chances of all items in the tree, tree).
  if len(entries) < 2:
    raise ValueError("can't make a tree with fewer than 2 entries. Try makeHuffmanTreeFromAscendingEntries instead.")
  entriesStart = 0
  while entriesStart < len(entries)-1:
    #print("morphAscendingEntriesIntoHuffmanTree: entries is " + str(entries)+".")
    eB, eA = (entries[entriesStart], entries[entriesStart+1])
    entries[entriesStart+1] = (eB[0]+eA[0], (eB[1], eA[1]))
    #print("morphAscendingEntriesIntoHuffmanTree: entries is " + str(entries)+" after unsorted insertion.")
    #entries[entriesStart] = None
    entriesStart += 1
    bubbleSortSingleItemRight(entries,entriesStart)
    #print("morphAscendingEntriesIntoHuffmanTree: entries is " + str(entries)+" after bubble sort.")
  return entries[-1] if includeTreeTotalChance else entries[-1][1]
    
def drainAscendingEntriesIntoHuffmanTree(entries,includeTreeTotalChance=False):
  #modifies the input array and returns a tree.
  #input must be in the same format as is specified in HuffmanMath.makeHuffmanTreeFromAscendingEntries.
  #The tree ends up in last item of the input array as (sum of the chances of all items in the tree, tree).
  if len(entries) < 2:
    raise ValueError("can't make a tree with fewer than 2 entries. Try makeHuffmanTreeFromAscendingEntries instead.")
  while len(entries) > 1:
    #print("drainAscendingEntriesIntoHuffmanTree: entries is " + str(entries)+".")
    eB, eA = (entries[0], entries[1])
    eNew = (eB[0]+eA[0], (eB[1], eA[1]))
    #entries[0] = (0,None)
    #entries[1] = (0,None)
    #print("drainAscendingEntriesIntoHuffmanTree: entries is now " + str(entries)+" before insort of " + str(eNew) + ".")
    insort(entries,eNew,keyFun=(lambda item: item[0]))
    #print("drainAscendingEntriesIntoHuffmanTree: entries is now " + str(entries)+" after insort.")
    del entries[0] #@ slow. start point could be tracked and adjusted instead.
    #print("drainAscendingEntriesIntoHuffmanTree: entries is now " + str(entries)+" after first shortening.")
    del entries[0]
    #print("drainAscendingEntriesIntoHuffmanTree: entries is now " + str(entries)+" after second shortening.")
  return entries[-1] if includeTreeTotalChance else entries[-1][1]
    
    
def findLowestItemsInArrOfSortedArrs(inputArrArr,n,keyFun=(lambda x: x)):
  #n is the number of items to find.
  lowest = []
  def trim(trimInputArr):
    while len(trimInputArr) > n:
      del trimInputArr[-1]
  for indexInInputArrArr,inputArr in enumerate(inputArrArr):
    for indexInInputArr,inputItem in enumerate(inputArr):
      if len(lowest) < n:
        insort(lowest,(indexInInputArrArr,indexInInputArr,inputItem),keyFun=(lambda itemForLowest: keyFun(itemForLowest[2])))
        #calling trimLowest at this time is unnecessary. It can't be too long right now.
        continue #don't let the same item be insorted twice!
      if keyFun(inputItem) <= keyFun(lowest[-1][2]): #it might be acceptable to use < here instead.
        insort(lowest,(indexInInputArrArr,indexInInputArr,inputItem),keyFun=(lambda itemForLowest: keyFun(itemForLowest[2])))
        trim(lowest)
      else:
        break #because the inputArr is sorted, this can be done!
  return lowest
  
def takeLowestItemsFromArrOfSortedArrs(inputArrArr,n,keyFun=(lambda x: x)):
  searchResults = findLowestItemsInArrOfSortedArrs(inputArrArr,n,keyFun=keyFun)
  #delete found items from their original locations:
  for searchResult in sorted(searchResults,key=(lambda xx: xx[1]))[::-1]: #sorting backwards by the second of two indices means that items will be deleted from the end of a list towards the start of it, so that they never move before they can be deleted.
    del inputArrArr[searchResult[0]][searchResult[1]]
  return searchResults
  
def depthBasedWaterfallDrainAscendingEntriesIntoHuffmanTree(entries,includeTreeTotalChance=False):
  #modifies the input array and returns a tree.
  #input must be in the same format as is specified in HuffmanMath.makeHuffmanTreeFromAscendingEntries.
  if len(entries) < 2:
    raise ValueError("can't make a tree with fewer than 2 entries. Try makeHuffmanTreeFromAscendingEntries instead.")
  workingArrArr = [entries]
  def restockWithAssumedDepth(productToRestock,assumedDepth):
    while len(workingArrArr)-1 < assumedDepth:
      workingArrArr.append([])
    insort(workingArrArr[assumedDepth],productToRestock,keyFun=(lambda xx: xx[0]))
  finishedTree = None
  while True:
    #print("depthBasedWaterfallDrainAscendingEntriesIntoHuffmanTree: in loop before fetch: workingArrArr="+str(workingArrArr)+".")
    reactantFetchedResults = takeLowestItemsFromArrOfSortedArrs(workingArrArr,2,keyFun=(lambda x: x[0]))
    #print("depthBasedWaterfallDrainAscendingEntriesIntoHuffmanTree: in loop after fetch: (workingArrArr, reactantFetchedResults)="+str((workingArrArr, reactantFetchedResults))+".")
    if len(reactantFetchedResults) < 2:
      assert len(reactantFetchedResults) == 1
      finishedTree = reactantFetchedResults[0][-1]
      break
    reactantDepths = [reactantFetchedResult[0] for reactantFetchedResult in reactantFetchedResults]
    assumedProductDepth = max(reactantDepths) + 1
    reactants = [reactantFetchedResult[-1] for reactantFetchedResult in reactantFetchedResults]
    #print("depthBasedWaterfallDrainAscendingEntriesIntoHuffmanTree: in loop after fetch: (reactantDepths, assumedProductDepth, reactants)="+str((reactantDepths, assumedProductDepth, reactants))+".")
    assert len(reactants) == 2
    product = (reactants[1][0]+reactants[0][0], (reactants[1][1], reactants[0][1]))
    restockWithAssumedDepth(product,assumedProductDepth)
  #print("depthBasedWaterfallDrainAscendingEntriesIntoHuffmanTree: finishedTree is {}.".format(finishedTree))
  return finishedTree if includeTreeTotalChance else finishedTree[1]
  





class SegmentedSelfSortingList:
  def __init__(self,inputList,segmentCount=None,inputLevelFun=None,expectedMaxAbsLogBase2=4,keyFun=None):
    if segmentCount != None:
      if segmentCount%2 != 0:
        raise ValueError("segmentCount must be divisible by 2.")
    else:
      segmentCount = int(min([(len(inputList)+1)**0.5,8*expectedMaxAbsLogBase2])) #@ crude.
    self.segmentCount = segmentCount
    
    if inputLevelFun == None:
      def inputLevelFun(levelFunInputValue):
        if levelFunInputValue <= 0:
          return 0 #avoid a later math domain error with math.log.
        return (segmentCount>>1) + StatCurveTools.roundedScaledHyperbolicTangent(math.log(levelFunInputValue)/float(expectedMaxAbsLogBase2),segmentCount>>1)
    self.levelFun = inputLevelFun
    
    if keyFun == None:
      keyFun = (lambda x: x)
    self.keyFun = keyFun
    
    self.data = [[] for i in range(self.segmentCount)]
    for inputItem in inputList:
      self.insort(inputItem)
    
    
  def __getitem__(self,index):
    if index < 0:
      raise NotImplementedError("SegmentedSortedList.__getitem__ can't handle negative indices.")
    workingIndex = index
    for i in range(self.segmentCount):
      if workingIndex < len(self.data[i]):
        return self.data[i][workingIndex]
      else:
        workingIndex -= len(self.data[i])
        assert workingIndex >= 0
        continue
    raise IndexError(str(index))
    
  def takeItem(self,index):
    if index != 0:
      raise NotImplementedError("SegmentedSortedList.takeItem can't handle indices other than 0.")
    for i in range(self.segmentCount):
      if len(self.data[i]) == 0:
        continue
      result = self.data[i][0]
      del self.data[i][0]
      return result
    raise IndexError()
  
  """
  def next(self):
    try:
      return self.takeItem(0)
    except IndexError:
      raise StopIteration()
  """
   
  def insort(self,inputItem):
    inputItemLevel = self.getLevelOfValue(self.keyFun(inputItem))
    insort(self.data[inputItemLevel], inputItem)
    
  def getLevelOfValue(self,inputValue): #might be an unnecessary layer.
    return self.levelFun(inputValue)
    





def segmentedSelfSortingListBasedDrainAscendingEntriesIntoHuffmanTree(entries, segmentCount=None, includeTreeTotalChance=False):
  #modifies the input array and returns a tree.
  #input must be in the same format as is specified in HuffmanMath.makeHuffmanTreeFromAscendingEntries.
  if len(entries) < 2:
    raise ValueError("can't make a huffman tree with fewer than 2 entries. Try makeHuffmanTreeFromAscendingEntries instead.")
  appxMaxAbsLogBase2 = (abs(math.log(sum(item[0] for item in entries),2)) + abs(math.log(min(item[0] for item in entries if item[0] != 0),2)))/2.0
  if segmentCount == None:
    segmentCount = int(appxMaxAbsLogBase2/2.0)*2 #make divisible by 2.
  workingSelfSortingList = SegmentedSelfSortingList(entries,segmentCount=segmentCount,expectedMaxAbsLogBase2=appxMaxAbsLogBase2,keyFun=(lambda xC: xC[0]))
  
  finishedTree = None
  reactants = None
  while True:
    reactants = [workingSelfSortingList.takeItem(0)]
    try:
      reactants.append(workingSelfSortingList.takeItem(0))
    except IndexError:
      assert len(reactants) == 1
      finishedTree = reactants[0]
      break
    assert len(reactants) == 2
    product = (reactants[1][0]+reactants[0][0], (reactants[1][1], reactants[0][1]))
    workingSelfSortingList.insort(product)
  return finishedTree if includeTreeTotalChance else finishedTree[1]


def makeHuffmanTreeFromAscendingEntries(entries,includeTreeTotalChance=False):
  #the input array must be in the format [(chance_0, item_0), (chance_1, item_1), ...].
  #the chances do not need to be probabilities, do not need to sum to 1.0, and do not need to be floats. They only need to be usable on either side of the '+' operator, and comparable on either side of the '>' operator.
  if len(entries) == 0:
    raise ValueError("can't make a tree with 0 entries.")
  elif len(entries) == 1:
    print("HuffmanMath.makeHuffmanTreeFromAscendingEntries: creating single-node tree, which is experimental and may cause other HuffmanMath tools to break. The tree total probability will be set to 1, ignoring any other info in the entries list item.")
    return (1,entries[0][1])
  workingArr = [item for item in entries]
  result = depthBasedWaterfallDrainAscendingEntriesIntoHuffmanTree(workingArr,includeTreeTotalChance=includeTreeTotalChance)
  #print("makeHuffmanTreeFromAscendingEntries: workingArr is " + str(workingArr)+".")
  return result

def makeHuffmanTreeFromEntries(entries,includeTreeTotalChance=False):
  ascendingEntries = sorted(entries)
  #print("makeHuffmanTreeFromEntries: (entries,ascendingEntries) is " + str((entries,ascendingEntries))+".")
  result = makeHuffmanTreeFromAscendingEntries(ascendingEntries,includeTreeTotalChance=includeTreeTotalChance)
  #print("makeHuffmanTreeFromEntries: result is " + str(result)+".")
  return result
  
  
def makeShannonFanoTreeFromAscendingEntries(entries, chanceSum=None): 
  if not len(entries) >= 2:
    raise ValueError("can't make Shannon-Fano tree with fewer than 2 entries.")
  if len(entries) == 2:
    return tuple(entry[1] for entry in entries)
  #assert not iter(entries) is iter(entries)
  if chanceSum == None:
    chanceSum = sum(entry[0] for entry in entries)
  chanceSumLeft = 0 #left side sum.
  i = None
  for i in range(len(entries)):
    #assert i < len(entries), "break should have happened earlier."
    chanceSumLeft += entries[i][0]
    #assert chanceSumLeft < 0.5*chanceSum, "break should have happened before this fails."
    if chanceSumLeft <= 0.5*chanceSum and chanceSumLeft + entries[i+1][0] >= 0.5*chanceSum:
      break
  else:
    assert False, "how can this happen?"
  #print("entries={}, i={}, chanceSumLeft={}, chanceSum={}".format(entries, i,chanceSumLeft,chanceSum))
  if abs(chanceSum*0.5-(chanceSumLeft+entries[i+1][0])) < abs(chanceSum*0.5-chanceSumLeft):
    tippingPoint = i+1
    chanceSumLeft += entries[i+1][0]
  else:
    tippingPoint = i
  tippingPoint += 1 #prepare it to be used as an index!
  #print("entries={}, tippingPoint={}, chanceSumLeft={}, chanceSum={}".format(entries, tippingPoint,chanceSumLeft,chanceSum))
  i = None #don't use again.
  if len(entries[0:tippingPoint]) == 1:
    leftBranch = entries[0][1]
  else:
    assert len(entries[0:tippingPoint]) > 1
    leftBranch = makeShannonFanoTreeFromAscendingEntries(entries[0:tippingPoint], chanceSum=chanceSumLeft)
  if len(entries[tippingPoint:]) == 1:
    rightBranch = entries[tippingPoint][1]
  else:
    assert len(entries[tippingPoint:]) > 1
    rightBranch = makeShannonFanoTreeFromAscendingEntries(entries[tippingPoint:], chanceSum=(chanceSum-chanceSumLeft))
  return (leftBranch,rightBranch)
  
def makeShannonFanoTreeFromEntries(entries,includeTreeTotalChance=False):
  if includeTreeTotalChance:
    raise NotImplementedError("can't include tree total chance for Shannon-Fano.")
  ascendingEntries = sorted(entries)
  result = makeShannonFanoTreeFromAscendingEntries(ascendingEntries,includeTreeTotalChance=includeTreeTotalChance)
  #print("makeHuffmanTreeFromEntries: result is " + str(result)+".")
  return result
  
  
  
  
  
  
  
  
  


def genLeafIDs(tree):
  #visit all paths to tree leaves as a generator.
  #yielded items are in the form of arrays of integers.
  if type(tree) == tuple:
    for i,item in enumerate(tree):
      for nextPath in genLeafIDs(item):
        yield [i] + nextPath
  else:
    yield []


def genLeafIDsAndItems(tree):
  #same as genLeafIDs(tree), but each yielded item is not just the leaf ID, but is a tuple bundling (leaf ID, leaf value).
  if type(tree) == tuple:
    for i,item in enumerate(tree):
      for nextResponse in genLeafIDsAndItems(item):
        yield ([i] + nextResponse[0],nextResponse[1])
  else:
    yield ([],tree)


def accessTreeLocation(tree,pathDefSeq,stopFun=None):
  #get a node from a tree at the location specified by pathDefSeq.
  if stopFun == None:
    stopFun = (lambda x: type(x) not in [list,tuple,dict])
  #pathDefSeq = makeGen(pathDefSeq)
  currentNode = tree
  loopRan = False
  stopFunStopped = False
  for item in pathDefSeq:
    loopRan = True
    currentNode = currentNode[item]
    if stopFun(currentNode):
      stopFunStopped = True
      break
  if not loopRan:
    raise ExhaustionError("Received an empty pathDefSeq.")
  if not stopFunStopped:
    raise ParseError("Ran out of pathDefSeq items before reaching a node that satisfies stopFun.")
  return currentNode


def treeToReverseDict(tree):
  #take an input tree and return a dictionary mapping tree leaves to their paths.
  #this is much slower than expected. In the case of shannon-fano trees, it is slower than creating the tree!
  result = dict()
  for entry in genLeafIDsAndItems(tree):
    result[entry[1]] = entry[0]
  return result

"""
def writeToTreeLocation(tree,pathDefSeq,value):
  #this would require a tree made of Lists instead of tuples.
  raise NotImplementedError()

def reverseDictToTree(reverseDict):
  raise NotImplementedError()
"""





class TreeBasedCodec(CodecTools.Codec):
  def __init__(self,inputStructure,initType=None,treeType=None):
    treeType = treeType.lower()
    if not treeType in ["huffman","shannon-fano"]:
      raise ValueError("invalid treeType argument value: {}.".format(repr(treeType)))
    self.extraDataDict = {}
    if initType == "ascending_entries": #a bit faster than "entries".
      assert type(inputStructure) == list
      self.extraDataDict["ascending_entries"] = inputStructure
      if treeType == "huffman":
        self.extraDataDict["tree"] = makeHuffmanTreeFromAscendingEntries(inputStructure)
      else:
        self.extraDataDict["tree"] = makeShannonFanoTreeFromAscendingEntries(inputStructure)
    elif initType == "entries":
      assert type(inputStructure) == list
      self.extraDataDict["entries"] = inputStructure
      if treeType == "huffman":
        self.extraDataDict["tree"] = makeHuffmanTreeFromEntries(inputStructure)
      else:
        self.extraDataDict["tree"] = makeShannonFanoTreeFromEntries(inputStructure)
    elif initType == "tree":
      assert type(inputStructure) == tuple
      self.extraDataDict["tree"] = inputStructure
    else:
      raise ValueError("invalid initType argument value: {}.".format(repr(initType)))
    self.extraDataDict["reverse_dict"] = treeToReverseDict(self.extraDataDict["tree"])
      
    def newEncodeFun(newEncInput):
      try:
        return self.extraDataDict["reverse_dict"][newEncInput]
      except KeyError:
        raise AlienError("HuffmanMath.TreeBasedCodec: Encode: can't encode this value.")
    
    def newDecodeFun(newDecInput):
      try:
        return accessTreeLocation(self.extraDataDict["tree"],newDecInput)
      except ExhaustionError as ee:
        raise ExhaustionError("HuffmanMath.TreeBasedCodec: Decode: " + str(ee.message) + ".")
      except ParseError as pe:
        raise ParseError("HuffmanMath.TreeBasedCodec: Decode: " + str(pe.message) + ".")
        
    #CodecTools.Codec.__init__(self,newEncodeFun,newDecodeFun,zeroSafe=(0 in self.extraDataDict["huffman_reverse_dict"].keys()))
    self.encodeFun = newEncodeFun
    self.decodeFun = newDecodeFun
    self.extraArgs = []
    self.extraKwargs = dict()
    self._domain = self.extraDataDict["reverse_dict"].keys()
    
  def zeroSafeEncode(self,*args,**kwargs):
    if 0 in self._domain:
      return self.encode(*args,**kwargs)
    raise NotImplementedError("TreeBasedCodec instances do not allow value offsets in zeroSafeEncode. The value 0 must be included in the tree.")
    
  def zeroSafeDecode(self,*args,**kwargs):
    if 0 in self._domain:
      return self.decode(*args,**kwargs)
    raise NotImplementedError("TreeBasedCodec instances do not allow value offsets in zeroSafeDecode. The value 0 must be included in the tree.")
    
  def clone(self,*args,**kwargs):
    raise NotImplementedError("TreeBasedCodec instances are not clonable.")







def makeTreeBasedCodecFromAscendingEntries(entries, treeType=None):
  #huffmanTree = makeHuffmanTreeFromEntries(entries)
  #huffmanReverseDict = treeToReverseDict(huffmanTree)
  #print(huffmanTree)
  #print(huffmanReverseDict)
  workingCodec = TreeBasedCodec(entries, initType="ascending_entries", treeType=treeType)
  return workingCodec

def makeTreeBasedCodecFromFormula(chanceFun, minInputInt, maxInputInt, treeType=None):
  entries = sorted((chanceFun(value),value) for value in range(minInputInt,maxInputInt+1))
  return makeTreeBasedCodecFromAscendingEntries(entries, treeType=treeType)

def makeTreeBasedCodecFromDictHist(inputDictHist, chanceExtractionFun=None, treeType=None):
  if chanceExtractionFun == None:
    chanceExtractionFun = (lambda x: x)
  entries = sorted((chanceExtractionFun(value),key) for key,value in inputDictHist.items())
  return makeTreeBasedCodecFromAscendingEntries(entries, treeType=treeType)

def makeTreeBasedCodecFromListHist(inputListHist, doPatch=False, treeType=None):
  workingListHist = StatCurveTools.patchedListHist(inputListHist) if doPatch else inputListHist
  entries = [(item,i) for i,item in enumerate(workingListHist)]
  print("HuffmanMath.makeHuffmanCodecFromListHist: finished patching {} item inputListHist.".format(len(inputListHist)))
  return makeTreeBasedCodecFromAscendingEntries(entries, treeType=treeType)
  
  


testArrArr1 = [[1,200,300],[2,300,400],[3,4,500],[5,6,7]]
#print(findLowestItemsInArrOfSortedArrs(testArrArr1,4))
assert findLowestItemsInArrOfSortedArrs(testArrArr1,4) == [(0,0,1),(1,0,2),(2,0,3),(2,1,4)]
assert testArrArr1 == [[1,200,300],[2,300,400],[3,4,500],[5,6,7]]

daeTest = sorted([(1,2),(3,4),(6,5),(8,7),(5,4),(3.1,2),(1.1,0)],key=(lambda x: x[0]))
maeTest = sorted([(1,2),(3,4),(6,5),(8,7),(5,4),(3.1,2),(1.1,0)],key=(lambda x: x[0]))
daeTestResult = drainAscendingEntriesIntoHuffmanTree(daeTest)
maeTestResult = morphAscendingEntriesIntoHuffmanTree(maeTest)
#print("HuffmanMath testing: " + str(daeTest) + ".")
#print("HuffmanMath testing: " + str(maeTest) + ".")
assert daeTestResult == maeTestResult
del daeTest
del daeTestResult
del maeTest
del maeTestResult

