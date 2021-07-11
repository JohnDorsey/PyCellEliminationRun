"""

IntArrMath.py by John Dorsey.

IntArrMath.py contains tools for analyzing or manipulating arrays, and must either take or return an array. Functions that both take a generator and return a generator should be put in IntSeqMath.py.

"""


import IntSeqMath

import IntMath

from PyGenTools import makeGen, zipGens


def is_sorted(inputArr):
  if len(inputArr) <= 1:
    return True
  for i in range(1,len(inputArr)):
    if inputArr[i] < inputArr[i-1]:
      return False
  return True


def mean(inputArr):
  inputArrSum = sum(inputArr)
  if type(inputArrSum) in [int,long] and inputArrSum%len(inputArr) == 0:
    return inputArrSum / len(inputArr)
  else:
    return float(inputArrSum)/len(inputArr)

def median(inputArr,middlePairHandlingFun=mean):
  if len(inputArr) == 0:
    raise ValueError("can't find the median of an empty list.")
  elif len(inputArr) == 1:
    return inputArr[0]
  elif len(inputArr) >= 2:
    #this might be faster without unecessary sorting.
    workingArr = sorted(inputArr)
    if len(workingArr)%2 == 1:
      return workingArr[len(workingArr)>>1]
    else:
      middlePair = workingArr[(len(workingArr)>>1)-1:(len(workingArr)>>1)+1]
      """if middlePairHandling == "mean":
        middlePairSum = sum(middlePair)
        if type(middlePairSum) == int and middlePairSum%2==0:
          return middlePairSum/2
        else:
          return middlePairSum/2.0
      elif middlePairHandling == "min"
      """
      return middlePairHandlingFun(middlePair)
  assert False, "reality error."


def genRunless(inputSeq):
  previousItem = None
  justStarted = True
  for item in inputSeq:
    if justStarted:
      justStarted = False
      previousItem = item
      yield item
    else:
      if item != previousItem:
        previousItem = item
        yield item



def genInterlacedIndices(inputEndpoints,startWithEndpoints=True,midpointMode="round_down"):
  #works like this:
  #1       2
  #|   3   |
  #| 4 | 5 |
  #|6|8|7|9|
  #|||||||||
  #at the index n in the output, the horizontal position of the vertical line labled with the number n is given. This horizontal position counts up from the first endpoint to the second one, including both if includeEndpoints==True and neither otherwise.
  #print("endpoints are " + str(inputEndpoints) + ".")
  assert midpointMode in ["fail","round_down","round_up","unsubdivided"], "bad midpointMode."
  if not inputEndpoints[0] <= inputEndpoints[1]:
    print("the endpoints " + str(inputEndpoints) + " are in the wrong order, and nothing will be yielded.")
    return

  domainSize = inputEndpoints[1]-inputEndpoints[0]+1

  if domainSize == 1:
    yield inputEndpoints[0]
  elif startWithEndpoints:
    yield inputEndpoints[0]
    yield inputEndpoints[1]
    if domainSize > 2:
      for item in genInterlacedIndices((inputEndpoints[0]+1,inputEndpoints[1]-1),startWithEndpoints=False,midpointMode=midpointMode):
        yield item
  else:
    perfectMidpoint = ((domainSize-1)%2 == 0)
    if not perfectMidpoint:
      if midpointMode == "fail":
        assert False, "bad midpoint."
      elif midpointMode == "unsubdivided":
        for i in range(inputEndpoints[0],inputEndpoints[1]+1):
          yield i
        return
    midpoint = int((domainSize-1)/2 + inputEndpoints[0])
    if midpointMode == "round_up" and not perfectMidpoint:
      midpoint += 1
    yield midpoint
    for item in zipGens([genInterlacedIndices((inputEndpoints[0],midpoint-1),startWithEndpoints=False,midpointMode=midpointMode),genInterlacedIndices((midpoint+1,inputEndpoints[1]),startWithEndpoints=False,midpointMode=midpointMode)]):
      yield item

"""
this math won't actually be needed.
a palettized int array arrdown has a palette of length a, a body of length b, and a length c
a + b = c
for all n in arrdown[-b:], n < a.
for all n in 0..a, n is in arrdown[-b:]
for i in 0..c:
  if max(arrdown[i:]) > i:
    note that a != i
  if arrdown[i] > c-1:
    note that a > i
  if not all in 0..i are in also in arrdown[i:]:
    note that a < i
"""

def headingDeltadPaletteIntArrEncode(inputIntArr):
  #store an integer array as a new array starting with a palette length, followed by a palette, followed by a finite sequence of palette indices.
  #the output could be made streamable, even though the input is not.
  values = [item for item in genRunless(sorted(inputIntArr))]
  result = []
  result.append(len(values))
  result.extend(IntSeqMath.genEncodeDelta(values))
  result.extend(values.index(item) for item in inputIntArr)
  return result

def headingDeltadPaletteIntArrDecode(inputIntArr):
  #both the output and the input could be made streamable.
  paletteLength = inputIntArr[0]
  palette = [item for item in IntSeqMath.genDecodeDelta(inputIntArr[1:1+paletteLength])]
  return [palette[item] for item in inputIntArr[1+paletteLength:]]


def headingFloorIntArrEncode(inputIntArr):
  #store an input integer array as a new array starting with a floor value, followed by each of the array's items minus that floor value.
  floorVal = min(inputIntArr)
  return [floorVal] + [item-floorVal for item in inputIntArr]

def headingFloorIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  floorVal = inputIntArr[0]
  return [item+floorVal for item in inputIntArr[1:]]


def headingMedianIntArrEncode(inputIntArr):
  #store an input integer array as a new array starting with its median, followed by each of the input array's items minus that median.
  medianVal = int(median(inputIntArr))
  return [medianVal] + [item-medianVal for item in inputIntArr]

def headingMedianIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  medianVal = inputIntArr[0]
  return [item+medianVal for item in inputIntArr[1:]]


def headingMedianStaggerIntArrEncode(inputIntArr):
  #like headingMedianIntArrEncode, but use staggering around the number line origin to format the output as an all-positive integer array.
  medianVal = int(median(inputIntArr))
  return [medianVal] + [IntMath.NOP_to_OP(item-medianVal) for item in inputIntArr]

def headingMedianStaggerIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  medianVal = inputIntArr[0]
  return [IntMath.OP_to_NOP(item)+medianVal for item in inputIntArr[1:]]


def headingMedianStaggerOPIntArrEncode(inputIntArr):
  #like headingMedianStaggerIntArrEncode, but takes advantage of an input array's limited value range [0,inf) to make the output consist of smaller values.
  medianVal = int(median(inputIntArr))
  return [medianVal] + [IntMath.unfocusedOP_to_focusedOP(item,medianVal) for item in inputIntArr]

def headingMedianStaggerOPIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  medianVal = inputIntArr[0]
  return [IntMath.focusedOP_to_unfocusedOP(item,medianVal) for item in inputIntArr[1:]]


