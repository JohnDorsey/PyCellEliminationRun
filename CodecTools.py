"""

CodecTools.py by John Dorsey.

CodecTools.py contains classes and other tools that might help make it easier to rapidly create and test codecs made from smaller codecs applied in stages.

"""

import itertools
from PyGenTools import makeArr, isGen, makeGen, ExhaustionError, genAddInt, arrAddInt


def measureIntArray(inputIntArr):
  rectBitSize = (len(inputIntArr),len(bin(max(inputIntArr))[2:]))
  return {"length":rectBitSize[0],"bit_depth":rectBitSize[1],"bit_area":rectBitSize[0]*rectBitSize[1]}

def printComparison(plainData,pressData):
  plainDataMeasures, pressDataMeasures = (measureIntArray(plainData), measureIntArray(pressData))
  estimatedCR = float(plainDataMeasures["bit_area"])/float(pressDataMeasures["bit_area"])
  estimatedSaving = 1.0 - 1.0/estimatedCR
  print("CodecTools.printComparison: plainData measures " + str(plainDataMeasures) + ". pressData measures " + str(pressDataMeasures) + ". Estimated CR is " + str(estimatedCR)[:8] + ". Estimated saving rate is " + str(estimatedSaving*100.0)[:8] + "%.")

def countTrailingZeroes(inputArr):
  i = 0
  while inputArr[-1-i] == 0:
    i += 1
  return i

def roundTripTest(testCodec, plainData, useZeroSafeMethods=False, showDetails=False):
  #test the input testCodec on testData to make sure that it is capable of reconstructing its original input. If it isn't, print additional information before returning False.
  if isGen(plainData):
    plainData = makeArr(plainData)
  if type(plainData) == list:
    if len(plainData) == 0:
      print("CodecTools.roundTripTest: warning: plainData is empty.")
  pressData = testCodec.zeroSafeEncode(plainData) if useZeroSafeMethods else testCodec.encode(plainData)
  if isGen(pressData):
    pressData = makeArr(pressData)
  if type(pressData) == list:
    if len(pressData) == 0:
      print("CodecTools.roundTripTest: Warning: pressData is empty.")
  if showDetails:
    printComparison(plainData,pressData)
  reconstPlainData = testCodec.zeroSafeDecode(pressData) if useZeroSafeMethods else testCodec.decode(pressData)
  if isGen(reconstPlainData):
    reconstPlainData = makeArr(reconstPlainData)
  if type(reconstPlainData) == list:
    if len(reconstPlainData) == 0:
      print("CodecTools.roundTripTest: Warning: reconstPlainData is empty.")
  result = (reconstPlainData == plainData)
  if not result:
    print("CodecTools.roundTripTest: Test failed.")
    print("CodecTools.roundTripTest: testData is " + str(plainData) + " and reconstData is " + str(reconstPlainData) + ". pressData is " + str(pressData) + ".")
    if type(plainData) == list and type(reconstPlainData) == list:
      print("CodecTools.roundTripTest: Lengths " + ("do not" if len(reconstPlainData)==len(plainData) else "") + " differ.")
  return result


"""
class Infinity:
  def __init__(self,signSrc):
    self.sign = signSrc
    
  def __le__(self
"""

class InfiniteIntSeq:
  def __len__(self,testValue):
    print("CodecTools.InfiniteIntSeq.__len__: Warning: this method should not be called, because no correct integer response is possible. returning 2**32.")
    return 2**32


class IntRay(InfiniteIntSeq):
  def __init__(self,startValue,direction=1):
    if not direction in [1,-1]:
      raise ValueError("direction must be 1 or -1.")
    self.startValue, self.direction = (startValue, direction)
    
  def __contains__(self,testValue):
    if type(testValue) != int:
      return False
    if self.direction > 0:
      return testValue >= self.startValue
    else:
      return testValue <= self.startValue
      
  def __getitem__(self,index):
    return self.startValue + index*self.direction
    
  def index(self,value):
    if value != self.startValue:
      if type(value) != int:
        raise ValueError("Value not found, because it is not possible for a value of type {} to be found.".format(type(value)))
      if (value - self.startValue)*self.direction < 0:
        raise ValueError("Value not found.")
    result = abs(value - self.startValue)
    return result
    
  def __iter__(self):
    return itertools.count(self.startValue, self.direction)
    
    
class IntStaggering(InfiniteIntSeq):
  def __init__(self,startValue,direction=1):
    if not direction in [1,-1]:
      raise ValueError("direction must be 1 or -1.")
    self.startValue, self.direction = (startValue, direction)
    
  def __contains__(self,testValue):
    if type(testValue) != int:
      return False
    return True
    
  def __getitem__(self,index):
    raise NotImplementedError()
  def index(self,value):
    raise NotImplementedError()
  def __iter__(self):
    raise NotImplementedError()
    
simpleIntDomains = {"UNSIGNED":IntRay(0),"UNSIGNED_NONZERO":IntRay(1),"SIGNED":IntStaggering(0)}


class Codec:
  def __init__(self, encodeFun, decodeFun, transcodeFun=None, zeroSafe=None, domain=None, extraArgs=None, extraKwargs=None):
  
    #initialize transcoding functions:
    self.encodeFun, self.decodeFun, self.transcodeFun = (encodeFun, decodeFun, transcodeFun)
    if not (self.encodeFun or self.decodeFun or self.transcodeFun):
      print("CodecTools.Codec.__init__: Warning: No functions for encoding, decoding, or transcoding were specified! They must be added manually before transcoding can take place!")
      
    #initialize extra arguments:
    self.extraArgs, self.extraKwargs = (extraArgs if extraArgs else [], extraKwargs if extraKwargs else {})
    
    #initialize domain:
    if zeroSafe != None:
      print("CodecTools.Codec.__init__: Warning: initialization using the zeroSafe argument is deprecated. Please specify a domain instead. A domain will be assumed.")
      domain = simpleIntDomains["UNSIGNED" if zeroSafe else "UNSIGNED_NONZERO"]
    if domain == None:
      print("CodecTools.Codec.__init__: Warning: No domain was provided. Assuming UNSIGNED.")
      domain = simpleIntDomains["UNSIGNED"]
    elif type(domain) == str:
      if domain not in simpleIntDomains.keys():
        raise ValueError("the domain string argument is not a valid key for CodecTools.simpleIntDomains.")
      domain = simpleIntDomains[domain]
    self.domain = domain
    self.zeroSafe = (0 in self.domain) #remove soon.
    
  def getDomain(self):
    return self.domain
    
  def isZeroSafe(self):
    return 0 in self.getDomain()
    

  def encode(self,data,*args,**kwargs):
    if not (self.encodeFun or self.transcodeFun):
      raise AttributeError("Either encodeFun or transcodeFun must be defined to decode.")
    argsToUse = args if args else self.extraArgs #a single extra argument specified when calling Codec.encode will override ALL stored values in Codec.extraArgs.
    kwargsToUse = kwargs if kwargs else self.extraKwargs #a single extra keyword argument specified when calling Codec.encode will override ALL stored values in Codec.extraKwargs.
    if self.encodeFun:
      return self.encodeFun(data,*argsToUse,**kwargsToUse)
    else:
      return self.transcodeFun(data,"encode",*argsToUse,**kwargsToUse)

  def decode(self,data,*args,**kwargs):
    if not (self.decodeFun or self.transcodeFun):
      raise AttributeError("Either decodeFun or transcodeFun must be defined to decode.")
    argsToUse = args if args else self.extraArgs
    kwargsToUse = kwargs if kwargs else self.extraKwargs
    if self.decodeFun:
      return self.decodeFun(data,*argsToUse,**kwargsToUse)
    else:
      return self.transcodeFun(data,"decode",*argsToUse,**kwargsToUse)
      
  def zeroSafeEncode(self,data,*args,**kwargs):
    #will be replaced with domain comparisons soon.
    if self.isZeroSafe():
      return self.encode(data,*args,**kwargs)
    else:
      if type(data) == int:
        return self.encode(data+1,*args,**kwargs)
      elif isGen(data):
        return self.encode(genAddInt(data,1),*args,**kwargs)
      elif type(data) == list:
        return self.encode(arrAddInt(data,1),*args,**kwargs)
      else:
        raise NotImplementedError("CodecTools.Codec.zeroSafeEncode can't handle data of this type.")
        
  def zeroSafeDecode(self,data,*args,**kwargs):
    #will be replaced with domain comparisons soon.
    if self.isZeroSafe():
      return self.decode(data,*args,**kwargs)
    else:
      result = self.decode(data,*args,**kwargs)
      if type(result) == int:
        return result-1
      elif isGen(result):
        return genAddInt(result,-1)
      elif type(result) == list:
        return arrAddInt(result,-1)
      else:
        raise NotImplementedError("CodecTools.Codec.zeroSafeDecode can't handle data of this type.")
        
  def clone(self,extraArgs=None,extraKwargs=None):
    if self.extraArgs != [] and extraArgs != None:
      print("CodecTools.Codec.clone: warning: some existing extraArgs will not be cloned.")
    if self.extraKwargs != {} and extraKwargs != None:
      print("CodecTools.Codec.clone: warning: some existing extraKwargs will not be cloned.")
    argsToUse = extraArgs if extraArgs else self.extraArgs
    kwargsToUse = extraKwargs if extraKwargs else self.extraKwargs
    return Codec(self.encodeFun,self.decodeFun,transcodeFun=self.transcodeFun,domain=self.domain,extraArgs=argsToUse,extraKwargs=kwargsToUse)










def makePlatformCodec(platCodec, mainCodec):
  return Codec((lambda x: platCodec.encode(mainCodec.encode(platCodec.decode(x)))),(lambda y: platCodec.encode(mainCodec.decode(platCodec.decode(y)))))

def makePlainDataNumOffsetClone(mainCodec, offset): #used in MarkovTools.
  return Codec((lambda x: mainCodec.encode(x+offset)),(lambda y: mainCodec.decode(y)-offset))

def makeChainedPairCodec(codec1,codec2):
  return Codec((lambda x: codec2.encode(codec1.encode(x))),(lambda y: codec1.decode(codec2.decode(y))))


def makeSeqCodec(inputCodec,demoPlainData,zeroSafe):
  demoEncodeInputType = type(demoPlainData)
  demoPressData = inputCodec.encode(demoPlainData)
  demoEncodeOutputType = type(demoPressData)
  demoReconstPlainData = inputCodec.decode(demoPressData)
  demoDecodeOutputType = type(demoReconstPlainData)

  newEncodeFun = None
  if demoEncodeInputType == int:
    if demoEncodeOutputType == int:
      def newEncodeFun(encodeInputSeq):
        encodeInputSeq = makeGen(encodeInputSeq)
        for encodeInputSeqItem in encodeInputSeq:
          yield inputCodec.encode(encodeInputSeqItem) 
    elif demoEncodeOutputType == list or demoEncodeOutputType == type((i for i in range(10))):
      def newEncodeFun(encodeInputSeq):
        encodeInputSeq = makeGen(encodeInputSeq)
        for encodeInputSeqItem in encodeInputSeq:
          for encodeOutputBit in inputCodec.encode(encodeInputSeqItem):
            yield encodeOutputBit
    else:
      raise NotImplementedError("demoEncodeOutputType is not acceptable.")
  else:
    raise NotImplementedError("demoEncodeInputType is not acceptable.")

  newDecodeFun = None
  if demoEncodeOutputType == int:
    def newDecodeFun(decodeInputSeq):
      decodeInputSeq = makeGen(decodeInputSeq)
      for decodeInputSeqItem in decodeInputSeq:
        yield inputCodec.decode(decodeInputSeqItem)
  elif demoEncodeOutputType == list or demoEncodeOutputType == type((i for i in range(10))):
    def newDecodeFun(decodeInputSeq):
      decodeInputSeq = makeGen(decodeInputSeq)
      while True:
        try:
          yield inputCodec.decode(decodeInputSeq)
        except ExhaustionError:
          return
  else:
    raise NotImplementedError("demoEncodeOutputType is not acceptable.")

  result = Codec(newEncodeFun,newDecodeFun,zeroSafe=zeroSafe)
  return result



def genConcatenatedElements(sourcesArr):
  for source in sourcesArr:
    if type(source) == list or isGen(source):
      for outputElement in source:
        yield outputElement
    else:
      yield source

"""
#disabled because it might not be finishable as a non-sequential codec.
def makeUnlimitedNumCodecWithEscapeCode(inputLimitedNumCodec,inputUnlimitedNumCodec,escapeCode):

  assert escapeCode in inputLimitedNumCodec.domain
  assert 0 in inputLimitedNumCodec.domain, "currently, inputLimitedNumCodec must be zero-safe."
  assert 0 in inputUnlimitedNumCodec.domain,"currently, inputUnlimitedNumCodec must be zero-safe."
  for i in range(1,len(inputLimitedNumCodec.domain)):
    assert abs(inputLimitedNumCodec.domain[i]-inputLimitedNumCodec.domain[i-1]) == 1, "non-contiguous inputLimitedNumCodec domains are not supported."
  def limitedEncodeSafe(testValue):
    return testValue in inputLimitedNumCodec.domain and testValue != escapeCode
  def newEncodeFun(newEncInput):
    if limitedEncodeSafe(newEncInput):
      return inputLimitedNumCodec.encode(newEncInput)
    return genConcatenatedElements(inputLimitedNumCodec.
  def newDecodeFun(newDecInput):
    pass
  result = Codec(newEncodeFun,newDecodeFun,domain="UNSIGNED")
"""

def makeUnlimitedNumCodecWithSelectionBit(inputLimitedNumCodec,inputUnlimitedNumCodec):
  assert 0 in inputLimitedNumCodec.getDomain(), "currently, inputLimitedNumCodec must be zero-safe."
  assert 0 in inputUnlimitedNumCodec.getDomain(),"currently, inputUnlimitedNumCodec must be zero-safe."
  for i in range(1,len(inputLimitedNumCodec.domain)):
    assert abs(inputLimitedNumCodec.domain[i]-inputLimitedNumCodec.domain[i-1]) == 1, "non-contiguous inputLimitedNumCodec domains are not yet supported."

  def newEncodeFun(newEncInput):
    #use the tools designed for MarkovTools.
    pass
  def newDecodeFun(newDecInput):
    pass
  result = Codec(newEncodeFun,newDecodeFun,domain="UNSIGNED")





bitSeqToStrCodec = Codec((lambda x: "".join(str(item) for item in x)),(lambda x: [int(char) for char in x]))











#tests:

get_delimitedStr_codec = lambda delimiter: Codec((lambda x: delimiter.join(x)),(lambda x: x.split(delimiter)))

assert get_delimitedStr_codec("&").encode(["hello","world!"]) == "hello&world!"
assert get_delimitedStr_codec("&").decode("hello&world!") == ["hello","world!"]

del get_delimitedStr_codec
