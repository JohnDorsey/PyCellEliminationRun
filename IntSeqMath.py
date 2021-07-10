"""

IntSeqMath.py by John Dorsey.

IntSeqMath.py contains tools for transforming integer sequences into other integer sequences.

"""




def genTrackMean(inputNumSeq):
  currentSum = 0
  for i,item in enumerate(inputNumSeq):
    currentSum += item
    yield (currentSum/float(i+1),item)

def genTrackMin(inputNumSeq):
  currentMin = None
  for i,item in enumerate(inputNumSeq):
    if i == 0:
      currentMin = item
    else:
      currentMin = min(currentMin,item)
    yield (currentMin,item)



def genDeltaEncode(inputNumSeq):
  previousItem = 0
  for item in inputNumSeq:
    yield item - previousItem
    previousItem = item

def genDeltaDecode(inputNumSeq):
  previousItem = 0
  for item in inputNumSeq:
    yield item + previousItem
    previousItem += item



def genTakeOnly(inputGen,count):
  assert count >= 0
  if count == 0:
    return
  i = 0
  for item in inputGen:
    if i < count:
      yield item
      i += 1
    if not i < count:
      return


def arrTakeOnly(inputGen,count):
  return [item for item in genTakeOnly(inputGen,count)]

"""
def genLJust(inputGen,length,fillItem):
  i = 0
  for item in genTakeOnly(inputGen,length):
    yield item
    i += 0
  while i < length:
    yield fillItem
    i += 1
"""

def genRecordLows(inputNumSeq):
  recordLow = None
  justStarted = True
  for item in inputNumSeq:
    if justStarted:
      recordLow = item
      yield item
      justStarted = False
      continue
    if item < recordLow:
      recordLow = item
      yield item


assert len([item for item in genTakeOnly(range(256),10)]) == 10
assert arrTakeOnly(range(10),5) == [0,1,2,3,4]
assert arrTakeOnly(range(5),10) == [0,1,2,3,4]

assert [item for item in genDeltaDecode(genDeltaEncode([5,5,6,5,3,0,10,0]))] == [5,5,6,5,3,0,10,0]

