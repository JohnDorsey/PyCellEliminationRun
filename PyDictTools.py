from PyGenTools import makeGen, makeArr


def augmentDict(dict0, dict1, recursive=True):
  for key in dict1.keys():
    if not key in dict0.keys():
      dict0[key] = dict1[key]
    else:
      if recursive:
        if type(dict0[key]) == dict:
          if type(dict1[key]) == dict:
            augmentDict(dict0[key],dict1[key],recursive=recursive)
          else:
            print("PyDictTools.augmentDict: recursive: warning: dict0 has a subdict where dict1 has something of type " + str(type(dict1[key])) + ".")
        else:
          if type(dict1[key]) == dict:
            print("PyDictTools.augmentDict: recursive: warning: dict1 has a subdict where dict0 has something of type " + str(type(dict0[key])) + ".")
   
def augmentedDict(dict0, dict1, recursive=True):
  result = {}
  for key in dict0.keys():
    result[key] = dict0[key]
  for key in dict1.keys():
    if not key in result.keys():
      result[key] = dict1[key]
    else:
      if recursive:
        if type(dict0[key]) == dict:
          if type(dict1[key]) == dict:
            result[key] = augmentedDict(dict0[key],dict1[key],recursive=recursive)
          else:
            print("PyDictTools.augmentedDict: recursive: warning: dict0 has a subdict where dict1 has something of type " + str(type(dict1[key])) + ".")
        else:
          if type(dict1[key]) == dict:
            print("PyDictTools.augmentedDict: recursive: warning: dict1 has a subdict where dict0 has something of type " + str(type(dict0[key])) + ".")
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



def makeKeySeqFromTemplate(template, sortDictKeys):
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
    
    
def makeBlankResultAndKeySeqFromTemplate(template,sortDictKeys):
  return (makeBlankResultFromTemplate(template),makeKeySeqFromTemplate(template, sortDictKeys))


def makeFromTemplateAndSeq(template, inputSeq, triggerFun, sortDictKeys=True, recursive=True):
  inputGen = makeGen(inputSeq)
  result, templateKeySeq = makeBlankResultAndKeySeqFromTemplate(template,sortDictKeys)

  for templateKey in templateKeySeq:
    originalValue = template[templateKey]
    if triggerFun(originalValue):
      if type(originalValue) in [list,dict]:
        raise ValueError("The provided triggerFun returned True when a value of type " + str(type(originalValue)) + " was tested with it. This makes recursion into that value impossible.")
      result[templateKey] = next(inputGen)
    else:
      if recursive and type(originalValue) in [list,dict]:
        result[templateKey] = makeFromTemplateAndSeq(originalValue,inputGen,triggerFun,sortDictKeys=sortDictKeys,recursive=recursive)
      else:
        result[templateKey] = originalValue
  return result


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
  templateKeySeq = makeKeySeqFromTemplate(template,sortDictKeys)
  destinationKeyArr = makeArr(makeKeySeqFromTemplate(destination,sortDictKeys))
  
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

