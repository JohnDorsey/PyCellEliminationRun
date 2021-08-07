
from PyGenTools import makeGen, arrTakeOnly
from PyArrTools import insort
import collections
import itertools



def coordRotatedCCW(coord):
  return (-coord[1],coord[0])

def coordRotatedCW(coord):
  return (coord[1],-coord[0])

def coordSum(coords):
  result = (0,0)
  for coord in coords:
    result = (result[0] + coord[0], result[1] + coord[1])
  return result

def scaledCoord(coord,scalar):
  return (coord[0]*scalar,coord[1]*scalar)

def directionIndexToVector(index):
  return [(0,1),(1,0),(0,-1),(-1,0)][index]

def coordsAreNeighbors(coord0,coord1):
  assert len(coord0) == len(coord1)
  return all((abs(coord0[i]-coord1[i]) <= 1) for i in range(len(coord0)))

def distance(coord0,coord1):
  assert len(coord0) == len(coord1)
  return float(sum((coord0[i]-coord1[i])**2 for i in range(len(coord0))))**0.5

def sign(x):
  return int(math.copysign(1,x))

def signs(coord):
  return tuple([sign(value) for value in coord])

def modularMinimumDistance(value0,value1,modulus):
  distances = [item for item in [value0 - value1, value1 - value0, value0 + modulus - value1, value1 + modulus - value0] if item >= 0]
  return min(distances)





def spiralCoordDecode(t, startXY, startDirection, rotationDirection):
  assert startDirection in [0,1,2,3] #N-E-S-W.
  assert rotationDirection in [1,-1] #1 is CW, -1 is CCW.
  basicResult = basicSpiralCoordDecode(t)
  result = (basicResult[0]*rotationDirection, basicResult[1])
  for i in range(startDirection):
    result = coordRotatedCW(result)
  result = coordSum([result, startXY])
  return result


def spiralCoordEncode(coord, startXY, startDirection, rotationDirection):
  spiralCoord = coordSum([coord,scaledCoord(startXY,-1)])
  for i in range(startDirection):
    spiralCoord = coordRotatedCCW(spiralCoord)
  spiralCoord = (spiralCoord[0]*rotationDirection, spiralCoord[1])
  return basicSpiralCoordEncode(spiralCoord)


def genBasicSpiralCoords(*args):
  #4 to 8 times faster for large spirals.
  startT = 0
  endT = None
  direction = 1
  eternal = True
  
  if len(args) == 1:
    endT = args[0]
    assert endT >= 0
    eternal = False
  if len(args) >= 2:
    startT, endT = args[0], args[1]
    assert startT >= 0
    assert endT >= 0
    if startT == endT:
      return
    eternal = False
  if len(args) >= 3:
    direction = args[2]
    assert direction in [1, -1]
  if len(args) > 3:
    raise ValueError("too many arguments.")
    
  if endT != None:
    if (endT-startT)*direction < 0:
      return

    
  t = startT
  if t == 0: #because spiralRingSideLength can't handle ring index 0.
    assert direction > 0
    yield (0,0)
    t += direction
    if t == endT:
      return
    
  print(startT,endT,direction,eternal)
  
  startRingIndex, tInStartRing = findSubdivisionAndInnerLocation(0, t, subdivisionSizeFun=spiralRingLength)
  startSideLen = spiralRingSideLength(startRingIndex, 1)
  sideInStartRing, tInStartSide = findSubdivisionAndInnerLocation(0, tInStartRing, subdivisionSize=startSideLen)
  """
  if eternal:
    endRingIndex, tInEndRing = None, None
    endSideInRing, tInEndSide = None, None
  else:
    endRingIndex, tInEndRing = findSubdivisionAndInnerLocation(0, endT, subdivisionSizeFun=spiralRingLength)
    if endRingIndex > 0:
      endSideLen = spiralRingSideLength(endRingIndex, 1)
      endSideInRing, tInEndSide = findSubdivisionAndInnerLocation(0, tInEndRing, subdivisionSize=endSideLen)"""
  
  #def printStatus():
  #  print("ringIndex",ringIndex
  for ringIndex in itertools.count(startRingIndex, direction): #iterate ringIndex
    print("ringIndex",ringIndex)
    if ringIndex == 0:
      yield (0,0)
      assert direction < 0
      return
    sideLen = spiralRingSideLength(ringIndex, 1)
    sideInRingSeq = (range(sideInStartRing,4,1) if direction==1 else range(sideInStartRing,-1,-1)) if (ringIndex == startRingIndex) else (range(0,4,1) if direction==1 else range(3,-1,-1))
    for sideInRing in sideInRingSeq: #iterate sideInRing
      tInSideSeq = (range(tInStartSide,sideLen,1) if direction==1 else range(tInStartSide,-1,-1)) if (ringIndex == startRingIndex and sideInRing == sideInStartRing) else (range(0,sideLen,1) if direction==1 else range(sideLen-1,-1,-1))
      print("sideInRing",sideInRing)
      sideDirection = directionIndexToVector((sideInRing+1)%4)
      sideStartCoord = spiralRingSideStartCoords(ringIndex)[sideInRing]
      for tInSide in tInSideSeq:
        print("tInSide",tInSide)
        if not eternal:
          if (endT-t)*direction <= 0:
            assert t == endT, "skip!"
            #assert ringIndex == endRingIndex, "skip!"
            #assert sideInRing == endSideInRing, "skip!"
            #assert tInSide == tInEndSide, "skip!"
            print("normal spiral end. t={}.".format(t))
            return
        result = coordSum([sideStartCoord,scaledCoord(sideDirection,tInSide)])
        yield result
        t += direction

def basicSpiralCoordDecode(t):
  assert t >= 0
  if t == 0: #because spiralRingSideLength can't handle ring index 0.
    return (0,0) 
  
  ringIndex, tInRing = findSubdivisionAndInnerLocation(0, t, subdivisionSizeFun=spiralRingLength)
  
  sideLen = spiralRingSideLength(ringIndex, 1)
  sideInRing, tInSide = findSubdivisionAndInnerLocation(0, tInRing, subdivisionSize=sideLen)

  sideDirection = directionIndexToVector((sideInRing+1)%4)
  sideStartCoord = spiralRingSideStartCoords(ringIndex)[sideInRing]
  result = coordSum([sideStartCoord,scaledCoord(sideDirection,tInSide)])
  return result


def basicSpiralCoordEncode(coord):
  ringIndex = max(abs(value) for value in coord)
  if ringIndex == 0:
    return 0
  if ringIndex == 1: #because the side index finding loop can't handle ring 1.
    return {(0,1):1,(1,1):2,(1,0):3,(1,-1):4,(0,-1):5,(-1,-1):6,(-1,0):7,(-1,1):8}[coord]
  ringSideStartCoords = spiralRingSideStartCoords(ringIndex)
  ringSideMatchableCoords = spiralRingSideMatchableCoords(ringIndex)
  sideInRing = None
  sideMatches = []
  for sideIndex,testCoord in enumerate(ringSideMatchableCoords):
    if (coord[0] == testCoord[0] or coord[1] == testCoord[1]):
      sideMatches.append(sideIndex)
  if len(sideMatches) == 1:
    sideInRing = sideMatches[0]
  else:
    assert len(sideMatches) == 2
    offset = modularMinimumDistance(sideMatches[0],sideMatches[1],4)
    assert offset == 1
    if sideMatches == [0,3]:
      sideInRing = 3
    else:
      assert sideMatches in [[0,1],[1,2],[2,3]]
      sideInRing = min(sideMatches)
  assert sideInRing != None
  sideStartCoord = ringSideStartCoords[sideInRing]
  tPassedRings = spiralRingInnerArea(ringIndex)
  tPassedSides = (sideInRing*spiralRingSideLength(ringIndex,1))
  tWithinSide = int(round(distance(coord,sideStartCoord)))
  #print("(ringIndex,sideInRing,tPassedRings,tPassedSides,tWithinSide)="+str((ringIndex,sideInRing,tPassedRings,tPassedSides,tWithinSide))+".")
  t = tPassedRings + tPassedSides + tWithinSide
  return t
  
  
def findSubdivisionAndInnerLocation(startingSubdivisionIndex, absoluteLocation, subdivisionSize=None, subdivisionSizeFun=None): #this can be modified to work in higher dimensions.
  assert not (subdivisionSize == None and subdivisionSizeFun == None)
  if subdivisionSizeFun == None:
    subdivisionSizeFun = (lambda ignore: subdivisionSize)
    
  currentSubdivisionIndex = startingSubdivisionIndex
  relativeLocation = absoluteLocation
  while True:
    currentSubdivisionSize = subdivisionSizeFun(currentSubdivisionIndex)
    if currentSubdivisionSize > relativeLocation:
      break
    relativeLocation -= currentSubdivisionSize
    currentSubdivisionIndex += 1
  return currentSubdivisionIndex, relativeLocation
  
  
def spiralRingSideLength(ringIndex,includedCorners):
  assert includedCorners in [0,1,2]
  assert ringIndex > 0
  return ((2*ringIndex)-1)+includedCorners

def spiralRingLength(ringIndex):
  assert ringIndex >= 0
  if ringIndex == 0:
    return 1
  return 4 * spiralRingSideLength(ringIndex,1)

def spiralRingArea(ringIndex):
  if ringIndex == 0:
    return 1
  if ringIndex == 1:
    return 9
  return spiralRingSideLength(ringIndex,2)**2

def spiralRingInnerArea(ringIndex):
  #return sum(spiralRingLength(i) for i in range(ringIndex))
  if ringIndex == 0:
    return 0
  return spiralRingArea(ringIndex-1)

def spiralRingSideStartCoords(ringIndex):
  assert ringIndex > 0
  if ringIndex == 1:
    return [(0,1),(1,0),(0,-1),(-1,0)]
  return [(0-(ringIndex-1),ringIndex),(ringIndex,ringIndex-1),(ringIndex-1,-ringIndex),(-ringIndex,0-(ringIndex-1))]

def spiralRingSideMatchableCoords(ringIndex):
  assert ringIndex > 0
  if ringIndex == 1:
    return [(None,1),(1,None),(None,-1),(-1,None)]
  return [(None,ringIndex),(ringIndex,None),(None,-ringIndex),(-ringIndex,None)]



def genDezigged(inputSeq,forbidLocalMinimaDecrease=True,forbidLocalMaximaDecrease=True,keyFun=None):
  if keyFun == None:
    keyFun = (lambda x: x)
  inputGen = makeGen(inputSeq)
  
  rememberedLocalMinima = collections.deque()
  rememberedLocalMaxima = collections.deque()
  history = []
  currentTriplet = collections.deque()
  
  sortKeyFun = (lambda itemA: itemA[0])
  
  getStatus = (lambda: "status:(history={}, rlmn={}, rlmx={}, triplet={}, canOutputNow()={})".format(history, rememberedLocalMinima, rememberedLocalMaxima, currentTriplet, canOutputNow()))
  
  if forbidLocalMinimaDecrease and forbidLocalMaximaDecrease:
    def localExtremaAllowOutputNow():
      testResult = sortKeyFun(rememberedLocalMinima[-1]) > sortKeyFun(rememberedLocalMaxima[0])
      #maybe they could be popped now?
      return testResult
  else:
    def localExtremaAllowOutputNow():
      return sortKeyFun(max(rememberedLocalMinima, key=sortKeyFun)) > sortKeyFun(min(rememberedLocalMaxima, key=sortKeyFun))
  
  def canOutputNow():
    if len(history) == 0:
      return False
    if len(rememberedLocalMinima) == 0 or len(rememberedLocalMaxima) == 0:
      return False
    return localExtremaAllowOutputNow()
    
  def detectLocalExtrema(suspendRules=False):
    assert len(currentTriplet) in [2,3]
    if sortKeyFun(min(currentTriplet ,key=sortKeyFun)) == sortKeyFun(currentTriplet[1]):
      if forbidLocalMinimaDecrease and not suspendRules:
        if len(rememberedLocalMinima) > 0:
          if not sortKeyFun(rememberedLocalMinima[-1]) <= sortKeyFun(currentTriplet[1]):
            raise ValueError("forbidLocalMinimaDecrease violated by inputSeq!")
      #print("SpiralMath.genDezigged.detectLocalExtrema: detected local minimum {}. before registering, {}.".format(currentTriplet[1],getStatus()))
      rememberedLocalMinima.append(currentTriplet[1])
      print("SpiralMath.genDezigged.detectLocalExtrema: detected local minimum {}. after registering, {}.\n".format(currentTriplet[1],getStatus()))
    if sortKeyFun(max(currentTriplet, key=sortKeyFun)) == sortKeyFun(currentTriplet[1]):
      if forbidLocalMaximaDecrease and not suspendRules:
        if len(rememberedLocalMaxima) > 0:
          if not sortKeyFun(rememberedLocalMaxima[-1]) <= sortKeyFun(currentTriplet[1]):
            raise ValueError("forbidLocalMaximaDecrease violated by inputSeq!")
      #print("SpiralMath.genDezigged.detectLocalExtrema: detected local maximum {}. before registering, {}.".format(currentTriplet[1],getStatus()))
      rememberedLocalMaxima.append(currentTriplet[1])
      print("SpiralMath.genDezigged.detectLocalExtrema: detected local maximum {}. after registering, {}.\n".format(currentTriplet[1],getStatus()))
    
  currentTripletFilledBefore = False
  inputItemsExhausted = False
    
  while True:
    assert len(currentTriplet) <= 3
    if len(currentTriplet) == 3:
      currentTripletFilledBefore = True
      
    if canOutputNow():
      print("SpiralMath.genDezigged: normal out: {}, yielding {}.\n".format(getStatus(), history[0][1]))
      yield history[0][1]
      if forbidLocalMinimaDecrease:
        if history[0] == rememberedLocalMinima[0]:
          rememberedLocalMinima.popleft()
      else:
        raise NotImplementedError("There is currently no way to remove items from rememberedLocalMaxima when they are not sorted. Try forbidding decreases in them.")
      if forbidLocalMaximaDecrease:
        if history[0] == rememberedLocalMaxima[0]:
          rememberedLocalMaxima.popleft()
      else:
        raise NotImplementedError("There is currently no way to remove items from rememberedLocalMaxima when they are not sorted. Try forbidding decreases in them.")
      del history[0] #@ slow!
      continue
      
    try:
      nextValue = next(inputGen)
      nextKey = keyFun(nextValue)
      nextItem = (nextKey, nextValue)
      print("SpiralMath.genDezigged: notice: {}, ingesting {}.".format(getStatus(), nextItem))
      assert len(currentTriplet) <= 3
      currentTriplet.append(nextItem)
      insort(history, nextItem, stable=True, keyFun=sortKeyFun)
      print("SpiralMath.genDezigged: notice: {}, ingested {}.\n".format(getStatus(), nextItem))
      #assert len(currentTriplet) <= 4
      #if len(currentTriplet) == 4:
      #  currentTriplet.popleft()
      #assert len(currentTriplet) <= 3
    except StopIteration:
      inputItemsExhausted = True
      
    if currentTripletFilledBefore:
      currentTriplet.popleft() #to make up for not doing it earlier in the try block above.
      assert len(currentTriplet) <= 3
    
      if len(currentTriplet) == 3:
        detectLocalExtrema()
        continue
      elif len(currentTriplet) == 2:
        assert inputItemsExhausted, "if not, then why is currentTriplet less than full?"
        detectLocalExtrema(suspendRules=True)
        continue
      elif len(currentTriplet) == 1:
        pass #allow endgame.
      elif len(currentTriplet) == 0:
        raise ValueError()
      else:
        assert False
    else:
      continue #don't reach the endgame before the right time.
        
    assert len(currentTriplet) == 1
    assert inputItemsExhausted
        
    for endgameItem in sorted(history):
      
      print("SpiralMath.genDezigged: endgame out: {}, yielding {}.\n".format(getStatus(), history[0][1]))
      yield endgameItem[1]
    return

  assert False, "unreachable statement."
          


for rotationDirection in [-1,1]:
  for startDirection in [0,1,2,3]:
    for startPosition in [(0,0),(20,100)]:
      assert [spiralCoordEncode(spiralCoordDecode(i,startPosition,startDirection,rotationDirection),startPosition,startDirection,rotationDirection) for i in range(50)] == [i for i in range(50)]

assert [basicSpiralCoordDecode(t) for t in range(16)] == [(0, 0), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (-1, 2), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (2, -1)]

