"""

Testing.py by John Dorsey.

Testing.py contains tools for testing compression of audio with PyCellElimRun.py's tools.
No other files require Testing.py

"""


import WaveIO
import Codes
import CodecTools
import PyCellElimRun as pcer
import IntArrMath
import IntSeqStore

import QuickTimers

from PyGenTools import makeArr, makeGen
from PyArrTools import ljustedArr
from MarkovTools import Hist


SAMPLE_VALUE_UPPER_BOUND = 256 #exclusive.

PEEK = 64 #these control how much information is shown in previews in the console.
PEEEK = 2048





def test(interpolationModesToTest=["hold", "nearest_neighbor", "linear", "linear&round", "sinusoidal", "finite_difference_cubic_hermite", "finite_difference_cubic_hermite&global_clip", "finite_difference_cubic_hermite&span_clip"], soundSrcStr="WaveIO.sounds[\"samples/moo8bmono44100.txt\"][15000:]", soundLength=1024):
  #This method tests that the round trip from raw audio to coded (using a universal code) data and back does not change the data.
  
  print("Testing.test: make sure that the sample rate is correct.") #this is necessary because the sample rate of some files, like the moo file, might have been wrong at the time of their creation. moo8bmono44100.wav once had every sample appear twice in a row.
  VERBOSE = True

  QuickTimers.startTimer("test")
  testSound = eval(soundSrcStr)[:soundLength]
  print("Testing.test: the sound source string is " + str(soundSrcStr) + ".")
  testSoundSize = [soundLength,SAMPLE_VALUE_UPPER_BOUND]
  assert max(testSound) < testSoundSize[1]
  assert min(testSound) >= 0

  print("Testing.test: the input data is length " + str(len(testSound)) + " and has a value range of " + str((min(testSound),max(testSound))) + ((" and is equal to " + str(testSound)) if VERBOSE else (" and the start of it looks like " + str(testSound[:PEEK])[:PEEK])) + ".")

  for interpolationMode in interpolationModesToTest: #test all specified interpolation modes.
    print("\nTesting.test: interpolation mode " + interpolationMode + ": ")
    testCERCodec = pcer.cellElimRunBlockCodec.clone(extraArgs=[interpolationMode,testSoundSize])

    pressDataNums = testCERCodec.encode(testSound)
    print("Testing.test: The sum of the pressDataNums from the Cell Elimination Run codec is " + str(sum(pressDataNums)) + ". They include " + str(pressDataNums.count(0)) + " zeroes, of which " + str(CodecTools.countTrailingZeroes(pressDataNums)) + " are trailing. The median of the nonzero numbers is " + str(IntArrMath.median([item for item in pressDataNums if item != 0])) + " and the maximum is " + str(max(pressDataNums)) + " at index " + str(pressDataNums.index(max(pressDataNums))) + ". The start of the numbers looks like " + str(pressDataNums[:PEEK])[:PEEK] + ".")
    if VERBOSE:
      print("Testing.test: The pressDataNums are " + str(pressDataNums))

    for numberSeqCodecSrcStr in ["Codes.codecs[\"{}\"]".format(codesCodecsName) for codesCodecsName in ["inSeq_fibonacci","inSeq_eliasGamma","inSeq_eliasDelta","inSeq_eliasGammaFib","inSeq_eliasDeltaFib"]]+["IntSeqStore.havenBucketCodecs[\"{}\"]".format(intSeqStoreCodecsName) for intSeqStoreCodecsName in ["HLL_fibonacci","HLL_eliasGamma","HLL_eliasDelta"]]:
      print("testing with "+numberSeqCodecSrcStr+":")
      numberSeqCodec = eval(numberSeqCodecSrcStr)
      CodecTools.printComparison(testSound,makeArr(numberSeqCodec.encode(num+(0 if numberSeqCodec.zeroSafe else 1) for num in pressDataNums)))

    reconstPlainDataNums = testCERCodec.decode(pressDataNums)
    if reconstPlainDataNums == testSound:
      print("Testing.test: test passed.\n")
      for i in range(len(testSound)):
        assert testSound[i] == reconstPlainDataNums[i]
    else:
      print("Testing.test: test failed. ~~~~~ FAIL ~~~~~ FAIL ~~~~~ FAIL ~~~~~ FAIL ~~~~~ FAIL ~~~~.\n")

  print("Testing.test: testing took " + str(QuickTimers.stopTimer("test")) + " seconds.")



def compressFull(soundName,destFileName,interpolationMode,blockWidth,numberSeqCodec):
  #access the entire sound based on its name, and use the functionalTest method to compress each block of audio, and delimit blocks with newlines in the output file.
  QuickTimers.startTimer("compressFull")
  sound = WaveIO.sounds[soundName]
  destFile = open(destFileName+" "+interpolationMode+" "+str(blockWidth),"w")
  offset = 0
  print("Testing.compressFull: starting compression on sound of length " + str(len(sound)) + "...")
  print("Testing.compressFull: the input data is length " + str(len(sound)) + " and has a range of " + str((min(sound),max(sound))) + " and the start of it looks like " + str(sound[:PEEEK])[:PEEEK] + ".")
  while offset + blockWidth + 1 < len(sound):
    print(str((100.0*offset)/float(len(sound)))[:6]+"%...")
    audioData = sound[offset:offset+blockWidth]
    offset += blockWidth
    pressDataNums = pcer.cellElimRunBlockTranscode(audioData,"encode",interpolationMode,[None,SAMPLE_VALUE_UPPER_BOUND])
    print("Testing.compressFull: there are " + str(len(pressDataNums)) + " pressDataNums to store.")
    pressDataBitStr = CodecTools.bitSeqToStrCodec.encode(numberSeqCodec.encode([item+(0 if numberSeqCodec.zeroSafe else 1) for item in pressDataNums])) + "\n"
    print("Testing.compressFull: the resulting pressDataBitStr has length " + str(len(pressDataBitStr)) + ".")
    destFile.write(pressDataBitStr)
  destFile.close()
  print("Testing.compressFull: compression took " + str(QuickTimers.stopTimer("compressFull")) + " seconds.")


def decompressFull(srcFileName,interpolationMode,blockWidth,numberSeqCodec):
  #inverse of compressFull.
  QuickTimers.startTimer("decompressFull")
  print("Testing.decompressFull: remember that this method returns a huge array which must be stored to a variable, not displayed. It will fill the console output history if shown on screen.")
  result = []
  srcFile = open(srcFileName,"r")
  offset = 0
  print("Testing.decompressFull: starting decompression on file named " + str(srcFileName) + "...")
  #print("the input data is length " + str(len(sound)) + " and has a range of " + str((min(sound),max(sound))) + " and the start of it looks like " + str(sound[:512]) + ".")
  while True:
    #print(str(100*offset/len(sound))[:5]+"%...")
    loadedLine = None
    try:
      loadedLine = srcFile.readlines(1)[0].replace("\n","")
    except:
      break
    print("Testing.decompressFull: loaded a line of length " + str(len(loadedLine)) + " which starts with " + loadedLine[:PEEK] + ".")
    pressDataBitArr = CodecTools.bitSeqToStrCodec.decode(loadedLine)
    pressDataNums = [item-(0 if numberSeqCodec.zeroSafe else 1) for item in numberSeqCodec.decode(pressDataBitArr)]
    assert min(pressDataNums) == 0
    if not len(pressDataNums) == blockWidth: #this happens when the provided UniversalCoding numberCoding incorrectly yields an extra zero when its input data is ending. It is less likely to happen now that the UniversalCoding class is no longer used.
      print("Testing.decompressFull: pressDataNums is the wrong length. Trimming will be attempted.") 
      pressDataNums = pressDataNums[:blockWidth]
    plainDataNums = pcer.cellElimRunBlockTranscode(pressDataNums,"decode",interpolationMode,[blockWidth,SAMPLE_VALUE_UPPER_BOUND])
    if not len(plainDataNums) == blockWidth:
      print("Testing.decompressFull: plainDataNums is the wrong length. Trimming will be attempted. This has never happened before.")
      plainDataNums = plainDataNums[:blockWidth]
    print("Testing.decompressFull: extending results by " + str(len(plainDataNums)) + " item array which starts with " + str(plainDataNums[:PEEK])[:PEEK] + ".")
    result.extend(plainDataNums)
  srcFile.close()
  print("Testing.decompressFull: result has length " + str(len(result)) + " and ends with " + str(result[-PEEK:])[-PEEK:] + ".")
  print("Testing.decompressFull: decompression took " + str(QuickTimers.stopTimer("decompressFull")) + " seconds.")
  return result








class PressNumsAnalysis:
  def __init__(self,plainDataSrcArr,numberSeqCodec,sliceLength,offsetSrcGen):
    self.plainDataSrcArr = plainDataSrcArr
    self.numberSeqCodec = numberSeqCodec
    self.sliceLength = sliceLength
    self.offsetSrcGen = makeGen(offsetSrcGen)
    self.collectedData = {"all_pressdata_nums":Hist(),"pressdata_nums_by_column":[Hist() for i in range(self.sliceLength)],"pressdata_lengths":Hist(),"pressdata_means_rounded":Hist(),"pressdata_medians_rounded":Hist(),"pressdata_maximums":Hist()}

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
    print("Testing.PressNumsAnalysis.run: Done.")


  def runOnce(self,offset):
    if offset > len(self.plainDataSrcArr) - self.sliceLength:
      print("Testing.PressNumsAnalysis.runOnce: The offset is too high. Returning False...")
      return False
    plainDataArr = self.plainDataSrcArr[offset:offset+self.sliceLength]

    pressDataArr = makeArr(self.numberSeqCodec.encode(plainDataArr))

    self.collectedData["all_pressdata_nums"].registerFrom(pressDataArr)
    for columnIndex,columnValue in enumerate(ljustedArr(pressDataArr,self.sliceLength,fillItem=None)):
      self.collectedData["pressdata_nums_by_column"][columnIndex].register(columnValue)
    self.collectedData["pressdata_lengths"].register(len(pressDataArr))
    self.collectedData["pressdata_means_rounded"].register(int(round(IntArrMath.mean(pressDataArr))))
    self.collectedData["pressdata_medians_rounded"].register(int(round(IntArrMath.median(pressDataArr))))
    self.collectedData["pressdata_maximums"].register(max(pressDataArr))
    return True



#tests performed on load.
assert len(WaveIO.sounds["samples/moo8bmono44100.txt"]) > 0

assert pcer.cellElimRunBlockTranscode([item-1 for item in Codes.codecs["inSeq_fibonacci"].decode(Codes.codecs["inSeq_fibonacci"].encode([item+1 for item in pcer.cellElimRunBlockTranscode(WaveIO.sounds["samples/moo8bmono44100.txt"][:256],"encode","linear",[256,SAMPLE_VALUE_UPPER_BOUND])]))],"decode","linear",[256,SAMPLE_VALUE_UPPER_BOUND]) == WaveIO.sounds["samples/moo8bmono44100.txt"][:256]

#test of streaming CER blocks:
assert [item for item in pcer.cellElimRunBlockSeqCodec.clone(extraArgs=["linear",{"size":(5,10),"endpoint_init_mode":"middle"}]).encode([5,6,7,6,5,5,6,7,6,5])] == [32,10,32,10]
assert [item for item in pcer.cellElimRunBlockSeqCodec.clone(extraArgs=["linear",{"size":(5,10),"endpoint_init_mode":"middle"}]).decode([32,10,32,10])] == [5,6,7,6,5,5,6,7,6,5]

