import CERWaves
import Codes
import PyCellElimRun as pcer





def test(interpolationModesToTest=["hold","nearest-neighbor","linear","sinusoidal","finite distance cubic hermite","finite distance cubic hermite&clip"]):
  #testSound = CERWaves.sounds["sampleNoise"]
  testSound = CERWaves.sounds["crickets8bmono44100.wav"][10000:10000+1024*2][::2] #this is necessary because the sample rate of the file was wrong when it was created and samples are duplicated.
  testSoundSize = [len(testSound),256]
  assert max(testSound) < testSoundSize[1]
  assert min(testSound) >= 0
  for interpolationMode in interpolationModesToTest:
    print("interpolation mode " + interpolationMode + ": ")
    pressDataNums = pcer.functionalTest(testSound,"encode",interpolationMode,testSoundSize)
    pressDataFibcodeSeqStr = Codes.intSeqToFibcodeSeqStr(num+1 for num in pressDataNums)
    print("the length of the fibcoded data is " + str(len(pressDataFibcodeSeqStr)) + ".")
    reconstPressDataNums = [num-1 for num in Codes.fibcodeSeqStrToIntArr(pressDataFibcodeSeqStr)]
    reconstPlainDataNums = pcer.functionalTest(reconstPressDataNums,"decode",interpolationMode,testSoundSize)
    if reconstPlainDataNums == testSound:
      print("test passed.")
    else:
      print("test failed.")


def compressFull():
  pass
