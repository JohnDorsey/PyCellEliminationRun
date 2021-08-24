

import itertools

import PyGenTools
from PyGenTools import isGen, makeGen, genTakeOnly, arrTakeOnly, ExhaustionError
import FibonacciMath
import IntSeqMath


def getStopcodeLIndicesInEnbocode(inputBitArr, order=None):
  assert order > 1
  stopcode = [1 for i in range(order)]
  result = []
  i = 0
  while i+order <= len(inputBitArr):
    if inputBitArr[i:i+order] == stopcode:
      result.append(i)
      i += order
    else:
      i += 1
  return result
assert getStopcodeLIndicesInEnbocode([1,1,0,1,1,1,1],order=2) == [0,3,5]
assert getStopcodeLIndicesInEnbocode([0,1,1,1,1,1,1,1,1],order=3) == [1,4]


def getStopcodeRIndicesInEnbocode(inputBitArr, order=None):
  assert order > 1
  return [item + order - 1 for item in getStopcodeLIndicesInEnbocode(inputBitArr,order=order)]
assert getStopcodeRIndicesInEnbocode([1,1,0,1,1,1,1],order=2) == [1,4,6]
assert getStopcodeRIndicesInEnbocode([0,1,1,1,1,1,1,1,1],order=3) == [3,6]



def clearEnbocode(bitArrToFix, order):
  assert order > 1
  for i in range(len(bitArrToFix)):
    bitArrToFix[i] = 0
  clearEnbocodeEnd(bitArrToFix, order)


def clearEnbocodeEnd(bitArrToClear, order):
  assert order > 1
  for i in range(len(bitArrToClear)-order, len(bitArrToClear)):
    bitArrToClear[i] = 1 #@ redundant at least once.
  #@ temp:
  assert sum(bitArrToClear) == order


def lengthenEnbocode(bitArrToFix, order=None):
  #lengthen enbocode by 1 bit and then clear it. Mainly for use in incrementEnbocode.
  assert order > 1
  bitArrToFix.append(-123456789) #this number should not show up anywhere else. clearEnbocode should overwrite it.
  clearEnbocode(bitArrToFix, order)
  

def finishLTRBinAddition(bitArrToFinish):
  #finish binary incrementation by interpreting a 2 as a place where the bit must flip over to 0 and carry a 1. mainly for use in incrementEnbocode.
  #this could all be replaced by making a bit set class based on an integer.
  while 2 in bitArrToFinish: #@ slow.
    for i in range(len(bitArrToFinish)-1):
      if bitArrToFinish[i] == 2:
        bitArrToFinish[i] = 0
        bitArrToFinish[i+1] += 1 #carry the 1.
    i = len(bitArrToFinish)-1
    if bitArrToFinish[i] == 2:
      bitArrToFinish[i] = 0
      bitArrToFinish.append(1) #carry the 1 and lengthen the number.


def incrementEnbocode(inputBitArr, order=None):
  assert order > 1
  originalLength = len(inputBitArr)
  inputBitArr[0] += 1
  finishLTRBinAddition(inputBitArr)
  if originalLength > order: #because the following test is not valid for the lowest possible enbocode.
    assert len(inputBitArr) == originalLength, "the length should not have changed yet. (inputBitArr,order)={}.".format((inputBitArr, order))
  if len(inputBitArr) > originalLength:
    assert len(inputBitArr) == originalLength+1, "the length should not have changed so much. (inputBitArr,order)={}.".format((inputBitArr, order))
    clearEnbocode(inputBitArr,order=order) #the enbocode simply grew during incrementation. This ensures that it is a valid enbocode before returning.
    return
  while True:
    stopcodeEndIndices = getStopcodeRIndicesInEnbocode(inputBitArr, order=order)
    if len(stopcodeEndIndices) == 1:
      if stopcodeEndIndices[0] == len(inputBitArr) - 1: #if perfectly valid...
        return
      if stopcodeEndIndices[0] == len(inputBitArr) - 2:
        lengthenEnbocode(inputBitArr,order=order)
        return
    #a new stopcode has been formed and needs to be corrected.
    assert len(stopcodeEndIndices) >= 1
    inputBitArr[stopcodeEndIndices[0]+1] += 1
    for i in range(stopcodeEndIndices[0]+1):
      inputBitArr[i] = 0
    finishLTRBinAddition(inputBitArr)
  assert False, "impossible error."
  
testArr = [1,1]
incrementEnbocode(testArr,order=2)
assert testArr == [0,1,1]
testArr = [0,1,0,1,1]
incrementEnbocode(testArr,order=2)
assert testArr == [0,0,0,0,1,1]
testArr = [1,1,1]
incrementEnbocode(testArr,order=3)
assert testArr == [0,1,1,1]
testArr = [1,0,1,0,1,1,1]
incrementEnbocode(testArr,order=3)
assert testArr == [0,1,1,0,1,1,1]
incrementEnbocode(testArr,order=3)
assert testArr == [0,0,0,0,0,1,1,1]
del testArr


def genEnbocodeBitArrs(order=None):
  workingBitArr = [1 for i in range(order)]
  while True:
    yield [outputBit for outputBit in workingBitArr] #make a copy!
    incrementEnbocode(workingBitArr,order=order)
    
testArr = arrTakeOnly(genEnbocodeBitArrs(order=2),12)
testArrCorrect = [[1,1],[0,1,1],[0,0,1,1],[1,0,1,1],[0,0,0,1,1],[1,0,0,1,1],[0,1,0,1,1],[0,0,0,0,1,1],[1,0,0,0,1,1],[0,1,0,0,1,1], [0,0,1,0,1,1], [1,0,1,0,1,1]]
if not testArr == testArrCorrect:
  print("testArr={}, testArrCorrect={}.".format(testArr,testArrCorrect))
  assert False
testArr = arrTakeOnly(genEnbocodeBitArrs(order=3),14)
testArrCorrect = [[1,1,1],[0,1,1,1],[0,0,1,1,1],[1,0,1,1,1],[0,0,0,1,1,1],[1,0,0,1,1,1],[0,1,0,1,1,1],[1,1,0,1,1,1],[0,0,0,0,1,1,1], [1,0,0,0,1,1,1], [0,1,0,0,1,1,1], [1,1,0,0,1,1,1], [0,0,1,0,1,1,1], [1,0,1,0,1,1,1]]
if not testArr == testArrCorrect:
  print("testArr={}, testArrCorrect={}.".format(testArr,testArrCorrect))
  assert False
del testArr
del testArrCorrect



def genRoundEnbocodeValueOffsetsSlow(order=None):
  print("Codes.genRoundEnbocodeValueOffsetsSlow: Warning: this method is unreasonably slow and should not be used outside of testing.")
  print("Codes.genRoundEnbocodeValueOffsetsSlow: WARNING: not thoroughly tested!")
  for expected,actual in itertools.izip(FibonacciMath.genEnbonacciNums(order=order,skipStart=True), genRoundEnbocodeValuesSlow(order=order)):
    yield expected-actual


def genRoundEnbocodeValueOffsets(order=None):
  #gives the difference between an expected enbocode column value and its actual value when it is first used because of the first bit of the stopcode.
  if order != 3:
    print("Codes.genRoundEnbocodeValueOffsets: WARNING: not tested for orders other than 3!")
  return (item[0] for item in IntSeqMath.genTrackInstantSum(FibonacciMath.genEnbonacciNums(order=order)))
  
  
  
def genRoundEnbocodeValuesSlow(order=None):
  print("Codes.genRoundEnbocodeValuesSlow: Warning: this method is unreasonably slow and should not be used outside of testing.")
  for index,bitArr in enumerate(genEnbocodeBitArrs(order=order)):
    if isRoundEnbocode(bitArr):
      value = index+1
      #print("Codes.genPureEnbocodeValuesSlow: {} is pure, yielding {}.".format(bitArr,value))
      yield value
      
      
def genRoundEnbocodeValues(order=None):
  #tested for order 4, for first 20 results.
  yield 1
  for value, _ in IntSeqMath.genTrackInstantSum(FibonacciMath.genEnbonacciNums(order=order)):
    if value != 0:
      yield value + 1
      



def makeRoundEnbocodeOfLength(length, order):
  result = [0 for i in range(length)]
  clearEnbocodeEnd(result, order)
  return result


def isRoundEnbocode(inputBitArr):
  zeroCount = inputBitArr.count(0)
  oneCount = inputBitArr.count(1)
  if zeroCount+oneCount == len(inputBitArr):
    if sum(inputBitArr[-oneCount:])==oneCount:
      return True
  return False
        
        
def predictEnbocodeTotalLength(inputInt, order):
  assert inputInt > 0
  assert order > 1
  lengthsAndValuesGen = enumerate(itertools.takewhile((lambda x: x <= inputInt), genRoundEnbocodeValues(order=order)), order)
  result = PyGenTools.getLast(lengthsAndValuesGen)[0]
  return result
    
    
def predictEnbocodeBodyLength(inputInt, order):
  assert order > 1
  assert inputInt > 0
  return predictEnbocodeTotalLength(inputInt, order) - order


def truncatedEnbocodeBitSeq(inputBitGen, order=None, maxInputInt=None): #does not detect some parse errors, such as when two codes are called one code bit arr.
  assert order > 1
  assert maxInputInt > 1
  inputBitGen = makeGen(inputBitGen)
  bodyLength = predictEnbocodeBodyLength(maxInputInt, order)
  assert bodyLength >= 0
  return genTakeOnly(inputBitGen, bodyLength, onExhaustion="partial")

  
def detruncatedEnbocodeBitSeq(inputBitGen, order=None, maxInputInt=None):
  assert isGen(inputBitGen) #debug
  #1/0
  assert order > 1
  assert maxInputInt > 1
  inputBitGen = makeGen(inputBitGen)
  bodyLength = predictEnbocodeBodyLength(maxInputInt, order)
  i = None
  for i in range(bodyLength):
    try:
      yield next(inputBitGen)
    except StopIteration:
      #print("Codes.detruncatedEnbocodeBitSeq: warning: inputBitGen ran out. Maybe this shouldn't happen.")
      if i==0:
        #print("Codes.detruncatedEnbocodeBitSeq: raising ExhaustionError because the inputBitGen was empty.")
        raise ExhaustionError("inputBitGen was empty.")
      break
  for ii in range(order):
    #print("Codes.detruncatedEnbocodeBitSeq: notice: yielding a stopcode bit.")
    yield 1
  print("Codes.detruncatedEnbocodeBitSeq: warning: overdrawn.")
  #yield None
