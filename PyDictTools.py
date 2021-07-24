from PyGenTools import makeGen


def augmentDict(dict0, dict1):
  for key in dict1.keys():
    if not key in dict0.keys():
      dict0[key] = dict1[key]

def modifyDict(dict0, dict1):
  for key in dict1.keys():
    if key in dict0.keys():
      dict0[key] = dict1[key]

def augmentedDict(dict0, dict1):
  result = {}
  for key in dict0.keys():
    result[key] = dict0[key]
  for key in dict1.keys():
    if not key in result.keys():
      result[key] = dict1[key]
  return result

def modifiedDict(dict0, dict1):
  result = {}
  for key in dict0.keys():
    result[key] = dict0[key]
  for key in dict1.keys():
    if key in result.keys():
      result[key] = dict1[key]
  return result


def makeFromTemplateAndSeq(template, inputSeq, triggerFun, sortDictKeys=True, recursive=True):
  inputGen = makeGen(inputSeq)
  result = None
  templateKeySeq = None
  if type(template) == dict:
    result = {}
    templateKeySeq = sorted(template.keys()) if sortDictKeys else template.keys()
  elif type(template) == list:
    result = [None for i in range(len(template))]
    templateKeySeq = range(len(template))
  else:
    raise TypeError("unsupported template type: " + str(type(template)) + ".")

  for templateKey in templateKeySeq:
    originalValue = template[templateKey]
    if triggerFun(originalValue):
      if type(originalValue) in [list,dict]:
        raise ValueError("The provided triggerFun returned True when a value of type " + str(type(originalValue)) + " was tested with it. This makes recursion impossible.")
      result[templateKey] = next(inputGen)
    else:
      if recursive and type(originalValue) in [list,dict]:
        result[templateKey] = makeFromTemplateAndSeq(originalValue,inputGen,triggerFun,sortDictKeys=sortDictKeys,recursive=recursive)
      else:
        result[templateKey] = originalValue
  return result


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

