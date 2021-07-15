"""

Codes.py by John Dorsey.

Codes.py contains tools for encoding and decoding universal codes like fibonacci coding, elias gamma coding, elias delta coding, and unary coding.

"""

import CodecTools
from PyGenTools import isGen, makeGen, makeArr, arrTakeOnly, ExhaustionError



fibNums = [1,1]

def expandFibNums():
  for i in range(256):
    fibNums.append(fibNums[-1]+fibNums[-2])

expandFibNums()

def genFibNums():
  i = 0
  while i < len(fibNums):
    yield fibNums[i]
    i += 1
  a, b = (fibNums[-2],fibNums[-1])
  while True:
    a, b = (b, a+b)
    yield b

def getFibNumAtIndexAndPredecessor(n):
  assert n > 0
  if n < len(fibNums):
    return (fibNums[n-1],fibNums[n])
  ib, a, b = (len(fibNums)-1,fibNums[-2],fibNums[-1])
  while ib < n:
    ib, a, b = (ib+1, b, a+b)
  return (a,b)

def getFibNumAboveValueAndPredecessor(value):
  index = len(fibNums)-1
  if value < fibNums[index]:
    assert index - 1 >= 0
    while value < fibNums[index-1]:
      index -= 1
    assert fibNums[index-1] <= value
    assert fibNums[index] > value
    return ((index-1,fibNums[index-1]),(index,fibNums[index]))
  ib, a, b = (len(fibNums)-1,fibNums[-2],fibNums[-1])
  while b <= value:
    ib, a, b = (ib+1, b, a+b)
  return ((ib-1,a),(ib,b))

def genFibNumsDescendingFromIndex(ib):
  a, b = getFibNumAtIndexAndPredecessor(ib)
  yield (ib,b)
  ia = ib - 1
  while a > 1:
    yield (ia,a)
    a, b, ia = (b-a, a, ia-1)
  assert ia == 1
  assert a == 1
  yield (1,1)
  yield (0,1)
    
def genFibNumsDescendingFromValue(value):
  aTup, bTup = getFibNumAboveValueAndPredecessor(value)
  a, b = (aTup[1], bTup[1])
  ia, ib = (aTup[0], bTup[0])
  assert ia == ib - 1
  yield (ib,b)
  while a > 1:
    yield (ia,a)
    a, b, ia = (b-a, a, ia-1)
  assert ia == 1
  assert a == 1
  yield (1,1)
  yield (0,1)


def isInt(x):
  return type(x) in [int,long]
try:
  assert isInt(2**128)
except NameError:
  print("Codes: long type does not exist in this version of python, so isInt(x) will not check for it.")
  def isInt(x):
    return type(x) == int


class ParseError(Exception):
  pass




def intToBinaryBitArr(inputInt):
  return [int(char) for char in bin(inputInt)[2:]]

def binaryBitArrToInt(inputBitArr):
  return sum(2**i*inputBitArr[-1-i] for i in range(len(inputBitArr)))

def rjustArr(inputArr,length,fillItem=0,crop=False):
  if length < 0:
    raise ValueError("length cannot be negative.")
  return [fillItem for i in range(length-len(inputArr))] + (([] if length == 0 else inputArr[-length:]) if crop else inputArr)

def extendIntByBits(headInt,inputBitSeq,bitCount,onExhaustion="fail"):
  #this function eats up to bitCount bits from an inputBitSeq and returns an integer based on the input headInt followed by those generated bits.
  assert onExhaustion in ["fail","warn+partial","warn+None","partial","None"]
  assert type(headInt) == int
  assert type(bitCount) == int
  if bitCount == 0:
    return headInt
  result = headInt
  i = 0
  for inputBit in inputBitSeq:
    #print("new inputBit is " +str(inputBit) + ".")
    result = result*2 + inputBit
    #print("result is " + str(result))
    i += 1
    if i >= bitCount:
      return result
  if onExhaustion == "fail":
    raise ExhaustionError("Codes.extendIntByBits ran out of bits, and its onExhaustion action is \"fail\".")
  if "warn" in onExhaustion:
    print("Codes.extendIntByBits ran out of bits, and may return an undesired value.")
  if "partial" in onExhaustion:
    return result
  elif "None" in onExhaustion:
    return None
  else:
    raise ValueError("Codes.extendIntByBits: the value of keyword argument onExhaustion is invalid.")

def intSeqToBitSeq(inputIntSeq,inputFun,addDbgChars=False):
  justStarted = True
  for inputInt in inputIntSeq:
    if addDbgChars:
      if justStarted:
        justStarted = False
      else:
        yield ","
    for outputBit in inputFun(inputInt):
      yield outputBit

def bitSeqToIntSeq(inputBitSeq,inputFun):
  inputBitSeq = makeGen(inputBitSeq)
  outputInt = None
  while True:
    try:
      outputInt = inputFun(inputBitSeq)
    except ExhaustionError:
      #print("bitSeqToIntSeq is stopping.")
      return
    if outputInt == None:
      raise ParseError("The inputFun " + str(inputFun) + " did not properly terminate.")
    yield outputInt


def intToHybridCodeBitSeq(inputInt,prefixEncoderFun,zeroSafe,addDbgChars=False):
  #the resulting hybrid code is never zero safe, and the zeroSafe arg only refers to whether the prefix function is.
  bodyBitArr = intToBinaryBitArr(inputInt)[1:]
  prefixBitSeq = prefixEncoderFun(len(bodyBitArr) + (0 if zeroSafe else 1))
  for outputBit in prefixBitSeq:
    yield outputBit
  if addDbgChars:
    yield "."
  for outputBit in bodyBitArr:
    yield outputBit

def hybridCodeBitSeqToInt(inputBitSeq,prefixDecoderFun,zeroSafe):
  #the resulting hybrid code is never zero safe, and the zeroSafe arg only refers to whether the prefix function is.
  inputBitSeq = makeGen(inputBitSeq)
  prefixParseResult = prefixDecoderFun(inputBitSeq) - (0 if zeroSafe else 1)
  decodedValue = None
  try:
    decodedValue = extendIntByBits(1,inputBitSeq,prefixParseResult)
  except ExhaustionError:
    raise ParseError("Codes.hybridCodeBitSeqToInt ran out of bits before receiving as many as its prefix promised.")
  return decodedValue









def intToFibcodeBitArr(inputInt):
  #This function hasn't been replaced with or converted to a generator because doing so has no benefits - the bits must be generated in backwards order anyway, so it makes no sense to convert to a generator and then convert back.
  assert isInt(inputInt)
  assert inputInt >= 1
  result = []
  currentInt = inputInt
  if (inputInt.bit_length() < fibNums[-1].bit_length()):
    index = len(fibNums)-1
    while index >= 0:
      if fibNums[index] <= currentInt:
        currentInt -= fibNums[index]
        result.append(1)
      else:
        if len(result) > 0:
          result.append(0)
      index -= 1
  else:
    #justStarted = True #just for testing.
    for index,fibNum in genFibNumsDescendingFromValue(inputInt*2+10):
      #if justStarted:
      #  assert fibNum > currentInt
      #  justStarted = False
      if fibNum <= currentInt:
        currentInt -= fibNum
        result.append(1)
      else:
        if len(result) > 0:
          result.append(0)
  result.reverse()
  result.append(1)
  assert len(result) > 1
  return result[1:] #I don't know why this is necessary.


def intToFibcodeBitSeq(inputInt):
  #exists only for uniform naming of functions.
  for outputBit in intToFibcodeBitArr(inputInt):
    yield outputBit

def fibcodeBitSeqToInt(inputBitSeq):
  #this function only eats as much of the provided generator as it needs.
  inputBitSeq = makeGen(inputBitSeq)
  result = 0
  previousBit = None
  fibNumGen = genFibNums()
  currentFibNum = next(fibNumGen)
  assert currentFibNum == 1
  loopRan = False
  for i,inputBit in enumerate(inputBitSeq):
    loopRan = True
    if inputBit == 1 and previousBit == 1:
      return result
    previousBit = inputBit
    currentFibNum = next(fibNumGen)
    assert currentFibNum > 0
    result += currentFibNum * inputBit
  if result != 0:
    raise ParseError("Codes.fibcodeBitSeqToInt ran out of input bits midword.")
    #print("Codes.fibcodeBitSeqToInt ran out of input bits midword. Returning None instead of " + str(result) + ".")
    #return None
  if loopRan:
    assert False, "impossible error."
  else:
    raise ExhaustionError("Codes.fibcodeBitSeqToInt received an empty generator.")


def intSeqToFibcodeBitSeq(inputIntSeq):
  return intSeqToBitSeq(inputIntSeq,intToFibcodeBitArr)

def fibcodeBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq,fibcodeBitSeqToInt)




def intToUnaryBitSeq(inputInt):
  for i in range(inputInt):
    yield 0
  yield 1

def unaryBitSeqToInt(inputBitSeq):
  inputBitSeq = makeGen(inputBitSeq)
  result = 0
  for inputBit in inputBitSeq:
    if inputBit == 0:
      result += 1
    else:
      return result
  if result != 0:
    raise ParseError("Codes.unaryBitSeqToInt ran out of input bits midword.")
  raise ExhaustionError("Codes.unaryBitSeqToInt ran out of bits.")








def intToEliasGammaBitSeq(inputInt):
  assert inputInt >= 1
  for outputBit in intToUnaryBitSeq(inputInt.bit_length()-1):
    yield outputBit
  for outputBit in (int(char) for char in bin(inputInt)[3:]):
    yield outputBit

def eliasGammaBitSeqToInt(inputBitSeq):
  inputBitSeq = makeGen(inputBitSeq)
  prefixValue = unaryBitSeqToInt(inputBitSeq)
  assert prefixValue != None, "None-based termination is being phased out."
  #print("Codes.eliasGammaBitSeqToInt: prefixValue is " + str(prefixValue) + ".")
  try:
    return extendIntByBits(1,inputBitSeq,prefixValue)
  except ExhaustionError:
    raise ParseError("Codes.eliasGammaBitSeqToInt ran out of input bits before receiving as many as its unary prefix promised.")
  #print("Codes.eliasGammaBitSeqToInt: result is " + str(result) + ".")


def intSeqToEliasGammaBitSeq(inputIntSeq):
  return intSeqToBitSeq(inputIntSeq,intToEliasGammaBitSeq)

def eliasGammaBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq,eliasGammaBitSeqToInt)




def intToEliasDeltaBitSeq(inputInt):
  assert inputInt >= 1
  payloadBits = intToBinaryBitArr(inputInt)[1:]
  for outputBit in intToEliasGammaBitSeq(len(payloadBits)+1):
    yield outputBit
  for outputBit in payloadBits:
    yield outputBit

def eliasDeltaBitSeqToInt(inputBitSeq):
  inputBitSeq = makeGen(inputBitSeq)
  prefixValue = eliasGammaBitSeqToInt(inputBitSeq)
  assert prefixValue != None, "None-based termination is being phased out."
  payloadBitCount = prefixValue - 1
  #print("payloadBitCount is " + str(payloadBitCount))
  try:
    return extendIntByBits(1,inputBitSeq,payloadBitCount)
  except ExhaustionError:
    raise ParseError("Codes.eliasDeltaBitSeqToInt ran out of input bits before receiving as many as its Elias Gamma prefix promised.")


def intSeqToEliasDeltaBitSeq(inputIntSeq):
  return intSeqToBitSeq(inputIntSeq,intToEliasDeltaBitSeq)

def eliasDeltaBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq,eliasDeltaBitSeqToInt)



#eliasGamaIota and eliasDeltaIota are two codings I created to store integers with a limited range by setting the prefix involved in regular elias codes to a fixed length.
#they are not perfect. When the maxInputInt looks like 10000010 and the prefix indicates that the body is 7 bits long, 7 bits are used to define the body when 2 would suffice.

def intToEliasGammaIotaBitSeq(inputInt,maxInputInt):
  assert inputInt > 0
  assert inputInt <= maxInputInt
  maxPayloadLength = len(bin(maxInputInt)[3:])
  prefixLength = len(bin(maxPayloadLength)[2:])
  payloadLength = len(bin(inputInt)[3:])
  assert payloadLength <= maxPayloadLength
  #print("maxPayloadLength="+str(maxPayloadLength))
  #print("prefixLength="+str(prefixLength))
  prefix = rjustArr(intToBinaryBitArr(payloadLength),prefixLength)
  assert len(prefix) == prefixLength
  result = prefix + intToBinaryBitArr(inputInt)[1:]
  for outputBit in result:
    yield outputBit

def eliasGammaIotaBitSeqToInt(inputBitSeq,maxInputInt):
  inputBitSeq = makeGen(inputBitSeq)
  maxPayloadLength = len(bin(maxInputInt)[3:])
  prefixLength = len(bin(maxPayloadLength)[2:])
  prefixValue = binaryBitArrToInt(arrTakeOnly(inputBitSeq,prefixLength,onExhaustion="fail"))
  assert prefixValue != None, "None-based termination is being phased out."
  try:
    return extendIntByBits(1,inputBitSeq,prefixValue)
  except ExhaustionError:
    raise ParseError("Codes.eliasGammaIotaBitSeqToInt ran out of input bits before receiving as many as its prefix promised.")
  

def intSeqToEliasGammaIotaBitSeq(inputIntSeq,maxInputInt):
  return intSeqToBitSeq(inputIntSeq,(lambda x: intToEliasGammaIotaBitSeq(x,maxInputInt)))

def eliasGammaIotaBitSeqToIntSeq(inputBitSeq,maxInputInt):
  return bitSeqToIntSeq(inputBitSeq,(lambda x: eliasGammaIotaBitSeqToInt(x,maxInputInt)))



def intToEliasDeltaIotaBitSeq(inputInt,maxInputInt):
  assert inputInt > 0
  assert inputInt <= maxInputInt
  maxBodyLength = len(bin(maxInputInt)[3:])
  result = intToHybridCodeBitSeq(inputInt,(lambda x: intToEliasGammaIotaBitSeq(x,maxBodyLength+1)),False)
  assert result != None
  return result

def eliasDeltaIotaBitSeqToInt(inputBitSeq,maxInputInt):
  assert maxInputInt > 0
  maxBodyLength = len(bin(maxInputInt)[3:])
  result = hybridCodeBitSeqToInt(inputBitSeq,(lambda x: eliasGammaIotaBitSeqToInt(x,maxBodyLength+1)),False)
  assert result != None
  return result


def intSeqToEliasDeltaIotaBitSeq(inputIntSeq,maxInputInt):
  return intSeqToBitSeq(inputIntSeq,(lambda x: intToEliasDeltaIotaBitSeq(x,maxInputInt)))

def eliasDeltaIotaBitSeqToIntSeq(inputBitSeq,maxInputInt):
  return bitSeqToIntSeq(inputBitSeq,(lambda x: eliasDeltaIotaBitSeqToInt(x,maxInputInt)))




def intToEliasGammaFibBitSeq(inputInt,addDbgChars=False):
  assert inputInt > 0
  result = intToHybridCodeBitSeq(inputInt,intToFibcodeBitSeq,False,addDbgChars=addDbgChars)
  assert result != None
  return result

def eliasGammaFibBitSeqToInt(inputBitSeq):
  result = hybridCodeBitSeqToInt(inputBitSeq,fibcodeBitSeqToInt,False)
  assert result != None
  return result

def intSeqToEliasGammaFibBitSeq(inputIntSeq):
  return intSeqToBitSeq(inputIntSeq,intToEliasGammaFibBitSeq)

def eliasGammaFibBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq,eliasGammaFibBitSeqToInt)



def intToEliasDeltaFibBitSeq(inputInt,addDbgChars=False):
  assert inputInt > 0
  result = intToHybridCodeBitSeq(inputInt,intToEliasGammaFibBitSeq,False,addDbgChars=addDbgChars)
  assert result != None
  return result

def eliasDeltaFibBitSeqToInt(inputBitSeq):
  result = hybridCodeBitSeqToInt(inputBitSeq,eliasGammaFibBitSeqToInt,False)
  assert result != None
  return result

def intSeqToEliasDeltaFibBitSeq(inputIntSeq):
  return intSeqToBitSeq(inputIntSeq,intToEliasDeltaFibBitSeq)

def eliasDeltaFibBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq,eliasDeltaFibBitSeqToInt)













"""
def compareEfficiencies(codecArr,valueGen):
  previousScores = [None for i in range(len(codecArr))]
  currentScores = [None for i in range(len(codecArr))]
  codecRecords = [[] for i in range(len(codecArr))]
  for testIndex,testValue in enumerate(valueGen):
    for ci,testCodec in enumerate(codecArr):
      previousScores[ci] = currentScores[ci]
      currentScores[ci] = len(makeArr(testCodec.encode(testValue)))
      if previousScores[ci] != currentScores[ci]:
        codecRecords[ci].append((testIndex,testValue,currentScores[ci]))
  return codecRecords
"""
def getNextSizeIncreaseBounded(numberCodec,startValue,endValue):
  assert startValue < endValue
  startLength = len(makeArr(numberCodec.encode(startValue)))
  endLength = len(makeArr(numberCodec.encode(endValue)))
  assert startLength <= endLength
  if startLength == endLength:
    return None
  if startValue + 1 == endValue:
    assert startLength < endLength
    return endValue
  midpoint = int((startValue+endValue)/2)
  assert midpoint not in [startValue,endValue]
  lowerResult = getNextSizeIncreaseBounded(numberCodec,startValue,midpoint)
  if lowerResult != None:
    return lowerResult
  upperResult = getNextSizeIncreaseBounded(numberCodec,midpoint,endValue)
  return upperResult


def getNextSizeIncreaseBoundedIterAction(numberCodec,startValue,endValue):
  assert startValue < endValue
  startLength = len(makeArr(numberCodec.encode(startValue)))
  endLength = len(makeArr(numberCodec.encode(endValue)))
  assert startLength <= endLength
  if startLength == endLength:
    return ("fail",None,startValue,endValue)
  if startValue + 1 == endValue:
    assert startLength < endLength
    return ("finished",endValue,None,None)
  midpoint = int((startValue+endValue)/2)
  assert midpoint not in [startValue,endValue]
  return ("recycle",None,startValue,midpoint)
  #return (None,midpoint,endValue)

def getNextSizeIncreaseBoundedIterative(numberCodec,startValue,endValue):
  result = None
  previousValues = (None,None)
  currentValues = (startValue,endValue)
  while True:
    result = getNextSizeIncreaseBoundedIterAction(numberCodec,currentValues[0],currentValues[1])
    if result[0] == "finished":
      return result[1]
    elif result[0] == "recycle":
      previousValues = currentValues
      currentValues = (result[2],result[3])
      assert currentValues[0] < currentValues[1]
      continue
    elif result[0] == "fail":
      currentValues = (result[3],previousValues[1])
      if not currentValues[0] < currentValues[1]:
        return None
      if currentValues[0] == currentValues[1]:
        return None
      previousValues = (None,None)
      assert currentValues[0] < currentValues[1]
      continue
  assert False

def getNextSizeIncrease(numberCodec,startValue):
  result = None
  i = 0
  try:
    while result == None:
      result = getNextSizeIncreaseBoundedIterative(numberCodec,startValue*(i+1),startValue*(i+2))
      i += 1
    if i > 2:
      print("getNextSizeIncrease: warning: i is " + str(i) + ".")
    return result
  except KeyboardInterrupt:
    raise KeyboardInterrupt("Codes.getNextSizeIncrease: i was " + str(i) + ".")


def compareEfficienciesLinear(codecDict,valueGen):
  previousScores = {}
  currentScores = {}
  codecHistory = {}
  recordHolderHistory = []
  for key in codecDict.keys():
    previousScores[key] = None
    currentScores[key] = None
    codecHistory[key] = []
  updateRankings = False
  for testIndex,testValue in enumerate(valueGen):
    for key in codecDict.keys():
      testCodec = codecDict[key]
      previousScores[key] = currentScores[key]
      currentScores[key] = (testIndex,testValue,len(makeArr(testCodec.encode(testValue))))
      if previousScores[key] != currentScores[key]:
        codecHistory[key].append((testIndex,testValue,currentScores[key]))
        updateRankings = True
    if updateRankings:
      updateRankings = False
      currentBest = min(currentScores.values())
      recordHolders = [key for key in codecDict.keys() if currentScores[key] == currentBest]
      if len(recordHolderHistory) == 0 or recordHolders != recordHolderHistory[-1][3]:
        recordHolderHistory.append((testIndex,testValue,currentBest,recordHolders))
  return recordHolderHistory


def getEfficiencyDict(numberCodec,startValue,endValue):
  spot = startValue
  result = {}
  while True:
    spot = getNextSizeIncreaseBoundedIterative(numberCodec,spot,endValue)
    if spot == None:
      break
    result[spot] = len(makeArr(numberCodec.encode(spot)))
  return result


def compareEfficiencies(codecDict,startValue,endValue):
  codecEfficiencies = {}
  for key in codecDict.keys():
    codecEfficiencies[key] = getEfficiencyDict(codecDict[key],startValue,endValue)
  events = {}

  #construct majorEvents:
  for codecKey in codecEfficiencies.keys():
    for numberKey in codecEfficiencies[codecKey].keys():
      eventToAdd = (codecKey,numberKey,codecEfficiencies[codecKey][numberKey])
      if numberKey in events.keys():
        events[numberKey].append(eventToAdd)
      else:
        events[numberKey] = [eventToAdd]

  currentScores = dict([(key,(None,None)) for key in codecDict.keys()])
  recordHolderHistory = [(None,None,[])]
  #traverse majorEvents:
  for eventKey in sorted(events.keys()): #the eventKey is the unencoded integer input value.
    for currentEvent in events[eventKey]: #multiple events may happen at the same input value.
      assert len(currentEvent) == 3
      currentScores[currentEvent[0]] = (currentEvent[1],currentEvent[2]) #currentScores[name of codec] = (input value, length of code).
      currentBest = min(item[1] for item in currentScores.values() if item[1] != None)
      currentRecordHolders = [key for key in currentScores.keys() if currentScores[key][1] == currentBest]
      if currentRecordHolders != recordHolderHistory[-1][2]:
        #add new recordHolderHistory entry.
        recordHolderHistory.append((eventKey,currentBest,currentRecordHolders))
  return recordHolderHistory












print("defining codecs...")

codecs = {}

codecs["fibonacci"] = CodecTools.Codec(intToFibcodeBitSeq,fibcodeBitSeqToInt,zeroSafe=False)
codecs["unary"] = CodecTools.Codec(intToUnaryBitSeq,unaryBitSeqToInt,zeroSafe=True)
codecs["eliasGamma"] = CodecTools.Codec(intToEliasGammaBitSeq,eliasGammaBitSeqToInt,zeroSafe=False)
codecs["eliasDelta"] = CodecTools.Codec(intToEliasDeltaBitSeq,eliasDeltaBitSeqToInt,zeroSafe=False)
codecs["eliasGammaIota"] = CodecTools.Codec(intToEliasGammaIotaBitSeq,eliasGammaIotaBitSeqToInt,zeroSafe=False)
codecs["eliasDeltaIota"] = CodecTools.Codec(intToEliasDeltaIotaBitSeq,eliasDeltaIotaBitSeqToInt,zeroSafe=False)
codecs["eliasGammaFib"] = CodecTools.Codec(intToEliasGammaFibBitSeq,eliasGammaFibBitSeqToInt,zeroSafe=False)
codecs["eliasDeltaFib"] = CodecTools.Codec(intToEliasDeltaFibBitSeq,eliasDeltaFibBitSeqToInt,zeroSafe=False)

codecs["inSeq_fibonacci"] = CodecTools.Codec(intSeqToFibcodeBitSeq,fibcodeBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasGamma"] = CodecTools.Codec(intSeqToEliasGammaBitSeq,eliasGammaBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasDelta"] = CodecTools.Codec(intSeqToEliasDeltaBitSeq,eliasDeltaBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasGammaIota"] = CodecTools.Codec(intSeqToEliasGammaIotaBitSeq,eliasGammaIotaBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasDeltaIota"] = CodecTools.Codec(intSeqToEliasDeltaIotaBitSeq,eliasDeltaIotaBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasGammaFib"] = CodecTools.Codec(intSeqToEliasGammaFibBitSeq,eliasGammaFibBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasDeltaFib"] = CodecTools.Codec(intSeqToEliasDeltaFibBitSeq,eliasDeltaFibBitSeqToIntSeq,zeroSafe=False)

#fibonacci coding is more efficient than eliasGamma coding for numbers 16..(10**60), so it's likely that eliasDeltaFib is more efficient than eliasDelta for numbers (2**15)..(2**(10**60-1)).
#eliasDelta coding is more efficient than fibonacci coding for numbers 317811..(10**60).
#it seems like eliasDeltaFib must be more efficient than EliasDelta eventually, but they trade blows all the way up to 10**606, with EDF seemingly being the only one able to break the tie.


print("performing over-eating tests...")

#the following 3 tests check to make sure functions that accept generators as arguments do not overeat from those generators.
testGen = makeGen(CodecTools.bitSeqToStrCodec.decode("10110011"))
assert fibcodeBitSeqToInt(testGen) == 4
assert makeArr(testGen) == [0,0,1,1]

testGen = makeGen([0,0,0,1,0,0,1])
assert unaryBitSeqToInt(testGen) == 3
assert makeArr(testGen) == [0,0,1]

testGen = makeGen([0,0,1,1,1,0,0,1])
assert eliasGammaBitSeqToInt(testGen) == 7
assert makeArr(testGen) == [0,0,1]



print("performing full codec tests...")

for testCodecName in ["fibonacci","unary","eliasGamma","eliasDelta"]:
  print("testing " + testCodecName)
  for testNum in [1,5,10,255,257,65535,65537,999999]:
    assert CodecTools.roundTripTest(codecs[testCodecName],testNum)

for testCodecName in ["inSeq_fibonacci","inSeq_eliasGamma","inSeq_eliasDelta"]:
  print("testing " + testCodecName)
  testArr = [1,2,3,4,5,100,1000,100,5,4,3,2,1]
  assert CodecTools.roundTripTest(codecs[testCodecName],testArr)

"""
for testCodecName in ["inStr_inSeq_fibonacci","inStr_inSeq_eliasGamma","inStr_inSeq_eliasDelta"]:
  print("testing " + testCodecName)
  testArr = [1,2,3,4,5,100,1000,100,5,4,3,2,1]
  testCodec = codecs[testCodecName]
  assert CodecTools.roundTripTest(testCodec,testArr) #to make sure there is nothing wrong with later tests in this block.
  pressData = testCodec.encode(testArr)
  assert type(pressData) == str
  reconstPlainData = [item for item in testCodec.decode(pressData)]
  assert reconstPlainData == testArr
"""


print("performing tests of Iota codings...")

assert CodecTools.roundTripTest(codecs["inSeq_eliasGammaIota"].clone(extraKwargs={"maxInputInt":15}),[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])


