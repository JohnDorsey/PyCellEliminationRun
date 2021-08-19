"""

IntArrMath.py by John Dorsey.

IntArrMath.py contains tools for analyzing or manipulating arrays, and must either take or return an array. Functions that both take a generator and return a generator should be put in IntSeqMath.py.

"""


import IntSeqMath
import IntDomainMath
import Curves

from PyGenTools import makeArr, makeGen, zipGens

def intify(inputArr,roundNearest=False,weakly=False):
  """
  recursively forces every number to be an int.
  when roundNearest=True, numbers will be rounded to the nearest integer instead of being rounded down.
  when weak=True, numbers will only be converted if doing so does not change their value.
  """
  for i,item in enumerate(inputArr):
    if type(item) == list:
      intify(item,roundNearest=roundNearest,weakly=weakly)
    elif item != None:
      if weakly:
        if int(item) == item:
          inputArr[i] = int(item)
      else:
        inputArr[i] = int(round(item)) if roundNearest else int(item)

def intified(inputArr,roundNearest=False,weakly=False):
  result = [None for i in range(len(inputArr))]
  for i,item in enumerate(inputArr):
    if type(item) == list:
      result[i] = intified(item,roundNearest=roundNearest,weakly=weakly)
    elif item != None:
      result[i] = (int(item) if int(item) == item else item) if weakly else (int(round(item)) if roundNearest else int(item))
  return result


def is_sorted(inputArr):
  #test whether the input array is sorted.
  if len(inputArr) <= 1:
    return True
  for i in range(1,len(inputArr)):
    if inputArr[i] < inputArr[i-1]:
      return False
  return True


def mean(inputArr):
  #find the mean of the input array. Might mishandle long type items in python2.
  inputArr = makeArr(inputArr)
  if len(inputArr) == 0:
    raise ValueError("can't find the mean of an empty list.")
  inputArrSum = sum(inputArr)
  if type(inputArrSum)==int and inputArrSum%len(inputArr) == 0:
    return inputArrSum / len(inputArr)
  else:
    return float(inputArrSum)/len(inputArr)


def median(inputArr,middlePairHandlingFun=mean):
  #find the median of the input array. Uses middlePairHandlingFun as the function to process the middle pair in even-length inputArrs to get the result.
  inputArr = makeArr(inputArr)
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
      return middlePairHandlingFun(middlePair)
  assert False, "reality error."


def genRunless(inputSeq):
  #this generator takes an input sequence and yields only the items that aren't the same as the previous item.
  #this generator eats only as much as it yields.
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



def genInterlacedIndices(inputEndpoints,startWithEndpoints=True,midpointMode="fail"):
  #This didn't need to be a generator, and probably doesn't save much memory by being a generator.
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
    #print("IntArrMath.genInterlacedIndices: the endpoints " + str(inputEndpoints) + " are in the wrong order, and nothing will be yielded. This is not always an error.")
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
        assert False, "bad midpoint is not allowed when midpointMode=\"fail\""
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


def genReverseIndexMap(inputMap):
  workingMap = makeArr(inputMap) #so that calls to .index works even if the input is a generator.
  for i in range(len(workingMap)):
    yield workingMap.index(i)

def applyIndexMap(inputArr,inputMap):
  return [inputArr[index] for index in inputMap]

def applyIndexMapReversed(inputArr,inputMap):
  #simply using return applyIndexMap(inputArr,genReverseIndexMap(inputMap)) would be O(N^2).
  #the following version is O(N).
  result = [None for i in range(len(inputArr))]
  for i,inputIndex in enumerate(inputMap):
    result[inputIndex] = inputArr[i]
  return result


def rulerOPIntArrTranscode(inputIntArr,opMode,spline=None,interlacingProvider=None):
  #ruler interlacing is what I call the method of interlacing described in IntArrMath.genInterlacedIndices.
  #ruler interlacing is used to add values to the array in a helpful order (no clusters). Interpolation is used to guess what a new value will be. The _Focused_ integer functions in IntDomainMath are used to focus a new value around the prediction for it to make it easier to compress using a universal code.
  #the interpolationProvider should be something like Curves.Spline WITH INTEGER OUTPUTS, such as by enabling the rounding output filter for Curves.Spline.
  #the output could be made streamable.
  assert opMode in ["encode","decode"]
  if spline == None:
    spline = Curves.Spline(interpolationMode="linear&round",size=[len(inputIntArr),None])
  if interlacingProvider == None:
    interlacingProvider = genInterlacedIndices((0,len(inputIntArr)-1),midpointMode="round_down")
  result = []
  for i,index in enumerate(interlacingProvider):
    localFocus = spline[index]
    assert type(localFocus) == int, "IntArrMath.rulerOPIntArrTranscode: Only integer foci are supported. Make sure the provided spline gives only integer outputs."
    #print("(i,index,localFocus,inputIntArr[i]) is " + str((i,index,localFocus,inputIntArr[i])) + ".")
    if opMode == "encode":
      spline[index] = inputIntArr[index]
      result.append(IntDomainMath.unfocusedOP_to_focusedOP(spline[index],localFocus))
      #print("result is " + str(result) + ".")
    else:
      spline[index] = IntDomainMath.focusedOP_to_unfocusedOP(inputIntArr[i],localFocus)
      #print("spline is " + str([item for item in spline]) + ".")
  if opMode == "encode":
    return result
  else:
    return [spline[i] for i in range(len(inputIntArr))]






def headingDeltadPaletteIntArrEncode(inputIntArr):
  #store an integer array as a new array starting with a palette length, followed by a palette, followed by a finite sequence of palette indices.
  #the output could be made streamable, even though the input is not.
  values = [item for item in genRunless(sorted(inputIntArr))]
  result = []
  result.append(len(values))
  result.extend(IntSeqMath.genDeltaEncode(values))
  result.extend(values.index(item) for item in inputIntArr)
  return result

def headingDeltadPaletteIntArrDecode(inputIntArr):
  #both the output and the input could be made streamable.
  paletteLength = inputIntArr[0]
  palette = [item for item in IntSeqMath.genDeltaDecode(inputIntArr[1:1+paletteLength])]
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
  return [medianVal] + [IntDomainMath.NOP_to_OP(item-medianVal) for item in inputIntArr]

def headingMedianStaggerIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  medianVal = inputIntArr[0]
  return [IntDomainMath.OP_to_NOP(item)+medianVal for item in inputIntArr[1:]]


def headingMedianStaggerOPIntArrEncode(inputIntArr):
  #like headingMedianStaggerIntArrEncode, but takes advantage of an input array's limited value range [0,inf) to make the output consist of smaller values.
  medianVal = int(median(inputIntArr))
  return [medianVal] + [IntDomainMath.unfocusedOP_to_focusedOP(item,medianVal) for item in inputIntArr]

def headingMedianStaggerOPIntArrDecode(inputIntArr):
  #the input and output could both be made streamable.
  medianVal = inputIntArr[0]
  return [IntDomainMath.focusedOP_to_unfocusedOP(item,medianVal) for item in inputIntArr[1:]]






assert applyIndexMap("abcdefg",[0,5,6,3,2,1,4]) == [ 'a', 'f', 'g', 'd', 'c', 'b', 'e']
assert applyIndexMapReversed("afgdcbe",[0,5,6,3,2,1,4]) == ['a', 'b', 'c', 'd', 'e', 'f', 'g']

