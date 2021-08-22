"""

CodecTools.py by John Dorsey.

CodecTools.py contains classes and other tools that might help make it easier to rapidly create and test codecs made from smaller codecs applied in stages.

"""



import traceback

import PyGenTools
from PyGenTools import makeArr, isGen, makeGen, ExhaustionError, genAddInt, arrAddInt
from PyArrTools import ljustedArr
from PyDictTools import augmentedDict

from IntDomains import simpleIntDomains

from TestingTools import printComparison



class ParseError(Exception):
  pass



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
      #print("CodecTools.Codec.__init__: Warning: No domain was provided.")
      #domain = simpleIntDomains["UNSIGNED"]
      pass
    elif type(domain) == str:
      if domain not in simpleIntDomains.keys():
        raise ValueError("the domain string argument is not a valid key for CodecTools.simpleIntDomains.")
      domain = simpleIntDomains[domain]
    self._domain = domain
    #self.zeroSafe = (0 in self.domain) #remove soon.
    
  def getDomain(self):
    if self._domain == None:
      raise AttributeError("No Codec domain was provided.")
    return self._domain
    
  def isZeroSafe(self):
    #print("CodecTools.Codec.isZeroSafe: this method is deprecated.")
    return 0 in self.getDomain()
    

  def encode(self,data,*args,**kwargs):
    if not (self.encodeFun or self.transcodeFun):
      raise AttributeError("Either encodeFun or transcodeFun must be defined to decode.")
    #argsToUse = args if args else self.extraArgs #a single extra argument specified when calling Codec.encode will override ALL stored values in Codec.extraArgs.
    #kwargsToUse = kwargs if kwargs else self.extraKwargs #a single extra keyword argument specified when calling Codec.encode will override ALL stored values in Codec.extraKwargs.
    if args and self.extraArgs:
      print("CodecTools.Codec.encode: warning: some args may be excluded.")
    argsToUse = args if args else self.extraArgs
    kwargsToUse = augmentedDict(kwargs, self.extraKwargs)
    if self.encodeFun:
      return self.encodeFun(data,*argsToUse,**kwargsToUse)
    else:
      return self.transcodeFun(data,"encode",*argsToUse,**kwargsToUse)

  def decode(self,data,*args,**kwargs):
    if not (self.decodeFun or self.transcodeFun):
      raise AttributeError("Either decodeFun or transcodeFun must be defined to decode.")
    #argsToUse = args if args else self.extraArgs
    #kwargsToUse = kwargs if kwargs else self.extraKwargs
    if args and self.extraArgs:
      print("CodecTools.Codec.encode: warning: some args may be excluded.")
    argsToUse = args if args else self.extraArgs
    kwargsToUse = augmentedDict(kwargs, self.extraKwargs)
    if self.decodeFun:
      return self.decodeFun(data,*argsToUse,**kwargsToUse)
    else:
      return self.transcodeFun(data,"decode",*argsToUse,**kwargsToUse)
      
  def zeroSafeEncode(self,data,*args,**kwargs):
    #will be replaced with domain comparisons soon.
    if self.isZeroSafe():
      dataToUse = data
      #return self.encode(data,*args,**kwargs)
    else:
      maxInputInt = kwargs.get("maxInputInt",None)
      if maxInputInt != None:
        kwargs["maxInputInt"] = maxInputInt+1
      if "seqSum" in kwargs:
        print("CodecTools.zeroSafeEncode: warning: can't adjust seqSum.")
        
      if type(data) == int:
        #return self.encode(data+1,*args,**kwargs)
        dataToUse = data+1
      elif isGen(data):
        #return self.encode(genAddInt(data,1),*args,**kwargs)
        dataToUse = genAddInt(data,1)
      elif type(data) == list:
        #return self.encode(arrAddInt(data,1),*args,**kwargs)
        dataToUse = arrAddInt(data,1)
      else:
        raise NotImplementedError("CodecTools.Codec.zeroSafeEncode can't handle data of this type.")
    try:
      return self.encode(dataToUse,*args,**kwargs)
    except AssertionError as ae:
      print("AssertionError encountered. Args were {}, kwargs were {}. Error will be re-raised.".format(args,kwargs))
      print(traceback.format_exc())
      raise ae
        
        
  def zeroSafeDecode(self,data,*args,**kwargs):
    #will be replaced with domain comparisons soon.
    if not self.isZeroSafe():
      maxInputInt = kwargs.get("maxInputInt",None)
      if maxInputInt != None:
        kwargs["maxInputInt"] = maxInputInt+1
      if "seqSum" in kwargs:
        print("CodecTools.zeroSafeDecode: warning: can't adjust seqSum.")
      
    try:      
      result = self.decode(data,*args,**kwargs)
    except AssertionError as ae:
      print("AssertionError encountered. Args were {}, kwargs were {}. Error will be re-raised.".format(args,kwargs))
      print(traceback.format_exc())
      raise ae
      
    if self.isZeroSafe():
      return result
    else:
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
      print("CodecTools.Codec.clone: warning: some existing extraKwargs may not be cloned.")
    argsToUse = extraArgs if extraArgs else self.extraArgs
    kwargsToUse = augmentedDict(extraKwargs, self.extraKwargs)
    return Codec(self.encodeFun, self.decodeFun, transcodeFun=self.transcodeFun, domain=self._domain, extraArgs=argsToUse, extraKwargs=kwargsToUse)










def makePlatformCodec(platCodec, mainCodec):
  return Codec((lambda x: platCodec.encode(mainCodec.encode(platCodec.decode(x)))), (lambda y: platCodec.encode(mainCodec.decode(platCodec.decode(y)))))

def makePlainDataNumOffsetClone(mainCodec, offset): #used in MarkovTools.
  return Codec((lambda x: mainCodec.encode(x+offset)), (lambda y: mainCodec.decode(y)-offset))

def makeChainedPairCodec(codec1,codec2):
  return Codec((lambda x: codec2.encode(codec1.encode(x))), (lambda y: codec1.decode(codec2.decode(y))))


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



def genConcatenatedElements(sourcesArr): #used only by makeUnlimitedNumCodecWithEscapeCode.
  for source in sourcesArr:
    if type(source) == list or isGen(source):
      for outputElement in source:
        yield outputElement
    else:
      yield source




def remapToOutsideValueArrTranscode(inputValue,opMode,predictedValues): #used in CodecTools and MarkovTools.
  if opMode == "encode":
    return inputValue - len([predictedValue for predictedValue in predictedValues if predictedValue < inputValue])
  elif opMode == "decode":
    return inputValue + len([predictedValue for predictedValue in predictedValues if predictedValue < inputValue])
  else:
    assert False, "invalid opMode."
    
  
def remapToValueArrTranscode(inputValue,opMode,predictedValues):
  if opMode not in ["encode","decode"]:
    raise ValueError("invalid opMode.")
  if opMode == "encode":
    if inputValue in predictedValues:
      resultValue = predictedValues.index(inputValue)
    else:
      resultValue = remapToOutsideValueArrTranscode(inputValue,opMode,predictedValues) + len(predictedValues)
  elif opMode == "decode":
    if inputValue < len(predictedValues):
      resultValue = predictedValues[inputValue]
    else:
      resultValue = remapToOutsideValueArrTranscode(inputValue,opMode,predictedValues) - len(predictedValues)
  else:
    assert False, "reality error."
  return resultValue
  
remapToValueArrCodec = Codec(None,None,transcodeFun=remapToValueArrTranscode)



def makeUnlimitedNumCodecWithSelectionBit(inputLimitedNumCodec,inputUnlimitedNumCodec):
  if not inputLimitedNumCodec.isZeroSafe():
    print("CodecTools.makeUnlimitedNumCodecWithSelectionBit: warning: inputLimitedNumCodec is not zero safe, which may reduce CR.")
  #for i in range(1,len(inputLimitedNumCodec.getDomain())):
  #  assert abs(inputLimitedNumCodec.getDomain()[i]-inputLimitedNumCodec.getDomain()[i-1]) == 1, "non-contiguous inputLimitedNumCodec domains are not yet supported."

  def newEncodeFun(newEncInput):
    if newEncInput in inputLimitedNumCodec.getDomain():
      return genConcatenatedElements([0,inputLimitedNumCodec.zeroSafeEncode(newEncInput)])
    else:
      return genConcatenatedElements([1,inputUnlimitedNumCodec.zeroSafeEncode(remapToOutsideValueArrTranscode(newEncInput,"encode",inputLimitedNumCodec.getDomain()))])
      
  def newDecodeFun(newDecInput):
    newDecInput = makeGen(newDecInput)
    selectionBit = None
    try:
      selectionBit = next(newDecInput)
    except StopIteration:
      raise ExhaustionError("CodecTools.makeUnlimitedNumCodecWithSelectionBit-made-CodecTools.Codec: newDecodeFun: Received an empty newDecInput.")
    if selectionBit == 0:
      return inputLimitedNumCodec.zeroSafeDecode(newDecInput)
    elif selectionBit == 1:
      valueBeforeRemapping = inputUnlimitedNumCodec.zeroSafeDecode(newDecInput)
      return remapToOutsideValueArrTranscode(valueBeforeRemapping,"decode",inputLimitedNumCodec.getDomain())
    else:
      raise ParseError("CodecTools.makeUnlimitedNumCodecWithSelectionBit-made-CodecTools.Codec: newDecodeFun: Received an invalid selection bit with the value " + str(selectionBit) + ".")
      
  result = Codec(newEncodeFun,newDecodeFun,domain="UNSIGNED")
  return result


def makeUnlimitedNumCodecWithEscapeCode(inputLimitedNumCodec,inputUnlimitedNumCodec,escapeCode):
  if not inputLimitedNumCodec.isZeroSafe():
    print("CodecTools.makeUnlimitedNumCodecWithSelectionBit: warning: inputLimitedNumCodec is not zero safe, which may reduce CR.")
  assert escapeCode in inputLimitedNumCodec.getDomain()
  
  noEscapeDomain = [item for item in inputLimitedNumCodec.getDomain() if item != escapeCode] #@ slow. Slow to search through later.

  storableWithoutEscape = (lambda x: x in inputLimitedNumCodec.getDomain() and x != escapeCode)

  def newEncodeFun(newEncInput):
    if storableWithoutEscape(newEncInput):
      return genConcatenatedElements([inputLimitedNumCodec.zeroSafeEncode(newEncInput)])
    else:
      return genConcatenatedElements([inputLimitedNumCodec.zeroSafeEncode(escapeCode), inputUnlimitedNumCodec.zeroSafeEncode(remapToOutsideValueArrTranscode(newEncInput, "encode", noEscapeDomain))])
      
  def newDecodeFun(newDecInput):
    newDecInput = makeGen(newDecInput)
    limitedResult = inputLimitedNumCodec.zeroSafeDecode(newDecInput)
    if limitedResult != escapeCode:
      return limitedResult
    else:
      valueBeforeRemapping = inputUnlimitedNumCodec.zeroSafeDecode(newDecInput)
      return remapToOutsideValueArrTranscode(valueBeforeRemapping,"decode",noEscapeDomain)

  result = Codec(newEncodeFun,newDecodeFun,domain="UNSIGNED")
  return result





bitSeqToStrCodec = Codec((lambda x: "".join(str(item) for item in x)),(lambda x: [int(char) for char in x]))

def bitSeqToBytearray(inputBitSeq):
  return bytearray(int("".join(str(bit) for bit in ljustedArr(subSeq,8,fillItem=0)), 2) for subSeq in PyGenTools.genChunksAsLists(inputBitSeq, n=8, partialChunkHandling="warn partial"))

def bytearrayToBitSeq(inputBytearray):
  raise NotImplementedError()
  
bitSeqToBytearrayCodec = Codec(bitSeqToBytearray, bytearrayToBitSeq, domain=range(0,256)) #@ might break in python3





#tests:

get_delimitedStr_codec = lambda delimiter: Codec((lambda x: delimiter.join(x)),(lambda x: x.split(delimiter)))

assert get_delimitedStr_codec("&").encode(["hello","world!"]) == "hello&world!"
assert get_delimitedStr_codec("&").decode("hello&world!") == ["hello","world!"]

del get_delimitedStr_codec
