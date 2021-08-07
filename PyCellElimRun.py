"""

PyCellElimRun.py by John Dorsey.

PyCellElimRun.py contains tools for converting audio samples into a sequence of integers that is more easily compressed.

"""

import math

import Curves
import CodecTools

from IntArrMath import intify

from Codes import ParseError
import PyGenTools
from PyGenTools import isGen, makeArr, makeGen, arrTakeOnly, ExhaustionError, accumulate, countIn, allAreEqual
from PyArrTools import ljustedArr, bubbleSortSingleItemRight, insort
import PyDeepArrTools
from PyDeepArrTools import shape, enumerateDeeply, iterateDeeply
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
    if self.storageMode == "limits":
      def finalInitFun(finalInitSize):
        return LimitsCellCatalogueColumn(size=finalInitSize)
    elif self.storageMode == "grid":
      def finalInitFun(finalInitSize):
        return GridCellCatalogueColumn(size=finalInitSize)
    else:
      raise KeyError("storageMode key {} is invalid.".format(repr(self.storageMode)))
    self.data = PyDeepArrTools.dataInitializer(self.size,finalInitFun)
    
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
    return enumerateDeeply(self.data,uniformDepth=True)
    
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
        assert extremeUnknownCell != None
        yield columnID + [extremeUnknownCell]

  def clampCell(self,cell): #move a cell's value to make it comply with the catalogue of eliminated cells.
    return cell[:-1] + [self.getColumn(cell[:-1]).clampCell(cell[-1])]














class CellTargeter:
  def __init__(self,size,spline,cellCatalogue,scoreFun,critCellCallbackMethod=None):
    #print("CellTargeter initialized.")
    self.size = size
    self.spline = spline
    self.cellCatalogue = cellCatalogue
    self.prepScoreMode(scoreFun)
    if critCellCallbackMethod == None:
      print("PyCellElimRun.CellTargeter: warning: creating a dud critCellCallbackMethod because one was not provided.")
      def critCellCallbackMethod(critCell):
        pass
    self.critCellCallbackMethod = critCellCallbackMethod
    self.rankings = None
    self.rankingsInsortKeyFun = (lambda item: item[0]) #used by genCellCheckOrder.
    
    
  def prepScoreMode(self,scoreFun): # -> None:
    if type(scoreFun)==str:
      if scoreFun=="vertical_distance":
        def scoreFun(cell):
          return self.size[1]-abs(self.spline.get_value_using_path(cell[:-1])-cell[-1]) #bad offset? probably not.
      elif scoreFun in ["absolute_distance", "bilog_distance","manhattan_distance"]:
        distanceFun = Curves.distance_2d_funs[scoreFun]
        def scoreFun(cell):
          assert len(cell) == 2, "this scoreFun can't handle more than 2 dimensions."
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
      assert CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE, "this return is not supposed to happen while DO_CRITICAL_COLUMN_ROUTINE is disabled!"
      return
      
    while True: #the generator loop.
      #during the generator loop, no test is done for whether self.rankings has been depleted, because if it is possible for this to happen, an index error would be more noticable. Also, performance reasons.
      
      outputCell = self.rankings[0][1]
      yield outputCell
      
      columnCritical = self.cellCatalogue.eliminateCell(outputCell)
      replacementCell = self.cellCatalogue.clampCell(outputCell)
      assert str(outputCell) != str(replacementCell) #debug.
      
      if columnCritical and CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE:
        #print("column is critical for " + str(outputCell) + ". column limits are " + str(self.cellCatalogue.limits[outputCell[0]]) + ".")
        #print("the replacementCell " + str(replacementCell) + " is now assumed to be a duplicate and will not be insorted into the rankings.")
        self.critCellCallbackMethod(replacementCell,dbgCatalogueValue=-438438)
        del self.rankings[0]
      else:
        del self.rankings[0]
        insort(self.rankings, (self.scoreFun(replacementCell), replacementCell), keyFun=self.rankingsInsortKeyFun)
    assert False, "genCellCheckOrder has ended. This has never happened before."


class Log:
  def __init__(self):
    pass
  def __call__(self,*args,**kwargs):
    return self.doLog(*args,**kwargs)

    
def implementLogging(otherSelf,existingLogList=None,loggingLinePrefix="",passthroughPrefix=True):
  if existingLogList == None:
    existingLogList = ["log list initialized."]
  
  assert not hasattr(otherSelf,"log"), "logging already implemented!"
  otherSelf.log = Log()
  if not hasattr(otherSelf.log,"logList"):
    otherSelf.log.logList = existingLogList
    
  def doLog(text):
    otherSelf.log.logList.append(otherSelf.log.loggingLinePrefix+str(text))
    if otherSelf.log.passthroughPrefix:
      if type(otherSelf.log.passthroughPrefix) == str:
        return otherSelf.log.passthroughPrefix + text
      else:
        return otherSelf.log.loggingLinePrefix + text
    else:
      return text
    
  def logToPrettyStr(lineStart="",lineEnd="",includeLineNumber=False,lineFormatFun=None):
    maxLineNumberLength = len(str(len(otherSelf.log.logList)))
    if lineFormatFun == None:
      if includeLineNumber:
        lineFormatFun = (lambda lineNumber, inputText: lineStart+str(lineNumber).rjust(maxLineNumberLength,fillchar="_")+". "+inputText+lineEnd)
      else:
        lineFormatFun = (lambda lineNumber, inputText: lineStart+inputText+lineEnd)
    return "\n".join(lineFormatFun(logLineIndex,logLine) for logLineIndex,logLine in enumerate(otherSelf.log.logList))

  def printLog():
    print("PyCellElimRun.CellElimRunCodecState.printLog: \n"+otherSelf.log.logToPrettyStr(includeLineNumber=True))
  
  otherSelf.log.loggingLinePrefix = loggingLinePrefix
  otherSelf.log.passthroughPrefix = passthroughPrefix
  otherSelf.log.doLog = doLog
  otherSelf.log.logToPrettyStr = logToPrettyStr
  otherSelf.log.printLog = printLog
  otherSelf.log("log implemented for object of type {}.".format(repr(type(otherSelf))))





class HeaderManager:
  def __init__(self, inputDataGen, opMode, inputHeaderDictTemplate, headerPathwiseOracleFun, logList=None):
    implementLogging(self, existingLogList=logList, loggingLinePrefix="HeaderManager: ")
    self.inputDataGen = inputDataGen
    self.opMode = opMode
    self.headerDictTemplate = inputHeaderDictTemplate
    self.headerPathwiseOracleFun = headerPathwiseOracleFun
    self.headerDict = {}
    self.pressHeaderValues = [] #this is to remain empty until populated by the header loader. it _may_ be populated if the headerDictTemplate tells it to embed or access header info from the regular inputData.
    augmentDict(self.headerDict, self.headerDictTemplate, recursive=True, recursiveTypes=[list,dict]) #this shouldn't be long-term. Once header tool design is finished, items will be absent from the header until they are resolved.
    
  def __getitem__(self, key):
    return self.headerDict[key]
    
  def __contains__(self, testValue):
    return self.headerDict.__contains__(testValue)

  def doPhase(self, phaseName):
    """
    This method is called at different stages of initialization, to fill in some new header data (whichever data is clearly marked by string placeholders matching \"EMBED:<the name of the phase>\"). While initializing for encode mode, header values are calculated based on the plaindata, which is known, and recorded in two places: replacing the placeholder in the headerDict, and appended to the end of the pressHeaderValues. While initializing for decode mode, the plaindata is unknown, and that's why header placeholder values of "EMBED:..." are immediately loaded from the front of the pressdata nums instead, where they were stored... as long as the inputHeaderTemplateDict telling which values are to be embedded is exactly the same as the one that was provided for the original encoding. It is also necessary that the order of processing for pressHeaderNums is constant. The standard is to visit dictionary keys and list indices in ascending order (which only impacts the output when different placeholders have the same phase name), evaluate the placeholders, and obey the placeholder phase names strictly. There is no proper time to resolve header placeholders with no phase name - they are just ignored.
    """
    #self.log("header phase " + phaseName +" started with opMode=" + str(self.opMode) + " and headerDict=" + str(self.headerDict)+".")
    #create self.headerDict based on self.inputHeaderDictTemplate. In decode mode, this may involve loading embedded values from self.inputDataGen when seeing the template value "EMBED".
    phaseEmbedCode = "EMBED:"+phaseName
    #PyDictTools.replace(self.headerDict,"EMBED",phaseEmbedCode)
    
    if self.opMode == "encode":
      pathwiseOracleFun = self.headerPathwiseOracleFun
      valueTriggerFun = (lambda x: x==phaseEmbedCode)
      PyDictTools.writeFromTemplateAndPathwiseOracle(self.headerDict, self.headerDictTemplate, pathwiseOracleFun, valueTriggerFun)
    elif self.opMode == "decode":
      valueTriggerFun = (lambda x: x==phaseEmbedCode)
      PyDictTools.writeFromTemplateAndNextFun(self.headerDict, self.headerDictTemplate, self.loadHeaderValue, valueTriggerFun) #@ the problem with this is that it doesn't populate the press header nums list, which would be helpful for knowing whether a parse error has occurred when processBlock is ending.
    else:
      assert False, "invalid opMode."
    #self.log("header phase " + phaseName +" ended with opMode=" + str(self.opMode) + " and headerDict=" + str(self.headerDict)+".")

  def saveHeaderValue(self,value):
    """
    Append a value to the pressHeaderValues and return it.
    """
    if type(value) != int:
      print("PyCellElimRun.HeaderManager.saveHeaderNum: Warning: the value being saved is of type " + str(type(value)) + ", not int! Codecs processing the output of this codec may not expect this!")
    self.pressHeaderValues.append(value)
    return value

  def loadHeaderValue(self):
    """
    Remove a value from the front of self.inputDataGen and return it. Do this only when it is known that a header value is at the front of self.inputDataGen.
    """
    loadedNum = None
    try:
      loadedNum = next(self.inputDataGen)
    except StopIteration:
      raise ExhaustionError("Ran out of inputData while trying to read the header info.")
    assert loadedNum != None
    self.pressHeaderValues.append(loadedNum)
    return loadedNum
    



class CellElimRunCodecState:
  """
  The CellElimRunCodecState is responsible for owning and operating a Spline and CellCatalogue, and using them to either encode or decode data. Encoding and decoding are supposed to share as much code as possible. This makes improving or expanding the core mathematics of the compression vastly easier - as long as the important code is only ever called in identical ways by both the encoding and the decoding methods, any change to the method of predicting unknown data from known data won't break the symmetry of those methods.
  """
  
  #the following column-related options control whether entire columns of unknown or un-visited cells can be eliminated from the cellCatalogue at various times that the cellCatalogue would NOT eliminate them on its own. For instance, the algorithm always eliminates the cellCatalogue column when it hits a live cell, but it's also possible to eliminate a column when that column has two unknown cells and one of them is visited but not hit - this is the purpose of the critical column routine.
  DO_COLUMN_ELIMINATION_AT_GEN_END = True #this should not be turned off, because it changes the output in a way that isn't simple. Compression Ratio seems to be better with it turned on, but this wasn't expected, so the loss of compression with it turned off is probably a bug. Changing this setting shouldn't break symmetry.
  DO_CRITICAL_COLUMN_ROUTINE = True #this is responsible for most of the process of ensuring that trailing zeroes are trimmed and CER blocks may be self-delimiting.
  DO_COLUMN_ELIMINATION_OFFICIALLY = True #This controls whether column elimination can be performed by setPlaindataSample. Some of the process of making CER blocks self-delimiting depends on the use of setPlaindataSample with the expectation that this is set to True.
  
  DEFAULT_HEADER_DICT_TEMPLATE = {"interpolation_mode":"linear", "score_mode":"vertical_distance", "space_definition":{"size":[256, 256], "bounds":{}, "bound_touches":{}, "endpoint_init_mode":"middle"}}
  ALLOW_BOUND_ASSUMPTIONS = False #allow bound touch locations to be specified in the header without also providing the locations of bounaries in the header info - in this case, the bounaries are assumed based on "size". In case bounds were excluded from the header on accident, this assumption is incorrect, the plaindata values that are set based on the bound touch parameters will be set incorrectly, and the transcoding process will either crash or produce garbage.



  def __init__(self, inputData, opMode, inputHeaderDictTemplate):
    """
    The initialization method takes arguments that resemble a structured header as much as possible. In the decode phase, it fills in missing data in headerManager.headerDict by decoding a few pressdata items as parameters. In the encode phase, it fills in missing data in headerManager.headerDict by analyzing the provided plaindata, encodes these parameters, and prepends them to the pressdata it will output.
    The initialization method also creates all of the attributes that processBlock needs to start running right away. By the time processBlock is called, there is no more initialization to do.
    """
    self.initializeByDefault()
    
    self.inputDataGen = makeGen(inputData) #this is necessary to make it so that prepSpaceDefinition can take some items from the front, before prepOpMode does anything.
    self.opMode = opMode #initialized here instead of in prepOpMode because it is needed by prepSpaceDefinition.

    self.headerManager = HeaderManager(self.inputDataGen, opMode, self.TO_COMPLETED_HEADER_DICT_TEMPLATE(inputHeaderDictTemplate), self.headerPathwiseOracleFun, logList=self.log.logList)

    self.headerManager.doPhase("BEFORE_PREP_GROUP")

    self.prepOpMode()
    self.headerManager.doPhase("AFTER_PREP_OP_MODE")
    self.headerManager.doPhase("AFTER_PREP_OP_MODE:1")
    self.prepSpaceDefinition()
    self.headerManager.doPhase("AFTER_PREP_SPACE_DEFINITION")
    self.spline.setInterpolationMode(self.headerManager["interpolation_mode"])
      
    self.headerManager.doPhase("AFTER_PREP_GROUP")

    self.runIndex = None #the run index determines which integer run length from the pressdata run length list is being read and counted towards with the stepIndex variable as a counter while decoding, or, it is the length of the current list of such integer run lengths that is being built by encoding.
    self.stepIndex = None #the step index counts towards the value of the current elimination run length - either it is compared to a known elimination run length in order to know when to terminate and record a cell as filled while decoding, or it counts and holds the new elimination run length value to be stored while encoding.

    self.applyHeader()
    assert self.size[0] == len(self.spline.data)
    
    #this is defined here because it must not take self as an argument, because the CellTargeter should not need a reference to this CERCS to us it.
    def cellTargeterCritCellCallbackMethod(critCell,dbgCatalogueValue=-498498): 
      self.setPlaindataItem(critCell,dbgCatalogueValue=dbgCatalogueValue)
    self.cellTargeterCritCellCallbackMethod = cellTargeterCritCellCallbackMethod
    
    self.log("finished __init__.")



  def initializeByDefault(self):
    """
    initializeByDefault initializes things that can't be changed by class settings and don't depend on header information.
    """
    implementLogging(self, loggingLinePrefix="CERCS: ", passthroughPrefix=True)
    self._input_plaindata_matrix, self._input_pressdata_gen = None, None
    self._output_pressdata_list = None
    self._output_plaindata_matrix = None
    self.TO_COMPLETED_HEADER_DICT_TEMPLATE = (lambda inputObject: augmentedDict(inputObject, CellElimRunCodecState.DEFAULT_HEADER_DICT_TEMPLATE))
    
    
    
  def applyHeader(self):
    """
    After loading the header, extract some information that is accessed in loops while encoding or decoding. No method that runs during initialization needs these to be initialized.
    """
    for keyA in makeFlatKeySeq(self.headerManager.headerDict):
      if keyA == "space_definition":
        for keyB in makeFlatKeySeq(self.headerManager.headerDict[keyA]):
          if keyB == "size":
            self.size = self.headerManager.headerDict[keyA][keyB]
            self.stepIndexTimeout = accumulate((measure+2 for measure in self.size),"*") #used in causing failure when processRun goes on for too long.
            self.expectedLiveCellCount = accumulate((measure for measure in self.size[:-1]),"*")
            self.dimensions = len(self.size)
            

    
    
  def headerPathwiseOracleFun(self, inputPath, inputValue):
    """
    This method is provided as an argument to methods in PyDictTools, and is used to initialize header values based on their location in the header (as a list of dict keys and list indices to be applied in order to reach that location in the header) and the original placeholder value inputValue. This method should not be responsible for knowing when it should run - it should be used only at the proper time, which is identified by a separate trigger function.
    """
    result = inputValue
    if inputPath[-3:-1] == ["space_definition","bound_touches"]:
      assert len(self.headerManager["space_definition"]["size"]) == 2, "space_definition.bound_touches is only available for 2D data."
      try:
        try:
          bounds = self.headerManager["space_definition"]["bounds"]
        except KeyError as ke:
          raise ke
        if inputPath[-1] == "north":
          if "upper" not in bounds.keys():
            warningText = "north bound touch should only be embedded if the upper bound is also embedded."
            if CellElimRunCodecState.ALLOW_BOUND_ASSUMPTIONS:
              print("PyCellElimRun.CellElimRunCodecState.headerPathwiseOracleFun: warning: " + warningText)
              print("Assuming upper bound is size[-1]...")
              bounds["upper"] = self.headerManager["space_definition"]["size"][-1]
            else:
              raise ValueError(warningText)
          result = self._input_plaindata_matrix.index(bounds["upper"]-1)
        elif inputPath[-1] == "south":
          if "lower" not in bounds.keys():
            warningText = "south bound touch should only be embedded if the upper bound is also embedded."
            if CellElimRunCodecState.ALLOW_BOUND_ASSUMPTIONS:
              print("PyCellElimRun.CellElimRunCodecState.headerPathwiseOracleFun: warning: " + warningText)
              print("Assuming lower bound is 0...")
              bounds["lower"] = 0
            else:
              raise ValueError(warningText)
          result = self._input_plaindata_matrix.index(bounds["lower"])
        elif inputPath[-1] == "east":
          result = self._input_plaindata_matrix[-1]
        elif inputPath[-1] == "west":
          result = self._input_plaindata_matrix[0]
        else:
          raise ValueError("unknown header item in space_definition.bound_touches.")
      except IndexError:
        raise IndexError("There is no such boundary touch as {}.".format(repr(inputPath[-1])))
    elif inputPath[-3:-1] == ["space_definition","bounds"]:
      assert len(self.headerManager["space_definition"]["size"]) == 2, "space_definition.bounds is currently only available for 2D data."
      if inputPath[-1] == "lower":
        result = min(self._input_plaindata_matrix)
      elif inputPath[-1] == "upper":
        result = max(self._input_plaindata_matrix) + 1
      else:
        raise ValueError("unknown header item in space_definition.bounds.")
    elif inputPath[-1] == "dbg_resolve_to_123456789":
      result = 123456789
    elif inputPath[-1] == "dbg_resolve_to_[123,456]":
      result = [123,456]
    else:
      print(self.log("PyCellElimRun.CellElimRunCodecState.headerPathwiseOracleFun: warning: no substitute was found for (inputPath,inputValue)="+str((inputPath, inputValue)) + "."))
    return self.headerManager.saveHeaderValue(result) #assume it should be saved, and save it.




  def setPlaindataItem(self, cellToSet, eliminateColumn=None, modifyOutputArr=False, dbgCatalogueValue=-260):
    """
    This method is used to update the common view of the data represented by the spline or interpolator, cell catalogue, and output plaindata matrix. This is the _only_ legal way to update this information, and this rule makes it easy to trust different parts of the program with updating this data at the earliest possible opportunity, which directly increases compression ratio.
    """
    self.spline.set_value_using_cell(cellToSet)
    if (eliminateColumn == None and CellElimRunCodecState.DO_COLUMN_ELIMINATION_OFFICIALLY) or (eliminateColumn):
      self.cellCatalogue.eliminateColumn(cellToSet[:-1], dbgCustomValue=dbgCatalogueValue)
    if modifyOutputArr:
      if self.opMode == "decode":
        assert len(cellToSet) == self.dimensions
        PyDeepArrTools.setValueUsingCell(self._output_plaindata_matrix, cellToSet)


  def getOutput(self):
    """
    This method exists because the property that stores the output varies with the opMode, and because the press header nums are a separate list for easier debugging, but should still be included in the same output whenever encoding has already completed without issue.
    """
    if self.opMode == "encode":
      return self.headerManager.pressHeaderValues + self._output_pressdata_list
    elif self.opMode == "decode":
      return self._output_plaindata_matrix
    else:
      assert False, "invalid opMode."



  def prepSpaceDefinition(self): # -> None:
    size = self.headerManager["space_definition"]["size"]
    
    self.cellCatalogue = ColumnCellCatalogue(size=size)

    endpointInitMode = self.headerManager["space_definition"]["endpoint_init_mode"]
    self.spline = Curves.Spline(size=size, endpointInitMode=endpointInitMode)
    
    if "bounds" in self.headerManager["space_definition"].keys():
      bounds = self.headerManager["space_definition"]["bounds"]
      if "lower" in bounds.keys():
        self.cellCatalogue.imposeMinimum(bounds["lower"])
      if "upper" in bounds.keys():
        self.cellCatalogue.imposeMaximum(bounds["upper"]-1)

    if "bound_touches" in self.headerManager["space_definition"].keys():
      if len(size) != 2:
        #raise NotImplementedError("bound touches are not available of data with more than 2 dimensions.")
        print(self.log("prepSpaceDefinition: warning: bound touches are not available of data with more than 2 dimensions. any included will be ignored."))
      boundTouches = self.headerManager["space_definition"]["bound_touches"]
      
      if "north" in boundTouches.keys():
        self.setPlaindataItem([boundTouches["north"], self.headerManager["space_definition"]["bounds"]["upper"]-1], dbgCatalogueValue=-720720)
      if "south" in boundTouches.keys():
        self.setPlaindataItem([boundTouches["south"], self.headerManager["space_definition"]["bounds"]["lower"]], dbgCatalogueValue=-722722)
      if "east" in boundTouches.keys():
        self.setPlaindataItem([size[0]-1, boundTouches["east"]], dbgCatalogueValue=-724724)
      if "west" in boundTouches.keys():
        self.setPlaindataItem([0, boundTouches["west"]], dbgCatalogueValue=-726726)
        
      if "northeast" in boundTouches.keys():
        self.setPlaindataItem([size[0]-1, self.headerManager["space_definition"]["bounds"]["upper"]-1], dbgCatalogueValue=-729729)
      if "northwest" in boundTouches.keys():
        self.setPlaindataItem([0, self.headerManager["space_definition"]["bounds"]["upper"]-1], dbgCatalogueValue=-731731)
      if "southeast" in boundTouches.keys():
        self.setPlaindataItem([size[0]-1, self.headerManager["space_definition"]["bounds"]["lower"]], dbgCatalogueValue=-733733)
      if "southwest" in boundTouches.keys():
        self.setPlaindataItem([0, self.headerManager["space_definition"]["bounds"]["lower"]], dbgCatalogueValue=-735735)
        

  def prepOpMode(self): # -> None:
    """
    prepare CellEliminationRunCodecState to operate in the specified opMode by creating and initializing only the things that are needed for that mode of operation.
    """
    if not self.opMode in ["encode","decode"]:
      raise ValueError("That opMode is nonexistent or not allowed.")
      
    size = self.headerManager["space_definition"]["size"]

    if self.opMode == "encode":
      self._input_plaindata_matrix = arrTakeOnly(self.inputDataGen, size[0], onExhaustion="partial")
      if not len(self._input_plaindata_matrix) > 0:
        raise ExhaustionError("The CellEliminationRunCodecState received empty input data while trying to encode.")
      if len(size) == 2:
        if len(self._input_plaindata_matrix) < size[0]:
          print(self.log("PyCellElimRun.CellEliminationRunCodecState.prepOpMode: the input plainData is shorter than the (block) size, so the missing values will be replaced with zeroes."))
        self._input_plaindata_matrix = ljustedArr(self._input_plaindata_matrix, size[0], fillItem=0)
        assert len(self._input_plaindata_matrix) == size[0]
      elif len(size) > 2:
        pass #there are no validation steps that only work for higher dimensions.
      else:
        raise ValueError("invalid length of size.")  
      assert PyDeepArrTools.arrIsUniformlyShape(self._input_plaindata_matrix, size[:-1]), "input data is not uniform!"
      self._output_pressdata_list = []
    elif self.opMode == "decode":
      self._input_pressdata_gen = self.inputDataGen
      #defaultSampleValue = None
      #self._output_plaindata_matrix = []
      #self._output_plaindata_matrix.extend([defaultSampleValue for i in range(size[0])])
      self._output_plaindata_matrix = PyDeepArrTools.noneInitializer(size[:-1])
      #print(("op mode debug", shape(self._output_plaindata_matrix), size[:-1]))
      assert PyGenTools.seqsAreEqual(shape(self._output_plaindata_matrix), size[:-1])
    else:
      assert False, "invalid opMode."
      
  

  def interpolateMissingValues(self,data):
    changeCounter = 0
    for columnID,_ in enumerateDeeply(data):
      newValue = self.spline.get_value_using_path(columnID)
      originalValue = PyDeepArrTools.setValueUsingPath(data, columnID, newValue)
    if originalValue != newValue:
      changeCounter += 1
      assert originalValue == None, "a non-none value was changed."
    if changeCounter > 0:
      print("interpolateMissingValues changed {} values.".format(changeCounter))
      
  
  def processBlock(self,allowMissingValues=False):
    """
    This method is the host to the encoding or decoding process of the Cell Elimination Run algorithm. This method processes all the data that is currently loaded into or available to the CellElimRunCodecState, which is supposed to be one block of data. It does not know about surrounding blocks of audio or the results of handling them. When finished, it does not clean up after itself in any way - the variables like self.runIndex and self.stepIndex are not reset, so that they can be reviewed later. For this purpose, the main transcode method (PyCellElimRun.cellElimRunBlockTranscode) has an argument to return the entire codec state instead of the output data.
    """
    self.processAllRuns()
    if self.opMode == "decode" and not allowMissingValues:
      self.interpolateMissingValues(self._output_plaindata_matrix)
    
    self.headerManager.doPhase("AFTER_PROCESS_BLOCK")
    return


  def processAllRuns(self):
    self.runIndex = 0
    while True:
      if self.runIndex >= self.expectedLiveCellCount:
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
          if allAreEqual(countIn(iterateDeeply(self._output_plaindata_matrix),None,includeDenominator=True)):
            raise ExhaustionError("CellElimRunCodecState.processRun threw an exhaustion error after {} runs. Maybe the input data was empty to begin with. The error was {}.".format(self.runIndex, repr(ee)))
          else:
            raise ParseError("CellElimRunCodecState.processRun threw an exhaustion error after {} runs, but self._output_plaindata_matrix is not empty, so it is unlikely that the codec state was initialized with empty input data. The error was {}.".format(self.runIndex, repr(ee)))
        else:
          assert False, "invalid opMode."

      if not processAllRunsShouldContinue:
        break



  def processRun(self): #do one run, either encoding or decoding.
    self.stepIndex = 0
    
    cellTargeter = CellTargeter(self.size, self.spline, self.cellCatalogue, self.headerManager["score_mode"], critCellCallbackMethod=self.cellTargeterCritCellCallbackMethod)
    cellTargeter.buildRankings() #this is probably slower than refreshing the rankings, but also simpler.
    
    if not cellTargeter.optionsExist(): #if there's no way to act on any pressNum that might be available, stop now before stealing a pressNum from self._input_pressdata_gen.
      return False #indicate that processing should stop.
    
    currentPressdataNum = None
    if self.opMode == "decode": #access to the currentPressDataNum is only needed while decoding. it doesn't exist while encoding.
      try:
        currentPressdataNum = next(self._input_pressdata_gen)
      except StopIteration:
        self.log("PyCellElimRun.CellElimRunCodecState.processRun has run out of pressData input items. This is uncommon.")
        raise ExhaustionError("ran out of pressDataInputGen items while decoding. This is ONLY supposed to happen when the input data is too short to represent a valid CER block.")
        return False #indicate that processing should stop. This shouldn't be reached anyway, due to the exhaustion error.
    
    hitTest = None
    if self.opMode == "encode":
      if self.dimensions < 2:
        raise ValueError("Invalid self.dimensions")
      if self.dimensions == 2:#this version is only different from the higher-dimensional version for performance reasons.
        hitTest = (lambda: self._input_plaindata_matrix[cellToCheck[0]] == cellToCheck[1]) 
      else:
        hitTest = (lambda: PyDeepArrTools.getValueUsingPath(self._input_plaindata_matrix, cellToCheck[:-1]) == cellToCheck[-1])
    elif self.opMode == "decode":
      hitTest = (lambda: currentPressdataNum == self.stepIndex)
    else:
      assert False, "Invalid opMode"
    
    targetSeq = cellTargeter.genCellCheckOrder()
    for cellToCheck in targetSeq:
      assert self.stepIndex <= self.stepIndexTimeout, "This loop has run for an impossibly long time ({} steps for size {}).".format(self.stepIndex,self.size)
      
      if not hitTest():
        self.stepIndex += 1
      else:
        if self.opMode == "encode":
          self._output_pressdata_list.append(self.stepIndex) #then a new run length is now known and should be added to the compressed data number list.
        elif self.opMode == "decode":
          pass #nothing in this branch because it is instead handled by setPlaindataItem in a few lines.
        else:
          assert False, "Invalid opMode."
        self.setPlaindataItem(cellToCheck, eliminateColumn=CellElimRunCodecState.DO_COLUMN_ELIMINATION_AT_GEN_END, modifyOutputArr=True, dbgCatalogueValue=-797797)
        return True #indicate that processing should continue.
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
    
    
    
    
    

def cellElimRunBlockTranscode(inputData, opMode, *args, **kwargs):
  assert opMode in ["encode","decode"]
  inputHeaderDict = expandArgsToCERCSHeaderDict(args)
  dbgReturnCERCS = getOrFallback(kwargs, "dbgReturnCERCS", False)

  tempCERCS = CellElimRunCodecState(inputData, opMode, inputHeaderDict)
  tempCERCS.processBlock()
  if dbgReturnCERCS:
    return tempCERCS
  else:
    return tempCERCS.getOutput()
  


def genCellElimRunBlockSeqTranscode(inputData, opMode, *args, **kwargs):
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
      currentResult = cellElimRunBlockTranscode(currentInputData, opMode, inputHeaderDict)
    except ExhaustionError:
      break
    assert currentResult != None
    if segmentOutput:
      yield currentResult
    else:
      for outputItem in currentResult:
        yield outputItem
  #print("PyCellElimRun.genCellElimRunBlockSeqTranscode: ended.")



cellElimRunBlockCodec = CodecTools.Codec(None, None, transcodeFun=cellElimRunBlockTranscode, domain="UNSIGNED")

cellElimRunBlockSeqCodec = CodecTools.Codec(None, None, transcodeFun=genCellElimRunBlockSeqTranscode, domain="UNSIGNED")





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


testResult = cellElimRunBlockTranscode([[1,2,3,2,1],[2,3,5,3,2],[3,5,8,5,3],[2,3,5,3,2],[1,2,3,2,1]],"encode",{"interpolation_mode":{"method_name":"inverse_distance_weighted"},"space_definition":{"size":[5,5,10]}})

assert testResult == [25, 31, 9, 25, 14, 74, 8, 0, 0, 0]



