


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

def basicSpiralCoordDecode(t):
  assert t >= 0
  if t == 0: #because spiralRingSideLength can't handle ring index 0.
    return (0,0) 
  ringIndex = 0
  tInRing = t
  while True:
    ringLen = spiralRingLength(ringIndex)
    if ringLen > tInRing:
      break
    tInRing -= ringLen
    ringIndex += 1
  sideInRing = 0
  tInSide = tInRing
  sideLen = spiralRingSideLength(ringIndex,1)
  while True:
    if sideLen > tInSide:
      break
    tInSide -= sideLen
    sideInRing += 1
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







for rotationDirection in [-1,1]:
  for startDirection in [0,1,2,3]:
    for startPosition in [(0,0),(20,100)]:
      assert [spiralCoordEncode(spiralCoordDecode(i,startPosition,startDirection,rotationDirection),startPosition,startDirection,rotationDirection) for i in range(50)] == [i for i in range(50)]

