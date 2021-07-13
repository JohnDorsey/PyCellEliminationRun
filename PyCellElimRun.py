"""

PyCellElimRun.py by John Dorsey.

PyCellElimRun.py contains tools for converting audio samples into a sequence of integers that is more easily compressed.

"""

import math

import Curves





#switching from linearInsort to bisectInsort in 1024x256 cell data improves run time from 3 minutes to under 10 seconds. But increasing cell area to 2048x256 makes encoding take 87 seconds, and 4096x256 makes encoding take 6 minutes.


DODBGPRINT = False #print debug info.
DOVIS = False #show pretty printing, mostly for debugging.

def dbgPrint(text,end="\n"): #only print if DODBGPRINT.
  if DODBGPRINT:
    print(text)
    print("custom line endings disabled for python2 compatibility.")



def insort(sortedList, newItem, keyFun=(lambda x: x)): #insert sorted using whichever method is not commented out.
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
  keyFunOfNewItem = keyFun(newItem) #@ cache this for probably a tiny performance gain, but not as much as rewriting the method to take a key instead of a keyFun would give.
  if endPoint == None:
    endPoint = len(sortedList)-1
  if endPoint - startPoint == 1:
    if keyFun(sortedList[endPoint]) < keyFunOfNewItem:
      sortedList.insert(endPoint+1,newItem)
    else:
      if keyFun(sortedList[startPoint]) < keyFunOfNewItem:
        sortedList.insert(endPoint,newItem)
      else:
        sortedList.insert(startPoint,newItem)
    return
  elif endPoint - startPoint == 0:
    if keyFun(sortedList[endPoint]) < keyFunOfNewItem:
      sortedList.insert(endPoint+1,newItem)
    else:
      sortedList.insert(endPoint,newItem)
    return
  testPoint = int((startPoint+endPoint)/2)
  testItem = sortedList[testPoint]
  testResult = keyFun(testItem) - keyFunOfNewItem
  if testResult > 0: #if we should search lower...
    bisectInsort(sortedList, newItem, startPoint=startPoint, endPoint=testPoint, keyFun=keyFun)
  elif testResult < 0: #if we should search higher...
    bisectInsort(sortedList, newItem, startPoint=testPoint, endPoint=endPoint, keyFun=keyFun)
  else:
    sortedList.insert(testPoint,newItem)


def clamp(value,minmax):
  return min(max(value,minmax[0]),minmax[1])


def intify(arr): #force every number to be an int.
  for i,item in enumerate(arr):
    if type(item) == list:
      intify(item)
    else:
      arr[i] = int(item)




class CellCatalogue:
  #a place to record the states of cells.
  #limits mode stores only the upper and lower bounds of un-eliminated cell areas per column. Grid mode allows cells to be eliminated in non-contiguous places at the cost of a lot of memory. Grid mode has not been tested, because none of the ideas I once had for cell visit orders which required grid cataloguing remained promising choices for how to improve compression.
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


  def toPrettyStr(self):
    alignmentError = False
    result = "PyCellElimRun.CellCatalogue.toPrettyStr generated string representation."
    sidebarWidth = len(str(self.size[1]))
    for y in range(self.size[1]-1,-1,-1):
      result += "\n"+str(y).rjust(sidebarWidth," ")+": "
      for x in range(self.size[0]):
        addition = str(self.getCell((x,y)))
        if len(addition) != 1:
          alignmentError = True
        result += addition
    result += "\nalignmentError="+str(alignmentError)
    return result


  def getCell(self,cell):
    if self.storageMode == "limits":
      return CellCatalogue.UNKVAL if (self.limits[cell[0]][0] < cell[1]) and (cell[1] < self.limits[cell[0]][1]) else CellCatalogue.ELIMVAL
    elif self.storageMode == "grid":
      return self.grid[cell[0]][cell[1]]
    assert False, "unknown storage mode."


  def eliminateColumn(self,columnIndex):
    #this makes it impossible for any other method to doubt that the column has no cells of any kind but eliminated.
    #it definitely changes the output, and seems to improve compression in some tests. It is only necessary because the generator for cells to check is usually responsible for eliminating cells in the catalogue, but it can't do that when the run terminates and the generator method is also terminated.
    #It is not really compatible with the AUTOLIVE idea.
    if self.storageMode == "limits":  
      self.limits[columnIndex][0] = -1
      self.limits[columnIndex][1] = -3
    elif self.storageMode == "grid":
      for i in range(len(self.grid[columnIndex])):
        self.grid[columnIndex][i] = CellCatalogue.ELIMVAL


  def eliminateCell(self,cell):
    #this method may someday make adjustments to fourier-transform-based predictions, if it eliminates a cell that any fourier transform in use would have guessed as an actual value. To do this, access to the Spline would be needed.
    if self.getCell(cell) == CellCatalogue.ELIMVAL:
      print("PyCellElimRun.CellCatalogue.eliminateCell: The cell " + str(cell) + " is already eliminated. eliminateCell should not be called on cells that are already eliminated! But let's see what happens if the program continues to run.")
    if self.storageMode == "limits":
      if cell[1] == self.limits[cell[0]][0]+1:
        self.limits[cell[0]][0] += 1
      elif cell[1] == self.limits[cell[0]][1]-1:
        self.limits[cell[0]][1] -= 1
      else:
        print("PyCellElimRun.CellCatalogue.eliminateCell: The cell " + str(cell) + " can't be eliminated, because it is not at the edge of the area of eliminated cells! but let's see what happens if the program continues to run.")
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
    if self.storageMode == "limits":
      result = (cell[0],clamp(cell[1],(self.limits[cell[0]][0]+1,self.limits[cell[0]][1]-1)))
      assert result != cell, "CellCatalogue.clampCell(cell): this function failed."
      return result
    else:
      assert False, "not all storage modes are yet supported for this function."





class CellElimRunCodecState:
  #the CodecState is responsible for owning and operating a Spline and CellCatalogue, and using them to either encode or decode data. Encoding and decoding are supposed to share as much code as possible. This makes improving or expanding the core mathematics of the compression vastly easier - as long as the important code is only ever called in identical ways by both the encoding and the decoding methods, any change to the method of predicting unknown data from known data won't break the symmetry of those methods.

  DO_COLUMN_ELIMINATION = True #this should not be turned off, because it affects the output.

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
    self.spline = Curves.Spline(size=self.size)
    self.cellCatalogue = CellCatalogue(size=self.size)


  def processBlock(self,allowMissingValues=False):
    #encode or decode. This method processes all the data that is currently loaded into the CodecState, which is supposed to be one block. It does not know about surrounding blocks of audio or the results of handling them. When finished, it does not clean up after itself in any way.
    self.runIndex = 0
    while True:
      self.processRun()
      self.runIndex += 1
      if (self.opMode == "encode" and self.runIndex >= len(self.plainDataSamples)) or (self.opMode == "decode" and self.runIndex >= len(self.pressDataNums)):
        break
    if self.opMode == "decode" and not allowMissingValues:
      self.interpolateMissingValues()
    return #finished, might be lossy if it ended while they were unequal lengths.


  def interpolateMissingValues(self):
    if None in self.plainDataSamples:
      print("PyCellElimRun.CellElimRunCodecState.interpolateMissingValues: " + str(self.plainDataSamples.count(None)) + " missing values exist and will be filled in using the interpolation settings of the spline object that was used for transcoding.")
      for index in range(len(self.plainDataSamples)):
        if self.plainDataSamples[index] == None:
          self.plainDataSamples[index] = self.spline[index]
    else:
      print("PyCellElimRun.CellElimRunCodecState.interpolateMissingValues: no missing values exist.")


  def processRun(self): #do one run, either encoding or decoding.
    dbgPrint("PyCellElimRun.CellElimRunCodecState.processRun: runIndex = " + str(self.runIndex) + ".")
    self.stepIndex = 0
    breakRun = False
    for cellToCheck in self.getGenCellCheckOrder():
      #dbgPrint("CodecState.processRun: (runIndex,stepIndex,cellToCheck) = " + str((self.runIndex,self.stepIndex,cellToCheck))) 
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
      assert self.stepIndex <= ((self.size[0]+1)*(self.size[1]+1)+2), "This loop has run for an impossibly long time."
      if breakRun:
        self.spline[cellToCheck[0]] = cellToCheck[1] #is it really that easy?
        if CellElimRunCodecState.DO_COLUMN_ELIMINATION:
          self.cellCatalogue.eliminateColumn(cellToCheck[0])
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
        assert False, "Not all scoreFuns are yet supported."
    else:
      assert type(scoreFun) == type(lambda x: x) #works in python3, untested in python2.
    rankings = [] #rankings array will store items in format [(index, value), likelyhood score (lower is less likely and better to visit in an elimination run)]. In more efficient versions of this codec, especially where the likelyhood scores of all cells don't change all over at the same time when new info is discovered (as could happen with fourier interpolation), the rankings should be passed into this method from the outside so that they can be edited from the outside (such as by setting the scores to None for all samples near a new sample added to a spline with linear interpolation, so that this method regenerates those scores and re-sorts the array that is already mostly sorted.
    
    for cell in self.cellCatalogue.getExtremeUnknownCells():
      insort(rankings, [cell, scoreFun(cell)], keyFun=rankingsInsortKeyFun)
    while True: #the generator loop.
      outputCell = rankings[0][0]
      #dbgPrint("getGenCellCheckOrder: yielding " + str(outputCell)) #debug. 
      yield outputCell
      del rankings[0] #@ room for optimization.
      self.cellCatalogue.eliminateCell(outputCell)
      replacementCell = self.cellCatalogue.clampCell(outputCell)
      assert str(outputCell) != str(replacementCell) #debug.
      #print([replacementCell, scoreFun(replacementCell)]) #debug.
      #print(rankings) #debug.
      insort(rankings, [replacementCell, scoreFun(replacementCell)], keyFun=rankingsInsortKeyFun)
    #^ this code caches cell scores and is up to 8x faster than not doing so in some tests.
    dbgPrint("getGenCellCheckOrder has ended.")



def cellElimRunTranscode(inputData,opMode,splineInterpolationMode,size,dbgReturnCERCS=False):
  if size[0] == None:
    dbgPrint("PyCellElimRun.functionalTest: assuming size.")
    size[0] = len(inputData)
  assert opMode in ["encode","decode"]
  tempCERCS = None
  outputData = []
  if opMode == "encode":
    tempCERCS = CellElimRunCodecState(size,plainDataSamples=[item for item in inputData],pressDataNums=outputData,opMode=opMode)
  elif opMode == "decode":
    tempCERCS = CellElimRunCodecState(size,plainDataSamples=outputData,pressDataNums=[item for item in inputData],opMode=opMode)
  else:
    assert False, "invalid opMode."
  tempCERCS.spline.setInterpolationMode(splineInterpolationMode) #@ this is a bad way to do it.
  tempCERCS.processBlock()
  if dbgReturnCERCS:
    return tempCERCS
  else:
    return outputData
  assert False

