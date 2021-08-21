"""

WavePrep.py by John Dorsey.

WavePrep.py provides tools to convert .wav files to new .wav files in a fixed format (normally 44.1kHz unsigned 8-bit mono) for easy testing of compression. Always listen to the output file to make sure it has been converted correctly!

"""

import WaveIO

#use a frame count of 88200 to replicate early sample files like moo.

def getDataPreviewStr(data, displayItemCount=1000):
  assert displayItemCount > 80
  endLength = (displayItemCount//2)-20
  dotCount = (len(data)-(endLength*2)).bit_length()
  assert dotCount >= 3
  return "{} ({} items).".format(
    (str(data) if len(data) < displayItemCount else str(data[:endLength])[:-1]+", " + ("."*dotCount) + ", "+str(data[-endLength:])[1:]),
    len(data)
  )
  

def convertAudio(source, destFileName, sourceFramerate=None, resamplingInterval=1):
  if not sourceFramerate % resamplingInterval == 0:
    raise ValueError("The resampling interval must divide the source framerate.")
    
  if type(source) == str:
    print("source argument is a filename.")
    data = WaveIO.loadSound(source)
  else:
    print("source argument is not a filename.")
    data = source.copy()

  print("sourceFramerate is {}.".format(sourceFramerate))
  print("data is " + getDataPreviewStr(data))
  
  for i in range(len(data)-8):
    if not i%4:
      data[i] = None #do not use this sample!

  old_rate_data_int8 = [data[i] for i in range(len(data)) if i%4==1]
  print("old_rate_data_int8 is " + getDataPreviewStr(old_rate_data_int8))
  old_rate_data_uint8 = [(old_rate_data_int8[i]+128)%256 for i in range(len(old_rate_data_int8))]
  print("old_rate_data_uint8 is " + getDataPreviewStr(old_rate_data_uint8))
  
  new_rate_data_uint8 = old_rate_data_uint8[::resamplingInterval]
  destFramerate = sourceFramerate / resamplingInterval
  
  print("destFramerate is {}.".format(destFramerate))
  print("new_rate_data_uint8 is " + getDataPreviewStr(new_rate_data_uint8))
  
  assert None not in new_rate_data_uint8, "something went wrong while adjusting the framerate."

  WaveIO.saveSound(destFileName+".wav", new_rate_data_uint8, framerate=destFramerate)
  
  WaveIO.serializeSound(destFileName+".txt", new_rate_data_uint8)
