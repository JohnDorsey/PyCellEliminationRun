"""

Codes.py by John Dorsey.

Codes.py contains tools for encoding and decoding universal codes like fibonacci coding, elias gamma coding, elias delta coding, and unary coding.

"""

import CodecTools
import FibonacciMath
from PyGenTools import isGen, makeGen, makeArr, arrTakeOnly, genSkipFirst, ExhaustionError




class ParseError(Exception):
  pass





def rjustArr(inputArr,length,fillItem=0,crop=False):
  if length < 0:
    raise ValueError("length cannot be negative.")
  return [fillItem for i in range(length-len(inputArr))] + (([] if length == 0 else ([inputArr[-1]] if length == 1 else inputArr[-length:])) if crop else inputArr)


def arrEndsWith(inputArr,testArr):
  testStartIndex = len(inputArr)-len(testArr)
  if testStartIndex < 0:
    raise ValueError("This test can't be performed because testArr is longer than inputArr.")
  return all((inputArr[testStartIndex+i]==testArr[i]) for i in range(len(testArr)))


def isInt(x):
  return type(x) in [int,long]
try:
  assert isInt(2**128)
except NameError:
  print("Codes: long type does not exist in this version of python, so isInt(x) will not check for it.")
  def isInt(x):
    return type(x) == int




def intToBinaryBitArr(inputInt):
  return [int(char) for char in bin(inputInt)[2:]]

def binaryBitArrToInt(inputBitArr):
  return sum(2**i*inputBitArr[-1-i] for i in range(len(inputBitArr)))


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









def intToEnbocodeBitArr(inputInt,order=2):
  #This function hasn't been replaced with or converted to a generator because doing so has no benefits - the bits must be generated in backwards order anyway, so it makes no sense to convert to a generator and then convert back.
  assert order == 2 #because the current design of this method is completely unable to handle other orders.
  assert isInt(inputInt)
  assert inputInt >= 1
  result = []
  currentInt = inputInt
  for index,enboNum in FibonacciMath.genEnboNumsDescendingFromValue(inputInt*2+10,order=order):

    #print("intToEnbocodeBitArr: before loop body: (inputInt,order,index,enboNum,result)=" + str((inputInt,order,index,enboNum,result)) + ".")
    if index < order:
      #print("intToEnbocodeBitArr: breaking loop because of index.")
      break
    assert enboNum > 0
    if enboNum <= currentInt:
      #print("intToEnbocodeBitArr: enboNum will be subtracted from currentInt. (currentInt,index,enboNum)"+str((currentInt,index,enboNum))+".")
      currentInt -= enboNum
      result.append(1)
      #print("intToEnbocodeBitArr: enboNum has been subtracted from currentInt. (currentInt,index,enboNum,result)"+str((currentInt,index,enboNum,result))+".")
    else:
      if len(result) > 0:
        result.append(0)
        #print("intToEnbocodeBitArr: nothing has been subtracted from currentInt this time around. (currentInt,index,enboNum,result)"+str((currentInt,index,enboNum,result))+".")
    if currentInt == 0:
      #print("intToEnbocodeBitArr: it is possible to break the loop because of currentInt. The loop won't be broken.")
      pass
    #print("intToEnbocodeBitArr: after loop body: (inputInt,order,index,enboNum,result)=" + str((inputInt,order,index,enboNum,result)) + ".")

  result.reverse()
  assert len(result) > 0
  result.extend([1 for i in range(order-1)])
  assert len(result) >= order
  #return result[1:] #I don't know why this is necessary.
  
  #print("fix intToEnbocodeBitArr")
  if order == 2:
    if inputInt <= 4:
      if not result == [None,[1,1],[0,1,1],[0,0,1,1],[1,0,1,1]][inputInt]:
        raise ValueError("intToEnbocodeBitArr: {}->{}".format(inputInt,result)+".")
  elif order == 3:
    if inputInt <= 4:
      if not result == [None,[1,1,1],[0,1,1,1],[0,0,1,1,1],[1,0,1,1,1]][inputInt]:
        raise ValueError("intToEnbocodeBitArr: order={}, {}->{}".format(order, inputInt,result)+".")
  
  #print("intToEnbocodeBitArr: before final tests: (inputInt,order,result)=" + str((inputInt,order,result)) + ".")

  if len(result) > order:
    if not arrEndsWith(result,[0]+[1 for i in range(order)]):
      print("intToEnbocodeBitArr: result ends the wrong way. This is never supposed to happen. (inputInt,order,result)=" + str((inputInt,order,result)) + ".")
  return result



def intToEnbocodeBitSeq(inputInt,order=2):
  #exists only for uniform naming of functions.
  assert order == 2 #to reflect the fact that the current design of this method is completely unable to handle other orders.
  for outputBit in intToEnbocodeBitArr(inputInt,order=order):
    yield outputBit



def enbocodeBitSeqToInt(inputBitSeq,order=2):
  #this function only eats as much of the provided generator as it needs.
  #it used to be more memory efficient by not keeping a bitHistory, but that design made upgrading to any-order fibonacci harder, so it was written out. It could be brought back now.
  assert order == 2 #to reflect the fact that the current design of this method is completely unable to handle other orders.
  
  assert order > 1
  inputBitSeq = makeGen(inputBitSeq)
  bitHistory = [] 
  for i,inputBit in enumerate(inputBitSeq):
    assert inputBit in [0,1]
    bitHistory.append(inputBit)
    if sum(bitHistory[-order:]) == order:
      break
  
  #print("enbocodeBitSeqToInt: (order,bitHistory)="+str((order,bitHistory))+".")

  if len(bitHistory) == 0:
    raise ExhaustionError("enbocodeBitSeqToInt received an empty inputBitSeq.")
  if len(bitHistory) > 0 and len(bitHistory) < order:
    raise ParseError("The inputBitSeq did not end in an enbonacci code.")
  
  #temp:
  if len(bitHistory) >= order:
    assert arrEndsWith(bitHistory,[1 for i in range(order)])
  if len(bitHistory) >= order+1:
    assert arrEndsWith(bitHistory,[0]+[1 for i in range(order)])

  enboNumGen = genSkipFirst(FibonacciMath.genEnbonacciNums(order),order) #@ cleanup.
  result = 0
  for i,currentEnboNum in enumerate(enboNumGen): #this might generate one more enboNum than is needed.
    assert currentEnboNum > 0
    if i == len(bitHistory) - (order-1): #if this was the last bit that wasn't part of the stopcode...
      break
    result += currentEnboNum * bitHistory[i]

  #temp:
  #print("fix enbocodeBitSeqToInt.")
  if all(bitHistory):
    assert len(bitHistory) == order
    assert result == 1
  elif bitHistory == [0] + [1 for i in range(order)]:
    assert result == 2
  elif bitHistory == [0,0] + [1 for i in range(order)]:
    assert result == 3
  assert result > 0
  return result
  """
  if result != 0:
    raise ParseError("Codes.enbocodeBitSeqToInt ran out of input bits midword.")
  else:
    if loopRan:
      assert False, "Codes.enbocodeBitSeqToInt crashed."
    else:
      raise ExhaustionError("Codes.enbocodeBitSeqToInt received an empty generator.")
  """



def intSeqToEnbocodeBitSeq(inputIntSeq,order=2):
  return intSeqToBitSeq(inputIntSeq,(lambda x: intToEnbocodeBitSeq(x,order=order)))

def enbocodeBitSeqToIntSeq(inputBitSeq,order=2):
  return bitSeqToIntSeq(inputBitSeq,(lambda x: enbocodeBitSeqToInt(x,order=order)))



#temp
def intToFibcodeBitSeq(inputInt):
  return intToEnbocodeBitSeq(inputInt,order=2)
def fibcodeBitSeqToInt(inputBitSeq):
  return enbocodeBitSeqToInt(inputBitSeq,order=2)



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

codecs["enbonacci"] = CodecTools.Codec(intToEnbocodeBitSeq,enbocodeBitSeqToInt,zeroSafe=False)
codecs["unary"] = CodecTools.Codec(intToUnaryBitSeq,unaryBitSeqToInt,zeroSafe=True)
codecs["eliasGamma"] = CodecTools.Codec(intToEliasGammaBitSeq,eliasGammaBitSeqToInt,zeroSafe=False)
codecs["eliasDelta"] = CodecTools.Codec(intToEliasDeltaBitSeq,eliasDeltaBitSeqToInt,zeroSafe=False)
codecs["eliasGammaIota"] = CodecTools.Codec(intToEliasGammaIotaBitSeq,eliasGammaIotaBitSeqToInt,zeroSafe=False)
codecs["eliasDeltaIota"] = CodecTools.Codec(intToEliasDeltaIotaBitSeq,eliasDeltaIotaBitSeqToInt,zeroSafe=False)
codecs["eliasGammaFib"] = CodecTools.Codec(intToEliasGammaFibBitSeq,eliasGammaFibBitSeqToInt,zeroSafe=False)
codecs["eliasDeltaFib"] = CodecTools.Codec(intToEliasDeltaFibBitSeq,eliasDeltaFibBitSeqToInt,zeroSafe=False)

codecs["inSeq_enbonacci"] = CodecTools.Codec(intSeqToEnbocodeBitSeq,enbocodeBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasGamma"] = CodecTools.Codec(intSeqToEliasGammaBitSeq,eliasGammaBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasDelta"] = CodecTools.Codec(intSeqToEliasDeltaBitSeq,eliasDeltaBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasGammaIota"] = CodecTools.Codec(intSeqToEliasGammaIotaBitSeq,eliasGammaIotaBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasDeltaIota"] = CodecTools.Codec(intSeqToEliasDeltaIotaBitSeq,eliasDeltaIotaBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasGammaFib"] = CodecTools.Codec(intSeqToEliasGammaFibBitSeq,eliasGammaFibBitSeqToIntSeq,zeroSafe=False)
codecs["inSeq_eliasDeltaFib"] = CodecTools.Codec(intSeqToEliasDeltaFibBitSeq,eliasDeltaFibBitSeqToIntSeq,zeroSafe=False)

codecs["fibonacci"] = codecs["enbonacci"].clone(extraKwargs={"order":2})
codecs["inSeq_fibonacci"] = codecs["inSeq_enbonacci"].clone(extraKwargs={"order":2})

FIBONACCI_ORDER_NICKNAMES = {"tribonacci":3,"tetranacci":4,"pentanacci":5,"hexanacci":6,"heptanacci":7,"octanacci":8,"enneanacci":9}

for orderName,order in FIBONACCI_ORDER_NICKNAMES.items():
  codecs[orderName] = codecs["enbonacci"].clone(extraKwargs={"order":order})
  codecs["inSeq_"+orderName] = codecs["inSeq_enbonacci"].clone(extraKwargs={"order":order})

#fibonacci coding is more efficient than eliasGamma coding for numbers 16..(10**60), so it's likely that eliasDeltaFib is more efficient than eliasDelta for numbers (2**15)..(2**(10**60-1)).
#eliasDelta coding is more efficient than fibonacci coding for numbers 317811..(10**60).
#it seems like eliasDeltaFib must be more efficient than EliasDelta eventually, but they trade blows all the way up to 10**606, with EDF seemingly being the only one able to break the tie.








print("performing over-eating tests...")

#the following 3 tests check to make sure functions that accept generators as arguments do not overeat from those generators.
testGen = makeGen(CodecTools.bitSeqToStrCodec.decode("11011"))
assert enbocodeBitSeqToInt(testGen,order=2) == 1
assert makeArr(testGen) == [0,1,1]

testGen = makeGen(CodecTools.bitSeqToStrCodec.decode("10110011"))
assert enbocodeBitSeqToInt(testGen,order=2) == 4
assert makeArr(testGen) == [0,0,1,1]

testGen = makeGen([0,0,0,1,0,0,1])
assert unaryBitSeqToInt(testGen) == 3
assert makeArr(testGen) == [0,0,1]

testGen = makeGen([0,0,1,1,1,0,0,1])
assert eliasGammaBitSeqToInt(testGen) == 7
assert makeArr(testGen) == [0,0,1]



print("performing full codec tests...")

for testCodecName in ["fibonacci","unary","eliasGamma","eliasDelta","eliasGammaFib","eliasDeltaFib"]:
  print("testing " + testCodecName + "...")
  for testNum in [1,5,10,255,257,65535,65537,999999]:
    assert CodecTools.roundTripTest(codecs[testCodecName],testNum)

for testCodecName in ["inSeq_fibonacci","inSeq_eliasGamma","inSeq_eliasDelta","inSeq_eliasGammaFib","inSeq_eliasDeltaFib"]:
  print("testing " + testCodecName + "...")
  testArr = [1,2,3,4,5,100,1000,1000000,1,1000,1,100,1,5,4,3,2,1]
  assert CodecTools.roundTripTest(codecs[testCodecName],testArr)

"""
for testCodecName in FIBONACCI_ORDER_NICKNAMES.keys():
  print("testing " + testCodecName + "...")
  for testNum in [1,5,10,255,257,65535,65537,999999]:
    print((testCodecName,testNum,CodecTools.roundTripTest(codecs[testCodecName],testNum)))
  testCodecName = "inSeq_" + testCodecName
  print("testing " + testCodecName + "...")
  testArr = [1,2,3,4,5,100,1000,1000000,1,1000,1,100,1,5,4,3,2,1]
  print((testCodecName,testArr,CodecTools.roundTripTest(codecs[testCodecName],testArr)))
"""


print("performing tests of Iota codings...")

assert CodecTools.roundTripTest(codecs["inSeq_eliasGammaIota"].clone(extraKwargs={"maxInputInt":15}),[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])


