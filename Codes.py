"""

Codes.py by John Dorsey.

Codes.py contains tools for encoding and decoding universal codes like fibonacci coding, elias gamma coding, elias delta coding, and unary coding.

"""

import CodecTools
from PyGenTools import isGen, makeGen, makeArr, arrTakeOnly, ExhaustionError



fibNums = [1,1]

for i in range(8192):
  fibNums.append(fibNums[-1]+fibNums[-2])



class ParseError(Exception):
  pass



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


def intSeqToBitSeq(inputIntSeq,inputFun):
  for inputInt in inputIntSeq:
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
      raise ParseError("The inputFun did not properly terminate.")
    yield outputInt















def intToFibcodeBitArr(inputInt,startPoint=None):
  #This function hasn't been replaced with or converted to a generator because doing so has no benefits - the bits must be generated in backwards order anyway, so it makes no sense to convert to a generator and then convert back.
  assert type(inputInt) == int
  assert inputInt >= 1
  if not int(inputInt) <= fibNums[-1]:
    raise ValueError("input value of " + str(inputInt) + " is larger than the largest known fibonacci number, " + str(fibNums[-1]) + ".")
  if startPoint == None:
    startPoint = len(fibNums)-1
    """while fibNums[startPoint-1] > inputInt:
      startPoint -= 1"""
  index = startPoint
  currentInt = inputInt
  result = []
  while index >= 0:
    if fibNums[index] <= currentInt:
      currentInt -= fibNums[index]
      result.append(1)
    else:
      if len(result) > 0:
        result.append(0)
    index -= 1
  result.reverse()
  result.append(1)
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
  for i,inputBit in enumerate(inputBitSeq):
    if inputBit == 1 and previousBit == 1:
      return result
    previousBit = inputBit
    result += fibNums[i+1] * inputBit
  if result != 0:
    raise ParseError("Codes.fibcodeBitSeqToInt ran out of input bits midword.")
    #print("Codes.fibcodeBitSeqToInt ran out of input bits midword. Returning None instead of " + str(result) + ".")
    #return None
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




def intToBinaryBitArr(inputInt):
  return [int(char) for char in bin(inputInt)[2:]]

def binaryBitArrToInt(inputBitArr):
  return sum(2**i*inputBitArr[-1-i] for i in range(len(inputBitArr)))


def validateBinaryBitStr(inputBitStr):
  if len(inputBitStr.replace("0","").replace("1","")) > 0:
    return False
  return True




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

def intToEliasGammaIotaBitSeq(inputInt,maxInputInt=None):
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

def eliasGammaIotaBitSeqToInt(inputBitSeq,maxInputInt=None):
  inputBitSeq = makeGen(inputBitSeq)
  maxPayloadLength = len(bin(maxInputInt)[3:])
  prefixLength = len(bin(maxPayloadLength)[2:])
  prefixValue = binaryBitArrToInt(arrTakeOnly(inputBitSeq,prefixLength,onExhaustion="fail"))
  assert prefixValue != None, "None-based termination is being phased out."
  try:
    return extendIntByBits(1,inputBitSeq,prefixValue)
  except ExhaustionError:
    raise ParseError("Codes.eliasGammaIotaBitSeqToInt ran out of input bits before receiving as many as its prefix promised.")
  

def intSeqToEliasGammaIotaBitSeq(inputIntSeq,maxInputInt=None):
  return intSeqToBitSeq(inputIntSeq,(lambda x: intToEliasGammaIotaBitSeq(x,maxInputInt=maxInputInt)))

def eliasGammaIotaBitSeqToIntSeq(inputBitSeq,maxInputInt=None):
  return bitSeqToIntSeq(inputBitSeq,(lambda x: eliasGammaIotaBitSeqToInt(x,maxInputInt=maxInputInt)))








print("defining codecs...")

codecs = {}

codecs["fibonacci"] = CodecTools.Codec(intToFibcodeBitSeq,fibcodeBitSeqToInt)
codecs["unary"] = CodecTools.Codec(intToUnaryBitSeq,unaryBitSeqToInt)
codecs["eliasGamma"] = CodecTools.Codec(intToEliasGammaBitSeq,eliasGammaBitSeqToInt)
codecs["eliasDelta"] = CodecTools.Codec(intToEliasDeltaBitSeq,eliasDeltaBitSeqToInt)
codecs["eliasGammaIota"] = CodecTools.Codec(intToEliasGammaIotaBitSeq,eliasGammaIotaBitSeqToInt)

codecs["inSeq_fibonacci"] = CodecTools.Codec(intSeqToFibcodeBitSeq,fibcodeBitSeqToIntSeq)
codecs["inSeq_eliasGamma"] = CodecTools.Codec(intSeqToEliasGammaBitSeq,eliasGammaBitSeqToIntSeq)
codecs["inSeq_eliasDelta"] = CodecTools.Codec(intSeqToEliasDeltaBitSeq,eliasDeltaBitSeqToIntSeq)
codecs["inSeq_eliasGammaIota"] = CodecTools.Codec(intSeqToEliasGammaIotaBitSeq,eliasGammaIotaBitSeqToIntSeq)

#a temporary fix for the fact that Testing.py methods expecting the old UniversalCoding class.
codecs["fibonacci"].zeroSafe = False
codecs["unary"].zeroSafe = True
codecs["eliasGamma"].zeroSafe = False
codecs["eliasDelta"].zeroSafe = False
codecs["eliasGammaIota"].zeroSafe = False
codecs["inSeq_fibonacci"].zeroSafe = False
codecs["inSeq_eliasGamma"].zeroSafe = False
codecs["inSeq_eliasDelta"].zeroSafe = False
codecs["inSeq_eliasGammaIota"].zeroSafe = False

codecs["inStr_inSeq_fibonacci"] = CodecTools.makeChainedPairCodec(codecs["inSeq_fibonacci"],CodecTools.bitSeqToStrCodec)
codecs["inStr_inSeq_eliasGamma"] = CodecTools.makeChainedPairCodec(codecs["inSeq_eliasGamma"],CodecTools.bitSeqToStrCodec)
codecs["inStr_inSeq_eliasDelta"] = CodecTools.makeChainedPairCodec(codecs["inSeq_eliasDelta"],CodecTools.bitSeqToStrCodec)

#temporary fix continued.
codecs["inStr_inSeq_fibonacci"].zeroSafe = False
codecs["inStr_inSeq_eliasGamma"].zeroSafe = False
codecs["inStr_inSeq_eliasDelta"].zeroSafe = False



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

for testCodecName in ["inStr_inSeq_fibonacci","inStr_inSeq_eliasGamma","inStr_inSeq_eliasDelta"]:
  print("testing " + testCodecName)
  testArr = [1,2,3,4,5,100,1000,100,5,4,3,2,1]
  testCodec = codecs[testCodecName]
  assert CodecTools.roundTripTest(testCodec,testArr) #to make sure there is nothing wrong with later tests in this block.
  pressData = testCodec.encode(testArr)
  assert type(pressData) == str
  reconstPlainData = [item for item in testCodec.decode(pressData)]
  assert reconstPlainData == testArr



print("performing tests of Iota codings...")

assert CodecTools.roundTripTest(codecs["inSeq_eliasGammaIota"].clone(extraKwargs={"maxInputInt":15}),[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])


