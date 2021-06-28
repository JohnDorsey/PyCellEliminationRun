import wave

#"Night_Sounds_-_Crickets-Lisa_Redfern-591005346.wav"
#"crickets8bmono44100.wav"

def convertAudio(sourceFileName,destFileName):
  readFile = wave.open(sourceFileName,mode='rb')
  data = [int(item) for item in readFile.readframes(88200)]
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

  data8b = [data[i] for i in range(len(data)) if i%4==1]


  print(len(data8b))
  print([int(item) for item in data8b][:2048])

  writeFile = wave.open(destFileName,mode='wb')
  writeFile.setnchannels(1)
  writeFile.setsampwidth(1)
  writeFile.setframerate(44100)
  writeFile.writeframesraw(bytes([(data8b[i]+128)%256 for i in range(len(data8b))]))
  writeFile.close()
