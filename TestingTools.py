
import IntArrMath


PEEK = 64


def logplog(logFile):
  def log(text, end="\n"):
    logFile.write(text + end)
    return "log passthrough: " + text
  def plog(text, end="\n"):
    print(text)
    log(text, end=end)
  return (log, plog)


def assertEqual(thing0, thing1):
  if not thing0 == thing1:
    if type(thing0) == list and type(thing1) == list:
      message = "The two lists are not equal: \n{}\n{}\n.".format(thing0,thing1)
      if len(thing0) == 0 or len(thing1) == 0:
        message += " One of them is empty."
      else:
        leftSimilarLength = 0
        while thing0[leftSimilarLength] == thing1[leftSimilarLength]:
          leftSimilarLength += 1
        rightSimilarLength = 0
        while thing0[-rightSimilarLength-1] == thing1[-rightSimilarLength-1]:
          rightSimilarLength += 1
        message += " They share {} left end items and {} right end items.".format(leftSimilarLength, rightSimilarLength)
    else:
      message = "{} is not equal to {}.".format(thing0,thing1)
    raise AssertionError(message)

def assertSame(thing0, thing1):
  if thing0 is not thing1:
    message = "{} is not {}.".format(repr(thing0), repr(thing1))
    raise AssertionError(message)



def measureIntArray(inputIntArr):
  rectBitSize = (len(inputIntArr),len(bin(max(inputIntArr))[2:]))
  return {"len":rectBitSize[0],"bit_depth":rectBitSize[1],"bit_area":rectBitSize[0]*rectBitSize[1]}

def printComparison(plainData,pressData):
  plainDataMeasures, pressDataMeasures = (measureIntArray(plainData), measureIntArray(pressData))
  estimatedCR = float(plainDataMeasures["bit_area"])/float(pressDataMeasures["bit_area"])
  estimatedSaving = 1.0 - 1.0/estimatedCR
  print("CT.printComp: plain meas: " + str(plainDataMeasures) + ". press meas: " + str(pressDataMeasures) + ". Est CR: " + str(estimatedCR)[:8] + ". Est SR: " + str(estimatedSaving*100.0)[:8] + "%.")

def countTrailingMatches(inputArr, matchFun):
  i = 0
  while matchFun(inputArr[-1-i]):
    i += 1
  return i
  
def countTrailingZeroes(inputArr):
  return countTrailingMatches(inputArr, (lambda x: x==0))
  
  
  
  
def printSimpleIntArrAnalysis(pressDataNums, argName="inputIntSeq", verbose=True):
  resultText = ""
  
  resultText += "TestingTools.printSimpleIntArrAnalysis: The sum of {} is {}. This includes {} zeroes, of which {} are trailing.".format(argName, sum(pressDataNums), pressDataNums.count(0), countTrailingZeroes(pressDataNums))
  
  #resultText += "The last " + str(TestingTools.countTrailingMatches(pressDataNums, (lambda x: x in [0,1]))) + " nums fall in 0..1. The last " + str(TestingTools.countTrailingMatches(pressDataNums, (lambda x: x in [0,1,2]))) + " nums fall in 0..2."
  includePercentage = lambda inputInt: (inputInt, str(inputInt*100.0/len(pressDataNums))[:6] + "%")
  tailShapeSummary = [(testUpperBound, includePercentage(countTrailingMatches(pressDataNums, (lambda x: x <= testUpperBound)))) for testUpperBound in [1,2,4,8,16,32,64,128,256,512,1024]]
  resultText += " Where f(a) gives greatest b such that max({}[-b:]) <= a, the start of f(a) looks like {}.".format(argName, tailShapeSummary)
  
  resultText += " The median of the nonzero numbers is " + str(IntArrMath.median([item for item in pressDataNums if item != 0])) + " and the maximum is " + str(max(pressDataNums)) + " at index " + str(pressDataNums.index(max(pressDataNums))) + "."
  
  if verbose:
    resultText += " {} is {}.".format(argName, pressDataNums)
  else:
    resultText += " The start of {} looks like {}...".format(argName, str(pressDataNums[:PEEK])[:PEEK])
    
  print(resultText)
  
  
  
  
  
  
  
  
