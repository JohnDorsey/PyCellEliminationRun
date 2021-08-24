"""

PyCellElimRun.py by John Dorsey.

PyCellElimRun.py contains tools for converting audio samples into a sequence of integers that is more easily compressed.

"""

from warnings import warn

from TestingTools import assertEqual

import CellCatalogues
import Curves
import CodecTools

from IntArrMath import intify, floatified

import HeaderTools

import PyGenTools
from PyGenTools import makeArr, makeGen, arrTakeOnly, ExhaustionError, countIn, allAreEqual
from PyArrTools import ljustedArr, insort
import PyDeepArrTools
from PyDeepArrTools import shape, iterateDeeply
from PyDictTools import augmentedDict, makeFlatKeySeq

try:
  range = xrange
except NameError:
  pass


DODBGPRINT = False #print debug info.
DOVIS = False #show pretty printing, mostly for debugging.

def dbgPrint(text,end="\n"): #only print if DODBGPRINT.
  if DODBGPRINT:
    print(text)
    print("custom line endings disabled for python2 compatibility.")







def stringifiedFloatified(inputArr):
  #used for debugging - check whether structures containing numbers are equal.
  return str(floatified(inputArr, listifiedContainers=True))








class CellTargeter:
  USE_STABLE_INSORT = False #set to False for old behavior. will affect output. shouldn't meaningfully affect CR.
  DO_FILTER_LOITERING_RANKINGS_IN_GENERATOR = False #set to True to filter items taken from the left of rankings and discard cells whose columns have been eliminated.
  #DO_CULL_LOITERING_RANKINGS_IN_OPTIONS_EXIST = True #there might be no point to this, and it can be removed.

  def __init__(self, size, spline, cellCatalogue, scoreFun, critCellCallbackMethod=None):
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
    return sorted(([self.scoreFun(extremeCell), extremeCell] for extremeCell in self.cellCatalogue.genExtremeUnknownCells()), key=self.rankingsInsortKeyFun)
    
    
  def buildRankings(self):
    self.rankings = self.newRankings()
    
    
  def refreshRankings(self, refreshType):
    if refreshType == "soft":
      self.softRefreshRankings()  
    elif refreshType == "hard":
      self.hardRefreshRankings()
    elif refreshType == "build":
      self.buildRankings()
    else:
      raise ValueError("unknown refresh type {}.".format(repr(refreshType)))
    
  
  print("PyCellElimRun.CellTargeter.softRefreshRankings is defined with a slow call to dbgCullRankings. If this method culls any rankings, then the compressed output may change when the filter is later removed.")
  def softRefreshRankings(self):
    for i,rankingsEntry in enumerate(self.rankings):
      self.rankings[i] = [self.scoreFun(rankingsEntry[1]), rankingsEntry[1]]
      
    deletionCount = self.dbgCullRankings()
    if not deletionCount == 0:
      #warn("PyCellElimRun.CellTargeter.softRefreshRankings: warning: deletion count due to extremeUnknownCell changes was {}, so removing this filtering step during refresh _may_ change compressed output.".format(deletionCount))
      pass
    self.rankings.sort(key=self.rankingsInsortKeyFun)
    
    
  def hardRefreshRankings(self):
    i = None
    for i,extremeCell in enumerate(self.cellCatalogue.genExtremeUnknownCells()):
      #assert type(extremeCell) in [list,tuple], repr(extremeCell)
      newRankingsEntry = [self.scoreFun(extremeCell), extremeCell]
      if i < len(self.rankings):
        self.rankings[i] = newRankingsEntry
      elif i == len(self.rankings):
        self.rankings.append(newRankingsEntry)
        assert len(self.rankings) == i+1
      else:
        assert False, "unexpected self.rankings length."
    
    if i is not None:
      assert len(self.rankings) >= i+1
      del self.rankings[i+1:]
      assert len(self.rankings) == i+1
      
    self.rankings.sort(key=self.rankingsInsortKeyFun)
      
    deletionCount = self.dbgCullRankings()
    if not deletionCount == 0:
      print("PyCellElimRun.CellTargeter.hardRefreshRankings: warning: deletion count due to extremeUnknownCell changes was {}, so removing this filtering step during refresh _may_ change compressed output.".format(deletionCount))
      
    if len(self.rankings) == 0:
      print("PyCellElimRun.CellTargeter.hardRefreshRankings: deletionCount={}. self.rankings is now empty, so we will attempt to build it again to avoid a crash.".format(deletionCount))
      self.buildRankings()
      if len(self.rankings) != 0:
        print("PyCellElimRun.CellTargeter.refreshRankings: WARNING: after buildRankings ran, length increased to {}. This means that the refresh is not working correctly.".format(len(self.rankings)))
        #pass
    print("PyCellElimRun.CellTargeter.hardRefreshRankings: SLOW: doing slow check of refreshed rankings!")
    assertEqual(self.rankings, self.newRankings()) #@ slow
    
    
  def dbgCullRankings(self):
    """
    check for inconsistencies (slow)
    this will only become unnecessary when all ways that cellCatalogue and spline can be changed trigger an update of rankings here.
    """
    warn("PyCellElimRun.CellTargeter.dbgCullRankings: warn: slow.")
    #stringifyEntry = (lambda entryToStringify: str((float(entryToStringify[0]),(float(entryToStringify[1][0]),float(entryToStringify[1][1])))))
    extremeUnknownCellStrs = set(stringifiedFloatified(item) for item in self.cellCatalogue.genExtremeUnknownCells())
    #for item in extremeUnknownCellStrs:
    #  assert "(" not in item
    #  assert ")" not in item
    #for item in self.rankings:
    #  assert "[" not in str(item[1]).replace("[","(").replace("]",")")
    #  assert "]" not in str(item[1]).replace("[","(").replace("]",")")
    deletionCount = 0
    i = 0
    while i < len(self.rankings):
      currentItemStr = stringifiedFloatified(self.rankings[i][1])
      if currentItemStr not in extremeUnknownCellStrs:
        #print("PyCellElimRun.CellTargeter.dbgCullRankings: warning: deleting {} with currentItemStr={} at index {} for not being in extremeUnknownCellStrs {}....".format(self.rankings[i], repr(currentItemStr), i, repr(extremeUnknownCellStrs)[:64]))
        self.rankings.__delitem__(i)
        deletionCount += 1
      else:
        i += 1
    return deletionCount
    
    
  def optionsExist(self):
    #if CellTargeter.DO_CULL_LOITERING_RANKINGS_IN_OPTIONS_EXIST:
    #  oldLength = len(self.rankings)
    #  self.rankings = [entry for entry in self.rankings if self.cellLoiteringReport(entry[1])[1] > 1] # @ could be faster.
    #  if len(self.rankings) != oldLength:
    #    raise AssertionError("rankings length should not have changed!")
    return len(self.rankings) > 0
    
  
  def cellLoiteringReport(self, cellToCheck):
    column = self.cellCatalogue.getColumn(cellToCheck[:-1])
    return (column.getCellStatus(cellToCheck[-1]), column.countUnknowns())
    
  
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
      
      if CellTargeter.DO_FILTER_LOITERING_RANKINGS_IN_GENERATOR:
        outputCellStatus, currentColumnUnknownCount = self.cellLoiteringReport(outputCell)
        if currentColumnUnknownCount == 0:
          del self.rankings[0]
          if len(self.rankings) == 0:
            print("PyCellElimRun.CellTargeter.genCellCheckOrder: warning: ran out of entries in rankings! This never happened before, but filtering for eliminated columns makes it possible.")
            return
          continue
        elif currentColumnUnknownCount == 1:
          assert False, "It seems like this column was improperly eliminated!"
        if outputCellStatus != CellCatalogues.CellCatalogue.UNKVAL:
          #NOTE that this may cause duplicates in rankings!
          outputCell = self.cellCatalogue.clampCell(outputCell)
          print("PyCellElimRun.CellTargeter.genCellCheckOrder: warning: This routine isn't finished yet. The output cell being yielded now will not be in the right order, which hurts CR. This cell might also be duplicated!")
          self.rankings[0] = (self.scoreFun(outputCell), outputCell)
      
      yield outputCell
      
      columnCritical = self.cellCatalogue.eliminateCell(outputCell)
      replacementCell = self.cellCatalogue.clampCell(outputCell)
      assert str(outputCell) != str(replacementCell) #@ debug.
      
      if columnCritical and CellElimRunCodecState.DO_CRITICAL_COLUMN_ROUTINE:
        #print("column is critical for " + str(outputCell) + ". column limits are " + str(self.cellCatalogue.limits[outputCell[0]]) + ".")
        #print("the replacementCell " + str(replacementCell) + " is now assumed to be a duplicate and will not be insorted into the rankings.")
        self.critCellCallbackMethod(replacementCell, dbgCatalogueValue=-438438)
        del self.rankings[0]
      else:
        del self.rankings[0]
        insort(self.rankings, (self.scoreFun(replacementCell), replacementCell), stable=CellTargeter.USE_STABLE_INSORT, keyFun=self.rankingsInsortKeyFun)
    assert False, "genCellCheckOrder has ended. This has never happened before."





class CellElimRunCodecState:
  """
  The CellElimRunCodecState is responsible for owning and operating a Spline and CellCatalogue, and using them to either encode or decode data. Encoding and decoding are supposed to share as much code as possible. This makes improving or expanding the core mathematics of the compression much easier - as long as the important code is only ever called in identical ways by both the encoding and the decoding methods, any change to the method of predicting unknown data from known data won't break the symmetry of those methods.
  """
  
  #the following column-related options control whether entire columns of unknown or un-visited cells can be eliminated from the cellCatalogue at various times that the cellCatalogue would NOT eliminate them on its own. For instance, the algorithm always eliminates the cellCatalogue column when it hits a live cell, but it's also possible to eliminate a column when that column has two unknown cells and one of them is visited but not hit - this is the purpose of the critical column routine.
  DO_COLUMN_ELIMINATION_AT_GEN_END = True #this should not be turned off, because it changes the output in a way that isn't simple. Compression Ratio seems to be better with it turned on, but this wasn't expected, so the loss of compression with it turned off is probably a bug. Changing this setting shouldn't break symmetry.
  DO_CRITICAL_COLUMN_ROUTINE = True #this is responsible for most of the process of ensuring that trailing zeroes are trimmed and CER blocks may be self-delimiting.
  DO_COLUMN_ELIMINATION_OFFICIALLY = True #This controls whether column elimination can be performed by setPlaindataSample. Some of the process of making CER blocks self-delimiting depends on the use of setPlaindataSample with the expectation that this is set to True.
  
  DEFAULT_HEADER_DICT_TEMPLATE = {"interpolation_mode":"linear", "score_mode":"vertical_distance", "space_definition":{"size":[256, 256], "bounds":{}, "bound_touches":{}, "endpoint_init_mode":"middle"}}
  ALLOW_BOUND_ASSUMPTIONS = False #allow bound touch locations to be specified in the header without also providing the locations of bounaries in the header info - in this case, the bounaries are assumed based on "size". In case bounds were excluded from the header on accident, this assumption is incorrect, the plaindata values that are set based on the bound touch parameters will be set incorrectly, and the transcoding process will either crash or produce garbage.
  
  CELL_TARGETER_REFRESH_TYPE = "soft" #"soft" changes rankings order by basing it on the previous rankings order. "hard" is slower than "soft". "hard" and "build" should have identical results.


  def __init__(self, inputData, opMode, inputHeaderDictTemplate):
    """
    The initialization method takes arguments that resemble a structured header as much as possible. In the decode phase, it fills in missing data in headerManager.headerDict by decoding a few pressdata items as parameters. In the encode phase, it fills in missing data in headerManager.headerDict by analyzing the provided plaindata, encodes these parameters, and prepends them to the pressdata it will output.
    The initialization method also creates all of the attributes that processBlock needs to start running right away. By the time processBlock is called, there is no more initialization to do.
    """
    self.initializeByDefault()
    
    self.inputDataGen = makeGen(inputData) #this is necessary to make it so that prepSpaceDefinition can take some items from the front, before prepOpMode does anything.

    self.headerManager = HeaderTools.HeaderManager(self.inputDataGen, opMode, self.TO_COMPLETED_HEADER_DICT_TEMPLATE(inputHeaderDictTemplate), self.headerPathwiseOracleFun, logList=self.log.logList)

    self.headerManager.doPhase("BEFORE_PREP_GROUP")

    self.prepOpMode(opMode, self.headerManager["space_definition"]["size"])
    
    self.headerManager.doPhases(["AFTER_PREP_OP_MODE", "AFTER_PREP_OP_MODE:1"])
    
    self.prepSpaceDefinition(self.headerManager["space_definition"])
    
    self.headerManager.doPhase("AFTER_PREP_SPACE_DEFINITION")
    
    self.spline.setInterpolationMode(self.headerManager["interpolation_mode"])
      
    self.headerManager.doPhase("AFTER_PREP_GROUP")

    self.runIndex = None #the run index determines which integer run length from the pressdata run length list is being read and counted towards with the stepIndex variable as a counter while decoding, or, it is the length of the current list of such integer run lengths that is being built by encoding.
    self.stepIndex = None #the step index counts towards the value of the current elimination run length - either it is compared to a known elimination run length in order to know when to terminate and record a cell as filled while decoding, or it counts and holds the new elimination run length value to be stored while encoding.

    self.applyHeader()
    assert self.size[0] == len(self.spline.data)
    
    self.log("finished __init__.")



  def initializeByDefault(self):
    """
    initializeByDefault initializes things that can't be changed by class settings and don't depend on header information.
    """
    HeaderTools.implementLogging(self, loggingLinePrefix="CERCS: ", passthroughPrefix=True)
    self.TO_COMPLETED_HEADER_DICT_TEMPLATE = (lambda inputObject: augmentedDict(inputObject, CellElimRunCodecState.DEFAULT_HEADER_DICT_TEMPLATE))
    
    #this is defined here because it must not take self as an argument, because the CellTargeter should not need a reference to this CERCS to us it.
    def cellTargeterCritCellCallbackMethod(critCell, dbgCatalogueValue=-498498): 
      self.setPlaindataItem(critCell, dbgCatalogueValue=dbgCatalogueValue)
    self.cellTargeterCritCellCallbackMethod = cellTargeterCritCellCallbackMethod
    
    
  def applyHeader(self):
    """
    After loading the header, extract some information that is accessed in loops while encoding or decoding. No method that runs during initialization needs these to be initialized.
    """
    for keyA in makeFlatKeySeq(self.headerManager.headerDict):
      if keyA == "space_definition":
        for keyB in makeFlatKeySeq(self.headerManager.headerDict[keyA]):
          if keyB == "size":
            self.size = self.headerManager.headerDict[keyA][keyB]
            self.stepIndexTimeout = PyGenTools.product(measure+2 for measure in self.size) #used in causing failure when processRun goes on for too long.
            self.expectedLiveCellCount = PyGenTools.product(measure for measure in self.size[:-1])
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
          if "upper" not in bounds:
            warningText = "north bound touch should only be embedded if the upper bound is also embedded."
            if CellElimRunCodecState.ALLOW_BOUND_ASSUMPTIONS:
              print("PyCellElimRun.CellElimRunCodecState.headerPathwiseOracleFun: warning: " + warningText)
              print("Assuming upper bound is size[-1]...")
              bounds["upper"] = self.headerManager["space_definition"]["size"][-1]
            else:
              raise ValueError(warningText)
          result = self._input_plaindata_matrix.index(bounds["upper"]-1)
        elif inputPath[-1] == "south":
          if "lower" not in bounds:
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


  def prepOpMode(self, opMode, size): # -> None:
    """
    prepare CellEliminationRunCodecState to operate in the specified opMode by creating and initializing only the things that are needed for that mode of operation.
    """
    assert size != None, "size can't be None."
    
    self.opMode = opMode

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
      self._output_plaindata_matrix = PyDeepArrTools.noneInitializer(size[:-1])
      assert PyGenTools.seqsAreEqual(shape(self._output_plaindata_matrix), size[:-1]), "output plaindata matrix has an incorrect shape after creation: {}, compared to size {}.".format(shape(self._output_plaindata_matrix), size[:-1])
    else:
      raise ValueError("That opMode is nonexistent or not allowed.")


  def prepSpaceDefinition(self, spaceDefinition): # -> None:
  
    size = spaceDefinition["size"]
    endpointInitMode = spaceDefinition["endpoint_init_mode"]
    
    self.cellCatalogue = CellCatalogues.ColumnCellCatalogue(size=size)
    self.spline = Curves.Spline(size=size, endpointInitMode=endpointInitMode)
    
    if "bounds" in spaceDefinition:
      bounds = spaceDefinition["bounds"]
      if "lower" in bounds:
        self.cellCatalogue.imposeMinimum(bounds["lower"])
      if "upper" in bounds:
        self.cellCatalogue.imposeMaximum(bounds["upper"]-1)

    if "bound_touches" in spaceDefinition:
      if len(size) != 2:
        #raise NotImplementedError("bound touches are not available of data with more than 2 dimensions.")
        print(self.log("prepSpaceDefinition: warning: bound touches are not available of data with more than 2 dimensions. any included will be ignored."))
      else:
        boundTouches = spaceDefinition["bound_touches"]
        
        if "north" in boundTouches:
          self.setPlaindataItem([boundTouches["north"], spaceDefinition["bounds"]["upper"]-1], dbgCatalogueValue=-720720)
        if "south" in boundTouches:
          self.setPlaindataItem([boundTouches["south"], spaceDefinition["bounds"]["lower"]], dbgCatalogueValue=-722722)
        if "east" in boundTouches:
          self.setPlaindataItem([size[0]-1, boundTouches["east"]], dbgCatalogueValue=-724724)
        if "west" in boundTouches:
          self.setPlaindataItem([0, boundTouches["west"]], dbgCatalogueValue=-726726)
          
        if "northeast" in boundTouches:
          self.setPlaindataItem([size[0]-1, spaceDefinition["bounds"]["upper"]-1], dbgCatalogueValue=-729729)
        if "northwest" in boundTouches:
          self.setPlaindataItem([0, spaceDefinition["bounds"]["upper"]-1], dbgCatalogueValue=-731731)
        if "southeast" in boundTouches:
          self.setPlaindataItem([size[0]-1, spaceDefinition["bounds"]["lower"]], dbgCatalogueValue=-733733)
        if "southwest" in boundTouches:
          self.setPlaindataItem([0, spaceDefinition["bounds"]["lower"]], dbgCatalogueValue=-735735)
       
       
  
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
      
  
  def processBlock(self,allowMissingValues=False):
    """
    This method is the host to the encoding or decoding process of the Cell Elimination Run algorithm. This method processes all the data that is currently loaded into or available to the CellElimRunCodecState, which is supposed to be one block of data. It does not know about surrounding blocks of audio or the results of handling them. When finished, it does not clean up after itself in any way - the variables like self.runIndex and self.stepIndex are not reset, so that they can be reviewed later. For this purpose, the main transcode method (PyCellElimRun.cellElimRunBlockTranscode) has an argument to return the entire codec state instead of the output data.
    """
    self.processAllRuns()
    if self.opMode == "decode" and not allowMissingValues:
      self.spline.interpolateMissingValues(self._output_plaindata_matrix)
      self.cellCatalogue.clampValues(self._output_plaindata_matrix)
      print("PyCellElimRun.CellElimRunCodecState.processBlock: using intify! this is not as reliable as transcoding correctly to begin with.")
      intify(self._output_plaindata_matrix, roundNearest=True)
    
    self.headerManager.doPhase("AFTER_PROCESS_BLOCK")
    return


  def processAllRuns(self):
    self.runIndex = 0
    cellTargeter = CellTargeter(self.size, self.spline, self.cellCatalogue, self.headerManager["score_mode"], critCellCallbackMethod=self.cellTargeterCritCellCallbackMethod)
    cellTargeter.buildRankings()
    try:
      while self.runIndex < self.expectedLiveCellCount:
        processAllRunsShouldContinue = self.processRun(cellTargeter)
        self.runIndex += 1 #moved here to make it reflect the number of successful runs and not include the last one if it fails.
        if not processAllRunsShouldContinue:
          return
    except ExhaustionError as ee:
      self.handleRunExhaustionError(ee, self.runIndex)
      return


  def handleRunExhaustionError(self, ee, runIndex):
    self.log("PyCellElimRun.CellElimRunCodecState.processAllRuns: an ExhaustionError was thrown by processRun. This is not supposed to happen while processing a lone block. While processing blocks in a stream, it is only supposed to happen when the stream ends.")
    if self.opMode == "encode":
      print(self.log("PyCellElimRun.CellElimRunCodecState.processAllRuns: this ExhaustionError is probably never supposed to happen while encoding. The error was {}.".format(ee)))
    elif self.opMode == "decode":
      if allAreEqual(countIn(iterateDeeply(self._output_plaindata_matrix),None,includeDenominator=True)):
        raise ExhaustionError("CellElimRunCodecState.processRun threw an exhaustion error after {} runs. Maybe the input data was empty to begin with. The error was {}.".format(runIndex, repr(ee)))
      else:
        print(self.log("Potential parse error: CellElimRunCodecState.processRun threw an exhaustion error after {} runs, but self._output_plaindata_matrix is not empty, so it is unlikely that the codec state was initialized with empty input data. The error was {}.".format(runIndex, repr(ee))))
    else:
      assert False, "invalid opMode."


  def processRun(self, cellTargeter): #do one run, either encoding or decoding.
    self.stepIndex = 0
    
    cellTargeter.refreshRankings(CellElimRunCodecState.CELL_TARGETER_REFRESH_TYPE)
    
    #debug:
    #self.dbgBuildRankings(cellTargeter)
    
    if not cellTargeter.optionsExist(): #if there's no way to act on any pressNum that might be available, stop now before stealing a pressNum from self._input_pressdata_gen.
      return False #indicate that processing should stop.
    
    currentPressdataNum = None
    if self.opMode == "decode": #access to the currentPressDataNum is only needed while decoding. it doesn't exist while encoding.
      try:
        currentPressdataNum = next(self._input_pressdata_gen)
      except StopIteration:
        raise ExhaustionError(self.log("ran out of pressDataInputGen items while decoding. This is ONLY supposed to happen when the input data is too short to represent a valid CER block."))
        return False
        
    hitTest = None
    if self.opMode == "encode":
      if self.dimensions == 2:#this version is only different from the higher-dimensional version for performance reasons.
        hitTest = (lambda: self._input_plaindata_matrix[cellToCheck[0]] == cellToCheck[1]) 
      elif self.dimensions > 2:
        hitTest = (lambda: PyDeepArrTools.getValueUsingPath(self._input_plaindata_matrix, cellToCheck[:-1]) == cellToCheck[-1])
      else:
        assert False, "Invalid self.dimensions."
    elif self.opMode == "decode":
      hitTest = (lambda: currentPressdataNum == self.stepIndex)
    else:
      assert False, "Invalid opMode"
    
    targetGen = cellTargeter.genCellCheckOrder()
    
    for cellToCheck in targetGen:
      assert self.stepIndex <= self.stepIndexTimeout, "This loop has run for an impossibly long time ({} steps for size {}).".format(self.stepIndex, self.size)
      
      if cellTargeter.DO_FILTER_LOITERING_RANKINGS_IN_GENERATOR:
        assert not self.dbgCellIsInBadColumn(cellToCheck)
      
      if not hitTest():
        self.stepIndex += 1
      else:
        self.doHit(self.stepIndex, cellToCheck)
        return True #indicate that processing should continue.
        
    raise ExhaustionError("The targetGen ran out of items. maybe it is filtering its own output.")


  def dbgBuildRankings(self, cellTargeter):
    print(self.log("PyCellElimRun.CellElimRunCodecState.dbgBuildRankings: warning: slow."))
    
    #print(self.log("PyCellElimRun.CellElimRunCodecState.dbgBuildRankings: notice: for testing purposes, no actions taken."))
    #return
    
    oldRankingStr = stringifiedFloatified(cellTargeter.rankings)
    cellTargeter.buildRankings()
    newRankingStr = stringifiedFloatified(cellTargeter.rankings)
    if not newRankingStr == oldRankingStr:
      print(self.log("PyCellElimRun.CellElimRunCodecState: warning: inconsistent: from scratch {}... vs refreshed {}....".format(newRankingStr[:64], oldRankingStr[:64])))


  def doHit(self, stepIndex, cell):
    if self.opMode == "encode":
      self._output_pressdata_list.append(self.stepIndex) #then a new run length is now known and should be added to the compressed data number list.
    elif self.opMode == "decode":
      pass #nothing in this branch because it is instead handled by setPlaindataItem in a few lines.
    else:
      assert False, "Invalid opMode."
    self.setPlaindataItem(cell, eliminateColumn=CellElimRunCodecState.DO_COLUMN_ELIMINATION_AT_GEN_END, modifyOutputArr=True, dbgCatalogueValue=-797797)
  
  
  def dbgCellIsInBadColumn(self, cell):
    """
    test whether a cell is in a column that should not even have any cells in the cellTargeter rankings. This is a test to see what kinds of consequences there are for neither updating cellTargeter.rankings upon crit cell callback nor filtering out invalid rankings entries as they are encountered.
    """
    warn("PyCellElimRun.CellElimRunCodecState.dbgCellIsInBadColumn: SLOW: this method should NOT be used outside of testing! It runs once per cell visited!")
    return (self.cellCatalogue.getColumn(cell[:-1]).countUnknowns() <= 1)





def expandArgsToCERCSHeaderDict(args):
  if len(args) == 1:
    if not type(args[0]) == dict:
      raise TypeError("unnaceptable type for single arg: {}.".format(repr(type(args[0]))))
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




def doLiteralTests():
  testResult = cellElimRunBlockTranscode([2,2,2,2,2],"encode","linear",{"size":[5,5]})
  assertEqual(testResult[0], 20)
  assertEqual(sum(testResult[1:]), 0)
  assertEqual(cellElimRunBlockTranscode([20],"decode","linear",{"size":[5,5]}), [2,2,2,2,2])

  testResult = cellElimRunBlockTranscode([5,6,7,6,5], "encode", "linear", {"size":[5,10], "endpoint_init_mode":"middle"})
  assertEqual(testResult[:2], [32,10])
  assertEqual(sum(testResult[2:]), 0)
  assertEqual(cellElimRunBlockTranscode([32,10,0,0,0], "decode", "linear", {"size":[5,10], "endpoint_init_mode":"middle"}), [5,6,7,6,5])

  testResult = makeArr(genCellElimRunBlockSeqTranscode([5,6,7,6,5,5,6,7,6,5], "encode", "linear", {"size":[5,10], "endpoint_init_mode":"middle"}))
  assertEqual(testResult, [32,10,32,10])
  assertEqual(makeArr(genCellElimRunBlockSeqTranscode([32,10,32,10], "decode", "linear", {"size":[5,10], "endpoint_init_mode":"middle"})), [5,6,7,6,5,5,6,7,6,5])

  testResult = cellElimRunBlockCodec.encode([5,6,7,8,9,8,7,6,5,4], {"space_definition":{"size":[10,10], "bounds":{"lower":"EMBED:AFTER_PREP_OP_MODE", "upper":"EMBED:AFTER_PREP_OP_MODE"}, "bound_touches":{"east":"EMBED:AFTER_PREP_OP_MODE:1", "north":"EMBED:AFTER_PREP_OP_MODE:1", "south":"EMBED:AFTER_PREP_OP_MODE:1",  "west":"EMBED:AFTER_PREP_OP_MODE:1"}}})
  assertEqual(testResult, [4,10,4,4,9,5,35])



  testResult = cellElimRunBlockTranscode([[1,2,3,2,1],[2,3,5,3,2],[3,5,8,5,3],[2,3,5,3,2],[1,2,3,2,1]],"encode",{"interpolation_mode":{"method_name":"inverse_distance_weighted"},"space_definition":{"size":[5,5,10]}})

  assertEqual(testResult, [25, 31, 9, 25, 14, 74, 8, 0, 0, 0], "it's actually {}.".format(testResult))
  
#doLiteralTests()
print("PyCellElimRun: skipping literal tests.")


for testEndpointInitMode in [["middle","middle"],["zero","maximum"],["zero","zero"]]:
  assert CodecTools.roundTripTest(cellElimRunBlockCodec.clone(extraArgs=["linear",{"size":(5,101),"endpoint_init_mode":testEndpointInitMode}]),[5,0,100,75,50])


