
import PyDictTools
from PyDictTools import augmentDict

from PyGenTools import ExhaustionError




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
    
  def doPhases(self, phaseNames):
    for phaseName in phaseNames:
      self.doPhase(phaseName)

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
    





def isEmbedCode(thing):
  if type(thing) == str:
    if thing.startswith("EMBED"):
      return True
  elif isinstance(thing, EmbedSign):
    return True
  else:
    return False
    
def getIncludedCodec(thing, default=None):
  if isinstance(thing,EmbedSign):
    return thing.getIncludedCodec(default=default)
  elif isEmbedCode(thing):
    if default == None:
      print("HeaderTools.getIncludedCodec: warning: default is None and will be returned.")
    return default
  else:
    print("HeaderTools.getIncludedCodec: warning: default will be returned because there is no embed code. default is {}.".format(default))
    return default

class EmbedSign:
  def __init__(self, includedCodec=None):
    self.includedCodec = includedCodec
    
  def getIncludedCodec(self, default=None):
    if self.includedCodec != None:
      return self.includedCodec
    elif default != None:
      return default
    else:
      print("HeaderTools.EmbedSign.getIncludedCodec: warning: returning None.")
      return None
      
      
      