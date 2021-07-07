"""

Curves.py by John Dorsey.

Curves.py contains tools like the Spline class for creating curves and doing calculations related to them. The Spline class is mainly used by the Cell Elimination Run codec in PyCellElimRun.py for predicting missing samples of audio.

"""

DODBGPRINT = False #print debug info.
DOVIS = False #show pretty printing, mostly for debugging.

def dbgPrint(text,end="\n"): #only print if DODBGPRINT.
  if DODBGPRINT:
    print(text)
    print("custom line endings disabled for python2 compatibility.")





class Spline:
  #the Spline is what holds sparse or complete records of all the samples of a wave, and uses whichever interpolation mode was chosen upon its creation to provide guesses about the values of missing samples. It is what will inform decisions about how likely a cell (combination of a sample location and sample value) is to be filled/true. 

  ENDPOINTS_AT_ZERO = False
  CACHE_BONE_DISTANCE_ABS = True

  def __init__(self, interpolationMode="finite difference cubic hermite", size=None, endpoints=None, outputFilters=[]):
    self.endpoints = endpoints
    assert self.endpoints == None, "avoid using preset endpoints for this stage of testing."
    self.setInterpolationMode(interpolationMode,outputFilters=outputFilters)
    self.size = size
    assert not (self.size == None and self.endpoints == None)
    if self.size == None:
      self.size = [self.endpoints[1][0] - self.endpoints[0][0] + 1,None]
      dbgPrint("Curves.Spline.__init__: self.size is incomplete.")
    elif self.endpoints == None:
      if Spline.ENDPOINTS_AT_ZERO:
        self.endpoints = ((0,0),(self.size[0]-1,0))
      else:
        self.endpoints = ((0,self.size[1]>>1),(self.size[0]-1,self.size[1]>>1))
    else:
      assert False, "impossible error."
    assert len(self.endpoints) == 2
    assert self.endpoints[0][0] == 0, "sample ranges not starting at zero are not yet supported."
    assert self.endpoints[1][0] == size[0]-1, "sample ranges not ending at their second endpoint are not supported."
    self.data = [None for i in range(self.endpoints[1][0]+1)]
    self.boneDistanceAbs = None
    if Spline.CACHE_BONE_DISTANCE_ABS:
      self.boneDistanceAbs = [None for i in range(len(self.data))]
    #self.data[0],self.data[-1] = (self.endpoints[0][1],self.endpoints[1][1]) #old way of setting data endpoints without cache awareness.
    self.__setitem__(0,self.endpoints[0][1])
    self.__setitem__(-1,self.endpoints[1][1])
    assert len(self.data) == self.size[0]

  def setInterpolationMode(self,interpolationMode,outputFilters=[]):
    self.interpolationMode = interpolationMode.split("&")[0]
    self.outputFilters = outputFilters
    if "&" in interpolationMode:
      self.outputFilters.extend(interpolationMode.split("&")[1].split(";")) #@ this is not ideal but it saves complexity in testing. It lets every configuration I want to test be described by a single string.
    assert self.interpolationMode in ["hold","nearest-neighbor","linear","sinusoidal","finite difference cubic hermite","fourier"], "this interpolation mode is not supported."
    assert self.interpolationMode in ["hold","nearest-neighbor","linear","sinusoidal","finite difference cubic hermite"], "this interpolation mode is not supported, but support is planned."
    for outputFilter in self.outputFilters:
      assert outputFilter in ["clip","monotonic"], "that output filter is not supported."

  #these functions are used in constructing cubic hermite splines.
  def hermite_h00(self,t):
    return 2*t**3 - 3*t**2 + 1
  def hermite_h10(self,t):
    return t**3 - 2*t**2 + t
  def hermite_h01(self,t):
    return -2*t**3 + 3*t**2
  def hermite_h11(self,t):
    return t**3-t**2


  def prettyPrint(self):
    if not DOVIS:
      return
    dbgPrint("Spline.prettyPrint():")
    assert self.endpoints[0][0] == 0
    tempValues = [self.__getitem__(index) for index in range(self.endpoints[1][0]+1)]
    valueRange = (min(tempValues),max(tempValues))
    for value in range(valueRange[1],valueRange[0]-1,-1):
      #print(str(value).rjust(10)+": ",end="")
      print("Curves.Spline.prettyPrint: prettyPrinting disabled for python2 compatibility.")
      for index in range(self.endpoints[1][0]+1):
        #print("#" if (tempValues[index] == value) else "-",end="")
        pass
      print("")


  def getPointInDirection(self,location,direction,skipStart=True):
    dbgPrint("Curves.Spline.getPointInDirection: "+str((location,direction,skipStart)))
    #assert type(direction) == int
    assert direction in [-1,1]
    #assert 0 <= location < len(self.data)
    #print(direction)
    if Spline.CACHE_BONE_DISTANCE_ABS:
      location += skipStart*direction
      while 0 <= location < len(self.data):
        if self.data[location] != None:
          return (location,self.data[location])
        location += direction * self.boneDistanceAbs[location]
      return None
    else:
      location += skipStart*direction
      if not 0 <= location < len(self.data):
        return None
      for i in range(len(self.data)*2):
        if self.data[location] != None:
          return (location,self.data[location])
        location += direction
        if location < 0 or location >= len(self.data):
          return None
    assert False


  def forceMonotonicSlopes(self,sur,slopes): #completely untested.
    #sur stands for surroundings.
    surRises = [sur[i+1][1] - sur[i][1] for i in range(len(sur)-1)] #changes in y between each pair of points.
    surMonotonicSlope = -1 if all(((item <= 0) for item in surRises)) else 1 if all(((item >= 0) for item in surRises)) else 0 #the sign of every surRise if those are all the same sign, else 0.
    if surMonotonicSlope == 1:
      for i in range(len(slopes)):
        slopes[i] = max(0,slopes[i])
    elif surMonotonicSlope == -1:
      for i in range(len(slopes)):
        slopes[i] = min(0,slopes[i])


  def __getitem__(self,index):
    #not integer-based yet. Also, some methods can't easily be integer-based.
    #Also, this is one of the biggest wastes of time, particularly because nothing is cached and slow linear time searches of a mostly empty array are used.
    if self.data[index] != None: #no interpolation is ever done when the index in question has a known value.
      return self.data[index]
    elif self.interpolationMode == "hold":
      result = self.getPointInDirection(index,-1)
      if result != None:
        return result[1]
      result = self.getPointInDirection(index,1)
      assert result != None, "zero known points is not enough to work with."
      return result[1]
    elif self.interpolationMode == "nearest-neighbor":
      #when two neighbors are equal distances away, the one on the left will be chosen.
      leftItemIndex,rightItemIndex = (index, index) #@ these don't really need to be separate variables.
      while True:
        leftItemIndex -= 1
        rightItemIndex += 1
        if leftItemIndex < 0:
          break
        if rightItemIndex >= len(self.data):
          break
        if self.data[leftItemIndex] != None:
          return self.data[leftItemIndex]
        if self.data[rightItemIndex] != None:
          return self.data[rightItemIndex]
      assert False, "this interpolation mode can't run with missing endpoints or a bad location." #saved some time by not handling this, even though it would be simple to handle.
    elif self.interpolationMode in ["linear","sinusoidal"]:
      
      #turning on this slow code slowed a round-trip test from 5.45 seconds to 7.77 seconds. But caching was disabled.
      """
      leftBone,rightBone = (self.getPointInDirection(index,-1), self.getPointInDirection(index,1)) 
      progression = float(index-leftBone[0])/float(rightBone[0]-leftBone[0])
      if self.interpolationMode == "linear":
        return leftBone[1]+((rightBone[1]-leftBone[1])*progression)
      elif self.interpolationMode == "sinusoidal":
        return leftBone[1]+((rightBone[1]-leftBone[1])*0.5*(1-math.cos(math.pi*progression)))
      """
      
      leftItemIndex,rightItemIndex = (index-1,index+1) #@ the following search procedure could be moved to another method.
      if Spline.CACHE_BONE_DISTANCE_ABS: #this cache and this search method dropped linear mode compression time from 5.3 to 4.9 seconds for 1024 samples, and from 28.8 to 26 seconds for 2048 samples.
        while self.data[leftItemIndex] == None:
          leftItemIndex -= self.boneDistanceAbs[leftItemIndex]
        while self.data[rightItemIndex] == None:
          rightItemIndex += self.boneDistanceAbs[rightItemIndex]
      else:
        while self.data[leftItemIndex] == None:
          leftItemIndex -= 1
        while self.data[rightItemIndex] == None:
          rightItemIndex += 1
      progression = float(index-leftItemIndex)/float(rightItemIndex-leftItemIndex)
      if self.interpolationMode == "linear":
        return self.data[leftItemIndex]+((self.data[rightItemIndex]-self.data[leftItemIndex])*progression)
      elif self.interpolationMode == "sinusoidal":
        return self.data[leftItemIndex]+((self.data[rightItemIndex]-self.data[leftItemIndex])*0.5*(1-math.cos(math.pi*progression)))
      
    #interpolationModes after this point generally end without using return so that the end of the function with outputFilter code may apply.
    result = None

    if self.interpolationMode == "finite difference cubic hermite":
      sur = [None,self.getPointInDirection(index,-1),self.getPointInDirection(index,1),None]
      sur[0],sur[3] = (self.getPointInDirection(sur[1][0],-1),self.getPointInDirection(sur[2][0],1))
      if None in sur[1:3]:
        assert False, "an important (inner) item is missing from the surroundings."
      slopes = [None,None]
      if sur[0] == None:
        slopes[0] = float(sur[2][1]-sur[1][1])/float(sur[2][0]-sur[1][0])
      else:
        slopes[0] = 0.5*(float(sur[2][1]-sur[1][1])/float(sur[2][0]-sur[1][0])+float(sur[1][1]-sur[0][1])/float(sur[1][0]-sur[0][0]))
      if sur[3] == None:
        slopes[1] = (sur[2][1]-sur[1][1])/(sur[2][0]-sur[1][0])
      else:
        slopes[1] = 0.5*(float(sur[3][1]-sur[2][1])/float(sur[3][0]-sur[2][0])+float(sur[2][1]-sur[1][1])/float(sur[2][0]-sur[1][0]))
      #if self.interpolationMode == "monotonic finite distance cubic hermite":
      #  Spline.forceMonotonicSlopes(sur,slopes)
      t = float(index-sur[1][0])/float(sur[2][0]-sur[1][0])
      result = self.hermite_h00(t)*sur[1][1]+self.hermite_h10(t)*slopes[0]+self.hermite_h01(t)*sur[2][1]+self.hermite_h11(t)*slopes[1]
    elif self.interpolationMode == "fourier":
      assert False, "fourier interpolationMode isn't fully supported."
    else:
      print("the interpolationMode is " + self.interpolationMode)
      assert False, "The current interpolationMode isn't fully supported."

    if "clip" in self.outputFilters: #this should be moved to the end of the function.
      result = max(min(result,max(sur[1][1],sur[2][1])),min(sur[1][1],sur[2][1])) #@ not tested.
    return result


  def __setitem__(self,index,value):
    #this method might someday adjust cached values if a cache is created.
    index = index%len(self.data) #this prevents problems with simple versions of caching code.
    if self.data[index] != None:
      dbgPrint("Curves.Spline.__setitem__: overwriting an item at index " + str(index) + ".")
    self.data[index] = value
    if Spline.CACHE_BONE_DISTANCE_ABS:
      self.boneDistanceAbs[index] = 0
      x = index + 1
      while x < len(self.data):
        oldDist = self.boneDistanceAbs[x]
        newDist = abs(x - index) #abs included even when the result is expected to be positive, just for symmetry.
        if oldDist != None:
          if newDist >= oldDist:
            break
        self.boneDistanceAbs[x] = newDist
        x += 1
      x = index - 1
      while x >= 0:
        oldDist = self.boneDistanceAbs[x]
        newDist = abs(x - index)
        if oldDist != None:
          if newDist >= oldDist:
            break
        self.boneDistanceAbs[x] = newDist
        x += -1



