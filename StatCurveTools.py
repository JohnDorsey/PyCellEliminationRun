"""

StatCurveTools.py by John Dorsey.

StatCurveTools.py contains tools for manipulating list histograms or other probability distribution data.

"""
import math
from math import pi,e
import IntArrMath
from PyGenTools import makeGen,makeArr



def patchListHist(inputListHist,holeMatchFun=None,patchFun=None,lowFix=None):
  #lowFix is the value to replace troublesome holes, like holes at the arr end.
  if len(inputListHist) == 0:
    print("StatCurveTools.patchListHist: Warning: received an empty inputListHist. no action will be taken.")
    return
  if holeMatchFun == None:
    holeMatchFun = (lambda x: x==None)
  if patchFun == None:
    patchFun = (lambda x1, x2, y1, y2, xHere: ((y1+y2)/4.0)/float(x2-x1-1))
  if lowFix == None: #None isn't allowed, so this kwarg is uninitialized.
    try:
      lowFix = min(value for value in inputListHist if value > 0)
    except ValueError:
      print("StatCurveTools.patchListHist: Warning: no nonzero integer values. giving up.")
      return
  assert not holeMatchFun(lowFix), "the lowFix value triggers the hole match function, so patchListHist can't proceed."
  if holeMatchFun(inputListHist[0]): #patchFun usage can't fix this, so fix it here.
    inputListHist[0] = lowFix
  if holeMatchFun(inputListHist[-1]): #patchFun usage can't fix this, so fix it here.
    inputListHist[-1] = lowFix
  for index in range(len(inputListHist)-1):
    if ((not holeMatchFun(inputListHist[index])) and holeMatchFun(inputListHist[index+1])):
      holeStartIndex = index
      holeStartY = inputListHist[index]
      holeEndIndex = None
      for testHoleEndIndex in range(holeStartIndex+1,len(inputListHist)):
        if not holeMatchFun(inputListHist[testHoleEndIndex]):
          holeEndIndex = testHoleEndIndex
          break
      assert holeEndIndex != None, "this should have been changed by now!"
      holeEndY = inputListHist[holeEndIndex]
      assert holeEndY != None
      for indexToPatch in range(holeStartIndex+1,holeEndIndex):
        inputListHist[indexToPatch] = patchFun(holeStartIndex,holeEndIndex,holeStartY,holeEndY,indexToPatch)
  assert None not in inputListHist
  noHoles = True
  for item in inputListHist:
    if holeMatchFun(item):
      noHoles = False
  if not noHoles:
    print("StatCurveTools.patchListHist: Warning: even though there are no more None values, the holeMatchFun (probably a custom one) identified holes.")


def patchedListHist(inputListHist,holeMatchFun=None,patchFun=None):
  outputListHist = [item for item in inputListHist]
  patchListHist(outputListHist,holeMatchFun=holeMatchFun,patchFun=patchFun)
  return outputListHist


def genMatchRunLengths(inputSeq,matchFun):
  """
  iterates through an input sequence and generates the lengths of runs of items which satisfy matchFun(item)==True.
  """
  currentRunLength = 0
  #matchRunLengths = [0]
  for currentItem in inputSeq:
    if matchFun(currentItem):
      currentRunLength += 1
    else:
      if currentRunLength > 0:
        yield currentRunLength
        currentRunLength = 0


def genMergeParallelSeqsUsingSetTool(inputSeqSeq,mergeTool):
  workingGenArr = [makeGen(inputSeq) for inputSeq in inputSeqSeq]
  while True:
    currentSet = set()
    for inputSeq in workingGenArr:
      try:
        itemToAdd = next(inputSeq)
      except StopIteration: #@ it's slow to do this over and over.
        continue
      currentSet.add(itemToAdd)
    if len(currentSet) == 0:
      return
    yield mergeTool(currentSet)


def makeAutoBlurredListHist(inputListHist,overdoLevel=2):
  assert type(inputListHist) == list
  assert overdoLevel >= 1
  #this might just be a faster, more complicated way of finding the mean hole width.
  #population = 1.0-(inputListHist.count(None)/float(len(inputListHist)))
  #populationBasedHillWidth = int(round(1.0/population))
  #populationBasedHillWidth += 1-(populationBasedHillWidth%2)
  holeWidths = makeArr(genMatchRunLengths(inputListHist,(lambda x: x in [None,0,0.0])))
  medianHoleWidth = 0
  if len(holeWidths) > 0:
    medianHoleWidth = int(round(IntArrMath.median(holeWidths)))
  medGaussHill = getGaussianBlurHillShape(medianHoleWidth*overdoLevel+1+2,3*overdoLevel,cutoffOps="cut_to_ground") #the +1 makes the width odd as is necessary, the +2 makes up for cutting to ground.
  meanHoleWidth = 0
  if len(holeWidths) > 0:
    meanHoleWidth = int(round(IntArrMath.mean(holeWidths)))
  meanGaussHill = getGaussianBlurHillShape(meanHoleWidth*overdoLevel+1+2,3*overdoLevel,cutoffOps="cut_to_ground")
  #print((medianHoleWidth,meanHoleWidth))
  patchedInput = patchedListHist(inputListHist,holeMatchFun=(lambda xx: xx in [None,0,0.0]))
  medGaussBlurredInput = convolved1d(inputListHist,medGaussHill)
  meanGaussBlurredInput = convolved1d(inputListHist,medGaussHill)
  result = makeArr(genMergeParallelSeqsUsingSetTool([patchedInput,medGaussBlurredInput,meanGaussBlurredInput],IntArrMath.mean))
  #print(patchedInput)
  #print(medGaussBlurredInput)
  #print(result)
  return result
  
  
def extendListHistMinimally(inputList, targetLength, valueSuggestion=1):
  assert type(inputList) == list
  if len(inputList) >= targetLength:
    return
  minNonZeroValue = min(item for item in inputList if item > 0)
  extensionValue = float(min(valueSuggestion,minNonZeroValue))
  inputList.extend((extensionValue for i in range(len(inputList),targetLength)))


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
  alphabet = "?zyxwvutsrqponmlkjihgfedcba=ABCDEFGHIJKLMNOPQRSTUVWXYZ!"
  alphabetCenter = alphabet.index("=")
  valueToChar = (lambda value: alphabet[alphabetCenter + int(round(scaledTanH(math.log(value,2),26)))])
  #assert valueToChar(2**1024)=="Z"
  result = "["+"".join(valueToChar(item)+("\n" if i%lineLength==0 and i>0 else "") for i,item in enumerate(inputListHist))+"]"
  return result
  
  
  
  
  
  
def vectorSum(vectors): #@ slow.
  result = [0 for i in range(max(len(vector) for vector in vectors))]
  for vector in vectors:
    for i,item in enumerate(vector):
      result[i] += item
  return result
  
def scaleVector(vector,value):
  for i in range(len(vector)):
    vector[i] *= value

def scaledVector(vector,value):
  return [item*value for item in vector]
  
