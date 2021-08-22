



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