"""

IntSeqMath.py by John Dorsey.

IntSeqMath.py contains tools for transforming integer sequences into other integer sequences.

"""

from PyGenTools import genTakeOnly, arrTakeOnly



def genTrackMean(inputNumSeq):
  currentSum = 0
  for i,item in enumerate(inputNumSeq):
    currentSum += item
    yield (currentSum/float(i+1),item)

def genTrackMin(inputNumSeq):
  currentMin = None
  for i,item in enumerate(inputNumSeq):
    if i == 0:
      currentMin = item
    else:
      currentMin = min(currentMin,item)
    yield (currentMin,item)



def genDeltaEncode(inputNumSeq):
  previousItem = 0
  for item in inputNumSeq:
    yield item - previousItem
    previousItem = item

def genDeltaDecode(inputNumSeq):
  previousItem = 0
  for item in inputNumSeq:
    yield item + previousItem
    previousItem += item




def genRecordLows(inputNumSeq):
  recordLow = None
  justStarted = True
  for item in inputNumSeq:
    if justStarted:
      recordLow = item
      yield item
      justStarted = False
      continue
    if item < recordLow:
      recordLow = item
      yield item

"""
def findBasicColumnInfo(inputSeq,delimiter):
  #in tattered data (lines of different lengths), for each index counting from the left, collect info on all values that exist at that index.
  i = 0
  columnMinimums = []
  columnMaximums = []
  columnSizes = []
  columnSums = []
  columnProducts = []
  for item in inputSeq:
    if item == delimiter:
      i = 0
      continue
    if i == len(columnMinimums):
      columnMinimums.append(item)
      assert i == len(columnMaximums)
      columnMaximums.append(item)
      assert i == len(columnSizes)
      columnSizes.append(1)
      assert i == len(columnSums)
      columnSums.append(item)
      assert i == len(columnProducts)
      columnProducts.append(item)
    else:
      columnMinimums[i] = min(columnMinimums[i],item)
      columnMaximums[i] = max(columnMaximums[i],item)
      columnSizes[i] += 1
      columnSums[i] += item
      columnProducts[i] *= item
    i += 1
  return {"columnMinimums":columnMinimums, "columnMaximums":columnMaximums, "columnSizes":columnSizes, "columnSums":columnSums, "columnProducts":columnProducts}
"""
def columnSetStatReporterFun(i,item,report):
  if report == None:
    return {"size":1,"min":item,"max":item,"sum":item,"product":item}
  else:
    return {"size":report["size"]+1,"min":min(item,report["min"]),"max":max(item,report["max"]),"sum":report["sum"]+item,"product":report["product"]*item}

def findColumnInfo(inputSeq,delimiter,reporterFun):
  #in tattered data (lines of different lengths), for each index counting from the left, collect info on all values that exist at that index.
  i = 0
  columnReports = []
  for item in inputSeq:
    if item == delimiter:
      i = 0
      continue
    if i == len(columnReports):
      columnReports.append(reporterFun(i,item,None))
    else:
      columnReports[i] = reporterFun(i,item,columnReports[i])
    i += 1
  return columnReports

def applyColumnAwareFun(inputSeq,transformerFun):
  i = 0
  for item in inputSeq:
    modifiedItem = transformerFun(i,item)
    reset = yield item
    if reset:
      i = 0
      continue


assert [item for item in genDeltaDecode(genDeltaEncode([5,5,6,5,3,0,10,0]))] == [5,5,6,5,3,0,10,0]

