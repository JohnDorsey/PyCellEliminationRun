import wave



readCrickets = wave.open("Night_Sounds_-_Crickets-Lisa_Redfern-591005346.wav",mode='rb')
data = [int(item) for item in readCrickets.readframes(44100)][44100:77175]
readCrickets.close()

print([int(item) for item in data][:4096])
for i in range(len(data)-8):
  #data[i] /= 2
  #data[i] += data[i+4]/32
  #data[i] = min(int(data[i]),255)
  if not i%2:
    data[i] = 0

data8b = [data[i] for i in range(len(data)) if i%2==1]

writeCrickets = wave.open("crickets8bmono44100.wav",mode='wb')
writeCrickets.setnchannels(1)
writeCrickets.setsampwidth(1)
writeCrickets.setframerate(44100)
writeCrickets.writeframesraw(bytes([(data8b[i]+128)%256 for i in range(len(data8b))]))
writeCrickets.close()
