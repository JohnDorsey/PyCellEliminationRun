


import IntSeqMath

import IntMath


"""
def is_sorted(inputArr):
  if len(inputArr) <= 1:
    return True
  for i in range(1,len(inputArr)):
    if inputArr[i] < inputArr[i-1]:
      return False
  return True
"""

def mean(inputArr):
  inputArrSum = sum(inputArr)
  if type(inputArrSum) in [int,long] and inputArrSum%len(inputArr) == 0:
    return inputArrSum / len(inputArr)
  else:
    return float(inputArrSum)/len(inputArr)

def median(inputArr,middlePairHandlingFun=mean):
  if len(inputArr) == 0:
    raise ValueError, "can't find the median of an empty list."
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
  floorVal = min(inputIntArr)
  return [floorVal] + [item-floorVal for item in inputIntArr]

def headingFloorIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  floorVal = inputIntArr[0]
  return [item+floorVal for item in inputIntArr[1:]]


def headingMedianIntArrEncode(inputIntArr):
  medianVal = int(median(inputIntArr))
  return [medianVal] + [item-medianVal for item in inputIntArr]

def headingMedianIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  medianVal = inputIntArr[0]
  return [item+medianVal for item in inputIntArr[1:]]


def headingMedianStaggerIntArrEncode(inputIntArr):
  medianVal = int(median(inputIntArr))
  return [medianVal] + [IntMath.NOP_to_OP(item-medianVal) for item in inputIntArr]

def headingMedianStaggerIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  medianVal = inputIntArr[0]
  return [IntMath.OP_to_NOP(item)+medianVal for item in inputIntArr[1:]]

