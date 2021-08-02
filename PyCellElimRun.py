"""

PyCellElimRun.py by John Dorsey.

PyCellElimRun.py contains tools for converting audio samples into a sequence of integers that is more easily compressed.

"""

import math

import Curves
import CodecTools

from IntArrMath import intify
from PyArrTools import insort

from Codes import ParseError
from PyGenTools import isGen,makeArr,makeGen,arrTakeOnly,ExhaustionError
from PyArrTools import ljustedArr, bubbleSortSingleItemRight
import PyDictTools
from PyDictTools import augmentDict, augmentedDict, makeFlatKeySeq


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


  def toPrettyStr(self):
    alignmentError = False
    result = "PyCellElimRun.CellCatalogue.toPrettyStr generated string representation."
    sidebarWidth = len(str(self.size[1]))
    for y in range(self.size[1]-1,-1,-1):
      result += "\n"+str(y).rjust(sidebarWidth," ")+": "
      for x in range(self.size[0]):
        addition = str(self.getCellStatus((x,y)))
        if len(addition) != 1:
          alignmentError = True
        result += addition
    result += "\nalignmentError="+str(alignmentError)
    return result

  def getCellStatus(self,cell):
    raise NotImplementedError("CellCatalogue feature getCellStatus was not implemented.")
  def countUnknowns(self): #this could just be tracked by the methods that eliminate cells, but that could be less reliable.
    raise NotImplementedError("CellCatalogue feature countUnknowns was not implemented.")
  def eliminateColumn(self,columnIndex,dbgCustomValue=-1):
    raise NotImplementedError("CellCatalogue feature eliminateColumn was not implemented.")
  def eliminateCell(self,cell):
    raise NotImplementedError("CellCatalogue feature eliminateCell was not implemented.")
  def genExtremeUnknownCells(self,sides=None): #a function to get a list of all cells at the edges of the area of cells that have not been eliminated (hopefully totalling two cells per column (sample)).
    raise NotImplementedError("CellCatalogue feature genExtremeUnknownCells was not implemented.")
  def clampCell(self,cell): #move a cell's value to make it comply with the catalogue of eliminated cells.
    raise NotImplementedError("CellCatalogue feature clampCell was not implemented.")



class CellCatalogueColumn(CellCatalogue):
    
  def imposeMinimum(self,newMinimum):
    raise NotImplementedError()
  
  def imposeMaximum(self,newMaximum):
    raise NotImplementedError()
    
  def getCellStatus(self,cellHeight):
    raise NotImplementedError()
    
  def toPrettyStr(self):
    alignmentError = False
    result = "CCCSTR:"
    for y in range(self.size):
      addition = str(self.getCellStatus(y))
      if len(addition) != 1:
        alignmentError = True
      result += addition
    result += ",alignmentError="+str(alignmentError)
    return result

  def countUnknowns(self):
    print("CellCatalogueColumn.countUnknowns: warning: falling back to potentially slow method because the subclass does not have countUnknowns.")
    return sum((self.getCellStatus(i) == CellCatalogue.UNKVAL) for i in range(self.size))

  def eliminateColumn(self,dbgCustomValue=-1):
    raise NotImplementedError()

  def eliminateCell(self,cellHeight):
    raise NotImplementedError()

  def genExtremeUnknownCells(self,sides=None):
    raise NotImplementedError()

  def clampCell(self,cellHeight):
    raise NotImplementedError()






class GridCellCatalogueColumn(CellCatalogueColumn):

  def __init__(self, size=0):
    self.size = size 
    self.grid = [CellCatalogue.UNKVAL for value in range(0,self.size)]

  def imposeMinimum(self,newMinimum):
    #remember to check whether critical.
    raise NotImplementedError()
  
  def imposeMaximum(self,newMaximum):
    #remember to check whether critical.
    raise NotImplementedError()
    
  def getCellStatus(self,cellHeight):
    return self.grid[cellHeight]

  def eliminateColumn(self,dbgCustomValue=-1):
    print("GridCellCatalogueColumn.eliminateColumn called for column " + str(columnIndex) + " and dbgCustomValue " + str(dbgCustomValue) + ". The dbgCustomValue will be ignored.")
    for i in range(len(self.grid)):
      self.grid[i] = CellCatalogue.ELIMVAL

  def eliminateCell(self,cellHeight):
    if self.getCellStatus(cellHeight) == CellCatalogue.ELIMVAL:
      print("PyCellElimRun.GridCellCatalogueColumn.eliminateCell: The cell " + str(cellHeight) + " is already eliminated. eliminateCell should not be called on cells that are already eliminated! But let's see what happens if the program continues to run.")
    self.grid[cellHeight] = CellCatalogue.ELIMVAL
    print("PyCellElimRun.GridCellCatalogueColumn.eliminateCell: warning: critical column support does not exist here yet!")
    return False #indicate that the column is not critical.



class LimitsCellCatalogueColumn(CellCatalogueColumn):

  def __init__(self, size=0): #size might be off by one.
    self.size = size #first component is sample index range end; the range currently must start at zero. second component is sample value range; the range currently must start at zero.
    self.limits = [-1,self.size]
    
  def imposeMinimum(self,newMinimum):
    self.limits[0] = max(self.limits[0],newMinimum-1)
    assert self.limits[1]-self.limits[0] > 4, "this could cause critical column routine problems."
  
  def imposeMaximum(self,newMaximum):
    self.limits[1] = min(self.limits[1],newMaximum+1)
    assert self.limits[1]-self.limits[0] > 4, "this could cause critical column routine problems."

  def getCellStatus(self,cellHeight):
    return CellCatalogue.UNKVAL if (self.limits[0] < cellHeight) and (cellHeight < self.limits[1]) else CellCatalogue.ELIMVAL
    
  def toPrettyStr(self):
    alignmentError = False
    result = "CCCSTR:"
    for y in range(self.size):
      addition = str(self.getCellStatus(y))
      if len(addition) != 1:
        alignmentError = True
      result += addition
    result += ",alignmentError="+str(alignmentError)
    return result

  def countUnknowns(self):
    return max(0,self.limits[1]-self.limits[0]-1)

  def eliminateColumn(self,dbgCustomValue=-1):
    self.limits[0] = dbgCustomValue
    self.limits[1] = dbgCustomValue

  def eliminateCell(self,cellHeight):
    if self.getCellStatus(cellHeight) == CellCatalogue.ELIMVAL:
      print("PyCellElimRun.LimitsCellCatalogueColumn.eliminateCell: The cell {} is already eliminated. eliminateCell should not be called on cells that are already eliminated (the limits for this column are {})! But let's see what happens if the program continues to run.".format(cellHeight,self.limits))
    if cellHeight == self.limits[0]+1:
      self.limits[0] += 1
    elif cellHeight == self.limits[1]-1:
      self.limits[1] -= 1
    else:
      print("PyCellElimRun.LimitsCellCatalogueColumn.eliminateCell: The cell {} can't be eliminated, because it is not at the edge of the area of eliminated cells (the limits for this column are {})! but let's see what happens if the program continues to run.".format(cellHeight,self.limits))
    if self.limits[0] + 2 == self.limits[1]:
      return True #indicate that the column is critical.
    return False #indicate that the column is not critical.

  def genExtremeUnknownCells(self,sides=None): #a function to get a list of all cells at the edges of the area of cells that have not been eliminated (hopefully totalling two cells per column (sample)).
    if sides == None:
      sides = [True,True] #sides[0] = include bottom cells?, sides[1] = include top cells?. if both are false, a cell can only be part of the output if it is the lone unknown cell in its column.
    if self.limits[1]-self.limits[0] < 2: #if there is no space between the floor and ceiling of what has not been eliminated...
      if self.limits[1]-self.limits[0] == 1:
        print("PyCellElimRun.LimitsCellCatalogueColumn.genExtremeUnknownCells: warning: column was improperly eliminated! does this have something to do with imposeMinimum?")
      return #nothing in this column.
    elif self.limits[1]-self.limits[0] == 2: #special case to avoid registering the same cell twice when the cell just above the floor and just below the ceiling are the same cell. At the time of this writing, I don't know whether this will ever happen because I haven't decided how the CellCatalogue will/should behave in columns where the sample's value is known.
      yield self.limits[0]+1
      print("WARNING: PyCellElimRun.LimitsCellCatalogueColumn.genExtremeUnknownCells had to merge two cells in its result, meaning that the column could have been eliminated earlier! does this have something to do with imposeMinimum?")
    else:
      if sides[0]:
        yield self.limits[0]+1
      if sides[1]:
        yield self.limits[1]-1
    return

  def clampCell(self,cellHeight): #move a cell's value to make it comply with the catalogue of eliminated cells.
    assert self.limits[1]-self.limits[0] > 1, "This column can no longer clamp cells, because it has no unknown space! Its limits are {}.".format(self.limits)
    result = clamp(cellHeight,(self.limits[0]+1,self.limits[1]-1))
    assert result != cellHeight, "this function failed."
    return result










class ColumnCellCatalogue(CellCatalogue):

  def __init__(self, storageMode="limits", size=[0,0]): #size might be off by one.
    self.size = size #first component is sample index range end; the range currently must start at zero. second component is sample value range; the range currently must start at zero.
    self.storageMode = storageMode
    def dataInitializer(initSize):
      if len(initSize) == 1:
        if storageMode == "limits":
          return LimitsCellCatalogueColumn(size=initSize[-1])
        elif storageMode == "grid":
          return GridCellCatalogueColumn(size=initSize[-1])
        else:
          raise KeyError("storageMode key {} is invalid.".format(repr(storageMode)))
      return [dataInitializer(initSize[1:]) for i in range(initSize[0])]
    self.data = dataInitializer(self.size)
    
  def imposeMinimum(self,newMinimum):
    for columnID,column in self.iterColumnsAndIDs():
      column.imposeMinimum(newMinimum)
    
  def imposeMaximum(self,newMaximum):
    for columnID,column in self.iterColumnsAndIDs():
      column.imposeMaximum(newMaximum)
    
  def toPrettyStr(self):
    result = ""
    for columnID,column in self.iterColumnsAndIDs():
      result += "\n"+str(columnID)+":"+column.toPrettyStr()
    return result

  def getColumn(self,columnID):
    if len(self.size) == 2 and type(columnID) == int:
      return self.data[columnID]
    workingSection = self.data
    for element in columnID:
      workingSection = workingSection[element]
    return workingSection
    
  def iterColumnsAndIDs(self):
    def deepIterator(inputItem):
      if type(inputItem) == list:
        for i,subItem in enumerate(inputItem):
          if isinstance(subItem,LimitsCellCatalogueColumn):
            yield [i, subItem]
          elif type(subItem) == list:
            subItemIterator = deepIterator(subItem)
            for item in subItemIterator:
              assert type(item) == list
              yield [i] + item
          else:
            raise ValueError("some item in the structure is of an invalid type: type {} at index {}.".format(repr(type(subItem)),str(i)))
      else:
        raise ValueError("deepIterator called on invalid type.")
    return ((outputArr[:-1],outputArr[-1]) for outputArr in deepIterator(self.data))
    
  def getCellStatus(self,cell):
    return self.getColumn(cell[:-1]).getCellStatus(cell[-1])

  def countUnknowns(self): #this could just be tracked by the methods that eliminate cells, but that could be less reliable.
    raise NotImplementedError()

  def eliminateColumn(self,columnID,dbgCustomValue=-1):
    self.getColumn(columnID).eliminateColumn(dbgCustomValue=dbgCustomValue)
    
  def isCellInBounds(self,cell):
    for i,cellElement in enumerate(cell):
      if cellElement < 0 or cellElement >= self.size[i]:
        return False
    return True
    
  def diagnoseCell(self,cell):
    #this method may be used to verify that there is nothing obviously wrong with a cell that has already caused a minor problem somewhere else.
    if not self.isCellInBounds(cell):
      try:
        raise ValueError("Cell {} is out of bounds. Its column limits are {}.".format(cell,self.getColumn(cell[:-1]).limits))
      except IndexError:
        raise ValueError("Cell {} is out of bounds on some axis other than vertical.".format(cell))

  def eliminateCell(self,cell):
    #this method may someday make adjustments to fourier-transform-based predictions, if it eliminates a cell that any fourier transform in use would have guessed as an actual value. To do this, access to the Spline would be needed.
    relevantColumn = self.getColumn(cell[:-1])
    return relevantColumn.eliminateCell(cell[-1])

  def genExtremeUnknownCells(self,sides=None): #a function to get a list of all cells at the edges of the area of cells that have not been eliminated (hopefully totalling two cells per column (sample)).
    if sides == None:
      sides = [True,True] #sides[0] = include bottom cells?, sides[1] = include top cells?. if both are false, a cell can only be part of the output if it is the lone unknown cell in its column.
    #result = []
    for columnID, column in self.iterColumnsAndIDs():
      for extremeUnknownCell in column.genExtremeUnknownCells(sides=sides):
        yield columnID + [extremeUnknownCell]

  def clampCell(self,cell): #move a cell's value to make it comply with the catalogue of eliminated cells.
    return cell[:-1] + [self.getColumn(cell[:-1]).clampCell(cell[-1])]














class CellTargeter:
  def __init__(self,size,spline,cellCatalogue,scoreFun):
    #print("CellTargeter initialized.")
    self.size = size
    self.spline = spline
    self.cellCatalogue = cellCatalogue
    self.prepScoreMode(scoreFun)
    self.rankings = None
    self.rankingsInsortKeyFun = (lambda item: item[0]) #used by genCellCheckOrder.
    
    
  def prepScoreMode(self,scoreFun): # -> None:
    if type(scoreFun)==str:
      if scoreFun=="vertical_distance":
        def scoreFun(cell):
          return self.size[1]-abs(self.spline[cell[0]]-cell[1]) #bad offset? probably not.
      elif scoreFun in ["absolute_distance", "bilog_distance","manhattan_distance"]:
        distanceFun = None
        if scoreFun == "absolute_distance":
          distanceFun = (lambda x, y: (x**2 + y**2)**0.5)
        elif scoreFun == "bilog_distance":
          distanceFun = (lambda x, y: (math.log(x+1)**2 + math.log(y+1)**2)**0.5)
        elif scoreFun == "manhattan_distance":
          distanceFun = (lambda x, y: x + y)
        else:
          assert False
        def scoreFun(cell):
          minKnownDist, curRiseLeft, curRiseRight, offset = distanceFun(0,abs(self.spline[cell[0]]-cell[1])), self.size[1], self.size[1], 1
          while distanceFun(offset,0) < minKnownDist:
            if cell[0]-offset >= 0:
              curRiseLeft = abs(self.spline[cell[0]-offset]-cell[1])
            if cell[0]+offset < self.size[0]:
              curRiseRight = abs(self.spline[cell[0]+offset]-cell[1])
            minKnownDist, offset = min(minKnownDist,distanceFun(offset,min(curRiseLeft,curRiseRight))), offset+1
          return self.size[1]-minKnownDist
      else:
        raise KeyError("unrecognized scoreFun key.")
    else:
      assert type(scoreFun) == type(lambda x: x) #works in python3, untested in python2.
    self.scoreFun = scoreFun

  def newRankings(self):
    return sorted(([self.scoreFun(extremeCell), extremeCell] for extremeCell in self.cellCatalogue.genExtremeUnknownCells()),key=self.rankingsInsortKeyFun)
    
  def buildRankings(self):
    self.rankings = self.newRankings()
    
  def refreshRankings(self):
    for i,rankingsEntry in enumerate(self.rankings):
      self.rankings[i][0] = self.scoreFun(rankingsEntry[1])
    self.rankings.sort(key=self.rankingsInsortKeyFun)
    #print("CellTargeter: doing slow check of refreshed rankings!")
    #assert self.rankings == self.newRankings() #@ slow
    
  def optionsExist(self):
    return len(self.rankings) > 0
  
  def genCellCheckOrder(self):
    #assert hasattr(self,"scoreFun")
    #assert hasattr(self,"rankingsInsortKeyFun")
    
    #pre-loop termination check:
    if not self.optionsExist():
      #self.log("genCellCheckOrder ran out of items before its main loop.")
      assert CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE, "this return is not supposed to happen while DO_CRITICAL_COLUMN_ROUTINE is disabled!"
      return
      
    while True: #the generator loop.
      
      #in-loop rankings depletion check is disabled because if it is possible for this to happen, an index error would be more noticable. Also, performance reasons.
      
      outputCell = self.rankings[0][1]
      #dbgPrint("getGenCellCheckOrder: yielding " + str(outputCell)) #debug. 
      yield ("visit", outputCell)
      
      columnCritical = self.cellCatalogue.eliminateCell(outputCell)
      replacementCell = self.cellCatalogue.clampCell(outputCell)
      assert str(outputCell) != str(replacementCell) #debug.
      
      if columnCritical and CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE:
        #print("column is critical for " + str(outputCell) + ". column limits are " + str(self.cellCatalogue.limits[outputCell[0]]) + ".")
        self.cellCatalogue.eliminateColumn(outputCell[:-1],dbgCustomValue=-777)
        #print("the replacementCell " + str(replacementCell) + " is now assumed to be a duplicate and will not be insorted into the rankings.")
        yield ("fix",replacementCell)
        del self.rankings[0]
      else:
        del self.rankings[0]
        insort(self.rankings, (self.scoreFun(replacementCell), replacementCell), keyFun=self.rankingsInsortKeyFun)
        #extremely slow:
        #rankings[0] = [scoreFun(replacementCell), replacementCell]
        #bubbleSortSingleItemRight(rankings,0)
    assert False, "genCellCheckOrder has ended. This has never happened before."




class CellElimRunCodecState:
  """
  the CellElimRunCodecState is responsible for owning and operating a Spline and CellCatalogue, and using them to either encode or decode data. Encoding and decoding are supposed to share as much code as possible. This makes improving or expanding the core mathematics of the compression vastly easier - as long as the important code is only ever called in identical ways by both the encoding and the decoding methods, any change to the method of predicting unknown data from known data won't break the symmetry of those methods.
  """
  
  #the following column-related options control whether entire columns of unknown or un-visited cells can be eliminated from the cellCatalogue at various times that the cellCatalogue would NOT eliminate them on its own. For instance, the algorithm always eliminates the cellCatalogue column when it hits a live cell, but it's also possible to eliminate a column when that column has two unknown cells and one of them is visited but not hit - this is the purpose of the critical column routine.
  DO_COLUMN_ELIMINATION_AT_GEN_END = True #this should not be turned off, because it changes the output in a way that isn't simple. Compression Ratio seems to be better with it turned on, but this wasn't expected, so the loss of compression with it turned off is probably a bug. Changing this parameter shouldn't break symmetry.
  DO_CRITICAL_COLUMN_ROUTINE = True #this is responsible for most of the process of ensuring that trailing zeroes are trimmed and CER blocks may be self-delimiting.
  DO_COLUMN_ELIMINATION_OFFICIALLY = True #This controls whether column elimination can be performed by setPlaindataSample. Some of the process of making CER blocks self-delimiting depends on the use of setPlaindataSample with the expectation that this is set to True.
  
  DEFAULT_HEADER_DICT_TEMPLATE = {"interpolation_mode":"linear", "score_mode":"vertical_distance", "space_definition":{"size":[256, 256], "bounds":{}, "bound_touches":{}, "endpoint_init_mode":"middle"}}
  ALLOW_BOUND_ASSUMPTIONS = False #allow bound touch locations to be specified in the header without also providing the locations of bounaries in the header info - in this case, the bounaries are assumed based on "size". In case bounds were excluded from the header on accident, this assumption is incorrect, the plaindata values that are set based on the bound touch parameters will be set incorrectly, and the transcoding process will either crash or produce garbage.


  def __init__(self, inputData, opMode, inputHeaderDictTemplate):
    """
    The initialization method takes arguments that resemble a structured header as much as possible. In the decode phase, it fills in missing data in headerDict by decoding a few pressdata items as parameters. In the encode phase, it fills in missing data in headerDict by analyzing the provided plaindata, encodes these parameters, and prepends them to the pressdata it will output.
    The initialization method also creates all of the attributes that processBlock needs to start running right away. By the time processBlock is called, there is no more initialization to do.
    """
    self.initializeByDefault()
    
    self.inputDataGen = makeGen(inputData) #this is necessary to make it so that prepSpaceDefinition can take some items from the front, before prepOpMode does anything.
    self.opMode = opMode #initialized here instead of in prepOpMode because it is needed by prepSpaceDefinition.

    self.headerDictTemplate = self.TO_COMPLETED_HEADER_DICT_TEMPLATE(inputHeaderDictTemplate)
    self.headerDict = {}
    self.pressHeaderValues = [] #this is to remain empty until populated by the header loader. it _may_ be populated if the headerDictTemplate tells it to embed or access header info from the regular inputData.
    augmentDict(self.headerDict, self.headerDictTemplate, recursive=True, recursiveTypes=[list,dict]) #this shouldn't be long-term. Once header tool design is finished, items will be absent from the header until they are resolved.
    
    self.headerPhaseRoutine("BEFORE_PREP_GROUP")

    self.prepOpMode()
    self.headerPhaseRoutine("AFTER_PREP_OP_MODE")
    self.headerPhaseRoutine("AFTER_PREP_OP_MODE:1")
    self.prepSpaceDefinition()
    self.headerPhaseRoutine("AFTER_PREP_SPACE_DEFINITION")
    self.spline.setInterpolationMode(self.headerDict["interpolation_mode"])
      
    self.headerPhaseRoutine("AFTER_PREP_GROUP")

    self.runIndex = None #the run index determines which integer run length from the pressdata run length list is being read and counted towards with the stepIndex variable as a counter while decoding, or, it is the length of the current list of such integer run lengths that is being built by encoding.
    self.stepIndex = None #the step index counts towards the value of the current elimination run length - either it is compared to a known elimination run length in order to know when to terminate and record a cell as filled while decoding, or it counts and holds the new elimination run length value to be stored while encoding.

    self.applyHeader()
    assert self.size[0] == len(self.spline.data)



  def initializeByDefault(self):
    """ initializeByDefault initializes things that can't be changed by class settings and don't depend on header information. """
    self.plainDataInputArr, self.pressDataInputGen = (None,None)
    self.pressDataOutputArr = None
    self.plainDataOutputArr = None
    self.TO_COMPLETED_HEADER_DICT_TEMPLATE = (lambda inputObject: augmentedDict(inputObject, CellElimRunCodecState.DEFAULT_HEADER_DICT_TEMPLATE))
    
  def applyHeader(self):
    for keyA in makeFlatKeySeq(self.headerDict):
      if keyA == "space_definition":
        for keyB in makeFlatKeySeq(self.headerDict[keyA]):
          if keyB == "size":
            self.size = self.headerDict[keyA][keyB]
            self.stepIndexTimeout = ((self.size[0]+1)*(self.size[1]+1)+2)
            
  def log(self,text):
    if not hasattr(self,"logStr"):
      self.logStr = ""
    self.logStr += str(text) + "\n"
    return text
    
    
    
  def headerRoutinePathwiseOracleFun(self, inputPath, inputValue):
    #print("headerRoutineGeneralPathwiseOracleFun called with args " + str([inputPath,inputValue]) + ".")
    result = inputValue
    if inputPath[-3:] == ["space_definition","size",1]:
      result = max(self.plainDataInputArr)+1
    elif inputPath[-3:-1] == ["space_definition","bound_touches"]:
      assert len(self.headerDict["space_definition"]["size"]) == 2, "space_definition.bound_touches is only available for 2D data."
      try:
        try:
          bounds = self.headerDict["space_definition"]["bounds"]
        except KeyError as ke:
          print(self.headerDictTemplate)
          print(self.headerDict)
          raise ke
        if inputPath[-1] == "north":
          if "upper" not in bounds.keys():
            warningText = "north bound touch should only be embedded if the upper bound is also embedded."
            if CellElimRunCodecState.ALLOW_BOUND_ASSUMPTIONS:
              print("PyCellElimRun.CellElimRunCodecState.headerRoutinePathwiseOracleFun: warning: " + warningText)
              print("Assuming upper bound is size[-1]...")
              bounds["upper"] = self.headerDict["space_definition"]["size"][-1]
            else:
              raise ValueError(warningText)
          result = self.plainDataInputArr.index(bounds["upper"]-1)
        elif inputPath[-1] == "south":
          if "lower" not in bounds.keys():
            warningText = "south bound touch should only be embedded if the upper bound is also embedded."
            if CellElimRunCodecState.ALLOW_BOUND_ASSUMPTIONS:
              print("PyCellElimRun.CellElimRunCodecState.headerRoutinePathwiseOracleFun: warning: " + warningText)
              print("Assuming lower bound is 0...")
              bounds["lower"] = 0
            else:
              raise ValueError(warningText)
          result = self.plainDataInputArr.index(bounds["lower"])
        elif inputPath[-1] == "east":
          result = self.plainDataInputArr[-1]
        elif inputPath[-1] == "west":
          result = self.plainDataInputArr[0]
        else:
          raise ValueError("unknown header item in space_definition.bound_touches.")
      except IndexError:
        raise IndexError("There is no such boundary touch as {}.".format(repr(inputPath[-1])))
    elif inputPath[-3:-1] == ["space_definition","bounds"]:
      assert len(self.headerDict["space_definition"]["size"]) == 2, "space_definition.bounds is currently only available for 2D data."
      if inputPath[-1] == "lower":
        result = min(self.plainDataInputArr)
      elif inputPath[-1] == "upper":
        result = max(self.plainDataInputArr) + 1
      else:
        raise ValueError("unknown header item in space_definition.bounds.")
    elif inputPath[-1] == "dbg_resolve_to_123456789":
      result = 123456789
    elif inputPath[-1] == "dbg_resolve_to_[123,456]":
      result = [123,456]
    else:
      print(self.log("PyCellElimRun.CellElimRunCodecState.headerRoutinePathwiseOracleFun: warning: no substitute was found for (inputPath,inputValue)="+str((inputPath,inputValue))+"."))
    return self.saveHeaderValue(result) #assume it should be saved, and save it.


  def headerPhaseRoutine(self,phaseName):
    self.log("header phase " + phaseName +" started with opMode=" + str(self.opMode) + " and headerDict=" + str(self.headerDict)+".")
    #create self.headerDict based on self.inputHeaderDictTemplate. In decode mode, this may involve loading embedded values from self.inputDataGen when seeing the template value "EMBED".
    phaseEmbedCode = "EMBED:"+phaseName
    #PyDictTools.replace(self.headerDict,"EMBED",phaseEmbedCode)
    
    if self.opMode == "encode":
      pathwiseOracleFun = self.headerRoutinePathwiseOracleFun
      valueTriggerFun = (lambda x: x==phaseEmbedCode)
      PyDictTools.writeFromTemplateAndPathwiseOracle(self.headerDict, self.headerDictTemplate, pathwiseOracleFun, valueTriggerFun)
    elif self.opMode == "decode":
      valueTriggerFun = (lambda x: x==phaseEmbedCode)
      PyDictTools.writeFromTemplateAndNextFun(self.headerDict, self.headerDictTemplate, self.loadHeaderValue, valueTriggerFun) #@ the problem with this is that it doesn't populate the press header nums list, which would be helpful for knowing whether a parse error has occurred when processBlock is ending.
    else:
      assert False, "invalid opMode."
    self.log("header phase " + phaseName +" ended with opMode=" + str(self.opMode) + " and headerDict=" + str(self.headerDict)+".")


  def saveHeaderValue(self,value):
    if type(value) != int:
      print(self.log("PyCellElimRun.CellElimRunCodecState.saveHeaderNum: Warning: the value being saved is of type " + str(type(value)) + ", not int! Codecs processing the output of this codec may not expect this!"))
    self.pressHeaderValues.append(value)
    return value

  def loadHeaderValue(self):
    loadedNum = None
    try:
      loadedNum = next(self.inputDataGen)
    except StopIteration:
      raise ExhaustionError("Ran out of inputData while trying to read the header info.")
    assert loadedNum != None
    self.pressHeaderValues.append(loadedNum)
    return loadedNum


  def setPlaindataItem(self, index, value, eliminateColumn=None, modifyOutputArr=False, dbgCatalogueValue=-260):
    """
    This method offers a simple way to adjust the spline and cellCatalogue simultaneously when new information is learned (such as when it is provided by the block header).
    """
    self.spline[index] = value
    if (eliminateColumn == None and CellElimRunCodecState.DO_COLUMN_ELIMINATION_OFFICIALLY) or (eliminateColumn):
      self.cellCatalogue.eliminateColumn(index, dbgCustomValue=dbgCatalogueValue)
    if modifyOutputArr:
      if self.opMode == "decode":
        self.plainDataOutputArr[index] = value


  def getOutput(self):
    if self.opMode == "encode":
      return self.pressHeaderValues + self.pressDataOutputArr
    elif self.opMode == "decode":
      return self.plainDataOutputArr
    else:
      assert False, "invalid opMode."



  def prepSpaceDefinition(self): # -> None:
    size = self.headerDict["space_definition"]["size"]
    
    self.cellCatalogue = ColumnCellCatalogue(size=size)

    endpointInitMode = self.headerDict["space_definition"]["endpoint_init_mode"]
    self.spline = Curves.Spline(size=size, endpointInitMode=endpointInitMode)
    
    if "bounds" in self.headerDict["space_definition"].keys():
      bounds = self.headerDict["space_definition"]["bounds"]
      if "lower" in bounds.keys():
        self.cellCatalogue.imposeMinimum(bounds["lower"])
      if "upper" in bounds.keys():
        self.cellCatalogue.imposeMaximum(bounds["upper"]-1)

    if "bound_touches" in self.headerDict["space_definition"].keys():
      boundTouches = self.headerDict["space_definition"]["bound_touches"]
      if "north" in boundTouches.keys():
        self.setPlaindataItem(boundTouches["north"], self.headerDict["space_definition"]["bounds"]["upper"]-1, dbgCatalogueValue=-518)
      if "south" in boundTouches.keys():
        self.setPlaindataItem(boundTouches["south"], self.headerDict["space_definition"]["bounds"]["lower"], dbgCatalogueValue=-520)
      if "east" in boundTouches.keys():
        self.setPlaindataItem(size[0]-1, boundTouches["east"], dbgCatalogueValue=-522)
      if "west" in boundTouches.keys():
        self.setPlaindataItem(0, boundTouches["west"], dbgCatalogueValue=-524)
        

  def prepOpMode(self): # -> None:
    """
    prepare CellEliminationRunCodecState to operate in the specified opMode by creating and initializing only the things that are needed for that mode of operation.
    """
    if not self.opMode in ["encode","decode"]:
      raise ValueError("That opMode is nonexistent or not allowed.")
      
    size = self.headerDict["space_definition"]["size"]

    if self.opMode == "encode":
      self.plainDataInputArr = arrTakeOnly(self.inputDataGen,size[0],onExhaustion="partial")
      if not len(self.plainDataInputArr) > 0:
        raise ExhaustionError("The CellEliminationRunCodecState received empty input data while trying to encode.")
      if len(self.plainDataInputArr) < size[0]:
        print(self.log("PyCellElimRun.CellEliminationRunCodecState.prepOpMode: the input plainData is shorter than the (block) size, so the missing values will be replaced with zeroes."))
      self.plainDataInputArr = ljustedArr(self.plainDataInputArr,size[0],fillItem=0)
      assert len(self.plainDataInputArr) == size[0]
      self.pressDataOutputArr = []
    elif self.opMode == "decode":
      self.pressDataInputGen = self.inputDataGen
      self.plainDataOutputArr = []
      defaultSampleValue = None
      self.plainDataOutputArr.extend([defaultSampleValue for i in range(size[0])])
    else:
      assert False, "invalid opMode."
      
  

  def interpolateMissingValues(self,targetArr):
    if None in targetArr:
      self.log("PyCellElimRun.CellElimRunCodecState.interpolateMissingValues: " + str(targetArr.count(None)) + " missing values exist and will be filled in using the interpolation settings of the spline object that was used for transcoding.")
      self.log("The missing values are at the indices " + str([i for i in range(len(targetArr)) if targetArr[i] == None]) + ".")
      for index in range(len(targetArr)):
        if targetArr[index] == None:
          targetArr[index] = self.spline[index]
    else:
      self.log("PyCellElimRun.CellElimRunCodecState.interpolateMissingValues: no missing values exist.")
      pass

  
  def processBlock(self,allowMissingValues=False):
    """
    This method is the host to the encoding or decoding process of the Cell Elimination Run algorithm. This method processes all the data that is currently loaded into or available to the CellElimRunCodecState, which is supposed to be one block of data. It does not know about surrounding blocks of audio or the results of handling them. When finished, it does not clean up after itself in any way - the variables like self.runIndex and self.stepIndex are not reset, so that they can be reviewed later. For this purpose, the main transcode method (PyCellElimRun.cellElimRunBlockTranscode) has an argument to return the entire codec state instead of the output data.
    """
    #assert allowMissingValues == True
    self.processAllRuns()
    if self.opMode == "decode" and not allowMissingValues:
      self.interpolateMissingValues(self.plainDataOutputArr)
    
    self.headerPhaseRoutine("AFTER_PROCESS_BLOCK")
    return


  def processAllRuns(self):
    self.runIndex = 0
    while True:
      if (self.opMode == "encode" and self.runIndex >= len(self.plainDataInputArr)) or (self.opMode == "decode" and self.runIndex >= self.size[0]):
        break
      processAllRunsShouldContinue = False
      try:
        processAllRunsShouldContinue = self.processRun()
        self.runIndex += 1 #moved here to make it reflect the number of successful runs and not include the last one if it fails.
      except ExhaustionError as ee:
        self.log("PyCellElimRun.CellElimRunCodecState.processAllRuns: an ExhaustionError was thrown by processRun. This is not supposed to happen while processing a lone block. While processing blocks in a stream, it is only supposed to happen when the stream ends.")
        if self.opMode == "encode":
          print(self.log("PyCellElimRun.CellElimRunCodecState.processAllRuns: this ExhaustionError is never supposed to happen while encoding."))
        elif self.opMode == "decode":
          if self.plainDataOutputArr.count(None) == len(self.plainDataOutputArr):
            raise ExhaustionError("CellElimRunCodecState.processRun threw an exhaustion error after {} runs. Maybe the input data was empty to begin with. The error was {}.".format(self.runIndex, repr(ee)))
          else:
            raise ParseError("CellElimRunCodecState.processRun threw an exhaustion error after {} runs, but self.plainDataOutputArr is not empty, so it is unlikely that the codec state was initialized with empty input data. The error was {}.".format(self.runIndex, repr(ee)))
        else:
          assert False, "invalid opMode."

      if not processAllRunsShouldContinue:
        break


      

  def processRun(self): #do one run, either encoding or decoding.
    self.stepIndex = 0
    runShouldContinue = True
    
    cellTargeter = CellTargeter(self.size,self.spline,self.cellCatalogue,self.headerDict["score_mode"])
    cellTargeter.buildRankings()
    
    if not cellTargeter.optionsExist(): #if there's no way to act on any pressNum that might be available, stop now before stealing a pressNum from self.pressDataInputGen.
      return False #indicate that processing should stop.
        
    currentPressDataNum = None
    if self.opMode == "decode": #access to the currentPressDataNum is only needed while decoding. it doesn't exist while encoding.
      try:
        currentPressDataNum = next(self.pressDataInputGen)
      except StopIteration:
        self.log("PyCellElimRun.CellElimRunCodecState.processRun has run out of pressData input items. This is uncommon.")
        raise ExhaustionError("ran out of pressDataInputGen items while decoding. This is ONLY supposed to happen when the input data is too short to represent a valid CER block.")
        return False #indicate that processing should stop. This shouldn't be reached anyway, due to the exhaustion error.
    
    targetSeq = cellTargeter.genCellCheckOrder()
    for targetEntry in targetSeq:
      assert self.stepIndex <= self.stepIndexTimeout, "This loop has run for an impossibly long time."
        
      cellToCheck = targetEntry[1]
      if targetEntry[0] == "fix":
        #print("order entry " + str(orderEntry) + " will be fixed")
        assert CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE, "fix is not supposed to happen while DO_CRITICAL_COLUMN_ROUTINE is disabled!"
        self.spline[cellToCheck[0]] = cellToCheck[1]
        continue
      assert targetEntry[0] == "visit"
      
      if self.opMode == "encode":
        if self.plainDataInputArr[cellToCheck[0]] == cellToCheck[1]: #if hit...
          runShouldContinue = False #run should not continue.
      elif self.opMode == "decode":
        if currentPressDataNum == self.stepIndex: #if run is ending...
          runShouldContinue = False #run should not continue.
      else:
        assert False, "Invalid opMode."
      
      if not runShouldContinue: #if cellToCheck is a hit:
        if self.opMode == "encode":
          self.pressDataOutputArr.append(self.stepIndex) #then a new run length is now known and should be added to the compressed data number list.
        elif self.opMode == "decode":
          pass #nothing in this branch because it is instead handled by setPlaindataItem.
        else:
          assert False, "Invalid opMode."
        self.setPlaindataItem(cellToCheck[0], cellToCheck[1], eliminateColumn=CellElimRunCodecState.DO_COLUMN_ELIMINATION_AT_GEN_END, modifyOutputArr=True, dbgCatalogueValue=-555)
        #self.spline[cellToCheck[0]] = cellToCheck[1] #is it really that easy?
        #if CellElimRunCodecState.DO_COLUMN_ELIMINATION_AT_GEN_END:
        #  self.cellCatalogue.eliminateColumn(cellToCheck[0],dbgCustomValue=-5)
        return True #indicate that processing should continue.
      self.stepIndex += 1
    assert False, "this statement should no longer be reachable, now that cellTargeter.optionsExist test is performed before the loop. Running out of options should be handled within the loop or generator, not here."

    
      
  






def expandArgsToCERCSHeaderDict(args):
  if len(args) == 1:
    assert type(args[0])==dict
    headerDict = args[0]
  elif len(args) == 2:
    interpolationMode, spaceDefinition = (args[0], args[1])
    if type(spaceDefinition) == list:
      if len(spaceDefinition) != 2 or (None in spaceDefinition):
        raise ValueError("spaceDefinition is a list that can't be converted to a dictionary.")
      assert len(spaceDefinition) == 2
      print("spaceDefinition will be expanded into a dictionary. The use of a 2-item list for a spaceDefinition is deprecated.")
      spaceDefinition = {"size":spaceDefinition}
    headerDict = {"interpolation_mode":interpolationMode,"space_definition":spaceDefinition}
  else:
    raise ValueError("wrong number of arguments.")
  return headerDict


def getOrFallback(inputDict,inputKey,fallbackValue):
  try:
    return inputDict[inputKey]
  except KeyError:
    return fallbackValue
  except IndexError:
    return fallbackValue
    
    
    
    
    

def cellElimRunBlockTranscode(inputData,opMode,*args,**kwargs):
  assert opMode in ["encode","decode"]
  inputHeaderDict = expandArgsToCERCSHeaderDict(args)
  dbgReturnCERCS = getOrFallback(kwargs,"dbgReturnCERCS",False)

  tempCERCS = CellElimRunCodecState(inputData,opMode,inputHeaderDict)
  tempCERCS.processBlock()
  if dbgReturnCERCS:
    return tempCERCS
  else:
    return tempCERCS.getOutput()
  


def genCellElimRunBlockSeqTranscode(inputData,opMode,*args,**kwargs):
  segmentInput = getOrFallback(kwargs,"segmentInput",False)
  segmentOutput = getOrFallback(kwargs,"segmentOutput",False)
  inputHeaderDict = expandArgsToCERCSHeaderDict(args)
  inputData = makeGen(inputData)
  while True:
    currentInputData = None
    if segmentInput:
      currentInputData = next(inputData)
    else:
      currentInputData = inputData
    currentResult = None
    try:
      currentResult = cellElimRunBlockTranscode(currentInputData,opMode,inputHeaderDict)
    except ExhaustionError:
      break
    assert currentResult != None
    if segmentOutput:
      yield currentResult
    else:
      for outputItem in currentResult:
        yield outputItem
  #print("PyCellElimRun.genCellElimRunBlockSeqTranscode: ended.")



cellElimRunBlockCodec = CodecTools.Codec(None,None,transcodeFun=cellElimRunBlockTranscode,domain="UNSIGNED")

cellElimRunBlockSeqCodec = CodecTools.Codec(None,None,transcodeFun=genCellElimRunBlockSeqTranscode,domain="UNSIGNED")





#tests:


testResult = cellElimRunBlockTranscode([2,2,2,2,2],"encode","linear",{"size":[5,5]})
assert testResult[0] == 20
assert sum(testResult[1:]) == 0
assert cellElimRunBlockTranscode([20],"decode","linear",{"size":[5,5]}) == [2,2,2,2,2]

testResult = cellElimRunBlockTranscode([5,6,7,6,5], "encode", "linear", {"size":[5,10], "endpoint_init_mode":"middle"})
assert testResult[:2] == [32,10]
assert sum(testResult[2:]) == 0
assert cellElimRunBlockTranscode([32,10,0,0,0], "decode", "linear", {"size":[5,10], "endpoint_init_mode":"middle"}) == [5,6,7,6,5]

testResult = makeArr(genCellElimRunBlockSeqTranscode([5,6,7,6,5,5,6,7,6,5], "encode", "linear", {"size":[5,10], "endpoint_init_mode":"middle"}))
assert testResult == [32,10,32,10]
assert makeArr(genCellElimRunBlockSeqTranscode([32,10,32,10], "decode", "linear", {"size":[5,10], "endpoint_init_mode":"middle"})) == [5,6,7,6,5,5,6,7,6,5]

testResult = cellElimRunBlockCodec.encode([5,6,7,8,9,8,7,6,5,4], {"space_definition":{"size":[10,10], "bounds":{"lower":"EMBED:AFTER_PREP_OP_MODE", "upper":"EMBED:AFTER_PREP_OP_MODE"}, "bound_touches":{"east":"EMBED:AFTER_PREP_OP_MODE:1", "north":"EMBED:AFTER_PREP_OP_MODE:1", "south":"EMBED:AFTER_PREP_OP_MODE:1",  "west":"EMBED:AFTER_PREP_OP_MODE:1"}}})
assert testResult == [4,10,4,4,9,5,35]


for testEndpointInitMode in [["middle","middle"],["zero","maximum"],["zero","zero"]]:
  assert CodecTools.roundTripTest(cellElimRunBlockCodec.clone(extraArgs=["linear",{"size":(5,101),"endpoint_init_mode":testEndpointInitMode}]),[5,0,100,75,50])


