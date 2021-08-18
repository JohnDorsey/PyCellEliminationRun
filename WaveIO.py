"""

WaveIO.py by John Dorsey.

When loaded, WaveIO.py loads sample audio for easy use in testing the codec. Audio samples included in the project have licenses described by /samples/licenses.txt.

"""


import sys
import wave
import IntArrMath

#don't use "samples/moo8bmono44100.wav":None "samples/crickets8bmono44100.wav":None,
sounds = {"samples/moo8bmono44100.txt":None,"samples/worthwhile-uint8mono96000.txt":None}



def loadSound(filename):
  if filename.endswith(".wav"):
    soundFile = wave.open(filename,mode="rb")
    result = None
    if sys.version[0] == "3":
      result = [int(item) for item in soundFile.readframes(2**32)]
    else:
      #result = [int(ord(item)) for item in soundFile.readframes(2**32)]
      #assert False
      print(".wav files won't be loaded in this version of python.")
    soundFile.close()
    return result
  elif filename.endswith(".raw"):
    soundFile = open(filename,mode="rb")
    result = None
    result = [int(item) for item in soundFile.read(2**32)][1:][::2]
    soundFile.close()
    return result
  elif filename.endswith(".txt"):
    return deserializeSound(filename)
  else:
    assert False, "unsupported file type."


def serializeSound(filename,sound):
  assert filename.endswith(".txt")
  soundFile = open(filename,"w")
  #soundFile.write("".join(chr(item) for item in sound))
  soundFile.write(str(sound))
  soundFile.close()


def deserializeSound(filename):
  assert filename.endswith(".txt")
  soundFile = open(filename,"r")
  #soundFile.write("".join(chr(item) for item in sound))
  result = soundFile.read(2**32)
  soundFile.close()
  return eval(result)


def saveSound(filename,sound):
  assert filename.endswith(".wav")
  soundFile = wave.open(filename,mode="wb")
  soundFile.setnchannels(1)
  soundFile.setsampwidth(1)
  soundFile.setframerate(44100)
  #soundFile.write("".join(chr(item) for item in sound))
  for item in sound:
    assert type(item) == int
    assert item < 256
    assert item >= 0
    #soundFile.write(eval("b'"+chr(item)+"'"))
    soundFile.writeframesraw(bytes([item]))
  soundFile.close()


def validateSound(sound):
  diffs = [0,0,0,0]
  if not type(sound) == list:
    return False
  for i in range(len(sound)-1):
    diffs[i%len(diffs)] += (sound[i] != sound[i+1])
  #print("diff sets are " + str(diffs) + ". these numbers should all be similar.")
  if 0 in diffs:
    return False
  ratios = [float(diffs[i])/float(diffs[ii]) for i in range(len(diffs)) for ii in range(i)]
  if min(ratios) < 0.8:
    return False
  return True


def loadSounds():
  for key in sounds.keys():
    sounds[key] = loadSound(key)

  sounds["sampleNoise"] = [128,128,127, 126, 124,113,112,89,32,16,17,14,0,1,9,8,77,78,97,201,210,203,185,183,144,101,99,96,99,124,129,156,146,149,177,181,185,184,170,160,140,110,50,55,75,125,11,123,245,254,255,255,255,254,251,236,249,237,234,221,201,145,103,96,91,115,119,144,144,145,147,149,155,165,175,185,188,193,250,230,210,205,160,50,40,35,31,31,32,39,47,88,86,82,41,13,9,8,6,5,4,4,3,3,3,4,3,2,0,1,2,4,7,17,45,23,46,36,49,62,61,65,98,127,128]
  sounds["sampleNoise"].extend([128 for i in range(128-len(sounds["sampleNoise"]))])
  assert len(sounds["sampleNoise"]) == 128
  for sound in sounds.values():
    if sound != None:
      assert validateSound(sound)


def toSerializableStr(inputSeq):
  return "["+",".join(("\n  " if (i%80==0 and i != 0) else "")+str(item) for i,item in enumerate(inputSeq))+"]"

def wrapStr(inputStr, targetLineLength, notifyInterval=8192):
  resultArr = []
  currentLine = ""
  for i,inputChar in enumerate(inputStr):
    if i%notifyInterval == 0 and i!=0:
      print("WaveIO.wrapStr: i="+str(i)+".")
    currentLine += inputChar
    if len(currentLine) > targetLineLength:
      if inputChar in [",", "[", "("]:
        resultArr.append(currentLine)
        currentLine = ""
  return "\n  ".join(resultArr)
    

def toPyShortStr(inputSeq,weaklyIntified=True):
  class Letter:
    def __init__(self,value):
      self.value = value
      self.count = 1
    def shallBeIntegrated(self): #approximate on the left side of the < maybe.
      lengthIfIntegrated = len(",".join(str(self.value) for i in range(self.count)))
      lengthIfNotIntegrated = len("]+["+str(self.value)+"]*"+str(self.count))
      result = lengthIfIntegrated < lengthIfNotIntegrated
      return result
    def mergeOrReturnAsLetter(self,newValue):
      if newValue == self.value:
        self.count += 1
        return None
      else:
        return Letter(newValue)
    def strSelf(self):
      return ",".join(str(self.value) for i in range(self.count)) if self.shallBeIntegrated() else "["+str(self.value)+"]*"+str(self.count)
    def strSelfBeginning(self): #if this item is the first of them all.
      return "[" if self.shallBeIntegrated() else ""
    def strSelfEnding(self): #if this item is the last of them all.
      return "]" if self.shallBeIntegrated() else ""
    def strBetweenSelfAndLeft(self,left):
      if left.shallBeIntegrated():
        return "," if self.shallBeIntegrated() else "]+"
      else:
        return "+[" if self.shallBeIntegrated() else "+"
  if weaklyIntified:
    inputSeq = IntArrMath.intified(inputSeq,weakly=True)
  holdingArr = []
  justStarted = True
  for item in inputSeq:
    if justStarted:
      holdingArr.append(Letter(item))
      justStarted = False
      continue
    addition = holdingArr[-1].mergeOrReturnAsLetter(item)
    if addition != None:
      assert isinstance(addition,Letter)
      holdingArr.append(addition)
  if len(holdingArr) == 0:
    #print("WaveIO.toPyShortStr: Warning: holdingArr is empty, so \"[]\" will be returned.")
    assert len(inputSeq) == 0
    return "[]"
  result = holdingArr[0].strSelfBeginning() + holdingArr[0].strSelf() + "".join(holdingArr[i].strBetweenSelfAndLeft(holdingArr[i-1])+holdingArr[i].strSelf() for i in range(1,len(holdingArr))) + holdingArr[-1].strSelfEnding()
  return result

def nestedToPyShortStr(inputSeqSeq,weaklyIntified=True):
  return "["+",".join(toPyShortStr(inputSeq,weaklyIntified=weaklyIntified) for inputSeq in inputSeqSeq)+"]"


#the following are disabled because they haven't been tested well and aren't as useful as toPyShortStr, which is self-decompressing.
"""
def genHumanRLEEncode(inputSeq):
  previousItem = None
  currentRunLength = 1
  justStarted = True
  for currentItem in inputSeq:
    if type(currentItem) == str:
      if currentItem.startswith("x"):
        raise ValueError("The input sequence already contains humanRLE signals.")
    if justStarted:
      previousItem = currentItem
      justStarted = False
      continue
    if previousItem == currentItem:
      currentRunLength += 1
    else:
      if currentRunLength > 1:
        yield "x"+str(currentRunLength)
        currentRunLength = 1
      yield currentItem
    previousItem = currentItem

def genHumanRLEDecode(inputSeq):
  previousItem = None
  for currentItem in inputSeq:
    if currentItem.startswith("x"):
      runLength = int(currentItem[1:])
      for i in range(runLength):
        yield previousItem
      continue
    else:
      yield currentItem
      previousItem = currentItem
"""


loadSounds()

