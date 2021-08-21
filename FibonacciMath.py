"""

FibonacciMath.py by John Dorsey.

FibonacciMath.py contains tools for generating different orders of Fibonacci sequences.

"""

import collections

import PyGenTools
from PyGenTools import arrTakeOnly, genTakeOnly, arrTakeLast




def unwrapArr(inputArr,startIndex):
  assert startIndex < len(inputArr)
  assert startIndex >= 0
  return inputArr[startIndex:] + inputArr[:startIndex]




def getEnbonacciStartArr(order=2):
  assert order > 1
  return [0 for i in range(order-1)] + [1]



def genEnbonacciNums(order=2,includeStartArr=True):
  assert order > 1
  startArr = getEnbonacciStartArr(order=order)
  i = 0
  while i < len(startArr):
    if includeStartArr:
      yield startArr[i]
    i += 1
  workingArr = [item for item in startArr]
  while True:
    i %= order
    workingArr[i] = sum(workingArr)
    yield workingArr[i]
    i += 1
  assert False, "genEnbonacciNums should never stop."


def applyNegativeEnumeration(inputArr, defaultValue=0, includeIndices=True):
  fillAmount = inputArr.count(None)
  if fillAmount > 0:
    for i in range(fillAmount):
      inputArr[fillAmount-i-1] = (-i-1, defaultValue) if includeIndices else defaultValue
      

def getEnboNumAtIndexAndPredecessors(n, order=2, includeIndices=True, indexStartArr=False):
  assert n >= -1
  enboNumGen = genTakeOnly(genEnbonacciNums(order=order,includeStartArr=True), (n if indexStartArr else n+order)+1)
  if includeIndices:
    enboNumGen = enumerate(enboNumGen, 0 if indexStartArr else -order)
  result = arrTakeLast(enboNumGen,order)
  assert len(result) == order
  if result.count(None) != 0:
    if includeIndices:
      assert indexStartArr, "disabling this is not possible yet."
    applyNegativeEnumeration(result,includeIndices=includeIndices)
  return result
  

def getEnboNumAboveValueAndPredecessors(value,order=2,includeIndices=True,indexStartArr=False):
  assert value >= 0
  enboNumGen = PyGenTools.genTakeUntil(genEnbonacciNums(order=order),(lambda testNum: testNum > value),stopSignalsNeeded=1)
  if includeIndices:
    enboNumGen = enumerate(enboNumGen,0 if indexStartArr else -order)
  result = arrTakeLast(enboNumGen,order)
  assert len(result) == order
  if result.count(None) != 0:
    if includeIndices:
      assert indexStartArr, "disabling this is not possible yet."
    applyNegativeEnumeration(result,includeIndices=includeIndices)
  return result


def genEnboNumsDescendingFromIndex(iEnd, order=2, includeIndices=True, indexStartArr=False):
  assert order > 1
  assert includeIndices
  workingArr = getEnboNumAtIndexAndPredecessors(iEnd, order=order, includeIndices=True, indexStartArr=indexStartArr)
  #print("FibonacciMath.genEnboNumsDescendingFromIndex: iEnd={}, order={}, workingArr={}.".format(iEnd,order,workingArr))
  return genEnboNumsDescendingFromPreset(workingArr, iEnd=None, order=order, includeIndices=includeIndices, indexStartArr=indexStartArr)


def genEnboNumsDescendingFromPreset(presetArr, iEnd=None, order=2, includeIndices=True, indexStartArr=False):
  assert order > 1
  presetArrIsEnumerated = hasattr(presetArr[-1],"__getitem__")
  if includeIndices:
    if iEnd==None:
      assert presetArrIsEnumerated, "iEnd must be specified somehow."
      #assert indexStartArr, "disabling this is not possible yet."
      iEnd = presetArr[-1][0]
  workingPresetArr = [item[1] for item in presetArr] if presetArrIsEnumerated else presetArr
  
  currentNums = collections.deque(workingPresetArr)
  while True:
    currentSum = sum(currentNums)
    leavingSuccessor = currentNums.pop()
    newPredecessor = leavingSuccessor-(currentSum-leavingSuccessor)
    currentSum += newPredecessor - leavingSuccessor
    yield (iEnd, leavingSuccessor) if includeIndices else leavingSuccessor
    if leavingSuccessor == 1:
      return
    if includeIndices:
      iEnd -= 1
    currentNums.appendleft(newPredecessor)

def genEnboNumsDescendingFromValue(value, order=2, includeIndices=True, indexStartArr=False):
  presetArr = getEnboNumAboveValueAndPredecessors(value, order=order, includeIndices=True, indexStartArr=indexStartArr)
  #print("getEnboNumsDescendingFromValue: (value,order,presetArr)=" + str((value,order,presetArr))+".")
  return genEnboNumsDescendingFromPreset(presetArr, iEnd=None, order=order, includeIndices=includeIndices, indexStartArr=indexStartArr)






assert getEnbonacciStartArr(order=2) == [0,1]
assert getEnbonacciStartArr(order=3) == [0,0,1]


assert arrTakeOnly(genEnbonacciNums(order=2),8) == [0,1,1,2,3,5,8,13]
assert arrTakeOnly(genEnbonacciNums(order=3),8) == [0,0,1,1,2,4,7,13]









