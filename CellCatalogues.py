"""

CellCatalogues.py by John Dorsey.

CellCatalogues.py contains classes for tracking the states of cells in the Cell Elimination Run Codec State.

"""

import PyDeepArrTools
from PyDeepArrTools import enumerateDeeply



def clamp(value, minmax):
  return min(max(value, minmax[0]), minmax[1])



class NoChangeError(Exception):
  pass



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
    
  def eliminateColumn(self, dbgCustomValue=-1):
    raise NotImplementedError("CellCatalogueColumn feature eliminateColumn was not implemented.")
  def eliminateCell(self, cellHeight):
    raise NotImplementedError("CellCatalogueColumn feature eliminateCell was not implemented.")
  def genExtremeUnknownCells(self, sides=None):
    raise NotImplementedError("CellCatalogueColumn feature genExtremeUnknownCells was not implemented.")
  def clampCell(self, cellHeight):
    raise NotImplementedError("CellCatalogueColumn feature clampCell was not implemented.")






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
    print("GridCellCatalogueColumn.eliminateColumn called with dbgCustomValue {}. The dbgCustomValue will be ignored.".format(dbgCustomValue))
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
    self.size = size
    self.limits = [-1,self.size]
    
    
  def imposeMinimum(self, newMinimum):
    self.limits[0] = max(self.limits[0], newMinimum-1)
    assert self.limits[1]-self.limits[0] > 4, "this could cause critical column routine problems."
  
  
  def imposeMaximum(self, newMaximum):
    self.limits[1] = min(self.limits[1], newMaximum+1)
    assert self.limits[1]-self.limits[0] > 4, "this could cause critical column routine problems."


  def getCellStatus(self, cellHeight):
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
    return max(0, self.limits[1]-self.limits[0]-1)


  def eliminateColumn(self, dbgCustomValue=-1):
    self.limits[0] = dbgCustomValue
    self.limits[1] = dbgCustomValue


  def eliminateCell(self, cellHeight):
    if self.getCellStatus(cellHeight) == CellCatalogue.ELIMVAL:
      print("PyCellElimRun.LimitsCellCatalogueColumn.eliminateCell: The cell {} is already eliminated. eliminateCell should not be called on cells that are already eliminated (the limits for this column are {})! But let's see what happens if the program continues to run.".format(cellHeight, self.limits))
    if cellHeight == self.limits[0]+1:
      self.limits[0] += 1
    elif cellHeight == self.limits[1]-1:
      self.limits[1] -= 1
    else:
      print("PyCellElimRun.LimitsCellCatalogueColumn.eliminateCell: The cell {} can't be eliminated, because it is not at the edge of the area of eliminated cells (the limits for this column are {})! but let's see what happens if the program continues to run.".format(cellHeight, self.limits))
    if self.limits[0] + 2 == self.limits[1]:
      assert self.countUnknowns() == 1
      return True #indicate that the column is critical.
    else:
      assert self.countUnknowns() > 1
      return False #indicate that the column is not critical.


  def genExtremeUnknownCells(self, sides=None): #a function to get a list of all cells at the edges of the area of cells that have not been eliminated (hopefully totalling two cells per column (sample)).
    if sides == None:
      sides = [True, True] #sides[0] = include bottom cells?, sides[1] = include top cells?. if both are false, a cell can only be part of the output if it is the lone unknown cell in its column.
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

  print("PyCellElimRun.LimitsCellCatalogueColumn: warning at definition time: slow: the clampCell method has redundant tests and should be fixed.")
  def clampCell(self, cellHeight): #move a cell's value to make it comply with the catalogue of eliminated cells.
    assert self.countUnknowns() >= 1, "This column can no longer clamp cells, because it has no unknown space! Its limits are {}.".format(self.limits)
    assert self.limits[1]-self.limits[0] > 1, "Impossible to fail this test after passing the previous one. limits are {}.".format(self.limits)
    result = clamp(cellHeight,(self.limits[0]+1,self.limits[1]-1))
    if result == cellHeight:
      raise NoChangeError("this method failed.")
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

  def genExtremeUnknownCells(self, sides=None): #a function to get a list of all cells at the edges of the area of cells that have not been eliminated (hopefully totalling two cells per column (sample)).
    if sides == None:
      sides = [True, True] #sides[0] = include bottom cells?, sides[1] = include top cells?. if both are false, a cell can only be part of the output if it is the lone unknown cell in its column.
    #result = []
    for columnID, column in self.iterColumnsAndIDs():
      for extremeUnknownCell in column.genExtremeUnknownCells(sides=sides):
        assert extremeUnknownCell != None
        yield columnID + [extremeUnknownCell]

  def clampCell(self,cell): #move a cell's value to make it comply with the catalogue of eliminated cells.
    return cell[:-1] + [self.getColumn(cell[:-1]).clampCell(cell[-1])]

  def clampValues(self, data):
    #similar to Curves.Spline.interpolateMissingValues.
    #this method wasn't necessary before tests involving exciting cer cell targeting because of rankings running out because of new rankings filtering for eliminated columns.
    clampCapableCounter = 0
    changeCounter = 0
    for columnID,valueInDataColumn in enumerateDeeply(data):
      column = self.getColumn(columnID)
      if column.countUnknowns() == 0:
        continue
      else:
        assert column.countUnknowns() != 1
        clampCapableCounter += 1
      try:
        newValue = column.clampCell(valueInDataColumn)
      except NoChangeError:
        continue
      originalValue = PyDeepArrTools.setValueUsingPath(data, columnID, newValue)
      if originalValue != newValue:
        changeCounter += 1
        assert originalValue == None, "a non-none value ({}) was changed.".format(originalValue)
    if changeCounter > 0:
      print("PyCellElimRun.ColumnCellCatalogue.clampValues changed {} values. {} columns were capable of clamping.".format(changeCounter, clampCapableCounter))

