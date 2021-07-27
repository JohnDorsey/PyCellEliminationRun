from PyGenTools import makeGen, makeArr








def makeFlatKeySeq(template, sortDictKeys=True): #flat means nonrescursive.
  templateKeySeq = None
  if type(template) == dict:
    templateKeySeq = sorted(template.keys()) if sortDictKeys else template.keys()
  elif type(template) == list:
    templateKeySeq = range(len(template))
  else:
    raise TypeError("unsupported template type: " + str(type(template)) + ".")
  return templateKeySeq

def makeBlankResultFromTemplate(template):
  if type(template) == dict:
    return {}
  elif type(template) == list:
    return [None for i in range(len(template))]
  else:
    raise TypeError("unsupported template type: " + str(type(template)) + ".")
    
def makeBlankResultAndKeySeqFromTemplate(template,sortDictKeys=True):
  return (makeBlankResultFromTemplate(template), makeFlatKeySeq(template, sortDictKeys=sortDictKeys))









def augmentDict(dict0, dict1, recursive=True, recursiveTypes=None):
  if recursiveTypes == None:
    recursiveTypes = [list,dict]
  if dict0 == None or dict1 == None:
    raise ValueError("received None for a dict argument.")
  for key in makeFlatKeySeq(dict1):
    if not key in makeFlatKeySeq(dict0):
      dict0[key] = dict1[key]
    else:
      if recursive:
        if type(dict0[key]) in recursiveTypes and type(dict1[key]) in recursiveTypes:
          if type(dict0[key]) == type(dict1[key]):
            augmentDict(dict0[key],dict1[key],recursive=recursive,recursiveTypes=recursiveTypes)
          else:
            print("PyDictTools.augmentDict: recursive: warning: inputs have a value type mismatch at key " + str(key) + " where recursion would otherwise be possible.")
          
def cloneDict(inputStructure):
  result, keySeq = makeBlankResultAndKeySeqFromTemplate(inputStructure,sortDictKeys=False)
  for key in keySeq:
    if type(inputStructure[key]) in [list,dict]:
      result[key] = cloneDict(inputStructure[key])
    elif type(inputStructure[key]) == str:
      result[key] = inputStructure[key]
    else:
      result[key] = eval(str(inputStructure[key]))
  return result

def augmentedDict(dict0, dict1, **kwargs):
  result = cloneDict(dict0)
  augmentDict(result, dict1, **kwargs)
  return result


         
"""
def modifyDict(dict0, dict1):
  for key in dict1.keys():
    if key in dict0.keys():
      dict0[key] = dict1[key]
"""
"""
def modifiedDict(dict0, dict1):
  result = {}
  for key in dict0.keys():
    result[key] = dict0[key]
  for key in dict1.keys():
    if key in result.keys():
      result[key] = dict1[key]
  return result
"""

def editDict(inputDict,editFun,recursive=True):
  for key in inputDict.keys():
    if type(inputDict[key]) == dict and recursive:
      editDict(inputDict[key],editFun,recursive=recursive)
    inputDict[key] = editFun(inputDict[key])
    
def replace(inputDict,a,b,recursive=True):
  editDict(inputDict,(lambda x: b if x==a else x),recursive=recursive)





def makeFromTemplateAndSeq(template, inputSeq, valueTriggerFun, sortDictKeys=True, recursive=True, recursiveTypes=None):
  if recursiveTypes == None:
    recursiveTypes = [list,dict]
  inputGen = makeGen(inputSeq)
  result, templateKeySeq = makeBlankResultAndKeySeqFromTemplate(template,sortDictKeys=sortDictKeys)

  for templateKey in templateKeySeq:
    originalValue = template[templateKey]
    if valueTriggerFun(originalValue):
      if type(originalValue) in recursiveTypes:
        raise ValueError("The provided valueTriggerFun returned True when a value of type " + str(type(originalValue)) + " was tested with it. This makes recursion into that value impossible.")
      result[templateKey] = next(inputGen)
    else:
      if recursive and type(originalValue) in recursiveTypes:
        result[templateKey] = makeFromTemplateAndSeq(originalValue, inputGen, valueTriggerFun, sortDictKeys=sortDictKeys, recursive=recursive, recursiveTypes=recursiveTypes)
      else:
        result[templateKey] = originalValue
  return result

def makeFromTemplateAndNextFun(template, inputNextFun, valueTriggerFun, sortDictKeys=True, recursive=True, recursiveTypes=None):
  if recursiveTypes == None:
    recursiveTypes = [list,dict]
  inputGen = (inputNextFun() for i in range(2**16))
  return makeFromTemplateAndSeq(template, inputGen, valueTriggerFun, sortDictKeys=sortDictKeys, recursive=recursive, recursiveTypes=recursiveTypes)
  
"""
def makeFromTemplateAndKeywiseOracle(template, keywiseOracleFun, valueTriggerFun, sortDictKeys=True, recursive=True):
  result, templateKeySeq = makeBlankResultAndKeySeqFromTemplate(template,sortDictKeys)

  for templateKey in templateKeySeq:
    originalValue = template[templateKey]
    if valueTriggerFun(originalValue):
      if type(originalValue) in [list,dict]:
        raise ValueError("The provided valueTriggerFun returned True when a value of type " + str(type(originalValue)) + " was tested with it. This makes recursion into that value impossible.")
      result[templateKey] = keywiseOracleFun(templateKey, originalValue)
    else:
      if recursive and type(originalValue) in [list,dict]:
        result[templateKey] = makeFromTemplateAndKeywiseOracle(originalValue, keywiseOracleFun, valueTriggerFun, sortDictKeys=sortDictKeys,recursive=recursive)
      else:
        result[templateKey] = originalValue
  return result
"""



def makeFromTemplateAndPathwiseOracle(template, pathwiseOracleFun, valueTriggerFun, path=None, sortDictKeys=True, recursive=True):
  if path == None:
    path = []
  result, templateKeySeq = makeBlankResultAndKeySeqFromTemplate(template,sortDictKeys)

  for templateKey in templateKeySeq:
    originalValue = template[templateKey]
    if valueTriggerFun(originalValue):
      if type(originalValue) in [list,dict]:
        raise ValueError("The provided valueTriggerFun returned True when a value of type " + str(type(originalValue)) + " was tested with it. This makes recursion into that value impossible.")
      result[templateKey] = pathwiseOracleFun(path+[templateKey], originalValue)
    else:
      if recursive and type(originalValue) in [list,dict]:
        result[templateKey] = makeFromTemplateAndPathwiseOracle(originalValue, pathwiseOracleFun, valueTriggerFun, path=(path+[templateKey]), sortDictKeys=sortDictKeys, recursive=recursive)
      else:
        result[templateKey] = originalValue
  return result


def writeFromTemplateAndPathwiseOracle(destination, template, pathwiseOracleFun, valueTriggerFun, path=None, sortDictKeys=True, recursive=True):
  if path == None:
    path = []
  templateKeySeq = makeFlatKeySeq(template,sortDictKeys)
  destinationKeyArr = makeArr(makeFlatKeySeq(destination,sortDictKeys))
  
  for templateKey in templateKeySeq:
    originalValue = template[templateKey]
    if valueTriggerFun(originalValue):
      if type(originalValue) in [list,dict]:
        raise ValueError("The provided valueTriggerFun returned True when a value of type " + str(type(originalValue)) + " was tested with it. This makes recursion into that value impossible.")
      newValue = pathwiseOracleFun(path+[templateKey], originalValue)
      if not templateKey in destinationKeyArr:
        if type(destination) == list:
          raise IndexError("Can't augment a list by lengthening it.")
        assert type(destination) == dict
        destination[templateKey] = newValue
      elif newValue != originalValue: #if the pathwiseOracleFun had anything to say at all, this is also cause to write the value to the destination.
        destination[templateKey] = newValue      
    else:
      if recursive and type(originalValue) in [list,dict]:
        if templateKey in destinationKeyArr:
          if type(destination[templateKey]) == type(template[templateKey]):
            writeFromTemplateAndPathwiseOracle(destination[templateKey], template[templateKey], pathwiseOracleFun, valueTriggerFun, path=(path+[templateKey]), sortDictKeys=sortDictKeys, recursive=recursive)
      else:
        pass

def writeFromTemplateAndNextFun(destination, template, inputNextFun, valueTriggerFun, **kwargs):
  writeFromTemplateAndPathwiseOracle(destination, template, (lambda ignorePath, ignoreValue: inputNextFun()), valueTriggerFun, **kwargs)



def dictToList(inputDict,extractionFun=None):
  if extractionFun == None:
    extractionFun = (lambda x: x)
  errorCount = 0
  try:
    maxKey = max(inputDict.keys())
    minKey = min(key for key in inputDict.keys() if type(key)==int)
  except ValueError as ve:
    print("PyDictTools.dictToList: Warning: returning an empty list in order to ignore ValueError: " + str(ve) + ".")
    return []
  result = [None for i in range(maxKey+1)]
  assert len(result) >= maxKey
  assert minKey >= 0
  for key in inputDict.keys():
    if type(key) == int:
      if result[key] == None:
        result[key] = extractionFun(inputDict[key])
      else:
        assert False, "duplicate keys???"
    else:
      errorCount += 1
  if errorCount > 0:
    print("PyDictTools.dictToList: errorCount was " + str(errorCount) + ".")
  return result


assert makeFromTemplateAndSeq([0,0,0,1,0,1,0,1,0,[0,1,1,0],0,1,1],"Hello, world!",lambda x: x==1) == [0, 0, 0, 'H', 0, 'e', 0, 'l', 0, [0, 'l', 'o', 0], 0, ",", " "]

