"""

PresetTools.py by John Dorsey.

PresetTools.py contains tools for creating and manipulating preset data and using it to create or train codecs.

Note: to see which presets exist in PresetData.py without scrolling through it, import it into python and read PresetData.__dict__.keys().

"""


import PresetData
import HuffmanMath
import StatCurveTools
import CodecTools


cerNumHuffmanCodecs = {}
cerBlockHuffmanCodecs = {}


def makeCerNumHuffmanCodec(inputData,extendToHeight=0,cutToHeight=None):
  print("PresetTools.makeCerNumHuffmanCodec: started.")
  assert type(inputData) in [str,list]
  if type(inputData) == str: #if it is the name of a preset...
    inputData = PresetData.__dict__[inputData]
  assert type(inputData) == list
  if not cutToHeight == None:
    inputData = inputData[:cutToHeight]
  probabilityDistribution = StatCurveTools.makeAutoBlurredListHist(inputData)
  StatCurveTools.extendListHistMinimally(probabilityDistribution, extendToHeight)
  print("PresetTools.makeCerNumHuffmanCodec: continuing to HuffmanCodec creation using probabilityDistribution of length {}.".format(len(probabilityDistribution)))
  return HuffmanMath.makeHuffmanCodecFromListHist(probabilityDistribution)
  
  
def makeCerBlockHuffmanCodec(inputData,extendToHeight=0):
  print("making new cerBlockHuffmanCodec...")
  assert type(inputData) in [str,list]
  if type(inputData) == str: #if it is the name of a preset...
    inputData = PresetData.__dict__[inputData]
  assert type(inputData) == list
  newCodec = CodecTools.Codec(None,None,None,zeroSafe=True)
  newCodec.huffmanCodecsByColumn = []
  backgroundData = StatCurveTools.vectorSum(inputData)
  for columnData in inputData:
    assert type(columnData) == list
    strongColumnData = StatCurveTools.scaledVector(columnData,len(inputData)) #this should make the columnData expressed about as strongly as the rest of the data combined.
    backedColumnData = StatCurveTools.vectorSum([backgroundData,strongColumnData])
    newCodec.huffmanCodecsByColumn.append(makeCerNumHuffmanCodec(backedColumnData,extendToHeight))
  def newEncodeFun(newEncDataInput):
    for iEnc,itemEnc in enumerate(newEncDataInput):
      for outputBit in newCodec.huffmanCodecsByColumn[iEnc].encode(itemEnc):
        yield outputBit
  def newDecodeFun(newDecDataInput):
    for iDec,itemDec in enumerate(newDecDataInput):
      yield newCodec.huffmanCodecsByColumn[iDec].decode(itemDec)
  newCodec.encodeFun = newEncodeFun
  newCodec.decodeFun = newDecodeFun
  return newCodec
  


  
  

cerNumHuffmanCodecs["linear_1024x256_moo_short"] = makeCerNumHuffmanCodec("CER_linear_1024_moo8bmono44100_id0_short_collectedData_all",extendToHeight=1)
cerNumHuffmanCodecs["linear_512x256_moo"] = makeCerNumHuffmanCodec("CER_linear_512_moo8bmono44100_id0_complete_every16_collectedData_all",extendToHeight=1)


#these could each take more than a hundred hours to build, even with pypy.
"""
cerBlockHuffmanCodecs["linear_1024x256_moo_short"] = makeCerBlockHuffmanCodec("CER_linear_1024_moo8bmono44100_id0_short_collectedData_by_column")
cerBlockHuffmanCodecs["linear_512x256_moo_short"] = makeCerBlockHuffmanCodec("CER_linear_512_moo8bmono44100_id0_complete_every16_collectedData_all_by_column")
"""




