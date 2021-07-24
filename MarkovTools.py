"""

MarkovTools.py by John Dorsey.

MarkovTools.py contains tools for transforming sequences using markov models.

"""

from PyGenTools import genTakeOnly, arrTakeOnly
from HistTools import OrderlyHist



def getStartingIndicesOfSubSequence(inputArr,subSequence):
  #search an entire input array and output a list of all indices where matches with a specified subSequence start.
  #the output could be streamable.
  #this method could be much faster. The faster version _is_ MarkovTools.getEndingIndicesOfGrowingSubSequences.
  assert len(subSequence) > 0
  result = []
  for i in range(len(inputArr)-len(subSequence)+1):
    if inputArr[i:i+len(subSequence)] == subSequence:
      result.append(i)
  return result


def getEndingIndicesOfGrowingSubSequences(inputArr, searchTerm, keepOnlyLongest=True):
  #search an entire input array, and output all ending indices of matches with any portion of searchTerm which ends at the end of searchTerm. So searching for [2,3,4,5] is the same as searching for [5], and then searching among those matches for places that also match [4,5], and so on. The time complexity is O(total number of matches). This makes it superior to using getStartingIndicesOfSubSequence repeatedly.
  #the keepOnlyLongest option is useful for avoiding double-counting. With it enabled, a search for "34567" in "1234567" finds only one match of length 5 instead of one match for each length in [1,2,3,4,5].
  #the output of this could be made streamable. But there is little use - most of the ways it is used require reversing the order of the items of its output.
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





def ordify(inputStr):
  return [ord(char) for char in inputStr]



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






def extendWithoutDupes(arrToExtend,extensionSrc):
  arrToExtend.extend(item for item in extensionSrc if not item in arrToExtend)


def genDynamicMarkovTranscode(inputSeq,opMode,maxContextLength=16,scoreMode="(max(l),f(max(l)),max(x(max(l))),-y)"):
  assert opMode in ["encode","decode"]
  #in a scoreMode definition, l is the set of all unique lengths of all matches (to what? it varies), the function f gives the frequency of matches of a length, the function x gives all positions of all matches of a length, and y is just the value of the item being analyzed.
  assert scoreMode in ["(max(l),f(max(l)),max(x(max(l))),-y)","(max(l)*f(max(l)),max(x(max(l))),-y)"]
  history = []
  singleUsageHist = OrderlyHist()

  for inputItem in inputSeq:
    #print("history: " + str(history))
    #print("inputItem: " + str(inputItem))
    predictedItems = []

    #analyze phase:
    #all known history, but NOT the current plainData or pressData item, is used to create a map that can be used to convert between a plainData item and a pressData item. This map will LATER be used to transcode whatever the current item is, in whichever direction it must be transcoded.
    if scoreMode == "(max(l),f(max(l)),max(x(max(l))),-y)":
      #the following code really is incompatible with the idea of merging the single analyzed item into the search term, because it needs to add things to predictedItems in strictly descending match length order.
      currentLengthContextHist = None
      for currentLength,matchesOfCurrentLength in getEndingIndicesOfGrowingSubSequences(history[:-1],history[-maxContextLength:])[::-1]:
        currentLengthContextHist = OrderlyHist()
        for matchEndLocation in matchesOfCurrentLength:
          if history[matchEndLocation+1] not in predictedItems:
            currentLengthContextHist.register(history[matchEndLocation+1])
        extendWithoutDupes(predictedItems,currentLengthContextHist.keysInDescendingRelevanceOrder())
      #print("predictedItems without general history = " + str(predictedItems))
      #print("general history = " + str(singleUsageHist.data))
      extendWithoutDupes(predictedItems,singleUsageHist.keysInDescendingRelevanceOrder())
    elif scoreMode == "(max(l)*f(max(l)),max(x(max(l))),-y)":
      #the following code is a change towards including the search item in the search term, and it avoids needing to apply a singleUsageHist at the end, because the main search includes these items when its match length is 1.
      assert False, "NOT FINISHED!"
      allLengthSearchItemHist = OrderlyHist()
      for searchItem in singleUsageHist.keysInDescendingRelevanceOrder():
        for currentLength,matchesOfCurrentLength in getEndingIndicesOfGrowingSubSequences(history,history[-maxContextLength:]+[searchItem])[::-1]:
          for matchEndLocation in matchesOfCurrentLength:
            assert history[matchEndLocation] == searchItem
            if history[matchEndLocation] not in predictedItems:
              allLengthSearchItemHist.registerMany(history[matchEndLocation],currentLength) #this currentLength is the "l" in "l*f", and the "f" is the result of repeatedly running this line.
          extendWithoutDupes(predictedItems,contextualHist.keysInDescendingRelevanceOrder())

    #transcode phase.
    resultItem = None
    if scoreMode.endswith(",-y)"):
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
    else:
      assert False, "unfinished."

    #yield phase.
    yield resultItem

    #update phase.
    if opMode == "encode":
      history.append(inputItem)
      singleUsageHist.register(inputItem)
    elif opMode == "decode":
      history.append(resultItem)
      singleUsageHist.register(resultItem)
    else:
      assert False





sampleTexts = ["hello, world!","123456789 123456789 123456789 123456789 123456789 3456789 3456789 3456789 3456789 56789 56789 56789 789 789 9"]




assert arrTakeOnly(genBleedSortedArr([5,8,10,11,15,16,17]),30) == [5,8,10,11,15,16,17,4,6,7,9,12,14,18,3,13,19,2,20,1,21,0,22,-1,23,-2,24,-3,25,-4]

for test in [(sampleTexts[0],"rld"),(sampleTexts[1],"678")]:
  assert [item+len(test[1])-1 for item in getStartingIndicesOfSubSequence(test[0],test[1])] == getEndingIndicesOfGrowingSubSequences(test[0],test[1])[-1][1]
  continue

assert [item for item in genDynamicMarkovTranscode([5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100,5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100,5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100,5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100],"encode")] == [5, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
assert [item for item in genDynamicMarkovTranscode([5, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],"decode")] == [5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100,5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100,5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100,5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100]

