import wave


sounds = {"crickets8bmono44100.wav":None}


def loadSound(filename):
  soundFile = wave.open(filename,mode="rb")
  result = [int(item) for item in soundFile.readframes(2**32)]
  soundFile.close()
  return result


for key in sounds.keys():
  sounds[key] = loadSound(key)




