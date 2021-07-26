
import CodecTools
import math

from PyGenTools import ExhaustionError
from Codes import ParseError
from PyArrTools import bubbleSortSingleItemRight

import StatCurveTools




class AlienError(KeyError):
  """
  This error is thrown by methods (especially of CodecTools.Codec instances configured for huffman coding) which respond to input based on a search of an internal database. This error is thrown to indicate that the database does not include anything that can be used to determine the proper response. It is used in MarkovTools.py.
  """
  pass



def morphAscendingEntriesIntoHuffmanTree(entries):
  #modifies the input array and returns nothing.
  #input must be in the same format as is specified in HuffmanMath.makeHuffmanTreeFromAscendingEntries.
  #The tree ends up in last item of the input array as (sum of the chances of all items in the tree, tree).
  if len(entries) < 2:
    raise ValueError("can't make a tree with fewer than 2 entries. Try makeHuffmanTreeFromAscendingEntries instead.")
  entriesStart = 0
  while entriesStart < len(entries)-1:
    #print("morphAscendingEntriesIntoHuffmanTree: entries is " + str(entries)+".")
    eB, eA = (entries[entriesStart], entries[entriesStart+1])
    entries[entriesStart+1] = (eB[0]+eA[0], (eB[1], eA[1]))
    #entries[entriesStart] = None
    entriesStart += 1
    bubbleSortSingleItemRight(entries,entriesStart)


def makeHuffmanTreeFromAscendingEntries(entries):
  #the input array must be in the format [(chance_0, item_0), (chance_1, item_1), ...].
  #the chances do not need to be probabilities, do not need to sum to 1.0, and do not need to be floats. They only need to be usable on either side of the '+' operator, and comparable on either side of the '>' operator (within HuffmanMath.bubbleSortSingleItemRight).
  if len(entries) == 0:
    raise ValueError("can't make a tree with 0 entries.")
  elif len(entries) == 1:
    print("HuffmanMath.makeHuffmanTreeFromAscendingEntries: creating single-node tree, which is experimental and may cause other HuffmanMath tools to break. The tree total probability will be set to 1, ignoring any other info in the entries list item.")
    return (1,entries[0][1])
  workingArr = [item for item in entries]
  morphAscendingEntriesIntoHuffmanTree(workingArr)
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

