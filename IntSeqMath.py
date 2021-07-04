"""

IntSeqMath.py by John Dorsey.

IntSeqMath.py contains tools for transforming integer sequences into other integer sequences.

"""




def genTrackMean(inputNumSeq):
  currentSum = 0
  for i,item in enumerate(inputNumSeq):
    currentSum += item
    yield (currentSum/float(i+1),item)

def genTrackMin(inputNumSeq):
  currentMin = None
  for i,item in enumerate(inputNumSeq):
    if i == 0:
      currentMin = item
    else:
      currentMin = min(currentMin,item)
    yield (currentMin,item)



def genDeltaEncode(inputNumSeq):
  previousItem = 0
  for item in inputNumSeq:
    yield item - previousItem
    previousItem = item

def genDeltaDecode(inputNumSeq):
  previousItem = 0
  for item in inputNumSeq:
    yield item + previousItem
    previousItem += item





def getStartingIndicesOfSubSequence(inputArr,subSequence):
  #the output could be streamable.
  assert len(subSequence) > 0
  result = []
  for i in range(len(inputArr)-len(subSequence)+1):
    if inputArr[i:i+len(subSequence)] == subSequence:
      result.append(i)
  return result


class Hist:
  #Hist is a histogram tool to track frequency, order first encountered, and order last encountered.
  def __init__(self):
    self.data = dict()
    self.writeCount = 0

  def __setitem__(self,key,value):
    print("Hist.__setitem__ should not be used.")
    assert len(value) == 3
    self.writeCount += 1
    self.data[key] = value

  def __getitem__(self,key):
    try:
      return self.data[key]
    except KeyError:
      return (None,None,None)

  def register(self,key):
    self.writeCount += 1
    currentValue = self.__getitem__(key)
    if None in currentValue:
      currentValue = (0,self.writeCount,self.writeCount)
    self.data[key] = (currentValue[0]+1,currentValue[1],self.writeCount)
    assert len(self.data[key]) == 3

  def keysInDescendingFreqOrder(self):
    return [itemC[0] for itemC in sorted([item for item in self.data.iteritems()],key=(lambda itemB: itemB[1]))[::-1]]

  def keysInDescendingRelevanceOrder(self):
    #it is important that this method sorts first by frequency and then sorts by recentness within identical frequencies.
    keyFun = (lambda itemB: itemB[1][0]*(self.writeCount+1)+itemB[1][2])
    for value in self.data.values():
      assert len(value) == 3
    return [itemC[0] for itemC in sorted([item for item in self.data.iteritems()],key=keyFun)[::-1]]


def genDynamicMarkovTranscode(inputSeq,opMode,maxContextLength=16):
  assert opMode in ["encode","decode"]
  history = []
  contextualHist = None
  singleUsageHist = Hist()
  for inputItem in inputSeq:
    print("inputItem: " + str(inputItem))
    predictedItems = []
    for contextLength in range(maxContextLength,0,-1):
      if contextLength > len(history)-1:
        continue #simpler than making a more complicated for loop range statement.
      contextLocations = [location+contextLength for location in getStartingIndicesOfSubSequence(history[:-1],history[-contextLength:])]
      contextualHist = Hist()
      for contextLocation in contextLocations:
        if history[contextLocation] not in predictedItems:
          contextualHist.register(history[contextLocation])
      #print("predictedItems before extension for contextLength of " + str(contextLength) + " = " + str(predictedItems))
      predictedItems.extend(key for key in contextualHist.keysInDescendingRelevanceOrder() if key not in predictedItems)
    print("predictedItems without general history = " + str(predictedItems))
    print("general history = " + str(singleUsageHist.data))
    """for historyItem in history[:-1][::-1]:
      if historyItem not in predictedItems:
        predictedItems.append(historyItem)"""
    predictedItems.extend(key for key in singleUsageHist.keysInDescendingRelevanceOrder() if key not in predictedItems)
    print("predictedItems = " + str(predictedItems))
    resultItem = None
    if opMode == "encode":
      if inputItem in predictedItems:
        resultItem = predictedItems.index(inputItem)
      else:
        resultItem = inputItem + len(predictedItems) - len([predictedItem for predictedItem in predictedItems if predictedItem < inputItem])
    elif opMode == "decode":
      if inputItem < len(predictedItems):
        resultItem = predictedItems[inputItem]
      else:
        resultItem = inputItem - len(predictedItems) + len([predictedItem for predictedItem in predictedItems if predictedItem < inputItem])
    else:
      assert False
    print("resultItem = " + str(resultItem))
    yield resultItem
    if opMode == "encode":
      history.append(inputItem)
      singleUsageHist.register(inputItem)
    elif opMode == "decode":
      history.append(resultItem)
      singleUsageHist.register(resultItem)
    else:
      assert False




assert [item for item in genDeltaDecode(genDeltaEncode([5,5,6,5,3,0,10,0]))] == [5,5,6,5,3,0,10,0]

