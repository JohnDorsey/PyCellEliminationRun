"""

Testing.py by John Dorsey.

Testing.py contains tools for testing compression of audio with PyCellElimRun.py's tools.
No other files require Testing.py


"""


import os

import Codes
import CodecTools
import PyCellElimRun as pcer
import IntArrMath
import IntSeqStore

import HeaderTools

import QuickClocks

import PyGenTools
from PyGenTools import makeArr, makeGen
from PyArrTools import ljustedArr
import HistTools

import WaveIO

SAMPLE_VALUE_UPPER_BOUND = 256 #exclusive.

PEEK = 64 #these control how much information is shown in previews in the console.
PEEEK = 2048
VERBOSE = True

defaultSampleSoundSrcStr = "WaveIO.sounds[\"samples/moo8bmono44100.txt\"][15000:]"
defaultNumSeqCodecSrcStr = "Codes.codecs[\"inSeq_fibonacci\"]"

sampleCerPressNums = {
  "linear":{
    key:{256:None} for key in [1024,512,256,128,64,32,16,8]
  }
}


def evalSoundSrcStr(soundSrcStr):
  print("Testing.evalSoundSrcStr: the sound source string is " + str(soundSrcStr) + ".")
  try:
    sound = WaveIO.sounds[soundSrcStr]
    print("Testing.evalSoundSrcStr: the soundSrcStr {} was used as a key.".format(repr(soundSrcStr)))
  except KeyError:
    sound = eval(soundSrcStr)
    print("Testing.evalSoundSrcStr: the soundSrcStr {} was used as an expression.".format(repr(soundSrcStr)))
  return sound
  



def test(interpolationModesToTest=["linear", "sinusoidal", {"method_name":"finite_difference_cubic_hermite"}, {"method_name":"inverse_distance_weighted","power":2,"output_filters":["span_clip"]}], scoreModesToTest=["vertical_distance"], soundSrcStr=defaultSampleSoundSrcStr, soundLength=1024):
  #This method tests that the round trip from raw audio to pressDataNums and back does not change the data.
  #print("Testing.test: make sure that the sample rate is correct.") #this is necessary because the sample rate of some files, like the moo file, might have been wrong at the time of their creation. moo8bmono44100.wav once had every sample appear twice in a row.
  QuickClocks.start("test")
  QuickClocks.create("test-cer-encode")
  QuickClocks.create("test-cer-decode")
  
  testSound = evalSoundSrcStr(soundSrcStr)[:soundLength]
  assert len(testSound) == soundLength, "testSound has an unacceptable length."
  testSoundSize = [soundLength,SAMPLE_VALUE_UPPER_BOUND]
  assert max(testSound) < testSoundSize[1]
  assert min(testSound) >= 0

  print("Testing.test: the input data is length " + str(len(testSound)) + " and has a value range of " + str((min(testSound),max(testSound))) + ((" and is equal to " + str(testSound)) if VERBOSE else (" and the start of it looks like " + str(testSound[:PEEK])[:PEEK])) + ".")

  for interpolationMode in interpolationModesToTest: #test all specified interpolation modes.
    for scoreMode in scoreModesToTest:
      inputHeaderDict = {"interpolation_mode":interpolationMode,"score_mode":scoreMode,"space_definition":{"size":testSoundSize}}
      print("\nTesting.test: settings: " + str(inputHeaderDict)+".")
      testCERCodec = pcer.cellElimRunBlockCodec.clone(extraArgs=[inputHeaderDict])
      testCellElimRunCodec(testCERCodec, testSound, testSoundSize=testSoundSize)

  print("Testing.test: testing took {} seconds. CER total={}, CER encode={}, CER decode={}.".format(QuickClocks.stop("test"),QuickClocks.peek("test-cer-encode")+QuickClocks.peek("test-cer-decode"),QuickClocks.stop("test-cer-encode"),QuickClocks.stop("test-cer-decode")))


def testCellElimRunCodec(testCERCodec, testSound, testSoundSize=None, compressAgain=False):
  QuickClocks.resume("test-cer-encode")
  pressDataNums = testCERCodec.encode(testSound)
  QuickClocks.pause("test-cer-encode")
  printSimpleAnalysis(pressDataNums)

  testVariousUniversalCodings(testSound, pressDataNums, testSoundSize=testSoundSize)

  QuickClocks.resume("test-cer-decode")
  reconstPlainDataNums = testCERCodec.decode(pressDataNums)
  QuickClocks.pause("test-cer-decode")
  if reconstPlainDataNums == testSound:
    print("Testing.testCellElimRunCodec: test passed.\n")
    for i in range(len(testSound)):
      assert testSound[i] == reconstPlainDataNums[i]
  else:
    print("Testing.testCellElimRunCodec: test failed. ~~~~~ FAIL ~~~~~ FAIL ~~~~~ FAIL ~~~~~ FAIL ~~~~~ FAIL ~~~~.")
  if compressAgain:
    testCellElimRunCodecAgain(testSound, pressDataNums, testSoundSize=testSoundSize)
  print("\n")
    
    
def testCellElimRunCodecAgain(testSound, testData, testSoundSize=None): #compresses testData again.
  inputHeaderDict2 = {"interpolation_mode":{"method_name":"linear"},"space_definition":{"size":[len(testData),sum(testData)],"bounds":{"upper":"EMBED:AFTER_PREP_OP_MODE"}}}
  print("\nTesting.testCellElimRunCodecAgain: settings: " + str(inputHeaderDict2)+".")
  testCERCodec2 = pcer.cellElimRunBlockCodec.clone(extraArgs=[inputHeaderDict2])
  pressNums2 = testCERCodec2.encode(testData)
  printSimpleAnalysis(pressNums2)
  testVariousUniversalCodings(testSound, pressNums2, testSoundSize=testSoundSize)
      
      
def testVariousUniversalCodings(testSound, pressDataNums, testSoundSize=None):
  families = {"seq":["Codes.codecs[\"{}\"]".format(codesCodecsName) for codesCodecsName in ["inSeq_fibonacci","inSeq_eliasGamma","inSeq_eliasDelta","inSeq_eliasGammaFib","inSeq_eliasDeltaFib"]],"haven bucket seq":["IntSeqStore.havenBucketCodecs[\"{}\"]".format(intSeqStoreCodecsName) for intSeqStoreCodecsName in ["0.125LL_fibonacci","0.25LL_fibonacci","0.375LL_fibonacci","HLL_fibonacci","0.625LL_fibonacci","0.75LL_fibonacci","0.875LL_fibonacci"]]}
  for numberSeqCodecSrcStr in families["seq"]:
    numberSeqCodec = eval(numberSeqCodecSrcStr)
    print("testing with seq codec " + numberSeqCodecSrcStr + " :")
    CodecTools.printComparison(testSound,makeArr(numberSeqCodec.zeroSafeEncode(pressDataNums)))
    assert CodecTools.roundTripTest(numberSeqCodec,pressDataNums,useZeroSafeMethods=True)
    
  for seqSumStrategy in ["without","with","with_embedded","with_embed_sign"]:
    print("") #new line.
    for numberSeqCodecSrcStr in families["haven bucket seq"]:      
      numberSeqCodec = eval(numberSeqCodecSrcStr)
      extraKwargs = dict()
      maxPossibleSeqSum = testSoundSize[0]*testSoundSize[1]
      if seqSumStrategy == "with":
        if testSoundSize != None:
          assert len(testSoundSize) == 2
          extraKwargs["seqSum"] = maxPossibleSeqSum
        else:
          print("testVariousUniversalCodings: warning: can't.")
          break
      elif seqSumStrategy == "with_embedded":
        extraKwargs["seqSum"] = "EMBED"
      elif seqSumStrategy == "with_embed_sign":
        extraKwargs["seqSum"] = HeaderTools.EmbedSign(includedCodec=Codes.codecs["fibonacci"].clone(extraKwargs={"maxInputInt":maxPossibleSeqSum}))
      else:
        assert seqSumStrategy == "without"
      print("testing with haven bucket seq codec " + numberSeqCodecSrcStr + ", seqSumStrategy={}:".format(seqSumStrategy))
      CodecTools.printComparison(testSound,makeArr(numberSeqCodec.zeroSafeEncode(pressDataNums, **extraKwargs)))
      assert CodecTools.roundTripTest(numberSeqCodec,pressDataNums,useZeroSafeMethods=True)
      
      
def printSimpleAnalysis(pressDataNums):
  resultText = ""
  
  resultText += "Testing.printSimpleAnalysis: The sum of the pressDataNums from the Cell Elimination Run codec is " + str(sum(pressDataNums)) + ". They include " + str(pressDataNums.count(0)) + " zeroes, of which " + str(CodecTools.countTrailingZeroes(pressDataNums)) + " are trailing."
  
  #resultText += "The last " + str(CodecTools.countTrailingMatches(pressDataNums, (lambda x: x in [0,1]))) + " nums fall in 0..1. The last " + str(CodecTools.countTrailingMatches(pressDataNums, (lambda x: x in [0,1,2]))) + " nums fall in 0..2."
  includePercentage = lambda inputInt: (inputInt, str(inputInt*100.0/len(pressDataNums))[:6] + "%")
  resultText += " Where f(a) gives greatest b such that max(pressDataNums[-b:]) <= a, the start of f(a) looks like {}.".format([(testUpperBound, includePercentage(CodecTools.countTrailingMatches(pressDataNums, (lambda x: x <= testUpperBound)))) for testUpperBound in [1,2,4,8,16,32,64,128,256,512,1024]])
  
  resultText += " The median of the nonzero numbers is " + str(IntArrMath.median([item for item in pressDataNums if item != 0])) + " and the maximum is " + str(max(pressDataNums)) + " at index " + str(pressDataNums.index(max(pressDataNums))) + "."
  
  if VERBOSE:
    resultText += "The pressDataNums are " + str(pressDataNums) + "."
  else:
    resultText += "The start of the pressDataNums look like " + str(pressDataNums[:PEEK])[:PEEK] + "..."
  print(resultText)
      
      
      

def prepareSampleCerPressNums(soundSrcStr=defaultSampleSoundSrcStr):
  soundToCompress = eval(soundSrcStr)
  for interpolationMode, IMSub in sampleCerPressNums.items():
    for blockSizeHoriz, BSHSub in IMSub.items():
      for blockSizeVert, BSVSub in BSHSub.items():
        sampleCerPressNums[interpolationMode][blockSizeHoriz][blockSizeVert] = makeArr(pcer.cellElimRunBlockCodec.encode(soundToCompress, {"interpolation_mode": interpolationMode, "space_definition": {"size": [blockSizeHoriz,blockSizeVert]}}))



def allocateDirectory(desiredName):
  alternativeName = desiredName
  i = 1
  while os.path.exists(alternativeName+"/"):
    i += 1
    alternativeName = desiredName+"(session{})".format(i)
  usedName = alternativeName
  os.mkdir(usedName)
  return usedName


def expandCERCSInputHeaderDict(inputHeaderDict, blockSize=None):
  if inputHeaderDict == None:
    inputHeaderDict = dict()
  elif type(inputHeaderDict) == str:
    if "@" in inputHeaderDict:
      raise NotImplementedError("@ splits are not handled by Testing.py full file compression methods.")
    if inputHeaderDict in pcer.Curves.Spline.SUPPORTED_INTERPOLATION_METHOD_NAMES:
      inputHeaderDict = {"interpolation_mode":{"method_name":inputHeaderDict}}
  else:
    if not isinstance(inputHeaderDict,dict):
      raise TypeError("input header dict can't be expanded because it is of invalid type {}.".format(repr(type(inputHeaderDict))))
  if "space_definition" not in inputHeaderDict:
    inputHeaderDict["space_definition"] = dict()
  spaceDefinition = inputHeaderDict["space_definition"]
  if "size" not in spaceDefinition:
    spaceDefinition["size"] = [None, None]
  size = spaceDefinition["size"]
  for i in range(len(size)):
    if size[i] == None:
      default = blockSize[i]
      size[i] = default
    if not size[i] == blockSize[i]:
      raise ValueError("differences between blockSize and inputHeaderDict[\"space_definition\"][\"size\"] are not yet handled in Testing.py methods.")
  assert isinstance(inputHeaderDict, dict)
  return inputHeaderDict


def compressFull(soundSrcStr, outputShortName, settings=None, blockSize=(256,256), numberSeqCodec=None):
  """
  access the entire sound based on its name, and use the functionalTest method to compress each block of audio, and delimit blocks with newlines in the output file.
  
  settings may be None (for default settings), or may be the name of any interpolation method, or may be an inputHeaderDict in the format specified in PyCellElimRun.CellElimRunCodecState.DEFAULT_HEADER_DICT_TEMPLATE at any level of completion.
  """
  
  sound = evalSoundSrcStr(soundSrcStr)
  
  blockWidth = blockSize[0]
  outputLongName = allocateDirectory("testingOutputs/{}".format(outputShortName))
  outputCommonName = outputLongName+"/out "+str(blockWidth)
  logFileName = outputCommonName+" log.txt"
  
  inputHeaderDict = expandCERCSInputHeaderDict(settings, blockSize=blockSize)
  
  if numberSeqCodec == None:
    numberSeqCodec = eval(defaultNumSeqCodecSrcStr)
  
  QuickClocks.start("compressFull")
  QuickClocks.create("compressFull-cer")
  
  with open(logFileName,"w") as logFile:

    def log(text,end="\n"):
      logFile.write(text+end)
      return "log passthrough: "+text
    def plog(text,end="\n"):
      print(text)
      log(text,end=end)
      
    plog("writing to log file {}.".format(logFileName))
    plog("\nTesting.compressFull: settings: " + str(inputHeaderDict)+".")
      
    plog("Testing.compressFull: starting compression on sound of length " + str(len(sound)) + "...")
    plog("Testing.compressFull: the input data is length " + str(len(sound)) + " and has a range of " + str((min(sound),max(sound))) + " and the start of it looks like " + str(sound[:PEEEK])[:PEEEK] + ".")
    
    cerBlockCodec = pcer.cellElimRunBlockCodec.clone(extraArgs=[inputHeaderDict])
    blockCount = len(sound)//blockWidth
    plog("\nTesting.compressFull: block count will be {}.".format(blockCount))
    
    with open(outputCommonName+" listStr.partial","w") as pressDataListStrDestFile, open(outputCommonName+" bitStr.partial","w") as pressDataBitStrDestFile, open(outputCommonName+" bytes.partial","w") as pressDataBytesDestFile, open(outputCommonName+" raw.partial","wb") as rawDestFile:
    
      for currentBlockIndex, currentBlockData in enumerate(PyGenTools.genChunksAsLists(sound, n=blockWidth, partialChunkHandling="discard")):
        if not len(currentBlockData) == blockWidth:
          raise ValueError(log("for block of index {}, invalid currentBlockData length: {}.".format(currentBlockIndex, len(currentBlockData))))
        plog(str((100.0*currentBlockIndex)/float(blockCount))[:6]+"%...")
        
        rawDestFile.write(bytearray(currentBlockData))
        
        QuickClocks.resume("compressFull-cer")
        pressDataNums = cerBlockCodec.encode(currentBlockData)
        QuickClocks.pause("compressFull-cer")
        plog("Testing.compressFull: there are " + str(len(pressDataNums)) + " pressDataNums to store.")
        pressDataListStrDestFile.write(str(pressDataNums)+"\n")
        
        pressDataBitArr = [item for item in numberSeqCodec.zeroSafeEncode(pressDataNums)]
        pressDataBitStr = CodecTools.bitSeqToStrCodec.encode(pressDataBitArr) + "\n"
        plog("Testing.compressFull: the resulting pressDataBitStr has length " + str(len(pressDataBitStr)) + ".")
        pressDataBitStrDestFile.write(pressDataBitStr)
        
        pressDataBytes = CodecTools.bitSeqToBytearrayCodec.encode(pressDataBitArr)
        assert len(pressDataBytes) > 0, log("pressDataBytes is empty, which should not be possible.")
        pressDataBytesDestFile.write(pressDataBytes)

    plog("Testing.compressFull: compression took {} seconds, of which {} was spent on the Cell Elimination Run codec.".format(QuickClocks.stop("compressFull"), QuickClocks.stop("compressFull-cer")))
    
    for scanFileName in os.listdir(outputLongName):
      scanFileFullName = outputLongName+"/"+scanFileName
      plog("Testing.compressFull: size of {} is {}".format(repr(scanFileName), os.path.getsize(scanFileFullName)))
    
    for scanFileName in os.listdir(outputLongName):
      scanFileFullName = outputLongName+"/"+scanFileName
      if scanFileFullName.endswith(".partial"):
        os.rename(scanFileFullName,scanFileFullName[:-8])
    plog("end of logging.")
  print("log file closed.")


def decompressFull(srcFileName, settings=None, blockSize=(256,256), numberSeqCodec=None):
  #inverse of compressFull.
  
  inputHeaderDict = expandCERCSInputHeaderDict(settings, blockSize=blockSize)
  blockWidth = blockSize[0]
  
  if numberSeqCodec == None:
    numberSeqCodec = eval(defaultNumSeqCodecSrcStr)
  
  QuickClocks.start("decompressFull")
  print("Testing.decompressFull: remember that this method returns a huge array which must be stored to a variable, not displayed. It will fill the console output history if shown on screen.")
  print("Testing.decompressFull: starting decompression on file named " + str(srcFileName) + "...")
  
  cerBlockCodec = pcer.cellElimRunBlockCodec.clone(extraArgs=[inputHeaderDict])
  result = []
  
  with open(srcFileName,"r") as srcFile:
    #print("the input data is length " + str(len(sound)) + " and has a range of " + str((min(sound),max(sound))) + " and the start of it looks like " + str(sound[:512]) + ".")
    for currentLineNumber, currentLine in enumerate(srcFile):
      #print(str(100*offset/len(sound))[:5]+"%...")
      currentLine = currentLine.replace("\n","")
      assert currentLine.count("0") + currentLine.count("1") == len(currentLine), "invalid line."
      print("Testing.decompressFull: loaded a line of length " + str(len(currentLine)) + " which starts with " + currentLine[:PEEK] + ".")
      pressDataBitArr = CodecTools.bitSeqToStrCodec.decode(currentLine)
      
      #@ the following line might make an unecessary conversion to a list.
      pressDataNums = [item for item in numberSeqCodec.zeroSafeDecode(pressDataBitArr)]
      if not min(pressDataNums) == 0:
        print("Testing.decompressFull: the minimum of the pressDataNums is not 0. this is unusual.")
      
      if not len(pressDataNums) <= blockWidth: #this happens when the provided UniversalCoding numberCoding incorrectly yields an extra zero when its input data is ending. It is less likely to happen now that the UniversalCoding class is no longer used.
        print("Testing.decompressFull: warning: pressDataNums is longer than the blockWidth. This is not supposed to happen with the Cell Elimination Run codec. Trimming will be attempted.") 
        pressDataNums = pressDataNums[:blockWidth]
        
      plainDataNums = cerBlockCodec.decode(pressDataNums)
      assert len(plainDataNums) == blockWidth, "plainDataNums is the wrong length. This has never happened before."
      print("Testing.decompressFull: extending results by " + str(len(plainDataNums)) + " item array which starts with " + str(plainDataNums[:PEEK])[:PEEK] + ".")
      result.extend(plainDataNums)
      
  print("Testing.decompressFull: result has length " + str(len(result)) + " and ends with " + str(result[-PEEK:])[-PEEK:] + ".")
  print("Testing.decompressFull: decompression took " + str(QuickClock.stop("decompressFull")) + " seconds.")
  return result








class PressNumsAnalysis:
  def __init__(self,plainDataSrcArr,numberSeqCodec,sliceLength,offsetSrcGen):
    self.plainDataSrcArr = plainDataSrcArr
    self.numberSeqCodec = numberSeqCodec
    self.sliceLength = sliceLength
    self.offsetSrcGen = makeGen(offsetSrcGen)
    histClass = HistTools.SimpleListHist
    self.collectedData = {"all":histClass(), "all_notcol0":histClass(), "all_by_column":[histClass() for i in range(self.sliceLength)], "lengths":histClass(), "means_rounded":histClass(), "medians_rounded":histClass(), "maxima":histClass(), "means_rounded_notcol0":histClass(), "medians_rounded_notcol0":histClass(), "maxima_notcol0":histClass()}
    
    self.dbgLastOffset = None

  def run(self,blockCount,timeLimit=None):
    def endPhrase():
      return str("Testing.PressNumsAnalysis.run will stop after running just {} of " + str(blockCount) + " requested blocks.")
    QuickTimers.startTimer("Testing.PressNumsAnalysis.run")
    for blockIndex in range(blockCount):
      if timeLimit != None:
        if QuickTimers.peekTimer("Testing.PressNumsAnalysis.run") >= timeLimit:
          print("Time limit reached. " + endPhrase().format(blockIndex))
          break
      currentOffset = None
      try:
        currentOffset = next(self.offsetSrcGen)
      except StopIteration:
        print("Testing.PressNumsAnalysis.offsetSrcGen ran out of offsets, so " + endPhrase().format(blockIndex))
        break
      shouldContinue = self.runOnce(currentOffset)
      if not shouldContinue:
        print("Testing.PressNumsAnalysis.run: runOnce returned false, so " + endPhrase().format(blockIndex))
        break
    QuickTimers.stopTimer("Testing.PressNumsAnalysis.run") #don't let it hang around uselessly.
    print("Testing.PressNumsAnalysis.run: Done.")


  def runOnce(self,offset):
    if offset > len(self.plainDataSrcArr) - self.sliceLength:
      print("Testing.PressNumsAnalysis.runOnce: The offset is too high. Returning False...")
      return False
    self.dbgLastOffset = offset
    plainDataArr = self.plainDataSrcArr[offset:offset+self.sliceLength]

    pressDataArr = makeArr(self.numberSeqCodec.encode(plainDataArr))

    self.collectedData["all"].registerFrom(pressDataArr)
    self.collectedData["all_notcol0"].registerFrom(pressDataArr[1:])
    for columnIndex,columnValue in enumerate(ljustedArr(pressDataArr,self.sliceLength,fillItem=None)):
      self.collectedData["all_by_column"][columnIndex].register(columnValue)
    self.collectedData["lengths"].register(len(pressDataArr))
    self.collectedData["means_rounded"].register(int(round(IntArrMath.mean(pressDataArr))))
    self.collectedData["medians_rounded"].register(int(round(IntArrMath.median(pressDataArr))))
    self.collectedData["maxima"].register(max(pressDataArr))
    self.collectedData["means_rounded_notcol0"].register(int(round(IntArrMath.mean(pressDataArr[1:]))))
    self.collectedData["medians_rounded_notcol0"].register(int(round(IntArrMath.median(pressDataArr[1:]))))
    self.collectedData["maxima_notcol0"].register(max(pressDataArr[1:]))
    return True



#tests performed on load.
assert len(WaveIO.sounds["samples/moo8bmono44100.txt"]) > 0

#fix these to use improved zero-safe design.
assert pcer.cellElimRunBlockTranscode([item-1 for item in Codes.codecs["inSeq_fibonacci"].decode(Codes.codecs["inSeq_fibonacci"].encode([item+1 for item in pcer.cellElimRunBlockTranscode(WaveIO.sounds["samples/moo8bmono44100.txt"][:256],"encode","linear",{"size":[256,SAMPLE_VALUE_UPPER_BOUND]})]))],"decode","linear",{"size":[256,SAMPLE_VALUE_UPPER_BOUND]}) == WaveIO.sounds["samples/moo8bmono44100.txt"][:256]

#test of streaming CER blocks:

assert [item for item in pcer.cellElimRunBlockSeqCodec.clone(extraArgs=["linear",{"size":(5,10),"endpoint_init_mode":"middle"}]).encode([5,6,7,6,5,5,6,7,6,5])] == [32,10,32,10]
assert [item for item in pcer.cellElimRunBlockSeqCodec.clone(extraArgs=["linear",{"size":(5,10),"endpoint_init_mode":"middle"}]).decode([32,10,32,10])] == [5,6,7,6,5,5,6,7,6,5]



"""

Testing.compressFull("WaveIO.sounds[\"samples/worthwhile-uint8mono48000.txt\"][:48000*3]","testingOutputs/worthwhile_48000_3sec_0.625LLfib",{"interpolation_mode":{"method_name":"linear"},"space_definition":{"size":[1024,256]}},1024,\
Testing\
.... .IntSeqStore.havenBucketCodecs["0.625LL_fibonacci"])


"""
