"""

CERWaves.py by John Dorsey.

When loaded, CERWaves.py loads sample audio for easy use in testing the codec. Audio samples included in the project are in the public domain.

"""



import wave


sounds = {"crickets8bmono44100.wav":None}


def loadSound(filename):
  soundFile = wave.open(filename,mode="rb")
  result = [int(item) for item in soundFile.readframes(2**32)]
  soundFile.close()
  return result


for key in sounds.keys():
  sounds[key] = loadSound(key)




