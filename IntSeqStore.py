"""

IntSeqStore.py by John Dorsey.

IntSeqStore.py contains tools for storing integer sequences with minimized storage overhead.


"""

import Codes #for haven bucket.
from Codes import rjustedArr
from PyGenTools import arrTakeOnly, makeGen, makeArr, sentinelize, ExhaustionError
import CodecTools


def lewisTrunc(seqSum,seqSrc,addDbgCommas=False): #left-weighted integer sequence truncated.
  #this generator processes a sequence of integers, and compares the provided sum of the entire sequence with the sum of items processed so far to determine the maximum value the current item could have, and truncates it to that length in the generated output.
  #it is generally much less efficient than fibonacci coding for storing the pressdata numbers produced by PyCellElimRun.
  #this method does not yet ignore trailing zeroes and will store them each as a bit "0" instead of stopping like it could.
  sumSoFar = 0
  justStarted = True
  for num in seqSrc:
    storeLength = int.bit_length(seqSum-sumSoFar)
    strToOutput = str(bin(num)[2:]).rjust(storeLength,'0')
    if addDbgCommas:
      if not justStarted:
        yield ","
      else:
        justStarted = False
    for char in strToOutput:
      yield char
    sumSoFar += num


def lewisDeTrunc(seqSum,seqSrc):
  sumSoFar = 0
  bitBufferStr = ""
  for bitChr in seqSrc:
    storeLength = int.bit_length(seqSum-sumSoFar)
    bitBufferStr += bitChr
    if len(bitBufferStr) < storeLength:
      continue
    num = int(bitBufferStr,2)
    sumSoFar += num
    bitBufferStr = ""
    yield num



def genDecodeWithHavenBucket(inputBitSeq,numberCodec,havenBucketSizeFun,initialHavenBucketSize=0):
  #parseFun must take only as many bits as it needs and return an integer.
  inputBitSeq = makeGen(inputBitSeq)
  havenBucketSize = initialHavenBucketSize
  while True:
    assert havenBucketSize >= 0
    parseResult = None
    try:
      parseResult = numberCodec.decode(inputBitSeq)
    except ExhaustionError:
      break #out of data.
    assert parseResult != None, "None-based generator stopping should be phased out."
    havenBucketBits = arrTakeOnly(inputBitSeq,havenBucketSize)
    decodedValue = ((parseResult-(0 if numberCodec.zeroSafe else 1))<<len(havenBucketBits)) + Codes.binaryBitArrToInt(havenBucketBits)
    yield decodedValue
    havenBucketSize = havenBucketSizeFun(decodedValue)


def genEncodeWithHavenBucket(inputIntSeq,numberCodec,havenBucketSizeFun,initialHavenBucketSize=0,addDbgCommas=False):
  #parseFun must take only as many bits as it needs and return an integer.
  havenBucketSize = initialHavenBucketSize
  justStarted = True #used only to control debug commas.
  for num in inputIntSeq:
    assert havenBucketSize >= 0
    encodedBitArr = makeArr(numberCodec.encode((num >> havenBucketSize) + (0 if numberCodec.zeroSafe else 1)))
    if addDbgCommas:
      encodedBitArr.append(".")
    havenBucketData = rjustedArr(Codes.intToBinaryBitArr(num),havenBucketSize,crop=True)
    encodedBitArr.extend(havenBucketData)
    if addDbgCommas:
      if not justStarted:
        yield ","
      else:
        justStarted = False
    for item in encodedBitArr:
      yield item
    havenBucketSize = havenBucketSizeFun(num)

havenBucketCodecs = {}
havenBucketCodecs["base"] = CodecTools.Codec(genEncodeWithHavenBucket,genDecodeWithHavenBucket,zeroSafe=True)
#HLL = half last length.
havenBucketCodecs["HLL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: len(bin(x)[2:])>>1)])
havenBucketCodecs["HLL_eliasGamma"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["eliasGamma"],(lambda x: len(bin(x)[2:])>>1)])
havenBucketCodecs["HLL_eliasDelta"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["eliasDelta"],(lambda x: len(bin(x)[2:])>>1)])

havenBucketCodecs["0.75LL_fibonacci"] = havenBucketCodecs["base"].clone(extraArgs=[Codes.codecs["fibonacci"],(lambda x: int(len(bin(x)[2:])*0.75))])


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








def intArrToBodyLengthArrAndBitArr(inputIntArr):
  result = [[],[]]
  for currentInt in inputIntArr:
    if currentInt < 1:
      raise ValueError("Not zero-safe!")
    currentBits = makeArr(Codes.intToBinaryBitArr(currentInt))
    result[0].append(len(currentBits)-1)
    result[1].extend(currentBits[1:])
  return result

def bodyLengthSeqAndBitSeqToIntSeq(bodyLengthSeq,bitSeq):
  bodyLengthSeq = makeGen(bodyLengthSeq)
  bitSeq = makeGen(bitSeq)
  for bodyLength in bodyLengthSeq:
    yield Codes.extendIntByBits(1,bitSeq,bodyLength)







assert [item for item in havenBucketCodecs["HLL_fibonacci"].encode([2,2,2000,2,2])] == [0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]

