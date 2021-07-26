
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



def morphAscendingEntriesIntoHuffmanTree(entries):
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
  return entries[-1]
    
def drainAscendingEntriesIntoHuffmanTree(entries):
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
  return entries[-1]
    
    
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
  
def depthBasedWaterfallDrainAscendingEntriesIntoHuffmanTree(entries):
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
    reactantFetchedResults = takeLowestItemsFromArrOfSortedArrs(workingArrArr,2,keyFun=(lambda x: x[0]))
    if len(reactantFetchedResults) < 2:
      assert len(reactantFetchedResults) == 1
      finishedTree = reactantFetchedResults[0][-1]
      break
    reactantDepths = [reactantFetchedResult[0] for reactantFetchedResult in reactantFetchedResults]
    assumedProductDepth = max(reactantDepths) + 1
    reactants = [reactantFetchedResult[-1] for reactantFetchedResult in reactantFetchedResults]
    assert len(reactants) == 2
    product = (reactants[1][0]+reactants[0][0], (reactants[1][1], reactants[0][1]))
    restockWithAssumedDepth(product,assumedProductDepth)
  return finishedTree
    
    

def makeHuffmanTreeFromAscendingEntries(entries):
  #the input array must be in the format [(chance_0, item_0), (chance_1, item_1), ...].
  #the chances do not need to be probabilities, do not need to sum to 1.0, and do not need to be floats. They only need to be usable on either side of the '+' operator, and comparable on either side of the '>' operator (within HuffmanMath.bubbleSortSingleItemRight).
  if len(entries) == 0:
    raise ValueError("can't make a tree with 0 entries.")
  elif len(entries) == 1:
    print("HuffmanMath.makeHuffmanTreeFromAscendingEntries: creating single-node tree, which is experimental and may cause other HuffmanMath tools to break. The tree total probability will be set to 1, ignoring any other info in the entries list item.")
    return (1,entries[0][1])
  workingArr = [item for item in entries]
  drainAscendingEntriesIntoHuffmanTree(workingArr)
  #print("makeHuffmanTreeFromAscendingEntries: workingArr is " + str(workingArr)+".")
  return workingArr[-1][1]

def makeHuffmanTreeFromEntries(entries):
  ascendingEntries = sorted(entries)
  #print("makeHuffmanTreeFromEntries: (entries,ascendingEntries) is " + str((entries,ascendingEntries))+".")
  return makeHuffmanTreeFromAscendingEntries(ascendingEntries)


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
  result = dict()
  for entry in genLeafIDsAndItems(tree):
    result[entry[1]] = entry[0]
  return result







def makeHuffmanCodecFromEntries(entries):
  huffmanTree = makeHuffmanTreeFromEntries(entries)
  huffmanReverseDict = treeToReverseDict(huffmanTree)
  #print(huffmanTree)
  #print(huffmanReverseDict)
  def newEncodeFun(x):
    try:
      return huffmanReverseDict[x]
    except KeyError:
      raise AlienError("The CodecTools.Codec instance configured for Huffman coding can't encode this value.")
  def newDecodeFun(y):
    try:
      return accessTreeLocation(huffmanTree,y)
    except ExhaustionError as ee:
      raise ExhaustionError("CodecTools.Codec instance configured for Huffman coding: Decode: " + str(ee.message) + ".")
    except ParseError as pe:
      raise ParseError("CodecTools.Codec instance configured for Huffman coding: Decode: " + str(pe.message) + ".")
  return CodecTools.Codec(newEncodeFun,newDecodeFun,zeroSafe=(0 in huffmanReverseDict.keys()))

def makeHuffmanCodecFromFormula(chanceFun,minInputInt,maxInputInt):
  entries = sorted((chanceFun(value),value) for value in range(minInputInt,maxInputInt+1))
  return makeHuffmanCodecFromEntries(entries)

def makeHuffmanCodecFromDictHist(inputDictHist,chanceExtractionFun=None):
  if chanceExtractionFun == None:
    chanceExtractionFun = (lambda x: x)
  entries = sorted((chanceExtractionFun(value),key) for key,value in inputDictHist.items())
  return makeHuffmanCodecFromEntries(entries)

def makeHuffmanCodecFromListHist(inputListHist,doPatch=False):
  workingListHist = StatCurveTools.patchedListHist(inputListHist) if doPatch else inputListHist
  entries = [(item,i) for i,item in enumerate(workingListHist)]
  return makeHuffmanCodecFromEntries(entries)
  
  


testArrArr1 = [[1,200,300],[2,300,400],[3,4,500],[5,6,7]]
#print(findLowestItemsInArrOfSortedArrs(testArrArr1,4))
assert findLowestItemsInArrOfSortedArrs(testArrArr1,4) == [(0,0,1),(1,0,2),(2,0,3),(2,1,4)]
assert testArrArr1 == [[1,200,300],[2,300,400],[3,4,500],[5,6,7]]

daeTest = sorted([(1,2),(3,4),(6,5),(8,7),(5,4),(3.1,2),(1.1,0)],key=(lambda x: x[0]))
maeTest = sorted([(1,2),(3,4),(6,5),(8,7),(5,4),(3.1,2),(1.1,0)],key=(lambda x: x[0]))
drainAscendingEntriesIntoHuffmanTree(daeTest)
morphAscendingEntriesIntoHuffmanTree(maeTest)
print("HuffmanMath testing: " + str(daeTest) + ".")
print("HuffmanMath testing: " + str(maeTest) + ".")
assert daeTest[-1] == maeTest[-1]
del daeTest
del maeTest

