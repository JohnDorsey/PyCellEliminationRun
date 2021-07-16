"""

FibonacciMath.py by John Dorsey.

FibonacciMath.py contains tools for generating different orders of Fibonacci sequences.

"""

from PyGenTools import makeArr, arrTakeOnly



#fibNums = [0,1,1,2,3,5,8,13,21,34,55]

"""
def expandFibNums():
  for i in range(256):
    fibNums.append(fibNums[-1]+fibNums[-2])

expandFibNums()
"""

#tribNums = [0, 0, 1, 1, 2, 4, 7, 13, 24, 44, 81, 149, 274, 504, 927, 1705, 3136, 5768, 10609, 19513, 35890, 66012]



def unwrapArr(inputArr,startIndex):
  assert startIndex < len(inputArr)
  assert startIndex >= 0
  return inputArr[startIndex:] + inputArr[:startIndex]

def offsetEnum(inputGen,offset):
  for i,item in enumerate(inputGen):
    yield (i+offset,item)




def getEnbonacciStartArr(order=2):
  assert order > 1
  return [0 for i in range(order-1)] + [1]

  

def genEnbonacciNums(order=2):
  assert order > 1
  startArr = getEnbonacciStartArr(order=order)
  i = 0
  while i < len(startArr):
    yield startArr[i]
    i += 1
  workingArr = [item for item in startArr]
  while True:
    i %= order
    workingArr[i] = sum(workingArr)
    yield workingArr[i]
    i += 1
  assert False, "genEnbonacciNums should never stop."


def getEnboNumAtIndexAndPredecessors(n,order=2):
  assert n > 0
  assert order > 1
  startArr = getEnbonacciStartArr(order=order)
  if n < len(startArr):
    result = rjustArr(startArr[:n+1],order,crop=True)
    return result
  workingArr = [item for item in startArr]
  i = order-1
  while i < n:
    i += 1
    ii = i%order
    workingArr[ii] = sum(workingArr)
  assert i == n
  return makeArr(offsetEnum(unwrapArr(workingArr,i%order),i))


def getEnboNumAboveValueAndPredecessors(value,order=2):
  assert order > 1
  startArr = getEnbonacciStartArr(order=order)
  index = len(startArr) - 1
  if value < startArr[index]:
    assert index - (order-1) >= 0
    while value < startArr[index-1]:
      index -= 1
    assert startArr[index-1] <= value
    assert startArr[index] > value
    #return ((index-1,fibNums[index-1]),(index,fibNums[index]))
    result = makeArr(enumerate(startArr)[:index+1])
    for i,item in enumerate(result):
      assert item[i][0] == i
    return result
  workingArr = [item for item in startArr]
  i = order-1
  #ii = None
  while True:
    i += 1
    ii = i%order
    workingArr[ii] = sum(workingArr)
    if not workingArr[ii] < value:
      break
  return makeArr(offsetEnum(unwrapArr(workingArr,(i+1)%order),i-(order-1)))


def genEnboNumsDescendingFromIndex(iEnd,order=2):
  assert order > 1
  workingArr = getEnboNumAtIndexAndPredecessors(iEnd,order=order)
  return genEnboNumsDescendingFromPreset(workingArr,iEnd,order=order)


def genEnboNumsDescendingFromPreset(presetArr,iEnd=None,order=2):
  assert order > 1
  #print("genEnboNumsDescendingFromPreset: on call: (presetArr,iEnd,order)=" + str((presetArr,iEnd,order)) + ".")
  isEnumerated = all(type(item) == tuple for item in presetArr)
  if isEnumerated and (iEnd != None):
    assert presetArr[-1][0] == iEnd
  else:
    iEnd = presetArr[-1][0]
  #print("genEnboNumsDescendingFromPreset: after adjustment: (presetArr,iEnd,order)=" + str((presetArr,iEnd,order)) + ".")
  workingArr = None
  if isEnumerated:
    workingArr = [item[1] for item in presetArr]
  else:
    workingArr = [item for item in presetArr] #make copy.
  yield (iEnd, workingArr[-1])
  #print("(workingArr,iEnd,order)="+str((workingArr,iEnd,order))+".")
  while iEnd >= order:
    workingArr.insert(0,workingArr[-1]-sum(workingArr[:-1]))
    del workingArr[-1]
    iEnd -= 1
    #print("genEnboNumsDescendingFromPreset: yielding " + str((iEnd, workingArr[-1])) + ".")
    yield (iEnd, workingArr[-1])
    #print("in loop, (workingArr,iEnd,order)="+str((workingArr,iEnd,order))+".")
  assert workingArr[0] == 0
  assert iEnd == order - 1
  #for i,item in makeArr(enumerate(getEnbonacciStartArr(order=order)))[::-1]:
  #  yield (i,item)
  for i,item in makeArr(enumerate(workingArr))[::-1]:
    if i == iEnd or i == iEnd-1:
      continue
    #print("genEnboNumsDescendingFromPreset: yielding " + str((i, item)) + ".")
    yield (i,item)


def genEnboNumsDescendingFromValue(value,order=2):
  presetArr = getEnboNumAboveValueAndPredecessors(value,order=order)
  #print("getEnboNumsDescendingFromValue: (value,order,presetArr)=" + str((value,order,presetArr))+".")
  return genEnboNumsDescendingFromPreset(presetArr,iEnd=None,order=order)





"""
11 = 1
011 = 2
0011 = 3
1011 = 4 = 3 + 1
00011 = 5
10011 = 6 = 5 + 1
01011 = 7 = 5 + 2
000011 = 8
100011 = 9 = 8 + 1
010011 = 10 = 8 + 2
001011 = 11 = 8 + 3
101011 = 12 = 8 + 3 + 1
0000011 = 13

111, = 1
0111, = 2
00111, = 3
10111, = 4 = 3 + 1
000111, = 5
100111, = 6 = 5 + 1
010111, = 7 = 5 + 2
110111, = 8 = 5 + 2 + 1
0000111, = 9
1000111, = 10 = 9 + 1
0100111, = 11 = 9 + 2
1100111 = ??? is this order correct?
0010111
1010111
0110111
00000111 = 16
10000111
01000111
11000111
00100111
10100111
01100111
00010111
10010111
01010111
11010111
00110111
10110111
000000111 = 29
100000111
010000111
110000111
001000111
101000111
011000111
000100111
100100111
010100111
110100111
001100111
101100111
000010111
100010111
010010111
110010111
001010111
101010111
011010111
000110111
100110111
010110111
110110111
(length, versions):
  (3, 1)
  (4, 1)
  (5, 2)
  (6, 4)
  (7, 7)
  these are the tribonacci numbers as expected.
(digit index from 1, apparent value at first appearance):
  (1, 1)
  (2, 2)
  (3, 3)
  (4, 5)
  (5, 9)
  (6, 16)
  This sequence is found by adding tribonacci numbers.
  Can each digit place really be given a fixed value?
"""




assert getEnbonacciStartArr(order=2) == [0,1]
assert getEnbonacciStartArr(order=3) == [0,0,1]


assert arrTakeOnly(genEnbonacciNums(order=2),8) == [0,1,1,2,3,5,8,13]
assert arrTakeOnly(genEnbonacciNums(order=3),8) == [0,0,1,1,2,4,7,13]









