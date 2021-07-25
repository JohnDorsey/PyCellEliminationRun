"""

MarkovTools.py by John Dorsey.

MarkovTools.py contains tools for transforming sequences using markov models.

"""

from PyGenTools import genTakeOnly, arrTakeOnly, makeGen, genDeduped, ExhaustionError
from HistTools import OrderlyHist
import HuffmanMath
import CodecTools
import Codes


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
    itemChanceDict[searchItem] = chanceFun(matchEndIndices,len(history))
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

def findMax(inputSeq,keyFun=None):
  if keyFun == None:
    keyFun = (lambda x: x)
  recordHigh = None
  recordHighIndex = None
  justStarted = True
  for i,item in enumerate(inputSeq):
    if justStarted:
      recordHigh = keyFun(item)
      recordHighIndex = i
      justStarted = False
      continue
    if keyFun(item) > recordHigh:
      recordHigh = keyFun(item)
      recordHighIndex = i
  return (recordHighIndex,recordHigh)
  

def basicMatchIndexArrArrScoreFun(inputMatchIndexArrArr,currentHistoryLength): #this is the demo/default scoreFun for genDynamicMarkovTranscode.
  #this function does not assume that the inputMatchIndexArrArr is sorted by the first item of each tuple. It also does NOT assume that the second item of each tuple is sorted, so it uses max() in a slow way.
  #this function assumes the matches are for searches involving an item being investigated, and including that item in the search term. it is correct to use currentHistoryLength when scaling using locationOfLatestLongestMatch because no match location can be higher than that.
  result = None
  #thereAreMatches = sum(len(pair[1]) for pair in inputMatchIndexArrArr) > 0
  #if thereAreMatches:
  maxMatchLengthIndex, maxMatchLength = findMax(inputMatchIndexArrArr,keyFun=(lambda pair: pair[0]))
  if maxMatchLengthIndex != None and len(inputMatchIndexArrArr[maxMatchLengthIndex][1]) > 0:
    #direction = inputMatchIndexArrArr[-1][0] > inputMatchIndexArrArr[0][0]
    #maxMatchLengthIndex = -1 if direction else 0
    
    locationOfLatestLongestMatch = float(max(inputMatchIndexArrArr[maxMatchLengthIndex][1]))
    assert 0 <= locationOfLatestLongestMatch <= currentHistoryLength
    result = sum((len(matchesOfLengthX)*x) for x,matchesOfLengthX in inputMatchIndexArrArr)
    #the following scaling operation avoids the need for floats and ensures that every scored value will have a unique integer score.
    result = (result * currentHistoryLength) + locationOfLatestLongestMatch
  else:
    result = 0
  return result


class Escape:
  """
  This class is for use inside genDynamicMarkovTranscode. This class indicates that the huffman codec _will not_ know what to do with the following value because it has never been encountered before. This class will probably only be used when a huffman codec is being used and the probabilityMode is "explicit". This class is a temporary solution to be used until there is something in place to give huffman coding codecs (either within this method or in general) an escape code that is always present in their database.
  """
  def __init__(self):
    pass










def genDynamicMarkovTranscodeFunctional(inputSeq, opMode, maxContextLength=16, noveltyCodec=None, scoreFun=None, addDbgChars=False, addDbgWords=False):
  """
  inputSeq is the source, which may be a generator.
  maxContextLength is the maximum length of a match that will be recognized. Larger values should give better compression without significant performance impact, see performance notes on getEndingIndicesOfGrowingSubSequence.
  noveltyCodec is used to transcode the values of novel symbols after an escape symbol. Right now it only applies to explicit probability mode.
  scoreFun is the scoring function used to score a possible new value based on its arguments, which are (1) a collection of known matches for that value and various context lengths before it and (2) the length of recorded history.
  """
  inputSeq = makeGen(inputSeq)
  assert opMode in ["encode","decode"]
  if scoreFun == None: #if the scoreFun still needs to be initialized to its default value...
    scoreFun = basicMatchIndexArrArrScoreFun
  if noveltyCodec == None:
    noveltyCodec = Codes.codecs["fibonacci"]
  escapeValue = Escape() #just keep one instance of this for use inside here.
  history = []

  getNewValueChanceDict = (lambda: getValueChancesFromHistory([escapeValue]+history,maxContextLength,scoreFun)) #this exists as a function just so that it can easily be repeated in the attempt loop. escapeValue is prepended to history so that encoding escapeValue should be immediately possible for the huffman coding codec created from the returned dict. using singleUsageHist as an argument to getValueChanceFromHistory is avoided here just to avoid needing to change it to include escapeValue to make escapeValue representable.
  getNewValueHuffmanCodec = (lambda: HuffmanMath.makeHuffmanCodecFromDictHist(valueChanceDict)) #this exists as a function just so that it can easily be repeated in the attempt loop.

  while True:
    inputValue = None #to be initialized later.

    #analyze phase.
    valueChanceDict = getNewValueChanceDict()
    valueHuffmanCodec = getNewValueHuffmanCodec()
    
    #parse phase. This is the same as the transcode phase in the case of huffman coding.
    resultValue = None
    if opMode == "encode":
      #the attempt loop.
      while True:
        try:
          inputValue = next(inputSeq)
          resultValue = valueHuffmanCodec.encode(inputValue)
          break
        except HuffmanMath.AlienError: #if the item is not representable by valueHuffmanCodec because it has never been seen before...
          
          if addDbgWords:
            yield "(fail in attempt loop; huffman-coded escapeValue and noveltyCodec-coded inputValue to follow.)"
            
          for outputComponent in valueHuffmanCodec.encode(escapeValue): #it should be able to do this.
            yield outputComponent
          if addDbgChars:
            yield ","
          history.append(escapeValue)
          #it isn't necessary to update valueHuffmanCodec at this time because it won't be used before the next time it is updated.
          
          for outputComponent in noveltyCodec.encode(inputValue):
            yield outputComponent
          if addDbgChars:
            yield ","
          history.append(inputValue)
          
          valueChanceDict = getNewValueChanceDict()
          valueHuffmanCodec = getNewValueHuffmanCodec()
      
      if addDbgWords:
        yield "(" + str(inputValue) + " became:)"
      for outputComponent in resultValue:
        yield outputComponent
      if addDbgChars:
        yield ","
      history.append(inputValue)
          
    elif opMode == "decode":
      try:
        resultValue = valueHuffmanCodec.decode(inputSeq)
      except ExhaustionError:
        print("MarkovTools.genDynamicMarkovTranscodeFunctional: ending due to ExhaustionError from valueHuffmanCodec.")
        return
      history.append(resultValue)
      #it isn't necessary to update valueHuffmanCodec at this time because it won't be used before the next time it is updated.
      if resultValue == escapeValue:
        #no version of the escapeValue will be yielded. Anyone reading the plaindata does not need to know!.
        resultValue = noveltyCodec.decode(inputSeq)
        history.append(resultValue)
        
      if addDbgWords:
        yield "(dec out:)"      
      yield resultValue
      if addDbgChars:
        yield ","
      valueChanceDict = getNewValueChanceDict()
      valueHuffmanCodec = getNewValueHuffmanCodec()
    else:
      assert False, "invalid opMode."













def genDynamicMarkovTranscodeNonFunctional(inputSeq, opMode, maxContextLength=16, scoreMode="(max(l),f(max(l)),max(x(max(l))),-y)", addDbgChars=False, addDbgWords=False):
  """
  deprecated. Anything this function can do, the functional version can do better.
  """
  inputSeq = makeGen(inputSeq)
  assert opMode in ["encode","decode"]
  #in a scoreMode definition, l is the set of all unique lengths of all matches (to what? it varies), the function f gives the frequency of matches of a length, the function x gives all positions of all matches of a length, and y is just the value of the item being analyzed.
  assert scoreMode in ["(max(l),f(max(l)),max(x(max(l))),-y)","(max(l)*f(max(l)),max(x(max(l))),-y)"]
        
  history = []
  singleUsageHist = OrderlyHist()

  while True:
    inputValue = None #to be initialized later.
    
    #parse phase.
    try:
      inputValue = next(inputSeq)
    except StopIteration:
      print("MarkovTools.genDynamicMarkovTranscodeNonFunctional: stopping because inputSeq is now empty.")
      return
    #analyze phase:
    #all known history, but NOT the current plainData or pressData item, is used to create a map that can be used to convert between a plainData value and a pressData value. This map will LATER be used to transcode whatever the current value is, in whichever direction it must be transcoded.
    predictedValues = getPredictedValuesFromHistory(history,singleUsageHist,maxContextLength,scoreMode)
    
    #transcode phase.
    resultValue = None
    if scoreMode.endswith(",-y)"):
      resultValue = remapToPredictedValuesTranscode(inputValue,opMode,predictedValues)
    else:
      assert False, "unfinished."
      
    #yield phase.
    if addDbgWords:
      yield "(norm out:)"
    yield resultValue
    if addDbgChars:
      yield ","
    
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

assert [item for item in genDynamicMarkovTranscodeNonFunctional([5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100], "encode")] == [5, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
assert [item for item in genDynamicMarkovTranscodeNonFunctional([5, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],"decode")] == [5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100, 5,5,5,8,5,5,5,8,5,5,5,8,5,5,5,100]

