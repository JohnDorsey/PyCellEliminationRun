"""

CodecTools.py by John Dorsey.

CodecTools.py contains classes and other tools that might help make it easier to rapidly create and test codecs made from smaller codecs applied in stages.

"""


def roundTripTest(testCodec, testData):
  return testCodec.decode(testCodec.encode(testData)) == testData


class Codec:
  def __init__(self,encodeFun,decodeFun):
    self.encode, self.decode = (encodeFun, decodeFun)
  
  def encode(self,data):
    assert False, "Codec.encode not implemented."

  def decode(self,data):
    assert False, "Codec.decode not implemented."


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





get_NSC_delimitedStr = lambda delimiter: NonStreamingCodec((lambda x: delimiter.join(x)),(lambda x: x.split(delimiter)))

assert get_NSC_delimitedStr("&").encode(["hello","world!"]) == "hello&world!"
assert get_NSC_delimitedStr("&").decode("hello&world!") == ["hello","world!"]

del get_NSC_delimitedStr

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

get_SC_delimitedStr = lambda delimiter: StreamingCodec((lambda x: genDelimitedStrEncode(x,delimiter)),(lambda x: genDelimitedStrDecode(x,delimiter)))

assert type(get_SC_delimitedStr("&").encode((item for item in ["hello","world!"]))) == type((i for i in range(10)))
assert type(get_SC_delimitedStr("&").decode((char for char in "hello&world!"))) == type((i for i in range(10)))
assert [char for char in get_SC_delimitedStr("&").encode((item for item in ["hello","world!"]))] == [char for char in "hello&world!"]
assert [word for word in get_SC_delimitedStr("&").decode((char for char in "hello&world!"))] == ["hello","world!"]

del genDelimitedStrEncode
del genDelimitedStrDecode
del get_SC_delimitedStr

