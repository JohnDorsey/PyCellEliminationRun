"""

PresetTools.py by John Dorsey.

PresetTools.py contains tools for creating and manipulating preset data and using it to create or train codecs.

Note: to see which presets exist in PresetData.py without scrolling through it, import it into python and read PresetData.__dict__.keys().

"""


import HuffmanMath
import StatCurveTools
import CodecTools
import Codes


print("PresetTools: importing PresetData...")
import PresetData

limitedCerNumCodecs = dict()

try:
  preserveLen = len(limitedCerBlockCodecs)
  print("The dictionary PresetTools.limitedCerBlockCodecs with {} items has been preserved.".format(preserveLen))
except:
  limitedCerBlockCodecs = dict()
  
try:
  preserveLen = len(unlimitedCerBlockCodecs)
  print("The dictionary PresetTools.unlimitedCerBlockCodecs with {} items has been preserved.".format(preserveLen))
except:
  unlimitedCerBlockCodecs = dict()


def makeCerNumTreeBasedCodec(inputData, extendToHeight=0, cutToHeight=None, treeType=None): # -> HuffmanMath.HuffmanCodec:
  print("PresetTools.makeCerNumTreeBasedCodec: started.")
  assert type(inputData) in [str,list]
  if type(inputData) == str: #if it is the name of a preset...
    inputData = PresetData.__dict__[inputData]
  assert type(inputData) == list
  probabilityDistribution = StatCurveTools.makeAutoBlurredListHist(inputData)
  StatCurveTools.extendListHistMinimally(probabilityDistribution, extendToHeight)
  if not cutToHeight == None:
    probabilityDistribution = probabilityDistribution[:cutToHeight]
  print("PresetTools.makeCerNumTreeBasedCodec: continuing to TreeBasedCodec creation using probabilityDistribution of length {}.".format(len(probabilityDistribution)))
  return HuffmanMath.makeTreeBasedCodecFromListHist(probabilityDistribution, treeType=treeType)
  
  
def makeSubdividedCodec(zeroSafe=None,domain=None): # -> CodecTools.Codec:
  newCodec = CodecTools.Codec(None,None,zeroSafe=zeroSafe,domain=domain)
  newCodec.extraDataDict = dict()
  newCodec.extraDataDict["subCodecs"] = []
  def newEncodeFun(encInput,encSubdivisionIndex):
    requestedCodec = None
    try:
      requestedCodec = newCodec.extraDataDict["subCodecs"][encSubdivisionIndex]
    except IndexError:
      raise IndexError("PresetTools.makeSubdividedCodec-made CodecTools.Codec instance: while encoding: encSubdivisionIndex is out of bounds!")
    for outputElement in requestedCodec.encode(encInput): #outputElement is probably a bit.
      yield outputElement
  def newDecodeFun(decInput,decSubdivisionIndex):
    requestedCodec = None
    try:
      requestedCodec = newCodec.extraDataDict["subCodecs"][decSubdivisionIndex]
    except IndexError:
      raise IndexError("PresetTools.makeSubdividedCodec-made CodecTools.Codec instance: while decoding: decSubdivisionIndex is out of bounds!")
    return requestedCodec.decode(decInput)
  newCodec.encodeFun = newEncodeFun
  newCodec.decodeFun = newDecodeFun
  return newCodec
  
def makeColumnAwareSeqCodec(baseSubdividedCodec,zeroSafe=None,domain=None): # -> CodecTools.Codec:
  newCodec = CodecTools.Codec(None,None,zeroSafe=zeroSafe,domain=domain)
  newCodec.extraDataDict = dict()
  newCodec.extraDataDict["baseSubdividedCodec"] = baseSubdividedCodec
  def newEncodeFun(encInput):
    for iEnc,itemEnc in enumerate(encInput):
      for outputElement in newCodec.extraDataDict["baseSubdividedCodec"].encode(itemEnc,iEnc): #outputElement is probably a bit.
        yield outputElement
  def newDecodeFun(decInput):
    iDec = 0
    while True:
      yield newCodec.extraDataDict["baseSubdividedCodec"].decode(decInput)
      iDec += 1
  newCodec.encodeFun = newEncodeFun
  newCodec.decodeFun = newDecodeFun
  return newCodec
  
def makeCerBlockTreeBasedCodec(inputData,treeType=None,extendToHeight=0,cutToHeight=None,subCodecTransformerFun=None,dbgPrintInterval=8): # -> CodecTools.Codec:
  print("making new cerBlockTreeBasedCodec: started.")
  assert type(inputData) in [str,list]
  if type(inputData) == str: #if it is the name of a preset...
    inputData = PresetData.__dict__[inputData]
  assert type(inputData) == list
  if subCodecTransformerFun == None: #this feature exists entirely to fill the need of applying escape code logic to the output codec.
    subCodecTransformerFun = (lambda x: x)
    
  subdividedCodec = makeSubdividedCodec(zeroSafe=True)
  backgroundData = StatCurveTools.vectorSum(inputData)
  for columnIndex,columnData in enumerate(inputData):
    if columnIndex%dbgPrintInterval == 0 and columnIndex != 0:
      print("columnIndex="+str(columnIndex)+".")
    assert type(columnData) == list
    strongColumnData = StatCurveTools.scaledVector(columnData,len(inputData)) #this should make the columnData expressed about as strongly as the rest of the data combined.
    backedColumnData = StatCurveTools.vectorSum([backgroundData,strongColumnData])
    newSubCodec = makeCerNumHuffmanCodec(backedColumnData, treeType=treeType, extendToHeight=extendToHeight, cutToHeight=cutToHeight)
    newSubCodec = subCodecTransformerFun(newSubCodec)
    subdividedCodec.extraDataDict["subCodecs"].append(newSubCodec)
  newCodec = makeColumnAwareSeqCodec(subdividedCodec,zeroSafe=True)
  return newCodec
  


  
  

limitedCerNumCodecs["linear_1024x256_moo_short_sub4096_Huffman"] = makeCerNumHuffmanCodec("CER_linear_1024_moo8bmono44100_id0_short_collectedData_all", extendToHeight=1, cutToHeight=4096)
limitedCerNumCodecs["linear_512x256_moo_sub4096_Huffman"] = makeCerNumHuffmanCodec("CER_linear_512_moo8bmono44100_id0_complete_every16_collectedData_all", extendToHeight=1, cutToHeight=4096)


quickUnlockers = dict()
quickUnlockers["selectionBit"] = lambda codecToUnlock: CodecTools.makeUnlimitedNumCodecWithSelectionBit(codecToUnlock, Codes.codecs["fibonacci"])
quickUnlockers["escapeCode"] = lambda codecToUnlock: CodecTools.makeUnlimitedNumCodecWithEscapeCode(codecToUnlock, Codes.codecs["fibonacci"], max(codecToUnlock.getDomain()))


unlimitedCerNumCodecs = dict()
for key in limitedCerNumCodecs:
  unlimitedCerNumCodecs[key+"_selectionBit_switch_to_fibonacci"] = quickSelectionBitUnlock(limitedCerNumCodecs[key])
  unlimitedCerNumCodecs[key+"_escapeCode_switch_to_fibonacci"] = quickEscapeCodeUnlock(limitedCerNumCodecs[key])





def prepareLimitedCerBlockCodecs():
  limitedCerBlockHuffmanCodecs["linear_1024x256_moo_short_sub256_Huffman"] = makeCerBlockHuffmanCodec("CER_linear_1024_moo8bmono44100_id0_short_collectedData_by_column", extendToHeight=256, cutToHeight=256)
  limitedCerBlockHuffmanCodecs["linear_512x256_moo_short_sub256_Huffman"] = makeCerBlockHuffmanCodec("CER_linear_512_moo8bmono44100_id0_complete_every16_collectedData_all_by_column", extendToHeight=256, cutToHeight=256)

def prepareUnlimitedCerBlockCodecsFromScratch(keepOld,transitionHeight):
  for blockSizeHoriz in [1024,512,256]:
    for switchMode in ["selectionBit","escapeCode"]:
      sourceName = "CER_linear_{}_moo8bmono44100_{}_collectedData_all_by_column".format(blockSizeHoriz,{1024:"id0_short",512:"id0_complete_every16",256:"id0_complete_every16"}[blockSizeHoriz]) #@ This must be fixed soon.
      destinationName = "linear_{}x256_moo_short_sub{}_Huffman_{}_switch_to_fibonacci".format(blockSizeHoriz,transitionHeight,switchMode)
      if keepOld and destinationName in unlimitedCerBlockCodecs:
        pass #keep the old value.
      else:
        unlimitedCerBlockCodecs[destinationName] = makeCerBlockHuffmanCodec(sourceName, extendToHeight=transitionHeight, cutToHeight=transitionHeight, subCodecTransformerFun=quickUnlockers[switchMode])

def prepareUnlimitedCerBlockCodecs():
  for key in limitedCerBlockCodecs:
    raise NotImplementedError()
    unlimitedCerBlockCodecs[key+"_selectionBit_switch_to_fibonacci"] = None
    unlimitedCerBlockCodecs[key+"_escapeCode_switch_to_fibonacci"] = None

  
  #CodecTools.makeUnlimitedNumCodecWithSelectionBit(limitedCerNumCodecs[key], Codes.codecs["fibonacci"])CodecTools.makeUnlimitedNumCodecWithEscapeCode(limitedCerNumCodecs[key], Codes.codecs["fibonacci"], max(limitedCerNumCodecs[key].getDomain()))
  

#example usage: len([item for item in CodecTools.makeSeqCodec(PresetTools.unlimitedCerNumCodecs["linear_1024x256_moo_short_sub4096_Huffman_selectionBit_switch_to_fibonacci"],0,zeroSafe=True).encode(Testing.sampleCerPressNums["linear"][1024][256])])


