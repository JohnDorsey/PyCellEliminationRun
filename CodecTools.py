"""

CodecTools.py by John Dorsey.

CodecTools.py contains classes and other tools that might help make it easier to rapidly create and test codecs made from smaller codecs applied in stages.

"""

from PyGenTools import makeArr, isGen



def roundTripTest(testCodec, testData):
  #test the input testCodec on testData to make sure that it is capable of reconstructing its original input. If it isn't, print additional information before returning False.
  reconstData = testCodec.decode(testCodec.encode(testData))
  if isGen(reconstData):
    reconstData = makeArr(reconstData)
  result = (reconstData == testData)
  if not result:
    print("CodecTools.roundTripTest: Test failed.")
    print("CodecTools.roundTripTest: Lengths " + ("do not" if len(reconstData)==len(testData) else "") + " differ. testData is " + str(testData) + " and reconstData is " + str(reconstData) + ".")
  return result


def makePlatformCodec(platCodec, mainCodec):
  return Codec((lambda x: platCodec.encode(mainCodec.encode(platCodec.decode(x)))),(lambda x: platCodec.encode(mainCodec.decode(platCodec.decode(x)))))


def makeChainedPairCodec(codec1,codec2):
  return Codec((lambda x: codec2.encode(codec1.encode(x))),(lambda x: codec1.decode(codec2.decode(x))))


class Codec:
  def __init__(self,encodeFun,decodeFun):
    self.encode, self.decode = (encodeFun, decodeFun)
  
  def encode(self,data):
    assert False, "Codec.encode not implemented."

  def decode(self,data):
    assert False, "Codec.decode not implemented."

  def getReversedCopy(self):
    return Codec(self.decode,self.encode)


"""
class NonStreamingCodec(Codec):
  def __init__(self,encodeFun,decodeFun):
    self.encode, self.decode = (encodeFun, decodeFun)
  
  def encode(self,data):
    assert False, "NonStreamingCoded.encode not implemented."

  def decode(self,data):
    assert False, "NonStreamingCodec.decode not implemented."


class StreamingCodec(Codec):
  def __init__(self,encodeFun,decodeFun):
    self.encode, self.decode = (encodeFun, decodeFun)
  
  def encode(self,data):
    assert False, "StreamingCodec.encode not implemented."

  def decode(self,data):
    assert False, "StreamingCodec.decode not implemented."
"""





bitSeqToStrCodec = Codec((lambda x: "".join(str(item) for item in x)),(lambda x: [int(char) for char in x]))











#tests:

get_delimitedStr_codec = lambda delimiter: Codec((lambda x: delimiter.join(x)),(lambda x: x.split(delimiter)))

assert get_delimitedStr_codec("&").encode(["hello","world!"]) == "hello&world!"
assert get_delimitedStr_codec("&").decode("hello&world!") == ["hello","world!"]

del get_delimitedStr_codec

def genDelimitedStrEncode(x,delimiter):
  justStarted = True
  for item in x:
    if justStarted:
      justStarted = False
    else:
      yield delimiter
    for char in item:
      yield char
def genDelimitedStrDecode(x,delimiter):
  currentItem = ""
  for char in x:
    if char == delimiter:
      yield currentItem
      currentItem = ""
    else:
      currentItem += char
  yield currentItem

"""
get_SC_delimitedStr = lambda delimiter: StreamingCodec((lambda x: genDelimitedStrEncode(x,delimiter)),(lambda x: genDelimitedStrDecode(x,delimiter)))

assert type(get_SC_delimitedStr("&").encode((item for item in ["hello","world!"]))) == type((i for i in range(10)))
assert type(get_SC_delimitedStr("&").decode((char for char in "hello&world!"))) == type((i for i in range(10)))
assert [char for char in get_SC_delimitedStr("&").encode((item for item in ["hello","world!"]))] == [char for char in "hello&world!"]
assert [word for word in get_SC_delimitedStr("&").decode((char for char in "hello&world!"))] == ["hello","world!"]

del get_SC_delimitedStr
"""

del genDelimitedStrEncode
del genDelimitedStrDecode
