


def getStartingIndicesOfSubSequence(inputArr,subSequence):
  #the output could be streamable.
  #this method could be much faster.
  assert len(subSequence) > 0
  result = []
  for i in range(len(inputArr)-len(subSequence)+1):
    if inputArr[i:i+len(subSequence)] == subSequence:
      result.append(i)
  return result

def getEndingIndicesOfGrowingSubSequences(inputArr, searchTerm, keepOnlyLongest=True):
  #the output of this could be made streamable.
  if len(searchTerm) == 0:
    return [(0,[])]
  result = [(0,[]),(1,[])]
  for location in range(len(inputArr)):
    if inputArr[location] == searchTerm[-1]:
      result[-1][1].append(location)
  for currentLength in range(2,len(searchTerm)+1):
    result.append((currentLength,[]))
    for location in result[-2][1]:
      if location+1-currentLength < 0: #This test prevents wrapping around to the other end of the inputArr and general chaos. Without this test, the method finds nonexistant matches.
        continue
      if searchTerm[-currentLength] == inputArr[location+1-currentLength]:
        result[-1][1].append(location)
    if keepOnlyLongest:
      i = 0
      while i < len(result[-2][1]):
        if result[-2][1][i] in result[-1][1]:
          del result[-2][1][i]
        else:
          i += 1
    if len(result[-1][1]) == 0:
      break
  return result

def takeOnly(inputGen,count):
  i = 0
  for item in inputGen:
    if i < count:
      yield item
      i += 1
    else:
      break

def ordify(inputStr):
  return [ord(char) for char in inputStr]
  
"""
def genBleedSortedArr(inputArr):
  for item in inputArr:
    yield item
  lowerSpots = [item for item in inputArr]
  upperSpots = [item for item in inputArr]
  lowerSpotIndex = 0
  upperSpotIndex = 0
  skipLower = False
  while True:
    lowerSpotIndex %= len(lowerSpots)
    upperSpotIndex %= len(upperSpots)
    if skipLower:
      skipLower = False
    else:
      print(("start lower",lowerSpots,lowerSpotIndex,upperSpots,upperSpotIndex))
      lowerSpots[lowerSpotIndex] -= 1
      print("trying to place low"+str(lowerSpots[lowerSpotIndex]))
      if lowerSpots[lowerSpotIndex] in inputArr or lowerSpots[lowerSpotIndex] in upperSpots:
        del upperSpots[upperSpots.index(lowerSpots[lowerSpotIndex])]
        del lowerSpots[lowerSpotIndex] #index does not increase when the current item is removed.
        continue
      else:
        resultItem = "low"+str(lowerSpots[lowerSpotIndex])
        print(resultItem)
        yield resultItem
        lowerSpotIndex += 1
    lowerSpotIndex %= len(lowerSpots)
    upperSpotIndex %= len(upperSpots)
    print(("start upper",lowerSpots,lowerSpotIndex,upperSpots,upperSpotIndex))
    upperSpots[upperSpotIndex] += 1
    print("trying to place upp"+str(upperSpots[upperSpotIndex]))
    if upperSpots[upperSpotIndex] in inputArr or upperSpots[upperSpotIndex] in lowerSpots:
      del lowerSpots[lowerSpots.index(upperSpots[upperSpotIndex])]
      del upperSpots[upperSpotIndex] #index does not increase when the current item is removed.
      skipLower = True
      continue
    else:
      resultItem = "upp"+str(upperSpots[upperSpotIndex])
      print(resultItem)
      yield resultItem
      upperSpotIndex += 1
"""

def genBleedSortedArr(inputArr):
  #this generator will help in using a markov model with values the model has not seen before, by mapping them to smaller numbers when they are closer to a value that has been seen before.
  for item in inputArr:
    yield item
  lowerSpots = [item for item in inputArr] #these move down.
  upperSpots = [item for item in inputArr] #these move up.
  collisionSpots = None #these only appear when a lowerSpot and an upperSpot collide, and this list exists to make it easier to track where it happened but then delete it at the end of a sweep of all spots in order.
  while True:
    collisionSpots = []
    #print("inputArr-based dedupe phase...")
    #print("lowerSpots start as " + str(lowerSpots))
    i = 0
    while i < len(lowerSpots):
      while lowerSpots[i]-1 in inputArr:
        #print("deleting from lowerSpots at " + str(i))
        del lowerSpots[i]
        if i >= len(lowerSpots):
          #print("breaking delete loop.")
          break
      if i >= len(lowerSpots):
        break
      lowerSpots[i] -= 1
      i += 1
    #print("lowerSpots end up as " + str(lowerSpots))
    #print("upperSpots start as " + str(upperSpots))
    i = 0
    while i < len(upperSpots):
      while upperSpots[i]+1 in inputArr:
        #print("deleting from upperSpots at " + str(i))
        del upperSpots[i]
        if i >= len(lowerSpots):
          #print("breaking delete loop.")
          break
      if i >= len(upperSpots):
        break
      upperSpots[i] += 1
      i += 1
    #print("upperSpots end up as " + str(upperSpots))
    #print("cleanup phase...")
    #print("lowerSpots start as " + str(lowerSpots))
    #print("upperSpots start as " + str(upperSpots))
    i = 0
    while i < len(lowerSpots): #cleanup.
      if lowerSpots[i] in upperSpots: #simple dedupe branch.
        collisionSpots.append(lowerSpots[i]) #track until this value is shown once, then forget it after the largest loop continues.
        del upperSpots[upperSpots.index(lowerSpots[i])]
        del lowerSpots[i]
        continue
      if lowerSpots[i]+1 in upperSpots: #if an overlap just happened...
        #then these spots should both be eliminated.
        del upperSpots[upperSpots.index(lowerSpots[i]+1)]
        del lowerSpots[i]
      else:
        i += 1
    #print("lowerSpots end up as " + str(lowerSpots))
    #print("upperSpots end up as " + str(upperSpots))
    currentArr = sorted(lowerSpots+upperSpots+collisionSpots)
    #print("iterating through " + str(currentArr))
    for item in currentArr:
      yield item


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
    print("history: " + str(history))
    print("inputItem: " + str(inputItem))
    predictedItems = []
    """
    for contextLength in range(maxContextLength,0,-1):
      if contextLength > len(history)-1:
        continue #simpler than making a more complicated for loop range statement.
      contextLocations = [location+contextLength for location in getStartingIndicesOfSubSequence(history[:-1],history[-contextLength:])]
      contextualHist = Hist()
      for contextLocation in contextLocations:
        if history[contextLocation] not in predictedItems:
          contextualHist.register(history[contextLocation])
      extension = [key for key in contextualHist.keysInDescendingRelevanceOrder() if key not in predictedItems]
      print("(predictedItems,extension untrimmed,extension) for contextLength of " + str(contextLength) + " = " + str((predictedItems,contextualHist.keysInDescendingRelevanceOrder(),extension)))
      predictedItems.extend(extension)
    
    """
    for currentLength,matchesOfCurrentLength in getEndingIndicesOfGrowingSubSequences(history[:-1],history[-maxContextLength:])[::-1]:
      contextualHist = Hist()
      for matchEndLocation in matchesOfCurrentLength:
        if history[matchEndLocation+1] not in predictedItems:
          contextualHist.register(history[matchEndLocation+1])
      extension = [key for key in contextualHist.keysInDescendingRelevanceOrder() if key not in predictedItems]
      print("(predictedItems,extension untrimmed,extension) for currentLength of " + str(currentLength) + " = " + str((predictedItems,contextualHist.keysInDescendingRelevanceOrder(),extension)))
      predictedItems.extend(extension)
    
    print("predictedItems without general history = " + str(predictedItems))
    print("general history = " + str(singleUsageHist.data))
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





sampleTexts = ["You are my sunshine,\nmy only sunshine.\nYou make me happy\nwhen skies are grey!\nYou'll never know, dear,\nhow much I love you...\nplease don't take\nmy sunshine away."]



assert len([item for item in takeOnly(range(256),10)]) == 10

assert [item for item in takeOnly(genBleedSortedArr([5,8,10,11,15,16,17]),30)] == [5,8,10,11,15,16,17,4,6,7,9,12,14,18,3,13,19,2,20,1,21,0,22,-1,23,-2,24,-3,25,-4]

for test in [("hello, world!","rld"),("123456789 123456789 123456789 3456789 56789 789","678")]:
  assert [item+len(test[1])-1 for item in getStartingIndicesOfSubSequence(test[0],test[1])] == getEndingIndicesOfGrowingSubSequences(test[0],test[1])[-1][1]
  continue
