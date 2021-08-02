
def shape(data):
  result = [len(data)]
  while type(data[0]) == list:
    data = data[0]
    result.append(len(data))
  return tuple(result)
  
  
def enumerateDeeply(data,uniformDepth=True):
    if uniformDepth:
      assert all(type(subItem)==list for subItem in data) or all(type(subItem)!=list for subItem in data)
    if type(data) == list:
      for i,subItem in enumerate(data):
        if type(subItem) != list:
          yield ([i], subItem)
        else:
          assert type(subItem) == list
          subItemIterator = enumerateDeeply(subItem,uniformDepth=uniformDepth)
          for item in subItemIterator:
            assert type(item) == list
            yield ([i] + item[0], item[1])
    else:
      raise ValueError("enumerateDeeply called on invalid type.")
      
      
def setValueUsingPath(data,path,value,requireSameType=True,allowOverwriteNone=True):
  assert type(data) == list
  for pathElement in path[:-1]:
    data = data[pathElement]
  assert type(data) == list, "path is too long for the data!"
  assert type(data[path[-1]]) != list, "path is too short for the data!"
  if requireSameType:
    assert type(data[path[-1]]) == type(value) or (allowOverwriteNone and data[path[-1]] == None)
  data[path[-1]] = value
  
def setValueUsingCell(data,cell,**kwargs):
  setValueUsingPath(data,cell[:-1],cell[-1],**kwargs)
