"""

PyCellElimRun.py by John Dorsey.

PyCellElimRun.py contains tools for converting audio samples into a sequence of integers that is more easily compressed.

"""

import math

import Curves

from PyGenTools import isGen,makeArr,makeGen




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


def intify(arr,roundNearest=False): #force every number to be an int.
  for i,item in enumerate(arr):
    if type(item) == list:
      intify(item,roundNearest=roundNearest)
    else:
      arr[i] = int(round(item)) if roundNearest else int(item)





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
      raise ValueError("unknown storage mode.")


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


  def countUnknowns(self): #this could just be tracked by the methods that eliminate cells, but that could be less reliable.
    total = 0
    if self.storageMode == "limits":
      for columnIndex in range(0,self.size[0]):
        total += max(0,self.limits[columnIndex][1]-self.limits[columnIndex][0]-1)
    else:
      assert False, "Not all storage modes are yet implemented for this function."
    return total


  def eliminateColumn(self,columnIndex,dbgCustomValue=-1):
    #this makes it impossible for any other method to doubt that the column has no cells of any kind but eliminated.
    #it definitely changes the output, and seems to improve compression in some tests. It is only necessary because the generator for cells to check is usually responsible for eliminating cells in the catalogue, but it can't do that when the run terminates and the generator method is also terminated.
    #It is not really compatible with the AUTOLIVE idea.
    #print("eliminateColumn called for column " + str(columnIndex) + " and dbgCustomValue " + str(dbgCustomValue) + ".")
    if self.storageMode == "limits":  
      self.limits[columnIndex][0] = dbgCustomValue
      self.limits[columnIndex][1] = dbgCustomValue
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
      if self.limits[cell[0]][0] + 2 == self.limits[cell[0]][1]:
        #print("WARNING: PyCellElimRun.CellCatalogue.eliminateCell: there is now only one cell within the limits of column " + str(cell[0]) + "!")
        return True #indicate that the column is critical.
    elif self.storageMode == "grid":
      self.grid[cell[0]][cell[1]] = CellCatalogue.ELIMVAL
    else:
      assert False, "unknown storage mode."
    return False #indicate that the column is not critical.


  def getExtremeUnknownCells(self,sides=None): #a function to get a list of all cells at the edges of the area of cells that have not been eliminated (hopefully totalling two cells per column (sample)).
    if sides == None:
      sides = [True,True] #sides[0] = include bottom cells?, sides[1] = include top cells?. if both are false, a cell can only be part of the output if it is the lone unknown cell in its column.
    if self.storageMode == "limits":
      result = []
      for columnIndex in range(0,self.size[0]):
        columnLimits = self.limits[columnIndex]
        if columnLimits[1]-columnLimits[0] < 1: #if there is no space between the floor and ceiling of what has not been eliminated...
          continue #register nothing for this column.
        if columnLimits[1]-columnLimits[0] == 1: #special case to avoid registering the same cell twice when the cell just above the floor and just below the ceiling are the same cell. At the time of this writing, I don't know whether this will ever happen because I haven't decided how the CellCatalogue will/should behave in columns where the sample's value is known.
          result.append((columnIndex,columnLimits[0]+1))
          print("WARNING: PyCellElimRun.CellCatalogue.getExtremeUnknownCells had to merge two cells in its result, meaning that column " + str(columnIndex) + " could have been eliminated earlier!")
        else:
          if sides[0]:
            result.append((columnIndex,columnLimits[0]+1))
          if sides[1]:
            result.append((columnIndex,columnLimits[1]-1))
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

  DO_COLUMN_ELIMINATION_AT_GEN_END = True #this should not be turned off, because it affects the output.
  DO_CRITICAL_COLUMN_ROUTINE = True

  def __init__(self, inputData, opMode, size):
    self.size = size
    self.prepMode(inputData,opMode)
    self.runIndex = None #the run index determines which integer run length from the pressdata run length list is being read and counted towards with the stepIndex variable as a counter while decoding, or, it is the length of the current list of such integer run lengths that is being built by encoding.
    self.stepIndex = None #the step index counts towards the value of the current elimination run length - either it is compared to a known elimination run length in order to know when to terminate and record a cell as filled while decoding, or it counts and holds the new elimination run length value to be stored while encoding.
    self.spline = Curves.Spline(size=self.size)
    self.cellCatalogue = CellCatalogue(size=self.size)


  def prepMode(self,inputData,opMode):
    self.opMode = opMode
    if not self.opMode in ["encode","decode"]:
      raise ValueError("That opMode is nonexistent or not allowed.")
    self.plainDataInputArr, self.pressDataInputGen = (None,None)
    self.plainDataOutputArr, self.pressDataOutputArr = (None,None)
    if self.opMode == "encode":
      assert type(inputData) == list
      self.plainDataInputArr = inputData
      assert len(self.plainDataInputArr) > 0
      self.pressDataOutputArr = []
    elif self.opMode == "decode":
      assert isGen(inputData)
      self.pressDataInputGen = inputData
      self.plainDataOutputArr = []
      defaultSampleValue = None
      self.plainDataOutputArr.extend([defaultSampleValue for i in range(self.size[0])])
    else:
      assert False, "invalid opMode."


  def processBlock(self,allowMissingValues=False):
    #encode or decode. This method processes all the data that is currently loaded into the CodecState, which is supposed to be one block. It does not know about surrounding blocks of audio or the results of handling them. When finished, it does not clean up after itself in any way.
    self.runIndex = 0
    while True:
      if (self.opMode == "encode" and self.runIndex >= len(self.plainDataInputArr)) or (self.opMode == "decode" and self.runIndex >= self.size[0]):
        break
      shouldContinue = self.processRun()
      self.runIndex += 1
      if not shouldContinue:
        break
    if self.opMode == "decode" and not allowMissingValues:
      self.interpolateMissingValues(self.plainDataOutputArr)
    return #finished, might be lossy if it ended while they were unequal lengths.


  def interpolateMissingValues(self,targetArr):
    if None in targetArr:
      print("PyCellElimRun.CellElimRunCodecState.interpolateMissingValues: " + str(targetArr.count(None)) + " missing values exist and will be filled in using the interpolation settings of the spline object that was used for transcoding.")
      #print("The missing values are at the indices " + str([i for i in range(len(self.plainDataSamples)) if self.plainDataSamples[i] == None]) + ".")
      for index in range(len(targetArr)):
        if targetArr[index] == None:
          targetArr[index] = self.spline[index]
    else:
      print("PyCellElimRun.CellElimRunCodecState.interpolateMissingValues: no missing values exist.")


  def processRun(self): #do one run, either encoding or decoding.
    #print("PyCellElimRun.CellElimRunCodecState.processRun: runIndex = " + str(self.runIndex) + ".")
    self.stepIndex = 0
    
    breakRun = False
    justStarted = True #so that (if decoding) pressDataInputGen.next() may be called only once and only after the loop starts successfully, since getGenCellCheckOrder yielding no items is one way that the end of processing is signalled.
    for orderEntry in self.getGenCellCheckOrder():
      if justStarted:
        currentPressDataNum = None
        if self.opMode == "decode":
          try:
            currentPressDataNum = next(self.pressDataInputGen)
          except StopIteration:
            print("PyCellElimRun.CellElimRunCodecState.processRun has run out of pressData input items. This is uncommon.")
            return False #indicate that processing should stop.
        justStarted = False #don't run this block again.
      cellToCheck = orderEntry[1]
      if orderEntry[0] == "fix":
        print("order entry " + str(orderEntry) + " will be fixed")
        assert CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE, "fix is not supposed to happen while DO_CRITICAL_COLUMN_ROUTINE is disabled!"
        self.spline[cellToCheck[0]] = cellToCheck[1]
        continue
      assert orderEntry[0] == "visit"
      #print("CodecState.processRun: (runIndex,stepIndex,cellToCheck) = " + str((self.runIndex,self.stepIndex,cellToCheck))) 
      if self.opMode == "encode":
        if self.plainDataInputArr[cellToCheck[0]] == cellToCheck[1]: #if hit...
          #then a new run length is now known and should be added to the compressed data number list.
          self.pressDataOutputArr.append(self.stepIndex)
          breakRun = True
        else:
          self.stepIndex += 1
      elif self.opMode == "decode":
        if currentPressDataNum == self.stepIndex: #if run is ending...
          #then a new hit is known.
          self.plainDataOutputArr[cellToCheck[0]] = cellToCheck[1]
          breakRun = True
        else:
          self.stepIndex += 1
      else:
        assert False, "invalid opMode."
      assert self.stepIndex <= ((self.size[0]+1)*(self.size[1]+1)+2), "This loop has run for an impossibly long time."
      if breakRun:
        #print("found " + str(cellToCheck) + ".")
        self.spline[cellToCheck[0]] = cellToCheck[1] #is it really that easy?
        if CellElimRunCodecState.DO_COLUMN_ELIMINATION_AT_GEN_END:
          self.cellCatalogue.eliminateColumn(cellToCheck[0],dbgCustomValue=-5)
        #print("breaking run; cellToCheck is " + str(cellToCheck) + ".")
        return True #indicate that processing should continue.
    #print("PyCellElimRun.processRun ended by running out of options.")
    return False #indicate that processing should stop.

  
  def getGenCellCheckOrder(self,scoreFun="vertical_distance"):
    #returns a generator whose next value is an (index,value) pair of the next cell to be checked while on a cell elimination run. It can be much more efficient than a function that finds the next best cell to check and is called again for every check.
    #print("getGenCellCheckOrder called.")
    rankingsInsortKeyFun = lambda item: item[0]
    if type(scoreFun)==str:
      assert scoreFun in ["vertical_distance","absolute_distance"]
      if scoreFun=="vertical_distance":
        def scoreFun(cell):
          return self.size[1]-abs(self.spline[cell[0]]-cell[1]) #bad offset? probably not.
      else:
        assert False, "Not all scoreFuns are yet supported."
    else:
      assert type(scoreFun) == type(lambda x: x) #works in python3, untested in python2.
    
    rankings = [] #rankings array will store items in format [(score, cell), likelyhood score (lower is less likely and better to visit in an elimination run)]. In more efficient versions of this codec, especially where the likelyhood scores of all cells don't change all over at the same time when new info is discovered (as could happen with fourier interpolation), the rankings should be passed into this method from the outside so that they can be edited from the outside (such as by setting the scores to None for all samples near a new sample added to a spline with linear interpolation, so that this method regenerates those scores and re-sorts the array that is already mostly sorted.
    
    for cell in self.cellCatalogue.getExtremeUnknownCells():
      insort(rankings, [scoreFun(cell), cell], keyFun=rankingsInsortKeyFun)
    if len(rankings) == 0:
      #print("getGenCellCheckOrder ran out of items before its main loop.")
      assert CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE, "this return is not supposed to happen while DO_CRITICAL_COLUMN_ROUTINE is disabled!"
      return
    while True: #the generator loop.
      #the following slow duplicate checker is disabled because dupes are now considered impossible.
      #print("getGenCellCheckOrder: checking for dupes! slow!")
      #for i in range(len(rankings)-1):
      #  if rankings[i][1] == rankings[i+1][1]:
      #    print("a dupe exists at " + str(i) + "! the compared entries are " + str(rankings[i]) + " and " + str(rankings[i]) + ".")
      if len(rankings) == 0:
        print("getGenCellCheckOrder ran out of items in its main loop. This has never happened before.")
        assert CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE, "this return is not supposed to happen while DO_CRITICAL_COLUMN_ROUTINE is disabled!"
        return
      outputCell = rankings[0][1]
      #dbgPrint("getGenCellCheckOrder: yielding " + str(outputCell)) #debug. 
      yield ("visit", outputCell)
      del rankings[0] #@ room for optimization.
      columnCritical = self.cellCatalogue.eliminateCell(outputCell)
      replacementCell = self.cellCatalogue.clampCell(outputCell)
      assert str(outputCell) != str(replacementCell) #debug.
      if columnCritical and CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE:
        #print("column is critical for " + str(outputCell) + ". column limits are " + str(self.cellCatalogue.limits[outputCell[0]]) + ".")
        self.cellCatalogue.eliminateColumn(outputCell[0],dbgCustomValue=-7)
        #print("the replacementCell " + str(replacementCell) + " is now assumed to be a duplicate and will not be insorted into the rankings.")
        yield ("fix",replacementCell)
      else:
        insort(rankings, [scoreFun(replacementCell), replacementCell], keyFun=rankingsInsortKeyFun)
    print("getGenCellCheckOrder has ended.")



def cellElimRunTranscode(inputData,opMode,splineInterpolationMode,size,dbgReturnCERCS=False):
  if size[0] == None:
    dbgPrint("PyCellElimRun.functionalTest: assuming size.")
    size[0] = len(inputData)
  assert opMode in ["encode","decode"]
  tempCERCS = None
  if opMode == "encode":
    tempCERCS = CellElimRunCodecState(makeArr(inputData),"encode",size)
  elif opMode == "decode":
    tempCERCS = CellElimRunCodecState(makeGen(inputData),"decode",size)
  else:
    assert False, "invalid opMode."
  tempCERCS.spline.setInterpolationMode(splineInterpolationMode) #@ this is a bad way to do it.
  tempCERCS.processBlock()
  if dbgReturnCERCS:
    return tempCERCS
  else:
    return tempCERCS.plainDataOutputArr if opMode=="decode" else tempCERCS.pressDataOutputArr
  assert False






testResult = cellElimRunTranscode([2,2,2,2,2],"encode","linear",[5,5])
assert testResult[0] == 20
assert sum(testResult[1:]) == 0
assert cellElimRunTranscode([20],"decode","linear",[5,5]) == [2,2,2,2,2]

testResult = cellElimRunTranscode([5,6,7,6,5],"encode","linear",[5,10])
assert testResult[:2] == [32,10]
assert sum(testResult[2:]) == 0
assert cellElimRunTranscode([32,10,0,0,0],"decode","linear",[5,10]) == [5,6,7,6,5]
