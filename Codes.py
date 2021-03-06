"""

Codes.py by John Dorsey.

Codes.py contains tools for encoding and decoding universal codes like fibonacci coding, elias gamma coding, elias delta coding, and unary coding.

"""




import itertools

import CodecTools
from CodecTools import ParseError

import FibonacciMath
import FibonacciCodeTools

import PyGenTools
from PyGenTools import makeGen, makeArr, arrTakeOnly, genSkipFirst, ExhaustionError, IterationFailure
from PyArrTools import rjustedArr, arrEndsWith









def isInt(x):
  return type(x) in [int, long] # noqa
try:
  assert isInt(2**128)
except NameError:
  print("Codes: long type does not exist in this version of python, so isInt(x) will not check for it.")
  def isInt(x):
    return type(x) == int





def intToBinaryBitArr(inputInt):
  return [int(char) for char in bin(inputInt)[2:]]

def binaryBitArrToInt(inputBitArr):
  result = 0
  for i in range(len(inputBitArr)):
    assert inputBitArr[-1-i] in [0,1]
    result += 2**i*inputBitArr[-1-i]
  return result
  
  
def intToBinaryBitSeq(inputInt, maxInputInt=None):
  assert inputInt >= 0
  assert maxInputInt > 0
  assert inputInt <= maxInputInt
  bodyLength = maxInputInt.bit_length()
  return makeGen(rjustedArr(intToBinaryBitArr(inputInt), bodyLength))
  
def binaryBitSeqToInt(inputBitSeq, maxInputInt=None):
  assert maxInputInt > 0
  bodyLength = maxInputInt.bit_length()
  return binaryBitArrToInt(arrTakeOnly(inputBitSeq, bodyLength))
  

def extendIntByBits(headInt, inputBitSeq, bitCount, onExhaustion="fail"):
  #this function eats up to bitCount bits from an inputBitSeq and returns an integer based on the input headInt followed by those generated bits.
  assert onExhaustion in ["fail","warn+partial","warn+None","partial","None"]
  assert type(headInt) == int
  assert type(bitCount) == int
  if bitCount == 0:
    return headInt
  result = headInt
  i = 0
  for inputBit in inputBitSeq:
    assert inputBit in [0,1]
    #print("new inputBit is " +str(inputBit) + ".")
    result = result*2 + inputBit
    #print("result is " + str(result))
    i += 1
    if i >= bitCount:
      return result
  if onExhaustion == "fail":
    raise IterationFailure("Codes.extendIntByBits ran out of bits, and its onExhaustion action is \"fail\".")
  if "warn" in onExhaustion:
    print("Codes.extendIntByBits ran out of bits, and may return an undesired value.")
  if "partial" in onExhaustion:
    return result
  elif "None" in onExhaustion:
    return None
  else:
    raise ValueError("Codes.extendIntByBits: the value of keyword argument onExhaustion is invalid.")


def intSeqToBitSeq(inputIntSeq, inputFun, addDbgChars=False):
  justStarted = True
  for inputInt in inputIntSeq:
    if addDbgChars:
      if justStarted:
        justStarted = False
      else:
        yield ","
    for outputBit in inputFun(inputInt):
      yield outputBit

def bitSeqToIntSeq(inputBitSeq, inputFun):
  #print("bitSeqToIntSeq called.")
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
    #print("bitSeqToIntSeq: yielding {}.".format(outputInt))
    yield outputInt


def intToHybridCodeBitSeq(inputInt, prefixEncoderFun, zeroSafe, addDbgChars=False):
  #the resulting hybrid code is never zero safe, and the zeroSafe arg only refers to whether the prefix function is.
  bodyBitArr = intToBinaryBitArr(inputInt)[1:]
  prefixBitSeq = prefixEncoderFun(len(bodyBitArr) + (0 if zeroSafe else 1))
  for outputBit in prefixBitSeq:
    yield outputBit
  if addDbgChars:
    yield "."
  for outputBit in bodyBitArr:
    yield outputBit

def hybridCodeBitSeqToInt(inputBitSeq, prefixDecoderFun, zeroSafe):
  #the resulting hybrid code is never zero safe, and the zeroSafe arg only refers to whether the prefix function is.
  inputBitSeq = makeGen(inputBitSeq)
  prefixParseResult = prefixDecoderFun(inputBitSeq) - (0 if zeroSafe else 1)
  decodedValue = None
  try:
    decodedValue = extendIntByBits(1, inputBitSeq, prefixParseResult)
  except ExhaustionError:
    raise ParseError("Codes.hybridCodeBitSeqToInt ran out of bits before receiving as many as its prefix promised.")
  return decodedValue





  
      








def intToFibcodeBitArr(inputInt): #this is based on math that is a special case for order 2 fibonacci sequence coding.
  assert isInt(inputInt)
  assert inputInt >= 1
  result = []
  currentInt = inputInt
  for index,fibNum in FibonacciMath.genEnboNumsDescendingFromValue(inputInt*2+10, order=2, includeIndices=True, indexStartArr=False):
    #print("intToEnbocodeBitArr: before loop body: (inputInt,order,index,enboNum,result)=" + str((inputInt,order,index,enboNum,result)) + ".")
    assert fibNum > 0
    if fibNum <= currentInt:
      #print("intToEnbocodeBitArr: enboNum will be subtracted from currentInt. (currentInt,index,enboNum)"+str((currentInt,index,enboNum))+".")
      currentInt -= fibNum
      result.append(1)
      #print("intToEnbocodeBitArr: enboNum has been subtracted from currentInt. (currentInt,index,enboNum,result)"+str((currentInt,index,enboNum,result))+".")
    else:
      if len(result) > 0:
        result.append(0)
        #print("intToEnbocodeBitArr: nothing has been subtracted from currentInt this time around. (currentInt,index,enboNum,result)"+str((currentInt,index,enboNum,result))+".")
    #if currentInt == 0:
      #print("intToEnbocodeBitArr: it is possible to break the loop because of currentInt. The loop won't be broken.")
      #pass
    #print("intToEnbocodeBitArr: after loop body: (inputInt,order,index,enboNum,result)=" + str((inputInt,order,index,enboNum,result)) + ".")
  result.reverse()
  assert len(result) > 0
  result.append(1)
  assert len(result) >= 2
  #print("intToEnbocodeBitArr: before final tests: (inputInt,order,result)=" + str((inputInt,order,result)) + ".")
  if len(result) > 2:
    if not arrEndsWith(result,[0,1,1]):
      print("intToFibcodeBitArr: result ends the wrong way. This is never supposed to happen. (inputInt,result)=" + str((inputInt,result)) + ".")
  return result
  
  
def intToHigherEnbocodeBitArr(inputInt, order=None):
  #stopcodeValue is the value that the stopcode has on its own - the plaindata integer value x of the largest round enbocode (the enbocode with all bits being zeroes except for the stopcode bits) such that x <= inputInt.
  stopcodeStartIndex, stopcodeValue = PyGenTools.getLast(enumerate(itertools.takewhile((lambda x: x <= inputInt), FibonacciCodeTools.genRoundEnbocodeValues(order=order))))
  #print(("Codes.intToHigherEnbocodeBitArr",stopcodeStartIndex, stopcodeValue))
  inputInt -= stopcodeValue
  result = [0 for i in range(stopcodeStartIndex)] + [1 for i in range(order)]
  for enboNumIndex,enboNum in FibonacciMath.genEnboNumsDescendingFromIndex(stopcodeStartIndex, order=order, includeIndices=True, indexStartArr=False):
    #print("Codes.intToHigherEnbocodeBitArr: {},{}.".format(enboNumIndex,enboNum))
    if inputInt == 0:
      #print("Codes.intToHigherEnbocodeBitArr: returning early.")
      return result
    assert enboNum > 0
    if inputInt >= enboNum:
      result[enboNumIndex] = 1
      inputInt -= enboNum
    else:
      pass
    #print("Codes.intToHigherEnbocodeBitArr: result={}, inputInt={}.".format(result,inputInt))
  assert inputInt == 0
  return result
  

def intToEnbocodeBitArr(inputInt, order=None):
  assert order > 1
  assert inputInt >= 1
  if order == 2:
    return intToFibcodeBitArr(inputInt)
  else:
    return intToHigherEnbocodeBitArr(inputInt, order=order)


def intToFibcodeBitSeq(inputInt):
  #exists only for uniform naming of functions.
  return makeGen(intToFibcodeBitArr(inputInt))
  

def intToEnbocodeBitSeq(inputInt, order=None, maxInputInt=None):
  assert order > 1
  if maxInputInt != None:
    assert inputInt <= maxInputInt
    return FibonacciCodeTools.truncatedEnbocodeBitSeq(intToEnbocodeBitSeq(inputInt, order=order), order=order, maxInputInt=maxInputInt)
  if order == 2:
    return intToFibcodeBitSeq(inputInt)
  else:
    return makeGen(intToEnbocodeBitArr(inputInt, order=order))


def fibcodeBitSeqToInt(inputBitSeq): #this is based on math that is a special case for order 2 fibonacci sequence coding.
  #this function only eats as much of the provided generator as it needs.
  #it used to be more memory efficient by not keeping a bitHistory. This was written out, but maybe should be brought back.
  inputBitSeq = makeGen(inputBitSeq)
  bitHistory = [] 
  for i,inputBit in enumerate(inputBitSeq):
    if not inputBit in [0,1]:
      raise ValueError("invalid input bit " + str(inputBit) + " at index " + str(i) + ".")
    bitHistory.append(inputBit)
    if sum(bitHistory[-2:]) == 2: 
      break
  #print("enbocodeBitSeqToInt: (order,bitHistory)="+str((order,bitHistory))+".")
  if len(bitHistory) == 0:
    raise ExhaustionError("Received an empty inputBitSeq.")
  elif len(bitHistory) == 1:
    raise ParseError("The inputBitSeq did not contain a proper fibonacci code and had a length of 1.")
  elif len(bitHistory) == 2:
    if not arrEndsWith(bitHistory,[1,1]):
      raise ParseError("Unlikely error: The inputBitSeq was length 2 but did not end in [1,1].")
  elif len(bitHistory) > 2:
    if not arrEndsWith(bitHistory,[0,1,1]):
      raise ParseError("Unlikely error: bitHistory is " + str(bitHistory) + " which does not end in [0,1,1].")
  fibNumGen = genSkipFirst(FibonacciMath.genEnbonacciNums(order=2), 2) #@ cleanup.
  result = 0
  for i,currentFibNum in enumerate(fibNumGen): #this might generate one more fibNum than is needed.
    assert currentFibNum > 0
    if i == len(bitHistory)-1: #if this was the last bit that wasn't part of the stopcode...
      break
    result += currentFibNum * bitHistory[i]
  assert result > 0
  return result
  

  
def higherEnbocodeBitSeqToInt(inputBitGen, order=None): #wastes memory with bitHistory. wastes time with izip.
  assert order > 2
  inputBitGen = makeGen(inputBitGen)
  bitHistory = []
  while not sum(bitHistory[-order:]) == order:
    try:
      bitHistory.append(next(inputBitGen))
    except StopIteration:
      if len(bitHistory) == 0:
        raise ExhaustionError("higherEnbocodeBitSeqToInt received empty input data.")
      raise ParseError("ran out of input bits midword. order={}, bitHistory was {}.".format(order, bitHistory))
  #print("Codes.higherEnbocodeBitSeqToInt: processing {}.".format(bitHistory))
  assert len(bitHistory) >= order
  if len(bitHistory) <= order + 1:
    return len(bitHistory) - order + 1
  placeValueGen = FibonacciMath.genEnbonacciNums(order=order, includeStartArr=False)
  #differenceGen = genPureEnbocodeValueOffsetsSlow(order=order)
  altPlaceValueGen = FibonacciCodeTools.genRoundEnbocodeValues(order=order)
  result = 0
  for currentPlaceIndex,currentPlaceValue in enumerate(placeValueGen):
    #print("Codes.higherEnbocodeBitSeqToInt: for index {}, expected value is {}.".format(currentPlaceIndex,currentPlaceValue))
    if currentPlaceIndex == len(bitHistory) - order:
      #usedOptionValue = currentPlaceValue - PyGenTools.valueAtIndexInGen(currentPlaceIndex, differenceGen)
      usedOptionValue = PyGenTools.valueAtIndexInGen(currentPlaceIndex, altPlaceValueGen)
      #print("Codes.higherEnbocodeBitSeqToInt: using branch Alt value {}.".format(usedOptionValue))
      assert usedOptionValue > 0
      result += bitHistory[currentPlaceIndex]*usedOptionValue
      #PyGenTools.valueAtIndexInGen(currentPlaceIndex - 2, tetranacciNumGen)
      break
    else:
      usedOptionValue = currentPlaceValue
      #print("Codes.higherEnbocodeBitSeqToInt: using branch Main value {}.".format(usedOptionValue))
      assert usedOptionValue > 0
      result += bitHistory[currentPlaceIndex]*usedOptionValue
  assert result > 0
  #print("Codes.higherEnbocodeBitSeqToInt: returning {}.".format(result))
  return result
    


def enbocodeBitSeqToInt(inputBitSeq, order=None, maxInputInt=None):
  #print("enbocodeBitSeqToInt called.")
  assert order > 1
  if maxInputInt != None:
    return enbocodeBitSeqToInt(FibonacciCodeTools.detruncatedEnbocodeBitSeq(makeGen(inputBitSeq), order=order, maxInputInt=maxInputInt), order=order)
  if order == 2:
    return fibcodeBitSeqToInt(inputBitSeq)
  else:
    return higherEnbocodeBitSeqToInt(inputBitSeq, order=order)


def intSeqToEnbocodeBitSeq(inputIntSeq, order=None, maxInputInt=None):
  return intSeqToBitSeq(inputIntSeq, (lambda x: intToEnbocodeBitSeq(x, order=order, maxInputInt=maxInputInt)))

def enbocodeBitSeqToIntSeq(inputBitSeq, order=None, maxInputInt=None):
  return bitSeqToIntSeq(inputBitSeq, (lambda x: enbocodeBitSeqToInt(x, order=order, maxInputInt=maxInputInt)))





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
  return intSeqToBitSeq(inputIntSeq, intToEliasGammaBitSeq)

def eliasGammaBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq, eliasGammaBitSeqToInt)


def intToEliasDeltaBitSeq(inputInt):
  assert inputInt >= 1
  payloadBits = intToBinaryBitArr(inputInt)[1:]
  for outputBit in intToEliasGammaBitSeq(len(payloadBits) + 1):
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
  return intSeqToBitSeq(inputIntSeq, intToEliasDeltaBitSeq)

def eliasDeltaBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq, eliasDeltaBitSeqToInt)





#eliasGamaIota and eliasDeltaIota are two codings I created to store integers with a limited maximum value, by replacing the normal unary prefix present in an Elias code with a fixed-length binary prefix whose length is determined by the requirement of storing the maximum value.
#they are not perfect. When the maxInputInt looks like 100010 and the prefix indicates that the body is 5 bits long, 5 bits are used to define the body when 2 would suffice.

#Elias Gamma Iota codes also have the annoying property of growing in size whenever the maxInputInt grows in binary length, while simultaneously not being zero-safe, which means that for any length of Elias Gamma Iota code, the maximum value any Elias Gamma Iota code of that length can store is in the form (2^(2^n))-1, not 2^(2^n). This means that in a sequence of numbers whose values are in the range 1..255 inclusive, increasing that allowed value range to 1..256 inclusive increases the length of _every_ code in the sequence by 1 bit. Since an Elias Delta Iota code's prefix is an Elias Gamma Iota code, this sudden loss of efficiency occurs for Elias Delta Iota codes less often.

#IntSeqStore uses the maxInputInt argument directly.

def intToEliasGammaIotaBitSeq(inputInt,maxInputInt):
  assert inputInt > 0
  assert inputInt <= maxInputInt
  maxPayloadLength = len(bin(maxInputInt)[3:])
  prefixLength = len(bin(maxPayloadLength)[2:])
  payloadLength = len(bin(inputInt)[3:])
  assert payloadLength <= maxPayloadLength
  #print("maxPayloadLength="+str(maxPayloadLength))
  #print("prefixLength="+str(prefixLength))
  prefix = rjustedArr(intToBinaryBitArr(payloadLength), prefixLength)
  assert len(prefix) == prefixLength
  result = prefix + intToBinaryBitArr(inputInt)[1:]
  for outputBit in result:
    yield outputBit

def eliasGammaIotaBitSeqToInt(inputBitSeq, maxInputInt):
  inputBitSeq = makeGen(inputBitSeq)
  maxPayloadLength = len(bin(maxInputInt)[3:])
  prefixLength = len(bin(maxPayloadLength)[2:])
  prefixValue = binaryBitArrToInt(arrTakeOnly(inputBitSeq,prefixLength,onExhaustion=ExhaustionError("Codes.eliasGammaIotaBitSeqToInt didn't have enough bits for the prefix.")))
  assert prefixValue != None, "None-based termination is being phased out."
  try:
    return extendIntByBits(1, inputBitSeq, prefixValue)
  except ExhaustionError:
    raise ParseError("Codes.eliasGammaIotaBitSeqToInt ran out of input bits before receiving as many as its prefix promised.")
  

def intSeqToEliasGammaIotaBitSeq(inputIntSeq, maxInputInt):
  fun = (lambda x: intToEliasGammaIotaBitSeq(x,maxInputInt))
  return intSeqToBitSeq(inputIntSeq, fun)

def eliasGammaIotaBitSeqToIntSeq(inputBitSeq, maxInputInt):
  fun = (lambda x: eliasGammaIotaBitSeqToInt(x,maxInputInt))
  return bitSeqToIntSeq(inputBitSeq, fun)



def intToEliasDeltaIotaBitSeq(inputInt, maxInputInt):
  assert inputInt > 0
  assert inputInt <= maxInputInt
  maxBodyLength = len(bin(maxInputInt)[3:])
  fun = (lambda x: intToEliasGammaIotaBitSeq(x, maxBodyLength + 1))
  result = intToHybridCodeBitSeq(inputInt, fun, False)
  assert result != None
  return result

def eliasDeltaIotaBitSeqToInt(inputBitSeq, maxInputInt):
  assert maxInputInt > 0
  maxBodyLength = len(bin(maxInputInt)[3:])
  fun = (lambda x: eliasGammaIotaBitSeqToInt(x, maxBodyLength + 1))
  result = hybridCodeBitSeqToInt(inputBitSeq, fun, False)
  assert result != None
  return result


def intSeqToEliasDeltaIotaBitSeq(inputIntSeq, maxInputInt):
  fun = (lambda x: intToEliasDeltaIotaBitSeq(x, maxInputInt))
  return intSeqToBitSeq(inputIntSeq, fun)

def eliasDeltaIotaBitSeqToIntSeq(inputBitSeq, maxInputInt):
  fun = (lambda x: eliasDeltaIotaBitSeqToInt(x, maxInputInt))
  return bitSeqToIntSeq(inputBitSeq, fun)



#eliasGammaFib and eliasDeltaFib are two universal codes I created. They replace the normal unary prefix present in an Elias code with a fibonacci-coded prefix.

def intToEliasGammaFibBitSeq(inputInt, addDbgChars=False):
  assert inputInt > 0
  result = intToHybridCodeBitSeq(inputInt, intToFibcodeBitSeq, False, addDbgChars=addDbgChars)
  assert result != None
  return result

def eliasGammaFibBitSeqToInt(inputBitSeq):
  result = hybridCodeBitSeqToInt(inputBitSeq, fibcodeBitSeqToInt, False)
  assert result != None
  return result


def intSeqToEliasGammaFibBitSeq(inputIntSeq):
  return intSeqToBitSeq(inputIntSeq, intToEliasGammaFibBitSeq)

def eliasGammaFibBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq, eliasGammaFibBitSeqToInt)



def intToEliasDeltaFibBitSeq(inputInt, addDbgChars=False):
  assert inputInt > 0
  result = intToHybridCodeBitSeq(inputInt, intToEliasGammaFibBitSeq, False, addDbgChars=addDbgChars)
  assert result != None
  return result

def eliasDeltaFibBitSeqToInt(inputBitSeq):
  result = hybridCodeBitSeqToInt(inputBitSeq, eliasGammaFibBitSeqToInt, False)
  assert result != None
  return result


def intSeqToEliasDeltaFibBitSeq(inputIntSeq):
  return intSeqToBitSeq(inputIntSeq, intToEliasDeltaFibBitSeq)

def eliasDeltaFibBitSeqToIntSeq(inputBitSeq):
  return bitSeqToIntSeq(inputBitSeq, eliasDeltaFibBitSeqToInt)








"""
def getCodec(name):
  if name in codecs:
    return codecs[name]
  elif name in IntSeqStore.havenBucketCodecs:
    return IntSeqStore.havenBucketCodecs[name]
  else:
    raise KeyError("num codec or num seq codec {} not found.".format(repr(name)))
"""









print("defining codecs...")

codecs = {}


codecs["binary"] = CodecTools.Codec(intToBinaryBitSeq, binaryBitSeqToInt, domain="UNSIGNED")

codecs["enbonacci"] = CodecTools.Codec(intToEnbocodeBitSeq, enbocodeBitSeqToInt, domain="UNSIGNED_NONZERO")
codecs["unary"] = CodecTools.Codec(intToUnaryBitSeq, unaryBitSeqToInt, domain="UNSIGNED")
codecs["eliasGamma"] = CodecTools.Codec(intToEliasGammaBitSeq, eliasGammaBitSeqToInt, domain="UNSIGNED_NONZERO")
codecs["eliasDelta"] = CodecTools.Codec(intToEliasDeltaBitSeq, eliasDeltaBitSeqToInt, domain="UNSIGNED_NONZERO")
codecs["eliasGammaIota"] = CodecTools.Codec(intToEliasGammaIotaBitSeq, eliasGammaIotaBitSeqToInt, domain="UNSIGNED_NONZERO")
codecs["eliasDeltaIota"] = CodecTools.Codec(intToEliasDeltaIotaBitSeq, eliasDeltaIotaBitSeqToInt, domain="UNSIGNED_NONZERO")
codecs["eliasGammaFib"] = CodecTools.Codec(intToEliasGammaFibBitSeq, eliasGammaFibBitSeqToInt, domain="UNSIGNED_NONZERO")
codecs["eliasDeltaFib"] = CodecTools.Codec(intToEliasDeltaFibBitSeq, eliasDeltaFibBitSeqToInt, domain="UNSIGNED_NONZERO")


codecs["inSeq_enbonacci"] = CodecTools.Codec(intSeqToEnbocodeBitSeq, enbocodeBitSeqToIntSeq, domain="UNSIGNED_NONZERO")
codecs["inSeq_eliasGamma"] = CodecTools.Codec(intSeqToEliasGammaBitSeq, eliasGammaBitSeqToIntSeq, domain="UNSIGNED_NONZERO")
codecs["inSeq_eliasDelta"] = CodecTools.Codec(intSeqToEliasDeltaBitSeq, eliasDeltaBitSeqToIntSeq, domain="UNSIGNED_NONZERO")
codecs["inSeq_eliasGammaIota"] = CodecTools.Codec(intSeqToEliasGammaIotaBitSeq, eliasGammaIotaBitSeqToIntSeq, domain="UNSIGNED_NONZERO")
codecs["inSeq_eliasDeltaIota"] = CodecTools.Codec(intSeqToEliasDeltaIotaBitSeq, eliasDeltaIotaBitSeqToIntSeq, domain="UNSIGNED_NONZERO")
codecs["inSeq_eliasGammaFib"] = CodecTools.Codec(intSeqToEliasGammaFibBitSeq, eliasGammaFibBitSeqToIntSeq, domain="UNSIGNED_NONZERO")
codecs["inSeq_eliasDeltaFib"] = CodecTools.Codec(intSeqToEliasDeltaFibBitSeq, eliasDeltaFibBitSeqToIntSeq, domain="UNSIGNED_NONZERO")

codecs["fibonacci"] = codecs["enbonacci"].clone(extraKwargs={"order":2})
codecs["inSeq_fibonacci"] = codecs["inSeq_enbonacci"].clone(extraKwargs={"order":2})

FIBONACCI_ORDER_NICKNAMES = {"tribonacci":3, "tetranacci":4, "pentanacci":5, "hexanacci":6, "heptanacci":7, "octanacci":8, "enneanacci":9}

for orderName, order in FIBONACCI_ORDER_NICKNAMES.items():
  codecs[orderName] = codecs["enbonacci"].clone(extraKwargs={"order":order})
  codecs["inSeq_"+orderName] = codecs["inSeq_enbonacci"].clone(extraKwargs={"order":order})

#fibonacci coding is more efficient than eliasGamma coding for numbers 16..(10**60), so it's likely that eliasDeltaFib is more efficient than eliasDelta for numbers (2**15)..(2**(10**60-1)).
#eliasDelta coding is more efficient than fibonacci coding for numbers 317811..(10**60).
#it seems like eliasDeltaFib must be more efficient than EliasDelta eventually, but they trade blows all the way up to 10**606, with EDF seemingly being the only one able to break the tie.





print("testing enbocode length prediction...")
  
for testOrder in [2,3,5,8]:
  for testNum in range(1,32):
    assert FibonacciCodeTools.predictEnbocodeTotalLength(testNum, order=testOrder) == len(intToEnbocodeBitArr(testNum, order=testOrder))




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




for testOrder in [3,4,5,8,14]:
  print("testing enbonacci fast decoding: order {}...".format(testOrder))
  #if order > 3:
  #  print("orders above 3 are currently broken.")
    #break
  testDataSrc = arrTakeOnly(FibonacciCodeTools.genEnbocodeBitArrs(order=testOrder), 32)
  #print(testDataSrc)
  testResult = [higherEnbocodeBitSeqToInt(item, order=testOrder) for item in testDataSrc]
  #print(testResult)
  assert testResult == [i for i in range(1,33)]



print("performing full codec tests...")

testNumCodecNames = ["fibonacci", "eliasGamma", "eliasDelta", "eliasGammaFib", "eliasDeltaFib"] + [key for key in FIBONACCI_ORDER_NICKNAMES.keys()]

for testCodecName in testNumCodecNames:
  print("testing " + testCodecName + "...")
  for testNum in [1, 5, 10, 255, 257, 65535, 65537, 999999]:
    assert CodecTools.roundTripTest(codecs[testCodecName], testNum)

testNumSeqCodecNames = ["inSeq_"+testNumCodecName for testNumCodecName in ["fibonacci", "eliasGamma", "eliasDelta", "eliasGammaFib", "eliasDeltaFib"] + [key for key in FIBONACCI_ORDER_NICKNAMES.keys()]] #no unary.

for testCodecName in testNumSeqCodecNames:
  print("testing " + testCodecName + "...")
  testArr = [1,2,3,4,5,100,1000,1000000,1,1000,1,100,1,5,4,3,2,1]
  assert CodecTools.roundTripTest(codecs[testCodecName], testArr)
  


print("performing tests of Iota codings...")

assert CodecTools.roundTripTest(codecs["inSeq_eliasGammaIota"].clone(extraKwargs={"maxInputInt":15}), [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])


