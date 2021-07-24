
import CodecTools
import math
from math import pi, e

from PyGenTools import ExhaustionError


def bubbleSortSingleItemRight(inputArr,startIndex):
  #an O(N) method to modify a provided array to correct a single out-of-place item. It could have fewer compares if it relied on a O(log(N)) search, but it couldn't have fewer writes.
  inputArrLen = len(inputArr)
  assert startIndex >= 0
  while (startIndex < inputArrLen - 1) and inputArr[startIndex] > inputArr[startIndex+1]:
    inputArr[startIndex], inputArr[startIndex+1] = (inputArr[startIndex+1], inputArr[startIndex])
    startIndex += 1



def morphAscendingEntriesIntoHuffmanTree(entries):
  #modifies the input array and returns nothing.
  #input must be in the same format as is specified in HuffmanMath.makeHuffmanTreeFromAscendingEntries.
  #The tree ends up in last item of the input array as (sum of the chances of all items in the tree, tree).
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
  for item in pathDefSeq:
    loopRan = True
    currentNode = currentNode[item]
    if stopFun(currentNode):
      break
  if not loopRan:
    raise ExhaustionError("HuffmanMath.accessTreeLocation received an empty pathDefSeq.")
  return currentNode


def treeToReverseDict(tree):
  #take an input tree and return a dictionary mapping tree leaves to their paths.
  result = dict()
  for entry in genLeafIDsAndItems(tree):
    result[entry[1]] = entry[0]
  return result





def patchListHist(inputListHist,patchFun=None):
  if patchFun == None:
    patchFun = (lambda x1, x2, y1, y2, xHere: ((y1+y2)/4.0)/float(x2-x1-1))
  if inputListHist[0] == None: #patchFun usage can't fix this, so fix it here.
    inputListHist[0] = 0
  if inputListHist[-1] == None: #patchFun usage can't fix this, so fix it here.
    inputListHist[-1] = 0
  for index in range(len(inputListHist)-1):
    if (inputListHist[index] != None and inputListHist[index+1] == None):
      holeStartIndex = index
      holeStartY = inputListHist[index]
      holeEndIndex = None
      for testHoleEndIndex in range(holeStartIndex+1,len(inputListHist)):
        if inputListHist[testHoleEndIndex] != None:
          holeEndIndex = testHoleEndIndex
          break
      assert holeEndIndex != None, "this should have been changed by now!"
      holeEndY = inputListHist[holeEndIndex]
      assert holeEndY != None
      for indexToPatch in range(holeStartIndex+1,holeEndIndex):
        inputListHist[indexToPatch] = patchFun(holeStartIndex,holeEndIndex,holeStartY,holeEndY,indexToPatch)
  assert None not in inputListHist

def patchedListHist(inputListHist,patchFun=None):
  outputListHist = [item for item in inputListHist]
  patchListHist(outputListHist,patchFun=patchFun)
  return outputListHist

"""
#too specialized, will probably be removed. use convolve1d instead.
def boxBlurredListHist(inputListHist,boxWidth,times=1):
  assert times > 0
  assert boxWidth%2
  #def calcBlurredValue(index):
  #  startIndex = min(max(index-(boxWidth>>1),0),len(inputListHist))
  #  endIndex = max(min(index+(boxWidth>>1),len(inputListHist)-1),0)
  #  assert startIndex >= 0
  #  assert endIndex >= 0
  #  usedBoxWidth = endIndex - startIndex + 1
  #  assert usedBoxWidth >= 0
  #  if usedBoxWidth == 0: #avoid division by zero.
  #    return 0
  #  return sum(inputListHist[startIndex:endIndex+1])/float(usedBoxWidth)
  
  workingListHist = [0 for i in range(boxWidth)] + inputListHist + [0 for i in range(boxWidth)]
  def calcBlurredValue(index,inputArr):
    startIndex = max(index-(boxWidth>>1),0)
    endIndex = min(index+(boxWidth>>1),len(inputArr)-1)
    assert 0 <= startIndex <= len(inputArr)
    assert 0 <= endIndex <= len(inputArr)-1
    usedBoxWidth = endIndex - startIndex + 1
    if startIndex > boxWidth and endIndex < len(inputArr)-boxWidth:
      assert usedBoxWidth == boxWidth
    assert usedBoxWidth >= 0
    if usedBoxWidth == 0: #avoid division by zero.
      return 0
    return sum(inputArr[startIndex:endIndex+1])/float(usedBoxWidth)
  result = [calcBlurredValue(i,workingListHist) for i in range(len(workingListHist))]
  #assert int(round(sum(result))) == int(round(sum(workingListHist)))
  for i in range(0,boxWidth):
    result[boxWidth+i] += result[i]
    result[-boxWidth-i-1] += result[-i-1]
  result = result[boxWidth:-boxWidth]
  if times == 1:
    return result
  else:
    return boxBlurredListHist(result,boxWidth,times=times-1)
"""

def normalDistribution(x,smallSigma,smallMu):
  return (1.0/(smallSigma*((2*pi)**0.5)))*(e**(-0.5*(((x-smallMu)/smallSigma)**2)))

def getGaussianBlurHillShape(shapeWidth,maxSmallSigma,cutoffOps="scale_to_1"):
  """
  scale_to_1 means the hill shape will be scaled until its sum is 1.
  add_to_1 means the hill shape will have the same amount added to every column until its sum is 1. This means multiplying by something like dx first. it might not be implemented because there is little need for it.
  sweep_to_ends means all curve area unaccounted for will be piled at either end of the shape as if the infinite tails of the curve were swept inwards with a broom.
  cut_to_ground subtracts the minimum value of all columns from each column so that the ends of the hill shape will be at y=0.
  """
  if type(cutoffOps) == str:
    cutoffOps = [cutoffOps]
  for cutoffOp in cutoffOps:
    assert cutoffOp in ["scale_to_1","add_to_1","sweep_to_ends","do_nothing","cut_to_ground"]
  hillShape = [normalDistribution(x-(shapeWidth>>1),(shapeWidth>>1)/float(maxSmallSigma),0) for x in range(shapeWidth)]
  for cutoffOp in cutoffOps:
    hillSum = sum(hillShape) #@ sometimes it isn't needed.
    if cutoffOp == "scale_to_1":
      scale = 1.0/hillSum
      for i in range(len(hillShape)):
        hillShape[i] *= scale
    elif cutoffOp == "add_to_1":
      addition = (1.0-hillSum)/float(shapeWidth)
      for i in range(len(hillShape)):
        hillShape[i] += addition
    elif cutoffOp == "sweep_to_ends":
      missing = (1.0-hillSum)
      hillShape[0] += missing/2.0
      hillShape[-1] += missing/2.0
    elif cutoffOp == "cut_to_ground":
      minimum = min(hillShape)
      for i in range(len(hillShape)):
        hillShape[i] -= minimum
  return hillShape

def convolved1d(inputArr,shapeArr):
  assert len(shapeArr)%2
  isInArr = (lambda srcArr, srcArrIndex: not (srcArrIndex < 0 or srcArrIndex >= len(srcArr)))
  getInArr = (lambda srcArr, srcArrIndex: 0 if not isInArr(srcArr,srcArrIndex) else srcArr[srcArrIndex])
  getShapeOverlapAmountCentered = (lambda mainArr, mainArrIndex, testShape: sum(testShape[testShapeIndex]*isInArr(mainArr,mainArrIndex+testShapeIndex-(len(testShape)>>1)) for testShapeIndex in range(len(testShape))))
  basicMultiplyCentered = (lambda mainArr, mainArrIndex, mulShape: sum(mulShape[mulShapeIndex]*getInArr(mainArr,mainArrIndex+mulShapeIndex-(len(mulShape)>>1)) for mulShapeIndex in range(len(mulShape))))
  fairMultiplyCentered = (lambda mainArr, mainArrIndex, mulShape: basicMultiplyCentered(mainArr,mainArrIndex,mulShape)/float(getShapeOverlapAmountCentered(mainArr,mainArrIndex,mulShape)))

  result = [0 for i in range(len(inputArr))]
  for i in range(len(result)):
    result[i] = fairMultiplyCentered(inputArr,i,shapeArr)
  return result



def scaledTanH(value,coef):
  return math.tanh(value/float(coef))*coef

def listHistToPrettyStr(inputListHist,lineLength=1024):
  alphabet = "zyxwvutsrqponmlkjihgfedcba=ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  alphabetCenter = alphabet.index("=")
  valueToChar = (lambda value: alphabet[alphabetCenter + int(round(scaledTanH(math.log(value,2),24)))])
  result = "["+"".join(valueToChar(item)+("\n" if i%lineLength==0 and i>0 else "") for i,item in enumerate(inputListHist))+"]"
  return result


def makeHuffmanCodecFromEntries(entries):
  huffmanTree = makeHuffmanTreeFromEntries(entries)
  huffmanReverseDict = treeToReverseDict(huffmanTree)
  #print(huffmanTree)
  #print(huffmanReverseDict)
  return CodecTools.Codec((lambda x: huffmanReverseDict[x]),(lambda y: accessTreeLocation(huffmanTree,y)),zeroSafe=(0 in huffmanReverseDict.keys()))

def makeHuffmanCodecFromFormula(chanceFun,minInputInt,maxInputInt):
  entries = sorted((chanceFun(value),value) for value in range(minInputInt,maxInputInt+1))
  return makeHuffmanCodecFromEntries(entries)

def makeHuffmanCodecFromDictHist(inputDictHist,chanceExtractionFun=None):
  if chanceExtractionFun == None:
    chanceExtractionFun = (lambda x: x)
  entries = sorted((chanceExtractionFun(value),key) for key,value in inputDictHist.items())
  return makeHuffmanCodecFromEntries(entries)

def makeHuffmanCodecFromListHist(inputListHist,doPatch=True):
  workingListHist = patchedListHist(inputListHist) if doPatch else inputListHist
  entries = [(item,i) for i,item in enumerate(workingListHist)]
  return makeHuffmanCodecFromEntries(entries)

