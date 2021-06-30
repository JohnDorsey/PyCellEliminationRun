#from __future__ import print_function as print
#from __future__ import print_function

import CERWaves
import Codes
import PyCellElimRun as pcer
import IntSeqStore



havenBucketFibonacciCoding = Codes.UniversalCoding(None,None,(lambda inputSeq: "".join(IntSeqStore.genEncodeWithHavenBucket(inputSeq,Codes.fibonacciCoding.intToBitStr,(lambda x: x>>1)))),(lambda inputBitStr: IntSeqStore.genDecodeWithHavenBucket(inputBitStr,(lambda xx: Codes.fibonacciCoding.bitStrToInt(xx,mode="detailed_parse")),(lambda x: x>>1)))) #@ ouch.





def test(interpolationModesToTest=["hold","nearest-neighbor","linear","sinusoidal","finite difference cubic hermite","finite difference cubic hermite&clip"],numberCoding=Codes.fibonacciCoding):
  soundSourceStr = "CERWaves.sounds[\"moo8bmono44100.txt\"][10000:10000+1024*2][::2]"
  #testSound = CERWaves.sounds["sampleNoise"]
  #testSound = CERWaves.sounds["crickets8bmono44100.wav"][10000:10000+1024]
  #testSound = CERWaves.sounds["moo8bmono44100.wav"][10000:10000+1024*2][::2] #this is necessary because the sample rate of the file was wrong when it was created and samples are duplicated.
  testSound = eval(soundSourceStr)
  print("the sound source is " + str(soundSourceStr))
  print("the sample rate migh be wrong. Check it.")
  testSoundSize = [None,256]
  assert max(testSound) < testSoundSize[1]
  assert min(testSound) >= 0
  for interpolationMode in interpolationModesToTest:
    print("interpolation mode " + interpolationMode + ": ")
    print("the input data is length " + str(len(testSound)) + " and has a range of " + str((min(testSound),max(testSound))) + " and the start of it looks like " + str(testSound[:16]) + ".")
    pressDataNums = pcer.functionalTest(testSound,"encode",interpolationMode,testSoundSize)
    pressDataCodeStr = numberCoding.intSeqToBitStr(num+1 for num in pressDataNums)
    print("the length of the coded data is " + str(len(pressDataCodeStr)) + ".")
    reconstPressDataNums = [num-1 for num in numberCoding.bitStrToIntSeq(pressDataCodeStr)]
    reconstPlainDataNums = pcer.functionalTest(reconstPressDataNums,"decode",interpolationMode,testSoundSize)
    if reconstPlainDataNums == testSound:
      print("test passed.")
    else:
      print("test failed.")


def compressFull(soundName,destFileName,interpolationMode,blockWidth,numberCoding=Codes.fibonacciCoding):
  sound = CERWaves.sounds[soundName]
  destFile = open(destFileName+" "+interpolationMode+" "+str(blockWidth),"w")
  offset = 0
  print("starting compression on sound of length " + str(len(sound)) + "...")
  print("the input data is length " + str(len(sound)) + " and has a range of " + str((min(sound),max(sound))) + " and the start of it looks like " + str(sound[:512]) + ".")
  while offset + blockWidth + 1 < len(sound):
    print(str(100*offset/len(sound))[:5]+"%...")
    audioData = sound[offset:offset+blockWidth]
    offset += blockWidth
    pressDataNums = pcer.functionalTest(audioData,"encode",interpolationMode,[None,256])
    print("there are " + str(len(pressDataNums)) + " pressDataNums to store.")
    pressDataBitStr = numberCoding.intSeqToBitStr([item+1 for item in pressDataNums]) + "\n"
    print("the resulting pressDataBitStr has length " + str(len(pressDataBitStr)) + ".")
    destFile.write(pressDataBitStr)
  destFile.close()


def decompressFull(srcFileName,interpolationMode,blockWidth,numberCoding=Codes.fibonacciCoding):
  print("remember that this method returns a huge array which must be stored to a variable, not displayed. It will fill the console output history if shown on screen.")
  #sound = CERWaves.sounds[soundName]
  result = []
  srcFile = open(srcFileName,"r")
  offset = 0
  print("starting decompression on file named " + str(srcFileName) + "...")
  #print("the input data is length " + str(len(sound)) + " and has a range of " + str((min(sound),max(sound))) + " and the start of it looks like " + str(sound[:512]) + ".")
  while True:
    #print(str(100*offset/len(sound))[:5]+"%...")
    loadedLine = None
    try:
      loadedLine = srcFile.readlines(1)[0].replace("\n","")
    except:
      break
    print("loaded a line of length " + str(len(loadedLine)) + " which starts with " + loadedLine[:64] + ".")
    pressDataNums = [item-1 for item in numberCoding.bitStrToIntSeq(loadedLine)]
    assert min(pressDataNums) == 0
    if not len(pressDataNums) == blockWidth:
      print("pressDataNums is the wrong length. Trimming will be attempted.")
      pressDataNums = pressDataNums[:blockWidth]
    plainDataNums = pcer.functionalTest(pressDataNums,"decode",interpolationMode,[blockWidth,256])
    if not len(plainDataNums) == blockWidth:
      print("plainDataNums is the wrong length. Trimming will be attempted.")
      plainDataNums = plainDataNums[:blockWidth]
    #audioData = sound[offset:offset+blockWidth]
    #offset += blockWidth
    #destFile.write(pressDataBitStr)
    print("extending results by " + str(len(plainDataNums)) + " item array which starts with " + str(plainDataNums[:16]) + ".")
    result.extend(plainDataNums)
  srcFile.close()
  print("result has length " + str(len(result)) + " and ends with " + str(result[-64:]) + ".")
  return result



assert len(CERWaves.sounds["moo8bmono44100.txt"]) > 0
assert pcer.functionalTest([item-1 for item in Codes.fibcodeSeqStrToIntArr(Codes.intSeqToFibcodeSeqStr([item+1 for item in pcer.functionalTest(CERWaves.sounds["moo8bmono44100.txt"][:256],"encode","linear",[256,256])]))],"decode","linear",[256,256])==CERWaves.sounds["moo8bmono44100.txt"][:256]
