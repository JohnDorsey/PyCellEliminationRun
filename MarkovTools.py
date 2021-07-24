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

def getEndingIndicesOfShrinkingSubSequences(inputArr, searchTerm, keepOnlyLongest=True):
  return getEndingIndicesOfGrowingSubSequences(inputArr, searchTerm, keepOnlyLongest=keepOnlyLongest)[::-1]



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


def getPredictedValuesFromHistory(history,singleUsageHist,maxContextLength,scoreMode):
  predictedValues = []
  if scoreMode == "(max(l),f(max(l)),max(x(max(l))),-y)":
    #the following code really is incompatible with the idea of merging the single analyzed item into the search term, because it needs to add things to predictedItems in strictly descending match length order.
    currentLengthContextHist = None
    for currentLength,matchesOfCurrentLength in getEndingIndicesOfShrinkingSubSequences(history[:-1],history[-maxContextLength:]):
      currentLengthContextHist = OrderlyHist()
      for matchEndLocation in matchesOfCurrentLength:
        if history[matchEndLocation+1] not in predictedValues:
          currentLengthContextHist.register(history[matchEndLocation+1])
      extendWithoutDupes(predictedValues,currentLengthContextHist.keysInDescendingRelevanceOrder())
    #print("predictedItems without general history = " + str(predictedItems))
    #print("general history = " + str(singleUsageHist.data))
    extendWithoutDupes(predictedValues,singleUsageHist.keysInDescendingRelevanceOrder())
  elif scoreMode == "(max(l)*f(max(l)),max(x(max(l))),-y)":
    #the following code is a change towards including the search item in the search term, and it avoids needing to apply a singleUsageHist at the end, because the main search includes these items when its match length is 1.
    assert False, "NOT FINISHED!"
    allLengthSearchItemHist = OrderlyHist()
    for searchItem in singleUsageHist.keysInDescendingRelevanceOrder():
      for currentLength,matchesOfCurrentLength in getEndingIndicesOfShrinkingSubSequences(history,history[-maxContextLength:]+[searchItem]):
        for matchEndLocation in matchesOfCurrentLength:
          assert history[matchEndLocation] == searchItem
          if history[matchEndLocation] not in predictedValues:
            allLengthSearchItemHist.registerMany(history[matchEndLocation],currentLength) #this currentLength is the "l" in "l*f", and the "f" is the result of repeatedly running this line.
        extendWithoutDupes(predictedValues,contextualHist.keysInDescendingRelevanceOrder())
  else:
    assert False, "invalid scoreMode."
  return predictedValues
  
def getValueChancesFromHistory(history,maxContextLength,chanceFun,singleUsageHist=None):
  itemChanceDict = dict()
  searchItemGen = None #searchItemGen may be built in different ways and give different item orders, but it doesn't really matter since in this method, the probability given to each item doesn't depend on when it is processed or what the unfinished output looks like so far.
  if singleUsageHist != None:
    try:
      searchItemGen = singleUsageHist.keysInDescendingRelevanceOrder()
    except AttributeError: #it's probably of type dict and not a histogram class.
      searchItemGen = singleUsageHist.keys()
  else:
    searchItemGen = genDeduped(history)
  for searchItem in searchItemGen:
    searchTerm = history[-maxContextLength:] + [searchItem]
    matchEndIndices = getEndingIndicesOfGrowingSubSequences(history,searchTerm)
    itemChanceDict[searchItem] = chanceFun(matchEndIndices)
  return itemChanceDict
  
  
def remapToPredictedValuesTranscode(inputValue,opMode,predictedValues):
  if opMode not in ["encode","decode"]:
    raise ValueError("invalid opMode.")
  if opMode == "encode":
    if inputValue in predictedValues:
      resultValue = predictedValues.index(inputValue)
    else:
      resultValue = inputValue + len(predictedValues) - len([predictedValue for predictedValue in predictedValues if predictedValue < inputValue])
  elif opMode == "decode":
    if inputValue < len(predictedValues):
      resultValue = predictedValues[inputValue]
    else:
      resultValue = inputValue - len(predictedValues) + len([predictedValue for predictedValue in predictedValues if predictedValue < inputValue])
  else:
    assert False, "reality error."
  return resultValue

        
def genDynamicMarkovTranscode(inputSeq,opMode,maxContextLength=16,scoreMode="functional",scoreFun=None):
  assert opMode in ["encode","decode"]
  #in a scoreMode definition, l is the set of all unique lengths of all matches (to what? it varies), the function f gives the frequency of matches of a length, the function x gives all positions of all matches of a length, and y is just the value of the item being analyzed.
  assert scoreMode in ["(max(l),f(max(l)),max(x(max(l))),-y)","(max(l)*f(max(l)),max(x(max(l))),-y)","functional"]
  probabilityMode = "explicit" if scoreMode == "functional" else "implicit"
  if scoreMode != "functional":
    if scoreFun != None:
      print("MarkovTools.genDynamicMarkovTranscode: warning: scoreFun will be ignored because scoreMode is not \"functional\".")
  else:
    if scoreFun == None: #if the scoreFun still needs to be initialized to its default value...
      def scoreFun(inputMatchIndexArrArr,currentHistoryLength):
        #this function assumes that the inputMatchIndexArrArr is sorted by the first item of each tuple. It does NOT assume that the second item of each tuple is sorted, so it uses max() in a slow way.
        #this function assumes the matches are for searches involving an item being investigated, and including that item in the search term. it is correct to use currentHistoryLength when scaling using locationOfLatestLongestMatch because no match location can be higher than that.
        maxMatchLength = max([inputMatchIndexArrArr[0][0],inputMatchIndexArrArr[-1][0]])
        direction = inputMatchIndexArrArr[-1][0] > inputMatchIndexArrArr[0][0]
        maxMatchLengthIndex = -1 if direction else 0
        locationOfLatestLongestMatch = float(max(inputMatchIndexArrArr[maxMatchLengthIndex]))
        assert 0 <= locationOfLatestLongestMatch <= 1
        result = sum((len(matchesOfLengthX)*x) for x,matchesOfLengthX in inputMatchIndexArrArr)
        #the following scaling operation avoids the need for floats and ensures that every scored value will have a unique integer score.
        result = (result * currentHistoryLength) + locationOfLatestLongestMatch
        return result
  history = []
  singleUsageHist = OrderlyHist()

  for inputValue in inputSeq:
    #print("history: " + str(history))
    #print("inputItem: " + str(inputItem))

    #analyze phase:
    #all known history, but NOT the current plainData or pressData item, is used to create a map that can be used to convert between a plainData value and a pressData value. This map will LATER be used to transcode whatever the current value is, in whichever direction it must be transcoded.
    if probabilityMode == "implicit": #in this mode, probabilities are assumed from the order of ranked predictions.
      predictedValues = getPredictedValuesFromHistory(history,singleUsageHist,maxContextLength,scoreMode)
      #transcode phase.
      resultValue = None
      if scoreMode.endswith(",-y)"):
        resultValue = remapToPredictedValuesTranscode(inputValue,opMode,predictedValues)
      else:
        assert False, "unfinished."
      #yield phase.
      yield resultValue
    elif probabilityMode == "explicit":
      raise NotImplementedError()
    else:
      assert False, "invalid probabilityMode."

    #update phase.
    if opMode == "encode":
      history.append(inputValue)
      singleUsageHist.register(inputValue)
    elif opMode == "decode":
      history.append(resultValue)
      singleUsageHist.register(resultValue)
    else:
      assert False





sampleTexts = ["hello, world!","123456789 123456789 123456789 123456789 123456789 3456789 3456789 3456789 3456789 56789 56789 56789 789 789 9"]




assert arrTakeOnly(genBleedSortedArr([5,8,10,11,15,16,17]),30) == [5,8,10,11,15,16,17,4,6,7,9,12,14,18,3,13,19,2,20,1,21,0,22,-1,23,-2,24,-3,25,-4]

for test in [(sampleTexts[0],"rld"),(sampleTexts[1],"678")]:
  assert [item+len(test[1])-1 for item in getStartingIndicesOfSubSequence(test[0],test[1])] == getEndingIndicesOfGrowingSubSequences(test[0],test[1])[-1][1]
  continue

assert [item for item in genDynamicMarkovTranscode([5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100], "encode", scoreMode="(max(l),f(max(l)),max(x(max(l))),-y)")] == [5, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
assert [item for item in genDynamicMarkovTranscode([5, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],"decode",scoreMode="(max(l),f(max(l)),max(x(max(l))),-y)")] == [5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100]

