"""

CodecTools.py by John Dorsey.

CodecTools.py contains classes and other tools that might help make it easier to rapidly create and test codecs made from smaller codecs applied in stages.

"""

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
      print("CodecTools.roundTripTest: warning: pressData is empty.")
  if showDetails:
    printComparison(plainData,pressData)
  reconstPlainData = testCodec.zeroSafeDecode(pressData) if useZeroSafeMethods else testCodec.decode(pressData)
  if isGen(reconstPlainData):
    reconstPlainData = makeArr(reconstPlainData)
  if type(reconstPlainData) == list:
    if len(reconstPlainData) == 0:
      print("CodecTools.roundTripTest: warning: reconstPlainData is empty.")
  result = (reconstPlainData == plainData)
  if not result:
    print("CodecTools.roundTripTest: Test failed.")
    print("CodecTools.roundTripTest: testData is " + str(plainData) + " and reconstData is " + str(reconstPlainData) + ". pressData is " + str(pressData) + ".")
    if type(plainData) == list and type(reconstPlainData) == list:
      print("CodecTools.roundTripTest: Lengths " + ("do not" if len(reconstPlainData)==len(plainData) else "") + " differ.")
  return result


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


class Codec:
  def __init__(self,encodeFun,decodeFun,transcodeFun=None,zeroSafe=None,extraArgs=None,extraKwargs=None):
    self.encodeFun, self.decodeFun, self.transcodeFun, self.zeroSafe = (encodeFun, decodeFun, transcodeFun, zeroSafe)
    if not (self.encodeFun or self.decodeFun or self.transcodeFun):
      print("CodecTools.Codec.__init__: No functions for encoding, decoding, or transcoding were specified! They must be added manually before transcoding can take place!")
    self.extraArgs, self.extraKwargs = (extraArgs if extraArgs else [], extraKwargs if extraKwargs else {})

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
    if self.zeroSafe:
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
    if self.zeroSafe:
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
    return Codec(self.encodeFun,self.decodeFun,transcodeFun=self.transcodeFun,zeroSafe=self.zeroSafe,extraArgs=argsToUse,extraKwargs=kwargsToUse)

  """
  def getMinPlainValue(self):
    if self.zeroSafe == None:
      print("CodecTools.Codec.getMinPlainValue: warning: zeroSafe was not set. assuming the codec is not zeroSafe.")
    return 0 if self.zeroSafe else 1
  """



bitSeqToStrCodec = Codec((lambda x: "".join(str(item) for item in x)),(lambda x: [int(char) for char in x]))











#tests:

get_delimitedStr_codec = lambda delimiter: Codec((lambda x: delimiter.join(x)),(lambda x: x.split(delimiter)))

assert get_delimitedStr_codec("&").encode(["hello","world!"]) == "hello&world!"
assert get_delimitedStr_codec("&").decode("hello&world!") == ["hello","world!"]

del get_delimitedStr_codec
