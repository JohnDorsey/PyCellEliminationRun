"""

IntSeqStore.py by John Dorsey.

IntSeqStore.py contains tools for storing integer sequences with minimized storage overhead.


"""

import Codes #for haven bucket.
from PyArrTools import rjustedArr
from PyGenTools import arrTakeOnly, makeGen, isGen, makeArr, sentinelize, ExhaustionError
import CodecTools
from IntSeqMath import genTrackDelayedSum



def genTrackDelayedRemainingSum(inputSeq,seqSum,enumerated=False):
  i = 0
  for delayedCurrentSum,item in genTrackDelayedSum(inputSeq):
    yield (i,seqSum-delayedCurrentSum,item) if enumerated else (seqSum-delayedCurrentSum,item)
    i += 1
    


def lewisTrackedSumTruncationEncode(inputIntSeq, seqSum, addDbgCommas=False): #left-weighted integer sequence truncated.
  #this generator processes a sequence of integers, and compares the provided sum of the entire sequence with the sum of items processed so far to determine the maximum value the current item could have, and truncates it to that length in the generated output.
  #it is generally much less efficient than fibonacci coding for storing the pressdata numbers produced by PyCellElimRun.
  #this method does not yet ignore trailing zeroes and will store them each as a bit "0" instead of stopping like it could.
  return lewisTrackedSumBoundedCodecEncode(inputIntSeq, seqSum, Codes.codecs["binary"], addDbgCommas=addDbgCommas)

def lewisTrackedSumTruncationDecode(inputBitSeq, seqSum, addDbgCommas=False):
  return lewisTrackedSumBoundedCodecDecode(inputBitSeq, seqSum, Codes.codecs["binary"], addDbgCommas=addDbgCommas)


def lewisTrackedSumBoundedCodecEncode(inputIntSeq, seqSum, boundedNumberCodec, addDbgCommas=False):
  justStarted = True
  sumSoFar = 0
  for delayedRemainingSum,currentInt in genTrackDelayedRemainingSum(inputIntSeq,seqSum):
    store = boundedNumberCodec.encode(currentInt, maxInputInt=delayedRemainingSum)
    assert isGen(store) or type(store) == list
    if addDbgCommas:
      if not justStarted:
        yield ","
      else:
        justStarted = False
    for outputBit in store:
      yield outputBit

def lewisTrackedSumBoundedCodecDecode(inputBitSeq, seqSum, boundedNumberCodec):
  inputBitSeq = makeGen(inputBitSeq)
  sumSoFar = 0
  num = None
  while True:
    delayedRemainingSum = seqSum - sumSoFar
    try:
      num = boundedNumberCodec.decode(inputBitSeq, maxInputInt=delayedRemainingSum)
    except ExhaustionError:
      break
    sumSoFar += num
    yield num


def getBucketSizeAdjustedKwargsForNumberCodec(havenBucketSize, maxInputInt):
  maxInputIntForNumberCodec = maxInputInt
  kwargsForNumberCodec = dict()
  if maxInputIntForNumberCodec != None:
    maxInputIntForNumberCodec >>= havenBucketSize
    kwargsForNumberCodec["maxInputInt"] = maxInputIntForNumberCodec
  return (kwargsForNumberCodec, maxInputIntForNumberCodec)



def intToHavenBucketedBitSeq(inputInt, numberCodec, havenBucketSize, maxInputInt=None, addDbgCommas=False):
  assert havenBucketSize >= 0
  if maxInputInt != None:
    assert inputInt <= maxInputInt
  
  kwargsForNumberCodec, maxInputIntForNumberCodec = getBucketSizeAdjustedKwargsForNumberCodec(havenBucketSize, maxInputInt)
  
  if maxInputIntForNumberCodec != 0: #avoid error.
    encodedBitArr = makeArr(numberCodec.zeroSafeEncode(inputInt >> havenBucketSize, **kwargsForNumberCodec))
  else:
    #assert kwargsForNumberCodec["maxInputInt"] == 0
    encodedBitArr = []
    
  if addDbgCommas:
    encodedBitArr.append(".")
  havenBucketData = rjustedArr(Codes.intToBinaryBitArr(inputInt), havenBucketSize, crop=True)
  encodedBitArr.extend(havenBucketData)
  for item in encodedBitArr:
    yield item

def genEncodeWithHavenBucket(inputIntSeq, numberCodec, havenBucketSizeFun, initialHavenBucketSize=0, seqSum=None, addDbgCommas=False):
  #parseFun must take only as many bits as it needs and return an integer.
  havenBucketSize = initialHavenBucketSize
  delayedRemainingSum = seqSum
  justStarted = True #used only to control debug commas.
  for inputInt in inputIntSeq:
    if addDbgCommas:
      if not justStarted:
        yield ","
      else:
        justStarted = False
    for outputBit in intToHavenBucketedBitSeq(inputInt, numberCodec, havenBucketSize, maxInputInt=delayedRemainingSum, addDbgCommas=addDbgCommas):
      yield outputBit
    havenBucketSize = havenBucketSizeFun(inputInt)
    if delayedRemainingSum != None:
      delayedRemainingSum -= inputInt
      assert delayedRemainingSum >= 0
    

def havenBucketedBitSeqToInt(inputBitGen, numberCodec, havenBucketSize, maxInputInt=None):
    inputBitGen = makeGen(inputBitGen)
    assert havenBucketSize >= 0
    
    kwargsForNumberCodec, maxInputIntForNumberCodec = getBucketSizeAdjustedKwargsForNumberCodec(havenBucketSize, maxInputInt)
    
    if maxInputIntForNumberCodec != 0: #avoid error.
      parseResult = numberCodec.zeroSafeDecode(inputBitGen, **kwargsForNumberCodec) #may raise ExhaustionError.
    else:
      #assert kwargsForNumberCodec["maxInputInt"] == 0
      parseResult = 0
    
    assert parseResult != None, "None-based generator stopping should be phased out."
    try:
      havenBucketBits = arrTakeOnly(inputBitGen, havenBucketSize, onExhaustion="ExhaustionError")
    except ExhaustionError:
      raise ParseError("ran out of input bits before completing the haven bucket.")
    #parseResult -= (0 if numberCodec.zeroSafe else 1)
    decodedValue = ((parseResult)<<len(havenBucketBits)) + Codes.binaryBitArrToInt(havenBucketBits)
    return decodedValue
    

def genDecodeWithHavenBucket(inputBitSeq, numberCodec, havenBucketSizeFun, initialHavenBucketSize=0, seqSum=None):
  #parseFun must take only as many bits as it needs and return an integer.
  inputBitSeq = makeGen(inputBitSeq)
  havenBucketSize = initialHavenBucketSize
  delayedRemainingSum = seqSum
  while True:
    try:
      decodedValue = havenBucketedBitSeqToInt(inputBitSeq, numberCodec, havenBucketSize, maxInputInt=delayedRemainingSum)
    except ExhaustionError:
      break
    yield decodedValue
    havenBucketSize = havenBucketSizeFun(decodedValue)
    if delayedRemainingSum != None:
      delayedRemainingSum -= decodedValue
      assert delayedRemainingSum >= 0




havenBucketCodecs = dict()
havenBucketCodecs["base"] = CodecTools.Codec(genEncodeWithHavenBucket,genDecodeWithHavenBucket,domain="UNSIGNED")
#HLL = half last length.
havenBucketCodecs["HLL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: len(bin(x)[2:])>>1)])
havenBucketCodecs["HLL_eliasGamma"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["eliasGamma"],(lambda x: len(bin(x)[2:])>>1)])
havenBucketCodecs["HLL_eliasDelta"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["eliasDelta"],(lambda x: len(bin(x)[2:])>>1)])


havenBucketCodecs["0.125LL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: int(len(bin(x)[2:])*0.125))])
havenBucketCodecs["0.25LL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: int(len(bin(x)[2:])*0.25))])
havenBucketCodecs["0.375LL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: int(len(bin(x)[2:])*0.375))])
havenBucketCodecs["0.625LL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: int(len(bin(x)[2:])*0.625))])
havenBucketCodecs["0.75LL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: int(len(bin(x)[2:])*0.75))])
havenBucketCodecs["0.875LL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: int(len(bin(x)[2:])*0.875))])


class StatefulFunctionHost:
  #this class is used to create state machines that appear like normal functions.
  #this class might not make most things easier. It might be easier to write new generators from scratch than to incorporate this class. It is more redundant to write each generator from scratch, but it might make them each easier to understand.

  def __init__(self,mainFunIn,state=[]):
    self.mainFunIn = mainFunIn
    #self.primerFunsIn = primerFunsIn
    self.state = state
    assert len(state) == 0
    self.callCount = -1


  def mainFunOut(self,inputData): #this method is to be used like a normal one.
    self.callCount += 1
    #if self.callCount < len(self.primerFunsIn):
    #  return self.primerFunsIn(state,inputData)
    return self.mainFunIn(self.callCount,self.state,inputData)


  def extrapolationDemoFun(callCount,state,inputData): #this method demonstrates linear extrapolation using a stateful function that is used like any other function, but returns the result of extrapolation to find y at location x+1 using the last argument it recieved as y at x-1 and the current argument as y at x.
    if callCount == 0:
      assert len(state) == 0
    if len(state) > 2:
      del state[0]
    state.append(inputData)
    if len(state) == 1:
      return state[0]
    return state[-1] + (state[-1]-state[-2])







def stackHeteroBaseDigits(valueSeq, baseSeq):
  valueGen, baseGen = (sentinelize(valueSeq), sentinelize(baseSeq))
  result = 0
  i = 0
  while True:
    currentValue, currentBase = (next(valueGen), next(baseGen))
    if None in [currentValue, currentBase]:
      break
    if currentValue >= currentBase:
      raise ValueError("A digit value exceeded the limits of its base at index " + str(i) + ".")
    if currentValue < 0:
      raise ValueError("Digit values must be positive. A negative digit value was encountered at index " + str(i) + ".")
    result *= currentBase
    result += currentValue
    i += 1
  if currentBase == None and currentValue != None:
    raise ValueError("baseSeq ran out before valueSeq did. The base provider must provide a base for each value to be stacked or unstacked.")
  return result

def unstackHeteroBaseDigits(inputInt, baseSeq, noTail=True):
  i = 0
  for currentBase in baseSeq:
    if currentBase < 1:
      raise ValueError("Digit base values must be at least 1. A digit base value less than 1 was encountered at index " + str(i) + ".")
    if currentBase > 0: #avoid division by zero.
      currentValue = inputInt%currentBase
      yield currentValue
      inputInt //= currentBase
    else:
      yield 0
    i += 1
    if noTail and inputInt == 0:
      break

def rankingsArrToInt(inputArr):
  rankCount = len(inputArr)
  for i in range(rankCount):
    if not i in inputArr:
      raise ValueError("The rankings array is invalid.")
  waiting = [True for i in range(len(inputArr))]
  positions = []
  #positions[x] tells where to find rank x in inputArr. Skip over locations known to belong to other ranks and eventually find, among locations with unknown contents, the positions[x]-th such location. It contains rank x.
  for currentRank in range(rankCount):
    locationOfCurrentRank = inputArr.index(currentRank)
    collapsedLocationOfCurrentRank = sum(waiting[:locationOfCurrentRank])
    positions.append(collapsedLocationOfCurrentRank)
    waiting[locationOfCurrentRank] = False
  bases = [item for item in range(len(inputArr),0,-1)]
  #print("unreversed positions: "+str(positions)+".")
  #print("unreversed bases: "+str(bases)+".")
  """
  testArr = []
  for i in range(rankCount):
    testArr.insert(positions[-i-1],rankCount-i-1)
  print("testArr: " +str(testArr)+".")
  assert testArr == inputArr
  """
  #print("positions: "+str(positions)+".")
  #print("bases: "+str(bases)+".")
  return stackHeteroBaseDigits(positions,bases)

def intToRankingsArr(inputInt):
  rankingsArr = []
  positions = makeArr(unstackHeteroBaseDigits(inputInt,range(1,2**32)))
  #print("positions: "+str(positions)+".")
  for i,insertLocation in enumerate(positions):
    rankingsArr.insert(insertLocation,i)
  #print("unflipped rankingsArr: " + str(rankingsArr) + ".")
  for i in range(len(rankingsArr)):
    rankingsArr[i] = len(rankingsArr) - rankingsArr[i] - 1
  #print("flipped rankingsArr: " + str(rankingsArr) + ".")
  return rankingsArr








def expeditedPrefixesEncode(inputIntArr):
  result = [[],[]]
  for currentInt in inputIntArr:
    if currentInt < 1:
      raise ValueError("Not zero-safe!")
    currentBits = makeArr(Codes.intToBinaryBitArr(currentInt))
    result[0].append(len(currentBits)-1)
    result[1].extend(currentBits[1:])
  return result

def expeditedPrefixesDecode(bodyLengthSeq,bitSeq):
  bodyLengthSeq = makeGen(bodyLengthSeq)
  bitSeq = makeGen(bitSeq)
  for bodyLength in bodyLengthSeq:
    yield Codes.extendIntByBits(1,bitSeq,bodyLength)


#def P0_Ic_p1IC_P1_Ic_for_p2I...
def intSeq_useCodecOnExpeditedPrefixes_encode(inputIntSeq,numberCodec,numberSeqCodec): #memory waste.
  result = expeditedPrefixesEncode(inputIntSeq)
  for outputBit in numberCodec.encode(len(result[0]) + (not numberCodec.zeroSafe)):
    yield outputBit
  for outputBit in numberSeqCodec.encode((item+(not numberSeqCodec.zeroSafe) for item in result[0])):
    yield outputBit
  for outputBit in result[1]:
    yield outputBit

def intSeq_useCodecOnExpeditedPrefixes_decode(inputBitSeq,numberCodec,numberSeqCodec):
  inputBitSeq = makeGen(inputBitSeq)
  remainingHeaderLength = numberCodec.decode(inputBitSeq)-(not numberCodec.zeroSafe)
  header = arrTakeOnly((item-(not numberSeqCodec.zeroSafe) for item in numberSeqCodec.decode(inputBitSeq)),remainingHeaderLength)
  return expeditedPrefixesDecode(header,inputBitSeq)

#these are inefficient for sequences with a lot of small numbers.
prefixExpeditionCodecs = {}
prefixExpeditionCodecs["base"] = CodecTools.Codec(intSeq_useCodecOnExpeditedPrefixes_encode,intSeq_useCodecOnExpeditedPrefixes_decode)
prefixExpeditionCodecs["HLL_fibonacci"] = prefixExpeditionCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],havenBucketCodecs["HLL_fibonacci"]])
prefixExpeditionCodecs["0.75LL_fibonacci"] = prefixExpeditionCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],havenBucketCodecs["HLL_fibonacci"]])















assert [item for item in havenBucketCodecs["HLL_fibonacci"].encode([2,2,2000,2,2])] == [0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]

