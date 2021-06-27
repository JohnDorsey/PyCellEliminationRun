"""

IntSeqStore.py by John Dorsey.

IntSeqStore.py contains tools for storing integer sequences with as little overhead as possible.


"""




def lewisTrunc(seqSum,seqSrc,addDebugCommas=False): #left-weighted integer sequence truncated.
  #this method does not yet ignore trailing zeroes and will store them each as a bit "0" instead of stopping like it could.
  sumSoFar = 0
  for num in seqSrc:
    storeLength = int.bit_length(seqSum-sumSoFar)
    strToOutput = str(bin(num)[2:]).rjust(storeLength,'0')
    for char in strToOutput:
      yield char
    if addDebugCommas:
      yield ","
    sumSoFar += num


"""
def lewisDeTrunc(seqSum,seqSrc): #left-weighted integer sequence truncated.
  sumSoFar = 0
  mode = 0
  storeLength = None
  bitsToProcess = None
  for bit in seqSrc:
    assert sumSoFar < seqSum
    if mode == 0:
      storeLength = int.bit_length(seqSum-sumSoFar)
      bitsToProcess = ""
      mode = 1
    if mode == 1:
      if len(bitsToProcess) < storeLength:
        bitsToProcess += bit
      else:
        mode = 2
    if mode == 2:
      num = int(bitsToProcess,2)
      sumSoFar += num
      yield num
      mode = 0
"""


#this method is a great example of how to write a generator that gives output items less frequently than it reads input items; The commented-out method of the same name is an example of how not to do it.
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



def genDecodeWithHavenBucket(inputStr,parseFun,havenBucketSizeFun,initialHavenBucketSize=0):
  #parseFun MUST be a parser (taking any length of string and reacting to the beginning of it only) in detailed mode (giving the result in form [the accepted input, result]).
  ASSUMEZEROSAFE = False
  offset = 0
  havenBucketSize = initialHavenBucketSize
  while True:
    parseResult = parseFun(inputStr[offset:])
    if None in parseResult:
    #out of data.
      break
    offset += len(parseResult[0])
    havenBucketData = inputStr[offset:offset+havenBucketSize]
    offset += len(havenBucketData)
    decodedValue = None
    if ASSUMEZEROSAFE:
      decodedValue = int(parseResult[1]+havenBucketData,2)
    else:
      decodedValue = (int(parseResult[1],2)-1)*(2**len(havenBucketData)) + int(havenBucketData,2)
    yield decodedValue
    havenBucketSize = havenBucketSizeFun(decodedValue)


def genEncodeWithHavenBucket(inputIntSeq,encodeFun,havenBucketSizeFun,initialHavenBucketSize=0,addDebugCommas=False):
  #parseFun MUST be a parser (taking any length of string and reacting to the beginning of it only) in detailed mode (giving the result in form [the accepted input, result]).
  ASSUMEZEROSAFE = False
  havenBucketSize = initialHavenBucketSize
  for num in inputIntSeq:
    havenBucketData = bin(num)[2:].rjust(havenBucketSize,"0")[-havenBucketSize:]
    if ASSUMEZEROSAFE:
      encodedStr = encodeFun(num >> havenBucketSize)
    else:
      encodedStr = encodeFun((num >> havenBucketSize) + 1)
    encodedStr += havenBucketData
    for char in encodedStr:
      yield char
    if addDebugCommas:
      yield "," #@ sometimes yields one too many.
    havenBucketSize = havenBucketSizeFun(num)

