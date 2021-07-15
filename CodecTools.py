"""

CodecTools.py by John Dorsey.

CodecTools.py contains classes and other tools that might help make it easier to rapidly create and test codecs made from smaller codecs applied in stages.

"""

from PyGenTools import makeArr, isGen


def measureIntArray(inputIntArr):
  rectSize = (len(inputIntArr),len(bin(max(inputIntArr))[2:]))
  return {"length":rectSize[0],"bit_depth":rectSize[1],"area":rectSize[0]*rectSize[1]}


def roundTripTest(testCodec, plainData, showDetails=False):
  #test the input testCodec on testData to make sure that it is capable of reconstructing its original input. If it isn't, print additional information before returning False.
  if isGen(plainData):
    plainData = makeArr(plainData)
  pressData = testCodec.encode(plainData)
  if isGen(pressData):
    pressData = makeArr(pressData)
  if showDetails:
    print("plainData measures " + str(measureIntArray(plainData)) + ".")
    print("pressData measures " + str(measureIntArray(pressData)) + ".")
  reconstPlainData = testCodec.decode(pressData)
  if isGen(reconstPlainData):
    reconstPlainData = makeArr(reconstPlainData)
  result = (reconstPlainData == plainData)
  if not result:
    print("CodecTools.roundTripTest: Test failed.")
    print("CodecTools.roundTripTest: testData is " + str(plainData) + " and reconstData is " + str(reconstPlainData) + ".")
    if type(plainData) == list and type(reconstPlainData) == list:
      print("CodecTools.roundTripTest: Lengths " + ("do not" if len(reconstPlainData)==len(plainData) else "") + " differ.")
  return result


def makePlatformCodec(platCodec, mainCodec):
  return Codec((lambda x: platCodec.encode(mainCodec.encode(platCodec.decode(x)))),(lambda x: platCodec.encode(mainCodec.decode(platCodec.decode(x)))))


def makeChainedPairCodec(codec1,codec2):
  return Codec((lambda x: codec2.encode(codec1.encode(x))),(lambda x: codec1.decode(codec2.decode(x))))


class Codec:
  def __init__(self,encodeFun,decodeFun,extraArgs=None,extraKwargs=None):
    self.encodeFun, self.decodeFun = (encodeFun, decodeFun)
    self.extraArgs, self.extraKwargs = (extraArgs if extraArgs else [], extraKwargs if extraKwargs else {})

  def encode(self,data,*args,**kwargs):
    argsToUse = args if args else self.extraArgs #a single extra argument specified when calling Codec.encode will override ALL stored values in Codec.extraArgs.
    kwargsToUse = kwargs if kwargs else self.extraKwargs #a single extra keyword argument specified when calling Codec.encode will override ALL stored values in Codec.extraKwargs.
    return self.encodeFun(data,*argsToUse,**kwargsToUse)

  def decode(self,data,*args,**kwargs):
    argsToUse = args if args else self.extraArgs
    kwargsToUse = kwargs if kwargs else self.extraKwargs
    return self.decodeFun(data,*argsToUse,**kwargsToUse)

  def clone(self,extraArgs=None,extraKwargs=None):
    if self.extraArgs != [] and extraArgs != None:
      print("CodecTools.Codec.clone: warning: some existing extraArgs will not be cloned.")
    if self.extraKwargs != {} and extraKwargs != None:
      print("CodecTools.Codec.clone: warning: some existing extraKwargs will not be cloned.")
    argsToUse = extraArgs if extraArgs else self.extraArgs
    kwargsToUse = extraKwargs if extraKwargs else self.extraKwargs
    return Codec(self.encodeFun,self.decodeFun,extraArgs=argsToUse,extraKwargs=kwargsToUse)







bitSeqToStrCodec = Codec((lambda x: "".join(str(item) for item in x)),(lambda x: [int(char) for char in x]))











#tests:

get_delimitedStr_codec = lambda delimiter: Codec((lambda x: delimiter.join(x)),(lambda x: x.split(delimiter)))

assert get_delimitedStr_codec("&").encode(["hello","world!"]) == "hello&world!"
assert get_delimitedStr_codec("&").decode("hello&world!") == ["hello","world!"]

del get_delimitedStr_codec
