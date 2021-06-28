"""

CERWaves.py by John Dorsey.

When loaded, CERWaves.py loads sample audio for easy use in testing the codec. Audio samples included in the project are in the public domain.

"""



import wave


sounds = {"crickets8bmono44100.wav":None,"moo8bmono44100.wav":None}




def loadSound(filename):
  soundFile = wave.open(filename,mode="rb")
  result = [int(item) for item in soundFile.readframes(2**32)]
  soundFile.close()
  return result


for key in sounds.keys():
  sounds[key] = loadSound(key)

sounds["sampleNoise"] = [128,128,127, 126, 124,113,112,89,32,16,17,14,0,1,9,8,77,78,97,201,210,203,185,183,144,101,99,96,99,124,129,156,146,149,177,181,185,184,170,160,140,110,50,55,75,125,11,123,245,254,255,255,255,254,251,236,249,237,234,221,201,145,103,96,91,115,119,144,144,145,147,149,155,165,175,185,188,193,250,230,210,205,160,50,40,35,31,31,32,39,47,88,86,82,41,13,9,8,6,5,4,4,3,3,3,4,3,2,0,1,2,4,7,17,45,23,46,36,49,62,61,65,98,127,128]
sounds["sampleNoise"].extend([128 for i in range(128-len(sounds["sampleNoise"]))])
assert len(sounds["sampleNoise"]) == 128



