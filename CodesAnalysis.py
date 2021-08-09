"""

CodesAnalysis.py by John Dorsey.

CodesAnalysis.py contains tools for comparing different universal codings (in the form of CodecTools.Codec instances).

"""



from PyGenTools import makeArr


def getNextSizeIncreaseBounded(numberCodec,startValue,endValue):
  """
  getNextSizeIncreaseBounded bisects the given range of numbers until it finds the exact (lowest) number at which the numberCodec's encoded output is larger than it is at the start of the given range.
  This is the simple recursive version. Large enough inputs (e.g. 2**1024) may cause the recursion limit to be reached. getNextSizeIncreaseBoundedIterative has no similar limitation.
  """
  assert startValue < endValue
  startLength = len(makeArr(numberCodec.encode(startValue)))
  endLength = len(makeArr(numberCodec.encode(endValue)))
  assert startLength <= endLength
  if startLength == endLength:
    return None
  if startValue + 1 == endValue:
    assert startLength < endLength
    return endValue
  midpoint = int((startValue+endValue)/2)
  assert midpoint not in [startValue,endValue]
  lowerResult = getNextSizeIncreaseBounded(numberCodec,startValue,midpoint)
  if lowerResult != None:
    return lowerResult
  upperResult = getNextSizeIncreaseBounded(numberCodec,midpoint,endValue)
  return upperResult

def getNextSizeIncreaseBoundedIterAction(numberCodec,startValue,endValue):
  #a tool used mainly by the function getNextSizeIncreaseBoundedIterative.
  assert startValue < endValue
  startLength = len(makeArr(numberCodec.encode(startValue)))
  endLength = len(makeArr(numberCodec.encode(endValue)))
  assert startLength <= endLength
  if startLength == endLength:
    return ("fail",None,startValue,endValue)
  if startValue + 1 == endValue:
    assert startLength < endLength
    return ("finished",endValue,None,None)
  midpoint = int((startValue+endValue)/2)
  assert midpoint not in [startValue,endValue]
  return ("recycle",None,startValue,midpoint)
  #return (None,midpoint,endValue)

def getNextSizeIncreaseBoundedIterative(numberCodec,startValue,endValue):
  """
  getNextSizeIncreaseBounded bisects the given range of numbers until it finds the exact (lowest) number at which the numberCodec's encoded output is larger than it is at the start of the given range.
  """
  result = None
  previousValues = (None,None)
  currentValues = (startValue,endValue)
  while True:
    result = getNextSizeIncreaseBoundedIterAction(numberCodec,currentValues[0],currentValues[1])
    if result[0] == "finished":
      return result[1]
    elif result[0] == "recycle":
      previousValues = currentValues
      currentValues = (result[2],result[3])
      assert currentValues[0] < currentValues[1]
      continue
    elif result[0] == "fail":
      currentValues = (result[3],previousValues[1])
      if not currentValues[0] < currentValues[1]:
        return None
      if currentValues[0] == currentValues[1]:
        return None
      previousValues = (None,None)
      assert currentValues[0] < currentValues[1]
      continue
  assert False

def getNextSizeIncrease(numberCodec,startValue):
  """
  With no search area defined, find the next value at which a numberCodec's encoded output increases in length.
  """
  result = None
  i = 0
  try:
    while result == None:
      result = getNextSizeIncreaseBoundedIterative(numberCodec,startValue*(i+1),startValue*(i+2))
      i += 1
    if i > 2:
      print("getNextSizeIncrease: warning: i is " + str(i) + ".")
      #letting the search window grow with repeated failures would take advantage of the fact that the search used within that search window takes O(log(windowSize)) time, but searching windows of the same size over and over has a worse time complexity itself. It shouldn't matter unless the numberCodec allows the input value to more than double before the output value length increases by one bit.
    return result
  except KeyboardInterrupt:
    raise KeyboardInterrupt("Codes.getNextSizeIncrease: i was " + str(i) + ".")


def compareEfficienciesLinear(codecDict,valueGen):
  """
  compares numberCodecs in the provided dict over a range of size N in O(N) time. For ranges longer than millions or billions, use compareEfficiencies instead.
  """
  previousScores = {}
  currentScores = {}
  codecHistory = {}
  recordHolderHistory = []
  for key in codecDict.keys():
    previousScores[key] = None
    currentScores[key] = None
    codecHistory[key] = []
  updateRankings = False
  for testIndex,testValue in enumerate(valueGen):
    for key in codecDict.keys():
      testCodec = codecDict[key]
      previousScores[key] = currentScores[key]
      currentScores[key] = (testIndex,testValue,len(makeArr(testCodec.encode(testValue))))
      if previousScores[key] != currentScores[key]:
        codecHistory[key].append((testIndex,testValue,currentScores[key]))
        updateRankings = True
    if updateRankings:
      updateRankings = False
      currentBest = min(currentScores.values())
      recordHolders = [key for key in codecDict.keys() if currentScores[key] == currentBest]
      if len(recordHolderHistory) == 0 or recordHolders != recordHolderHistory[-1][3]:
        recordHolderHistory.append((testIndex,testValue,currentBest,recordHolders))
  return recordHolderHistory

def getEfficiencyDict(numberCodec,startValue,endValue):
  spot = startValue
  result = {}
  while True:
    spot = getNextSizeIncreaseBoundedIterative(numberCodec,spot,endValue)
    if spot == None:
      break
    result[spot] = len(makeArr(numberCodec.encode(spot)))
  return result

def compareEfficiencies(codecDict,startValue,endValue):
  """
  Directly compare the efficiencies of any number of numberCodecs over a given range of numbers. The output includes details on which input values give different answers for which of the numberCodecs is best. Wherever a numberCodec does not at least tie for first place in storage efficiency, its efficiency is not tracked. The first two entries in any output (the one with no winner and the one after it) provide no reliable information.
  """
  codecEfficiencies = {}
  for key in codecDict.keys():
    codecEfficiencies[key] = getEfficiencyDict(codecDict[key],startValue,endValue)
  events = {}

  #construct events:
  for codecKey in codecEfficiencies.keys():
    for numberKey in codecEfficiencies[codecKey].keys():
      eventToAdd = (codecKey,numberKey,codecEfficiencies[codecKey][numberKey])
      if numberKey in events.keys():
        events[numberKey].append(eventToAdd)
      else:
        events[numberKey] = [eventToAdd]

  currentScores = dict([(key,(None,None)) for key in codecDict.keys()])
  recordHolderHistory = [(None,None,[])]
  #traverse majorEvents:
  for eventKey in sorted(events.keys()): #the eventKey is the unencoded integer input value.
    for currentEvent in events[eventKey]: #multiple events may happen at the same input value.
      assert len(currentEvent) == 3
      currentScores[currentEvent[0]] = (currentEvent[1],currentEvent[2]) #currentScores[name of codec] = (input value, length of code).
      currentBest = min(item[1] for item in currentScores.values() if item[1] != None)
      currentRecordHolders = [key for key in currentScores.keys() if currentScores[key][1] == currentBest]
      if currentRecordHolders != recordHolderHistory[-1][2]:
        #add new recordHolderHistory entry.
        recordHolderHistory.append((eventKey,currentBest,currentRecordHolders))
  return recordHolderHistory




"""
>>>> def testFun(exp2Range):
....     for testExp2 in exp2Range:
....         testExp = 2**testExp2
....         print("\n2**{} (2**2**{})".format(testExp,testExp2))
....         result = [[testOrder,len([item for item in Codes.codecs["enbonacci"].encode(2**testExp,order=testOrder)])] for testOrder in range(2,30)]
....         for item in result:
....             item.extend([item[1]-testExp,float(item[1])/float(testExp)])
....         print(result)
....         


"""
