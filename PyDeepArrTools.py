import itertools

def shape(data):
  if not isinstance(data,list):
    raise TypeError("invalid input type {}.".format(repr(type(data))))
  result = [len(data)]
  while isinstance(data[0],list):
    data = data[0]
    result.append(len(data))
  return tuple(result)
  
def dataShape(data):
  raise NotImplementedError()
  
def isInShape(testPoint, testShape):
  return all(0<=pair[0]<pair[1] for pair in itertools.izip_longest(testPoint,testShape))
  
def arrIsUniform(data):
  return arrIsUniformlyShape(data,shape(data))
  
def arrIsUniformlyShape(data,dataShape):
  if len(data) != dataShape[0]:
    return False
  if len(dataShape) == 1: #if recursion should be avoided now:
    return True #there is no longer way to fail within this call.
  return all(arrIsUniformlyShape(subArr,dataShape[1:]) for subArr in data)
  
  
def iterateDeeply(*args,**kwargs):
  return (item[1] for item in enumerateDeeply(*args,**kwargs))
  
  
def enumerateDeeply(data,uniformDepth=True):
    if uniformDepth:
      assert all(type(subItem)==list for subItem in data) or all(type(subItem)!=list for subItem in data) #@ replace with pyGenTools.allAreEqual?
    if type(data) == list:
      for i,subItem in enumerate(data):
        if type(subItem) != list:
          yield ([i], subItem)
        else:
          assert type(subItem) == list
          subItemIterator = enumerateDeeply(subItem,uniformDepth=uniformDepth)
          for subSubItem in subItemIterator:
            if not type(subSubItem) == tuple:
              raise AssertionError("subSubItem has type {}.".format(repr(type(subSubItem))))
            yield ([i] + subSubItem[0], subSubItem[1])
    else:
      raise ValueError("enumerateDeeply called on invalid type.")
      
      

def dataInitializer(initSize,initFun): #broken?
  if len(initSize) == 1:
    return initFun(initSize[-1])
  return [dataInitializer(initSize[1:],initFun) for i in range(initSize[0])]
  
def noneInitializer(initSize):
  #return dataInitializer(initSize,(lambda length: [None for nonei in range(length)]))
  if len(initSize) == 1:
    return [None for nonei in range(initSize[0])]
  return [noneInitializer(initSize[1:]) for subi in range(initSize[0])]
      
def setValueUsingPath(data,path,value,requireSameType=True,allowOverwriteNone=True): # returns original value
  assert type(data) == list
  workingData = data
  try:
    for pathElementIndex,pathElement in enumerate(path[:-1]):
      workingData = workingData[pathElement]
  except IndexError:
    raise IndexError("pathElement with value {} at index {} in path {} out of range in data of shape {}; couldn't set value {}.".format(pathElement, pathElementIndex, path, shape(data), value)) 
  if type(workingData) != list:
    raise ValueError("path is too long for the data! path={}, shape(data)={}, shape(workingData)={}.".format(path,shape(data),shape(workingData)))
  if type(workingData[path[-1]]) == list:
    raise ValueError("path is too short for the data! path={}, shape(data)={}, type(workingData[path[-1]])={}, shape(workingData)={}.".format(path,shape(data),type(workingData[path[-1]]),shape(workingData)))
  if requireSameType:
    assert type(workingData[path[-1]]) == type(value) or (allowOverwriteNone and workingData[path[-1]] == None)
  oldValue = workingData[path[-1]]
  workingData[path[-1]] = value
  return oldValue
  
def getValueUsingPath(data,path,allowShortPath=False):
  assert type(data) == list
  for pathElement in path[:-1]:
    data = data[pathElement]
  assert type(data) == list, "path is too long for the data!"
  if not allowShortPath:
    assert type(data[path[-1]]) != list, "path is too short for the data!"
  return data[path[-1]]
  
def setValueUsingCell(data,cell,**kwargs):
  setValueUsingPath(data,cell[:-1],cell[-1],**kwargs)
  
  
  

