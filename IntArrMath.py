
import IntSeqMath


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



