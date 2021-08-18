"""

WavePrep.py by John Dorsey.

WavePrep.py provides tools to convert .wav files to new .wav files in a fixed format (normally 44.1kHz unsigned 8-bit mono) for easy testing of compression. Always listen to the output file to make sure it has been converted correctly!

"""


import wave
import WaveIO

#"Night_Sounds_-_Crickets-Lisa_Redfern-591005346.wav"
#"crickets8bmono44100.wav"

#use a frame count of 88200 to replicate early sample files like moo.


def convertAudio(sourceFileName, destFileName, destFramerate=44100):
  readFile = wave.open(sourceFileName,mode='rb')
  data = [int(item) for item in readFile.readframes(2**32)]
  #data = data[44100:77175]
  readFile.close()

  print(len(data))
  print([int(item) for item in data][:2048])
  for i in range(len(data)-8):
    #data[i] /= 2
    #data[i] += data[i+4]/32
    #data[i] = min(int(data[i]),255)
    if not i%4:
      data[i] = 0

  data_int8 = [data[i] for i in range(len(data)) if i%4==1]
  data_uint8 = [(data_int8[i]+128)%256 for i in range(len(data_int8))]

  print(len(data_uint8))
  print([int(item) for item in data_uint8][:2048])

  writeFile = wave.open(destFileName+".wav", mode='wb')
  writeFile.setnchannels(1)
  writeFile.setsampwidth(1)
  writeFile.setframerate(destFramerate)
  writeFile.writeframesraw(bytes(data_uint8))
  writeFile.close()
  
  WaveIO.serializeSound(destFileName+".txt",data_uint8)
