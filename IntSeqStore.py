"""

IntSeqStore.py by John Dorsey.

IntSeqStore.py contains tools for storing integer sequences with as little overhead as possible.


"""

import Codes #for haven bucket.
from Codes import rjustArr
from PyGenTools import arrTakeOnly, makeGen, makeArr, ExhaustionError
import CodecTools


def lewisTrunc(seqSum,seqSrc,addDebugCommas=False): #left-weighted integer sequence truncated.
  #this generator processes a sequence of integers, and compares the provided sum of the entire sequence with the sum of items processed so far to determine the maximum value the current item could have, and truncates it to that length in the generated output.
  #it is generally much less efficient than fibonacci coding for storing the pressdata numbers produced by PyCellElimRun.
  #this method does not yet ignore trailing zeroes and will store them each as a bit "0" instead of stopping like it could.
  sumSoFar = 0
  justStarted = True
  for num in seqSrc:
    storeLength = int.bit_length(seqSum-sumSoFar)
    strToOutput = str(bin(num)[2:]).rjust(storeLength,'0')
    if addDebugCommas:
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


def genEncodeWithHavenBucket(inputIntSeq,numberCodec,havenBucketSizeFun,initialHavenBucketSize=0,addDebugCommas=False):
  #parseFun must take only as many bits as it needs and return an integer.
  havenBucketSize = initialHavenBucketSize
  justStarted = True #used only to control debug commas.
  for num in inputIntSeq:
    assert havenBucketSize >= 0
    encodedBitArr = makeArr(numberCodec.encode((num >> havenBucketSize) + (0 if numberCodec.zeroSafe else 1)))
    if addDebugCommas:
      encodedBitArr.append(".")
    havenBucketData = rjustArr(Codes.intToBinaryBitArr(num),havenBucketSize,crop=True)
    encodedBitArr.extend(havenBucketData)
    if addDebugCommas:
      if not justStarted:
        yield ","
      else:
        justStarted = False
    for item in encodedBitArr:
      yield item
    havenBucketSize = havenBucketSizeFun(num)



havenBucketFibonacciCoding = CodecTools.Codec(genEncodeWithHavenBucket,genDecodeWithHavenBucket,extraArgs=[Codes.codecs["fibonacci"],(lambda x: len(bin(x)[2:])>>1)])
havenBucketFibonacciCoding.zeroSafe = True




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


assert [item for item in havenBucketFibonacciCoding.encode([2,2,2000,2,2])] == [0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0]

