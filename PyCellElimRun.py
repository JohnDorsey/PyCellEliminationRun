
"""

PyCellElimRun.py by John Dorsey.

PyCellElimRun.py contains tools for converting audio samples into a sequence of integers that is more easily compressed.

"""


import math

"""
possible block format:
  value range start.
  value range end.
  sample index range start.
  sample index range end.
  first sample value.
  last sample value.
  missing sample prediction mode ID (0=linear, 1=linear with bias towards sinusoidal swoops, 2=cubic spline, 3=polynomial, 4=fourier, ...).
  cell (given sample and value, the question of whether that sample has that value) probability scoring mode ID (0=vertical distance to best guess waveform only, 1=direct distance to nearest point on best guess waveform, ...).
  //more advanced versions might allow the prediction mode and cell scoring mode to dynamically change for certain ranges of samples when the known samples at either end of the range both deserved a different prediction method than was used.
  //more advanced versions might allow file-globally defined custom mathematical functions.

todo:
  -verify that endpoint storage is not wasteful, and that the usage of CellCatalogue is perfectly correct in all situations in order to not leave any improvements to compression ratio on the table.
  -make an integer-only mode.
  -make a fourier interpolation mode for the spline.
  -make an AI interpolation mode for the spline:
    -a mode where the NN is included in the file.
    -a mode where the NN learns as it goes.
  -spackle-based compression of pressDataNums based on the fact that they all add up to a known value. --> actually this should be developed separately.
  -inclusion of gzip.
  -for performance:
    -numba.
    -spline caching.
    -move to another language.
"""


#switching from linearInsort to bisectInsort in 1024x256 cell data improves run time from 3 minutes to under 10 seconds. But increasing cell area to 2048x256 makes encoding take 87 seconds, and 4096x256 makes encoding take 6 minutes.


DODBGPRINT = False
DOVIS = False


def dbgPrint(text,end="\n"):
  if DODBGPRINT:
    print(text,end=end)


def insort(sortedList, newItem, keyFun=(lambda x: x)):
  #linearInsort(sortedList, newItem, keyFun=keyFun)
  bisectInsort(sortedList, newItem, keyFun=keyFun)
  

def linearInsort(sortedList, newItem, keyFun=(lambda x: x)): #insert sorted with linear search.
  keyFunOfNewItem = keyFun(newItem) #caching this probably improves performance a lot.
  for i,item in enumerate(sortedList):
    #print("insort: " + str(item) + " versus " + str(newItem)) #debug.
    if keyFun(item) > keyFunOfNewItem:
      sortedList.insert(i,newItem)
      return
  sortedList.append(newItem) #because it didn't go before any item, it goes after the last one.
  return


def bisectInsort(sortedList, newItem, startPoint=0, endPoint=None, keyFun=(lambda x: x)):
  if len(sortedList) == 0:
    sortedList.append(newItem)
    return
  if endPoint == None:
    endPoint = len(sortedList)-1
  if endPoint - startPoint == 1:
    if keyFun(sortedList[endPoint]) < keyFun(newItem):
      sortedList.insert(endPoint+1,newItem)
    else:
      if keyFun(sortedList[startPoint]) < keyFun(newItem):
        sortedList.insert(endPoint,newItem)
      else:
        sortedList.insert(startPoint,newItem)
    return
  elif endPoint - startPoint == 0:
    if keyFun(sortedList[endPoint]) < keyFun(newItem):
      sortedList.insert(endPoint+1,newItem)
    else:
      sortedList.insert(endPoint,newItem)
    return
  testPoint = int((startPoint+endPoint)/2)
  testItem = sortedList[testPoint]
  testResult = keyFun(testItem) - keyFun(newItem)
  if testResult > 0: #if we should search lower...
    """if testPoint-startPoint <= 1:
      if keyFun(newItem) <= keyFun(sortedList[startPoint]):
        
      else:
        sortedList.insert(testPoint,newItem)"""
    bisectInsort(sortedList, newItem, startPoint=startPoint, endPoint=testPoint, keyFun=keyFun)
  elif testResult < 0: #if we should search higher...
    bisectInsort(sortedList, newItem, startPoint=testPoint, endPoint=endPoint, keyFun=keyFun)
  else:
    sortedList.insert(testPoint,newItem)


def clamp(value,minmax):
  return min(max(value,minmax[0]),minmax[1])


sampleNoise = [128,128,127, 126, 124,113,112,89,32,16,17,14,0,1,9,8,77,78,97,201,210,203,185,183,144,101,99,96,99,124,129,156,146,149,177,181,185,184,170,160,140,110,50,55,75,125,11,123,245,254,255,255,255,254,251,236,249,237,234,221,201,145,103,96,91,115,119,144,144,145,147,149,155,165,175,185,188,193,250,230,210,205,160,50,40,35,31,31,32,39,47,88,86,82,41,13,9,8,6,5,4,4,3,3,3,4,3,2,0,1,2,4,7,17,45,23,46,36,49,62,61,65,98,127,128]
sampleNoise.extend([128 for i in range(128-len(sampleNoise))])
assert len(sampleNoise) == 128


def intify(arr):
  for i,item in enumerate(arr):
    if type(item) == list:
      intify(item)
    else:
      arr[i] = int(item)




class Spline:
  #the Spline is what holds sparse or complete records of all the samples of a wave, and uses whichever interpolation mode was chosen upon its creation to provide guesses about the values of missing samples. It is what will inform decisions about how likely a cell (combination of a sample location and sample value) is to be filled/true. 


  def __init__(self, interpolationMode="cubic-hermite", length=None, endpoints=None, doPopuMap=True):
    assert endpoints == None, "avoid using preset endpoints for this stage of testing."
    self.interpolationMode = interpolationMode
    assert self.interpolationMode in ["linear","sinusoidal","cubic-hermite","fourier"], "this interpolation mode is not supported."
    assert self.interpolationMode in ["linear","sinusoidal","cubic-hermite"], "this interpolation mode is not supported, but support is planned."
    self.length = length
    self.endpoints = endpoints
    assert not (self.length == None and self.endpoints == none)
    if self.length == None:
      self.length = self.endpoints[1][0] - self.endpoints[0][0] + 1
    elif self.endpoints == None:
      self.endpoints = ((0,0),(self.length-1,0))
    else:
      assert False, "impossible error."
    assert len(self.endpoints) == 2
    assert self.endpoints[0][0] == 0, "sample ranges not starting at zero are not yet supported."
    self.data = [None for i in range(self.endpoints[1][0]+1)]
    self.data[0],self.data[-1] = (self.endpoints[0][1],self.endpoints[1][1])
    assert len(self.data) == self.length
    self.doPopuMap = doPopuMap
    if doPopuMap:
      pass


  #these functions are used in constructing cubic hermite splines.
  def hermite_h00(t):
    return 2*t**3 - 3*t**2 + 1
  def hermite_h10(t):
    return t**3 - 2*t**2 + t
  def hermite_h01(t):
    return -2*t**3 + 3*t**2
  def hermite_h11(t):
    return t**3-t**2


  def prettyPrint(self):
    if not DOVIS:
      return
    dbgPrint("Spline.prettyPrint():")
    assert self.endpoints[0][0] == 0
    tempValues = [self.__getitem__(index) for index in range(self.endpoints[1][0]+1)]
    valueRange = (min(tempValues),max(tempValues))
    for value in range(valueRange[1],valueRange[0]-1,-1):
      print(str(value).rjust(10)+": ",end="")
      for index in range(self.endpoints[1][0]+1):
        print("#" if (tempValues[index] == value) else "-",end="")
      print("")


  def getPointInDirection(self,location,direction,skipStart=True):
    print("getPointInDirection: "+str((location,direction,skipStart)))
    #assert type(direction) == int
    assert direction in [-1,1]
    #assert 0 <= location < len(self.data)
    #print(direction)
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


  def __getitem__(self,index): #not integer-based yet. Also, this is one of the biggest wastes of time.
    result = self.data[index]
    if result != None:
      return result
    if self.interpolationMode in ["linear","sinusoidal"]:
      leftItemIndex,rightItemIndex = (index-1, index+1) #the following search procedure could be moved to another method.
      while self.data[leftItemIndex] == None:
        leftItemIndex -= 1
      while self.data[rightItemIndex] == None:
        rightItemIndex += 1
      progression = (index-leftItemIndex)/(rightItemIndex-leftItemIndex)
      if self.interpolationMode == "linear":
        return self.data[leftItemIndex]+((self.data[rightItemIndex]-self.data[leftItemIndex])*progression)
      elif self.interpolationMode == "sinusoidal":
        return self.data[leftItemIndex]+((self.data[rightItemIndex]-self.data[leftItemIndex])*0.5*(1-math.cos(math.pi*progression)))
    elif self.interpolationMode == "cubic-hermite":
      sur = [None,self.getPointInDirection(index,-1),self.getPointInDirection(index,1),None]
      sur[0],sur[3] = (self.getPointInDirection(sur[1][0],-1),self.getPointInDirection(sur[2][0],1))
      #surx = [item[0] for item in sur]
      #sury = [item[1]
      if None in sur[1:3]:
        assert False, "an important (inner) item is missing from the surroundings."
      slopes = [None,None]
      if sur[0] == None:
        #sur[0] = sur[1]
        slopes[0] = (sur[2][1]-sur[1][1])/(sur[2][0]-sur[1][0])
      else:
        slopes[0] = 0.5*((sur[2][1]-sur[1][1])/(sur[2][0]-sur[1][0])+(sur[1][1]-sur[0][1])/(sur[1][0]-sur[0][0]))
      if sur[3] == None:
        #sur[3] = sur[2]
        slopes[1] = (sur[2][1]-sur[1][1])/(sur[2][0]-sur[1][0])
      else:
        slopes[1] = 0.5*((sur[3][1]-sur[2][1])/(sur[3][0]-sur[2][0])+(sur[2][1]-sur[1][1])/(sur[2][0]-sur[1][0]))
      t = float(index-sur[1][0])/float(sur[2][0]-sur[1][0])
      return Spline.hermite_h00(t)*sur[1][1]+Spline.hermite_h10(t)*slopes[0]+Spline.hermite_h01(t)*sur[2][1]+Spline.hermite_h11(t)*slopes[1]
      #assert False, "The current interpolationMode isn't fully supported."
    elif self.interpolationMode == "fourier":
      assert False, "The current interpolationMode isn't fully supported."
    else:
      assert False, "The current interpolationMode isn't fully supported."


  def __setitem__(self,index,value):
    #this method might someday adjust cached values if a cache is created.
    self.data[index] = value




class CellCatalogue:
  ELIMVAL = 0
  UNKVAL = 1
  LIVEVAL = 2
  AUTOLIVE = True #whether or not the only non-eliminated cell in a column should become live. This feature has not been implemented.


  def __init__(self, storageMode="limits", size=(0,0)): #size might be off by one.
    self.storageMode = storageMode
    assert self.storageMode in ["limits","grid"], "That storageMode is nonexistent or not allowed."
    self.size = size #first component is sample index range end; the range currently must start at zero. second component is sample value range; the range currently must start at zero.
    self.grid,self.limits = (None, None)
    if self.storageMode == "limits":
      self.limits = [[-1,self.size[1]] for i in range(self.size[0])]
    elif self.storageMode == "grid":
      self.grid = [[CellCatalogue.UNKVAL for value in range(0,self.size[1])] for index in range(0,self.size[0])]
    else:
      assert False, "unknown storage mode."


  def prettyPrint(self):
    if not DOVIS:
      return
    dbgPrint("CellCatalogue.prettyPrint():")
    for y in range(self.size[1]):
      print("  ",end="")
      for x in range(self.size[0]):
        print(self.getCell((x,y)),end="")
      print(" ",end="")


  def getCell(self,cell):
    if self.storageMode == "limits":
      return CellCatalogue.UNKVAL if (self.limits[cell[0]][0] < cell[1]) and (cell[1] < self.limits[cell[0]][1]) else CellCatalogue.ELIMVAL
    elif self.storageMode == "grid":
      return self.grid[cell[0]][cell[1]]
    else:
      assert False, "unknown storage mode."

  
  def eliminateCell(self,cell):
    #this method may someday make adjustments to fourier-transform-based predictions, if it eliminates a cell that any fourier transform in use would have guessed as an actual value. To do this, access to the Spline would be needed.
    if self.getCell(cell) == CellCatalogue.ELIMVAL:
      print("CellCatalogue.eliminateCell: cell " + str(cell) + " is already eliminated. eliminateCell should not be called on cells that are already eliminated! But let's see what happens if the program continues to run.")
      self.prettyPrint()
    if self.storageMode == "limits":
      if cell[1] == self.limits[cell[0]][0]+1:
        self.limits[cell[0]][0] += 1
      elif cell[1] == self.limits[cell[0]][1]-1:
        self.limits[cell[0]][1] -= 1
      else:
        print("The cell " + str(cell) + " can't be eliminated, because it is not at the edge of the area of eliminated cells! but let's see what happens if the program continues to run.")
        self.prettyPrint()
        return
    elif self.storageMode == "grid":
      self.grid[cell[0]][cell[1]] = CellCatalogue.ELIMVAL
    else:
      assert False, "unknown storage mode."


  def getExtremeUnknownCells(self): #a function to get a list of all cells at the edges of the area of cells that have not been eliminated (hopefully totalling two cells per column (sample)).
    if self.storageMode == "limits":
      result = []
      for columnIndex in range(0,self.size[0]):
        columnLimits = self.limits[columnIndex]
        if columnLimits[1]-columnLimits[0] < 1: #if there is no space between the floor and ceiling of what has not been eliminated...
          continue #register nothing for this column.
        if columnLimits[1]-columnLimits[0] == 1: #special case to avoid registering the same cell twice when the cell just above the floor and just below the ceiling are the same cell. At the time of this writing, I don't know whether this will ever happen because I haven't decided how the CellCatalogue will/should behave in columns where the sample's value is known.
          result.append((columnIndex,columnLimits[0]+1))
        else:
          result.extend([(columnIndex,columnLimits[0]+1),(columnIndex,columnLimits[1]-1)])
      return result #returns all extreme unknown cells in no special order, but probably from left to right.
    else:
      assert False, "not all storage modes are yet supported for this function."


  def clampCell(self,cell): #move a cell's value to make it comply with the catalogue of eliminated cells.
    """if self.getCell(cell) == CellCatalogue.UNKVAL: #if no action needed...
      print("CellCatalogue.clampCell(cell): this cell is already unknown, returning unmodified input.")
      return cell""" #this never runs and wasn't needed.
    if self.storageMode == "limits":
      result = (cell[0],clamp(cell[1],(self.limits[cell[0]][0]+1,self.limits[cell[0]][1]-1)))
      assert result != cell, "CellCatalogue.clampCell(cell): this function failed."
      return result
    else:
      assert False, "not all storage modes are yet supported for this function."





class CodecState:


  def __init__(self, size, plainDataSamples=None, pressDataNums=None, opMode="encode"):
    self.size = size
    self.plainDataSamples, self.pressDataNums = (plainDataSamples, pressDataNums)
    if self.plainDataSamples == None:
      self.plainDataSamples = []
    if self.pressDataNums == None:
      self.pressDataNums = []
    self.opMode = opMode
    assert self.opMode in ["encode","decode"], "That opMode is nonexistent or not allowed"
    if self.opMode == "encode":
      assert len(self.plainDataSamples) > 0
      assert len(self.pressDataNums) == 0
    elif self.opMode == "decode":
      if len(self.plainDataSamples) == 0:
        #defaultSampleValue = int(self.size[1]/2) #<- do not switch back to this without fixing the processBlock method!
        defaultSampleValue = None
        self.plainDataSamples.extend([defaultSampleValue for i in range(self.size[0])])
      assert len(self.pressDataNums) > 0
    else:
      assert False, "invalid opMode."
    self.runIndex = None #the run index determines which integer run length from the pressdata run length list is being read and counted towards with the stepIndex variable as a counter while decoding, or, it is the length of the current list of such integer run lengths that is being built by encoding.
    self.stepIndex = None #the step index counts towards the value of the current elimination run length - either it is compared to a known elimination run length in order to know when to terminate and record a cell as filled while decoding, or it counts and holds the new elimination run length value to be stored while encoding.
    self.spline = Spline(length=self.size[0])
    self.cellCatalogue = CellCatalogue(size=self.size)


  def processBlock(self,interpolateMissingValues=True):
    #encode or decode.
    self.runIndex = 0
    while True:
      self.processRun()
      self.spline.prettyPrint()
      self.runIndex += 1
      if (self.opMode == "encode" and self.runIndex >= len(self.plainDataSamples)) or (self.opMode == "decode" and self.runIndex >= len(self.pressDataNums)):
        if self.opMode == "decode" and interpolateMissingValues:
          if None in self.plainDataSamples:
            print("CodecState.processBlock: missing values exist and will be filled in using the interpolation settings of the spline object that was used for transcoding.")
            for index in range(len(self.plainDataSamples)):
              if self.plainDataSamples[index] == None:
                self.plainDataSamples[index] = self.spline[index]
        return #finished, might be lossy if it ended while they were unequal lengths.


  def processRun(self): #do one run, either encoding or decoding.
    dbgPrint("CodecState.processRun: runIndex = " + str(self.runIndex))
    self.stepIndex = 0
    breakRun = False
    for cellToCheck in self.getGenCellCheckOrder():
      dbgPrint("CodecState.processRun: (runIndex,stepIndex,cellToCheck) = " + str((self.runIndex,self.stepIndex,cellToCheck))) 
      if self.opMode == "encode":
        if self.plainDataSamples[cellToCheck[0]] == cellToCheck[1]: #if hit...
          #then a new run length is now known and should be added to the compressed data number list.
          self.pressDataNums.append(self.stepIndex)
          breakRun = True
        else:
          self.stepIndex += 1
      elif self.opMode == "decode":
        if self.pressDataNums[self.runIndex] == self.stepIndex: #if run is ending...
          #then a new hit is known.
          self.plainDataSamples[cellToCheck[0]] = cellToCheck[1]
          breakRun = True
        else:
          self.stepIndex += 1
      else:
        assert False, "invalid opMode."
      assert self.stepIndex <= ((self.size[0]+1)*(self.size[1]+1)+2), "CodecState.processRun: this loop has run for an impossibly long time."
      if breakRun:
        self.spline[cellToCheck[0]] = cellToCheck[1] #is it really that easy?
        dbgPrint("breaking run; cellToCheck is " + str(cellToCheck) + ".")
        return

  
  def getGenCellCheckOrder(self,scoreFun="vertical_distance"):
    #returns a generator whose next value is an (index,value) pair of the next cell to be checked while on a cell elimination run. It can be much more efficient than a function that finds the next best cell to check and is called again for every check.
    rankingsInsortKeyFun = lambda item: item[1]
    if type(scoreFun)==str:
      assert scoreFun in ["vertical_distance","absolute_distance"]
      if scoreFun=="vertical_distance":
        def scoreFun(cell):
          return self.size[1]-abs(self.spline[cell[0]]-cell[1]) #bad offset? probably not.
      else:
        assert False, "not all scoreFuns are yet supported."
    else:
      assert type(scoreFun)==type(lambda x: x) #works in python3, untested in python2.
    rankings = [] #rankings array will store items in format [(index, value), likelyhood score (lower is less likely and better to visit in an elimination run)]. In more efficient versions of this codec, especially where the likelyhood scores of all cells don't change all over at the same time when new info is discovered (as could happen with fourier interpolation), the rankings should be passed into this method from the outside so that they can be edited from the outside (such as by setting the scores to None for all samples near a new sample added to a spline with linear interpolation, so that this method regenerates those scores and re-sorts the array that is already mostly sorted.
    
    for cell in self.cellCatalogue.getExtremeUnknownCells():
      insort(rankings, [cell, scoreFun(cell)], keyFun=rankingsInsortKeyFun)
    while True: #the generator loop.
      outputCell = rankings[0][0]
      dbgPrint("getGenCellCheckOrder: yielding " + str(outputCell)) #debug. 
      yield outputCell
      del rankings[0]
      self.cellCatalogue.eliminateCell(outputCell)
      replacementCell = self.cellCatalogue.clampCell(outputCell)
      assert str(outputCell) != str(replacementCell) #debug.
      #print([replacementCell, scoreFun(replacementCell)]) #debug.
      #print(rankings) #debug.
      insort(rankings, [replacementCell, scoreFun(replacementCell)], keyFun=rankingsInsortKeyFun)
    #^ this code caches cell scores and might have much better performance potential, but might not work.
    #the below code, which recalculates the cell score for every compare of every insort, is around 8x slower for 128x256 cell randomish data tests.
    """for cell in self.cellCatalogue.getExtremeUnknownCells():
      insort(rankings, cell, keyFun=scoreFun)
    while True: #the generator loop.
      outputCell = rankings[0]
      dbgPrint("getGenCellCheckOrder: yielding " + str(outputCell)) #debug. 
      yield outputCell
      del rankings[0]
      self.cellCatalogue.eliminateCell(outputCell)
      replacementCell = self.cellCatalogue.clampCell(outputCell)
      assert str(outputCell) != str(replacementCell) #debug.
      #print([replacementCell, scoreFun(replacementCell)]) #debug.
      #print(rankings) #debug.
      insort(rankings, replacementCell, keyFun=scoreFun)"""
    dbgPrint("getGenCellCheckOrder has ended.")



def functionalTest(inputData,opMode,size=(8,8)):
  assert opMode in ["encode","decode"]
  tempCS = None
  outputData = []
  if opMode == "encode":
    tempCS = CodecState(size,plainDataSamples=[item for item in inputData],pressDataNums=outputData,opMode=opMode)
  elif opMode == "decode":
    tempCS = CodecState(size,plainDataSamples=outputData,pressDataNums=[item for item in inputData],opMode=opMode)
  else:
    assert False
  tempCS.processBlock()
  return outputData
