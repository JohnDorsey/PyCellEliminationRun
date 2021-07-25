"""

PyCellElimRun.py by John Dorsey.

PyCellElimRun.py contains tools for converting audio samples into a sequence of integers that is more easily compressed.

"""

import math

import Curves
import CodecTools

from IntArrMath import intify
from PyArrTools import insort

from PyGenTools import isGen,makeArr,makeGen,arrTakeOnly,ExhaustionError
from PyArrTools import ljustedArr, bubbleSortSingleItemRight
from PyDictTools import augmentDict,makeFromTemplateAndSeq


#switching from linearInsort to bisectInsort in 1024x256 cell data improves run time from 3 minutes to under 10 seconds. But increasing cell area to 2048x256 makes encoding take 87 seconds, and 4096x256 makes encoding take 6 minutes.


DODBGPRINT = False #print debug info.
DOVIS = False #show pretty printing, mostly for debugging.

def dbgPrint(text,end="\n"): #only print if DODBGPRINT.
  if DODBGPRINT:
    print(text)
    print("custom line endings disabled for python2 compatibility.")





def clamp(value,minmax):
  return min(max(value,minmax[0]),minmax[1])








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
  """
  the CellElimRunCodecState is responsible for owning and operating a Spline and CellCatalogue, and using them to either encode or decode data. Encoding and decoding are supposed to share as much code as possible. This makes improving or expanding the core mathematics of the compression vastly easier - as long as the important code is only ever called in identical ways by both the encoding and the decoding methods, any change to the method of predicting unknown data from known data won't break the symmetry of those methods.
  """
  
  #the following column-related options control whether entire columns of unknown or un-visited cells can be eliminated from the cellCatalogue at various times that the cellCatalogue would NOT eliminate them on its own. For instance, the algorithm always eliminates the cellCatalogue column when it hits a live cell, but it's also possible to eliminate a column when that column has two unknown cells and one of them is visited but not hit - this is the purpose of the critical column routine.
  DO_COLUMN_ELIMINATION_AT_GEN_END = True #this should not be turned off, because it changes the output in a way that isn't simple. Compression Ratio seems to be better with it turned on, but this wasn't expected, so the loss of compression with it turned off is probably a bug. Changing this parameter shouldn't break symmetry.
  DO_CRITICAL_COLUMN_ROUTINE = True #this is responsible for most of the process of ensuring that trailing zeroes are trimmed and CER blocks may be self-delimiting.
  DO_COLUMN_ELIMINATION_OFFICIALLY = True #This controls whether column elimination can be performed by setPlaindataSample. Some of the process of making CER blocks self-delimiting depends on the use of setPlaindataSample with the expectation that this is set to True.


  def __init__(self, inputData, opMode, interpolationMode=None, spaceDefinition=None):
    """
    The initialization method takes arguments that resemble a structured header as much as possible. In the decode phase, it fills in missing data in headerDict by decoding a few pressdata items as parameters. In the encode phase, it fills in missing data in headerDict by analyzing the provided plaindata, encodes these parameters, and prepends them to the pressdata it will output.
    The initialization method also creates all of the attributes that processBlock needs to start running right away. By the time processBlock is called, there is no more initialization to do.
    """
    self.initializeByDefault()
    
    self.inputDataGen = makeGen(inputData) #this is necessary to make it so that prepSpaceDefinition can take some items from the front, before prepOpMode does anything.
    self.opMode = opMode #initialized here instead of in prepOpMode because it is needed by prepSpaceDefinition.

    self.inputHeaderDictTemplate = self.TO_COMPLETED_SPACE_DEFINITION(spaceDefinition)
    self.headerDict = {}
    self.pressHeaderValues = [] #this is to remain empty until populated by the header loader. it _may_ be populated if the headerDictTemplate tells it to embed or access header info from the regular inputData.

    self.headerRoutineBeforeInit()
    self.tempApplyHeader() #@ FIX! this must be removed eventually!

    self.prepSpaceDefinition()
    self.spline.setInterpolationMode(interpolationMode)  #@ this should also pull from the loaded header someday maybe.
    self.prepOpMode()

    self.headerRoutineAfterInit()

    self.runIndex = None #the run index determines which integer run length from the pressdata run length list is being read and counted towards with the stepIndex variable as a counter while decoding, or, it is the length of the current list of such integer run lengths that is being built by encoding.
    self.stepIndex = None #the step index counts towards the value of the current elimination run length - either it is compared to a known elimination run length in order to know when to terminate and record a cell as filled while decoding, or it counts and holds the new elimination run length value to be stored while encoding.

  def initializeByDefault(self):
    """
    initializeByDefault initializes things that can't be changed by class settings and don't depend on header information.
    """
    self.rankingsInsortKeyFun = (lambda item: item[0]) #used by getGenCellCheckOrder.

  def GET_DEFAULT_SPACE_DEFINITION(self):
    #return {"plaindata_num_count":256,"plaindata_num_upper_limit":256,"endpoint_init_mode":"middle"}
    return {"size":[256,256],"endpoint_init_mode":"middle"}

  def TO_COMPLETED_SPACE_DEFINITION(self,inputObject):
    workingObject = eval(str(inputObject))
    #print("CellElimRunCodecState.prepSpaceDefinition: None was provided, so the default spaceDefinition will be used. The default is " + str(spaceDefinition) + ".")
    if type(workingObject) == list:
      print("CellElimRunCodecState.TO_COMPLETED_SPACE_DEFINITION: the inputObject is a two-item list and will be used as the size.")
      assert len(workingObject) == 2
      assert all(type(item)==int for item in workingObject)
      workingObject = {"size":workingObject}
    elif type(workingObject) == dict:
      pass
    else:
      print("CellElimRunCodecState.TO_COMPLETED_SPACE_DEFINITION: the inputObject is an incompatible type and will be ignored completely.")
      workingObject = {}
    augmentDict(workingObject,self.GET_DEFAULT_SPACE_DEFINITION())
    return workingObject
    

  def headerRoutineBeforeInit(self):
    #create self.headerDict based on self.inputHeaderDictTemplate. In decode mode, this may involve loading embedded values from self.inputDataGen when seeing the template value "EMBED".
    if self.opMode == "encode":
      for key in sorted(self.inputHeaderDictTemplate.keys()):
        inputValue = self.inputHeaderDictTemplate[key]
        if inputValue == "EMBED":
          print("while encoding, header value EMBED will remain EMBED until processing is finished.")
          self.headerDict[key] = inputValue
        else:
          self.headerDict[key] = inputValue
    elif self.opMode == "decode":
      """
      for key in sorted(self.inputHeaderDictTemplate.keys()):
        finalValue = None
        inputValue = self.inputHeaderDictTemplate[key]
        if inputValue == "EMBED":
          finalValue = self.loadHeaderNum()
        else:
          finalValue = inputValue
        self.headerDict[key] = finalValue
      """
      augmentDict(self.headerDict, makeFromTemplateAndSeq(self.inputHeaderDictTemplate, self.inputDataGen,(lambda x: x=="EMBED"))) #@ the problem with this is that it doesn't populate the press header nums list, which would be helpful for knowing whether a parse error has occurred when processBlock is ending.
    else:
      assert False, "invalid opMode."

  def tempApplyHeader(self):
    #this is a TEMPORARY method for quickly applying header values to the CellElimRunCodecState's attributes. Later, the codec will operate by directly reading the header.
    for key in sorted(self.headerDict.keys()):
      if key == "size":
        self.size = self.headerDict[key]
      
  def headerRoutineAfterInit(self):
    #if there are some parts of the header data that can't be decided until after initialization, such as the maximum plainData value, then handle those here.
    if self.opMode == "encode":
      pass
    elif self.opMode == "decode":
      pass
    else:
      assert False, "invalid opMode."

  def headerRoutineAfterProcessBlock(self):
    def resolveAndEncodeHeaderValues(name):
      if name == "dbg_resolve_to_123456789":
        return 123456789
      elif name == "dbg_resolve_to_[123,456]":
        return [123,456]
      else:
        raise NotImplementedError("The CellElimRunCodecState in opMode " + self.opMode + " didn't know how to resolve the header key " + str(name) + " of type " + str(type(name)) + ".")
    if self.opMode == "encode":
      for key in sorted(self.headerDict.keys()):
        if self.headerDict[key] == "EMBED":
          pressHeaderAddition = resolveAndEncodeHeaderValues(key)
          if type(pressHeaderAddition) == int:
            self.saveHeaderNum(pressHeaderAddition)
          elif type(pressHeaderAddition) == list:
            for value in pressHeaderAddition:
              self.saveHeaderNum(value)
          else:
            raise ValueError("The resolved value of the header item " + key + " was not an integer or a list.")
        else:
          pass #skip the item, because this is information that doesn't need to be embedded - either the setting's value is the default value for that setting, the setting is stored globally for the file, or the setting must be remembered by the user.
    elif self.opMode == "decode":
      #print("CellElimRunCodecState.headerRoutineAfterProcessBlock has no job to do when opMode is decode.")
      pass
    else:
      assert False, "invalid opMode."

  def saveHeaderNum(self,value):
    if type(value) != int:
      print("PyCellElimRun.CellElimRunCodecState.saveHeaderNum: Warning: the value being saved is of type " + str(type(value)) + ", not int! Codecs processing the output of this codec may not expect this!")
    self.pressHeaderValues.append(value)
    return value

  def loadHeaderNum(self):
    loadedNum = None
    try:
      loadedNum = next(self.inputDataGen)
    except StopIteration:
      raise ExhaustionError("Ran out of inputData while trying to read the header info.")
    assert loadedNum != None
    self.pressHeaderValues.append(loadedNum)
    return loadedNum


  def setPlaindataItem(self,index,value,dbgCatalogueValue=-260):
    """
    This method offers a simple way to adjust the spline and cellCatalogue simultaneously when new information is learned (such as when it is provided by the block header).
    """
    self.spline[index] = value
    if CellElimRunCodecState.DO_COLUMN_ELIMINATION_OFFICIALLY:
      self.cellCatalogue.eliminateColumn(index,dbgCustomValue=dbgCatalogueValue)


  def getOutput(self):
    if self.opMode == "encode":
      return self.pressHeaderValues + self.pressDataOutputArr
    elif self.opMode == "decode":
      return self.plainDataOutputArr
    else:
      assert False, "invalid opMode."



  def prepSpaceDefinition(self):

    self.cellCatalogue = CellCatalogue(size=self.size)

    endpointInitMode = self.headerDict["endpoint_init_mode"]
    self.spline = Curves.Spline(size=self.size,endpointInitMode=endpointInitMode)

    if "bound_touches" in self.headerDict.keys():
      boundTouches = self.headerDict["bound_touches"]
      if "north" in boundTouches.keys():
        self.setPlaindataItem(boundTouches["north"],self.size[1]-1,dbgCatalogueValue=-238)
      if "south" in boundTouches.keys():
        self.setPlaindataItem(boundTouches["south"],0,dbgCatalogueValue=-239)


  def prepOpMode(self):
    """
    prepare CellEliminationRunCodecState to operate in the specified opMode by creating and initializing only the things that are needed for that mode of operation. This method requires self.size to be defined, so, prepSpaceDefinition should be run before this method.
    """
    if not self.opMode in ["encode","decode"]:
      raise ValueError("That opMode is nonexistent or not allowed.")
    self.plainDataInputArr, self.pressDataInputGen = (None,None)
    self.plainDataOutputArr, self.pressDataOutputArr = (None,None)

    #if not isGen(inputData):
    #  print("PyCellElimRun.CellEliminationRunCodecState.prepOpMode: inputData is not a generator, but to make testing simpler, maybe it should be.")
    
    if self.opMode == "encode":
      self.plainDataInputArr = arrTakeOnly(self.inputDataGen,self.size[0],onExhaustion="warn+partial")
      if not len(self.plainDataInputArr) > 0:
        raise ExhaustionError("The CellEliminationRunCodecState received empty input data while trying to encode.")
      if len(self.plainDataInputArr) < self.size[0]:
        print("PyCellElimRun.CellEliminationRunCodecState.prepOpMode: the input plainData is shorter than the (block) size, so the missing values will be replaced with zeroes.")
      self.plainDataInputArr = ljustedArr(self.plainDataInputArr,self.size[0],fillItem=0)
      assert len(self.plainDataInputArr) == self.size[0]
      self.pressDataOutputArr = []
    elif self.opMode == "decode":
      self.pressDataInputGen = self.inputDataGen
      self.plainDataOutputArr = []
      defaultSampleValue = None
      self.plainDataOutputArr.extend([defaultSampleValue for i in range(self.size[0])])
    else:
      assert False, "invalid opMode."


  def processBlock(self,allowMissingValues=False):
    """
    This method is the host to the encoding or decoding process of the Cell Elimination Run algorithm. This method processes all the data that is currently loaded into or available to the CellElimRunCodecState, which is supposed to be one block of data. It does not know about surrounding blocks of audio or the results of handling them. When finished, it does not clean up after itself in any way - the variables like self.runIndex and self.stepIndex are not reset, so that they can be reviewed later. For this purpose, the main transcode method (PyCellElimRun.cellElimRunBlockTranscode) has an argument to return the entire codec state instead of the output data.
    """
    self.runIndex = 0
    while True:
      if (self.opMode == "encode" and self.runIndex >= len(self.plainDataInputArr)) or (self.opMode == "decode" and self.runIndex >= self.size[0]):
        break
      blockShouldContinue = False
      try:
        blockShouldContinue = self.processRun()
        self.runIndex += 1 #moved here to make it reflect the number of successful runs and not include the last one if it fails.
      except ExhaustionError as ee:
        #print("PyCellElimRun.CellElimRunCodecState.processBlock: an ExhaustionError was thrown by processRun. This is not supposed to happen while processing a lone block. While processing blocks in a stream, it is only supposed to happen when the stream ends.")
        if self.opMode == "encode":
          print("PyCellElimRun.CellElimRunCodecState.processBlock: this ExhaustionError is never supposed to happen while encoding.")
        elif self.opMode == "decode":
          if self.plainDataOutputArr.count(None) == len(self.plainDataOutputArr):
            raise ExhaustionError("CellElimRunCodecState was probably initialized with empty input data.")
          else:
            raise ParseError("CellElimRunCodecState.processRun through an exhaustion error, but the pressDataOutputArr is not empty, so it is unlikely that the codec state was initialized with empty input data.")
        else:
          assert False, "invalid opMode."

      if not blockShouldContinue:
        break
    if self.opMode == "decode" and not allowMissingValues:
      self.interpolateMissingValues(self.plainDataOutputArr)
    self.headerRoutineAfterProcessBlock()
    return


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
    
    runShouldContinue = True
    justStarted = True #so that (if decoding) pressDataInputGen.next() may be called only once and only after the loop starts successfully, since getGenCellCheckOrder yielding no items is one way that the end of processing is signalled.

    for orderEntry in self.getGenCellCheckOrder():
      assert self.stepIndex <= ((self.size[0]+1)*(self.size[1]+1)+2), "This loop has run for an impossibly long time."
    
      if justStarted:
        currentPressDataNum = None
        if self.opMode == "decode":
          try:
            currentPressDataNum = next(self.pressDataInputGen)
          except StopIteration:
            print("PyCellElimRun.CellElimRunCodecState.processRun has run out of pressData input items. This is uncommon.")
            raise ExhaustionError("ran out of pressDataInputGen items while decoding. This is ONLY supposed to happen when the input data is too short to represent a valid CER block.")
            return False #indicate that processing should stop.
        justStarted = False
      cellToCheck = orderEntry[1]
      if orderEntry[0] == "fix":
        #print("order entry " + str(orderEntry) + " will be fixed")
        assert CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE, "fix is not supposed to happen while DO_CRITICAL_COLUMN_ROUTINE is disabled!"
        self.spline[cellToCheck[0]] = cellToCheck[1]
        continue
      assert orderEntry[0] == "visit"
      
      if self.opMode == "encode":
        if self.plainDataInputArr[cellToCheck[0]] == cellToCheck[1]: #if hit...
          self.pressDataOutputArr.append(self.stepIndex) #then a new run length is now known and should be added to the compressed data number list.
          runShouldContinue = False #run should not continue.
        else:
          self.stepIndex += 1
          #runShouldContinue remains True.
      elif self.opMode == "decode":
        if currentPressDataNum == self.stepIndex: #if run is ending...
          self.plainDataOutputArr[cellToCheck[0]] = cellToCheck[1] #then a new hit is known.
          runShouldContinue = False #run should not continue.
        else:
          self.stepIndex += 1
          #runShouldContinue remains True.
      else:
        assert False, "invalid opMode."
      
      if not runShouldContinue:
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
      insort(rankings, [scoreFun(cell), cell], keyFun=self.rankingsInsortKeyFun)
    #this looks like it should be faster, but isn't:
    #rankings = sorted(([scoreFun(extremeCell), extremeCell] for extremeCell in self.cellCatalogue.getExtremeUnknownCells()))
    
    #pre-loop termination check:
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
      
      #in-loop termination check is disabled because if it is possible for this to happen, an index error would be more noticable.
      #if len(rankings) == 0:
      #  print("getGenCellCheckOrder ran out of items in its main loop. This has never happened before.")
      #  assert CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE, "this return is not supposed to happen while DO_CRITICAL_COLUMN_ROUTINE is disabled!"
      #  return
      outputCell = rankings[0][1]
      #dbgPrint("getGenCellCheckOrder: yielding " + str(outputCell)) #debug. 
      yield ("visit", outputCell)
      
      columnCritical = self.cellCatalogue.eliminateCell(outputCell)
      replacementCell = self.cellCatalogue.clampCell(outputCell)
      assert str(outputCell) != str(replacementCell) #debug.
      
      if columnCritical and CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE:
        #print("column is critical for " + str(outputCell) + ". column limits are " + str(self.cellCatalogue.limits[outputCell[0]]) + ".")
        self.cellCatalogue.eliminateColumn(outputCell[0],dbgCustomValue=-7)
        #print("the replacementCell " + str(replacementCell) + " is now assumed to be a duplicate and will not be insorted into the rankings.")
        yield ("fix",replacementCell)
        del rankings[0]
      else:
        del rankings[0]
        insort(rankings, [scoreFun(replacementCell), replacementCell], keyFun=self.rankingsInsortKeyFun)
        #extremely slow:
        #rankings[0] = [scoreFun(replacementCell), replacementCell]
        #bubbleSortSingleItemRight(rankings,0)
    print("getGenCellCheckOrder has ended.")



def cellElimRunBlockTranscode(inputData,opMode,interpolationMode,spaceDefinition,dbgReturnCERCS=False):
  if type(spaceDefinition) == list:
    if len(spaceDefinition) != 2 or (None in spaceDefinition):
      raise ValueError("spaceDefinition is a list that can't be converted to a dictionary.")
    assert len(spaceDefinition) == 2
    print("spaceDefinition will be expanded into a dictionary. The use of a 2-item list for a spaceDefinition is deprecated.")
    spaceDefinition = {"size":spaceDefinition,"endpointInitMode":"middle"}
  assert opMode in ["encode","decode"]

  tempCERCS = CellElimRunCodecState(inputData,opMode,interpolationMode=interpolationMode,spaceDefinition=spaceDefinition)
  tempCERCS.processBlock()
  if dbgReturnCERCS:
    return tempCERCS
  else:
    return tempCERCS.getOutput()
  assert False


def genCellElimRunBlockSeqTranscode(inputData,opMode,interpolationMode,spaceDefinition,segmentInput=False,segmentOutput=False):
  if not isGen(inputData):
    print("PyCellElimRun.genCellElimRunBlockSeqTranscode: inputData is not a generator, so it will be converted to one.")
  inputData = makeGen(inputData)
  while True:
    currentInputData = None
    if segmentInput:
      currentInputData = next(inputData)
    else:
      currentInputData = inputData
    currentResult = None
    try:
      currentResult = cellElimRunBlockTranscode(currentInputData,opMode,interpolationMode,spaceDefinition)
    except ExhaustionError:
      break
    assert currentResult != None
    if segmentOutput:
      yield currentResult
    else:
      for outputItem in currentResult:
        yield outputItem
  print("PyCellElimRun.genCellElimRunBlockSeqTranscode: ended.")



cellElimRunBlockCodec = CodecTools.Codec(None,None,transcodeFun=cellElimRunBlockTranscode,zeroSafe=True)

cellElimRunBlockSeqCodec = CodecTools.Codec(None,None,transcodeFun=genCellElimRunBlockSeqTranscode,zeroSafe=True)





#tests:

#these tests are disabled because they break with different sort methods.
"""
testResult = cellElimRunBlockTranscode([2,2,2,2,2],"encode","linear",{"size":[5,5]})
assert testResult[0] == 20
assert sum(testResult[1:]) == 0
assert cellElimRunBlockTranscode([20],"decode","linear",{"size":[5,5]}) == [2,2,2,2,2]

testResult = cellElimRunBlockTranscode([5,6,7,6,5],"encode","linear",{"size":[5,10],"endpoint_init_mode":"middle"})
assert testResult[:2] == [32,10]
assert sum(testResult[2:]) == 0
assert cellElimRunBlockTranscode([32,10,0,0,0],"decode","linear",{"size":[5,10],"endpoint_init_mode":"middle"}) == [5,6,7,6,5]

testResult = makeArr(genCellElimRunBlockSeqTranscode([5,6,7,6,5,5,6,7,6,5],"encode","linear",{"size":[5,10],"endpoint_init_mode":"middle"}))
assert testResult == [32,10,32,10]
assert makeArr(genCellElimRunBlockSeqTranscode([32,10,32,10],"decode","linear",{"size":[5,10],"endpoint_init_mode":"middle"})) == [5,6,7,6,5,5,6,7,6,5]
"""

for testEndpointInitMode in [["middle","middle"],["zero","maximum"],["zero","zero"]]:
  assert CodecTools.roundTripTest(cellElimRunBlockCodec.clone(extraArgs=["linear",{"size":(5,101),"endpoint_init_mode":testEndpointInitMode}]),[5,0,100,75,50])



