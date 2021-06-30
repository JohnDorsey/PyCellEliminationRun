
"""

Codes.py by John Dorsey.

Codes.py contains tools for encoding and decoding universal codes like fibonacci coding, elias gamma coding, elias delta coding, and unary coding.

"""



"""
from wikipedia:
  Symbol 	Fibonacci representation 	Fibonacci code word 	Implied probability
1 	F ( 2 ) {\displaystyle F(2)} F(2) 	11 	1/4
2 	F ( 3 ) {\displaystyle F(3)} F(3) 	011 	1/8
3 	F ( 4 ) {\displaystyle F(4)} F(4) 	0011 	1/16
4 	F ( 2 ) + F ( 4 ) {\displaystyle F(2)+F(4)} F(2)+F(4) 	1011 	1/16
5 	F ( 5 ) {\displaystyle F(5)} F(5) 	00011 	1/32
6 	F ( 2 ) + F ( 5 ) {\displaystyle F(2)+F(5)} F(2)+F(5) 	10011 	1/32
7 	F ( 3 ) + F ( 5 ) {\displaystyle F(3)+F(5)} F(3)+F(5) 	01011 	1/32
8 	F ( 6 ) {\displaystyle F(6)} F(6) 	000011 	1/64
9 	F ( 2 ) + F ( 6 ) {\displaystyle F(2)+F(6)} F(2)+F(6) 	100011 	1/64
10 	F ( 3 ) + F ( 6 ) {\displaystyle F(3)+F(6)} F(3)+F(6) 	010011 	1/64
11 	F ( 4 ) + F ( 6 ) {\displaystyle F(4)+F(6)} F(4)+F(6) 	001011 	1/64
12 	F ( 2 ) + F ( 4 ) + F ( 6 ) {\displaystyle F(2)+F(4)+F(6)} F(2)+F(4)+F(6) 	101011 	1/64
13 	F ( 7 ) {\displaystyle F(7)} F(7) 	0000011 	1/128
14 	F ( 2 ) + F ( 7 ) {\displaystyle F(2)+F(7)} F(2)+F(7) 	1000011 	1/128 """

fibNums = [1,1]

for i in range(8192):
  fibNums.append(fibNums[-1]+fibNums[-2])


def parsePrefix(inputStr,conditionFun):
  #this slow method can search the beginning of an input string for the proper slice length to satisfy a condition, and then return it.
  prefixLength = None
  #print("parsePrefix starts.")
  #print([inputStr,prefixLength,inputStr[:prefixLength],conditionFun(inputStr[:prefixLength])])
  if len(inputStr) == 1:
    if conditionFun(inputStr):
      return inputStr
    else:
      return None
  for i in range(1,len(inputStr)+1):
    #print([inputStr,i,prefixLength,inputStr[:i],inputStr[:prefixLength],conditionFun(inputStr[:i]),conditionFun(inputStr[:prefixLength])])
    if conditionFun(inputStr[:i]):
      #print("condition true, ")
      #print([inputStr,i,prefixLength,inputStr[:i],inputStr[:prefixLength],conditionFun(inputStr[:i]),conditionFun(inputStr[:prefixLength])])
      prefixLength = i
      assert conditionFun(inputStr[:prefixLength])
    else:
      #print("condition false, ")
      #print([inputStr,i,prefixLength,inputStr[:i],inputStr[:prefixLength],conditionFun(inputStr[:i]),conditionFun(inputStr[:prefixLength])])

      if not prefixLength == None:
        assert conditionFun(inputStr[:prefixLength])
        assert prefixLength == i-1
        assert not conditionFun(inputStr[:i])
        return inputStr[:prefixLength]
      assert prefixLength == None
  if prefixLength == None:
    #assert False
    return None
  #assert False
  return None





def intToHybridCodeBitStr(inputInt,prefixConverterFun,prefixValueGetterFun=(lambda payloadString: len(payloadString)),payloadConverterFun=(lambda payloadInt: bin(payloadInt)[3:])): #not tested thoroughly.
  payloadString = payloadConverterFun(inputInt)
  prefixValue = prefixValueGetterFun(payloadString)
  return prefixConverterFun(prefixValue) + payloadString

def hybridCodeBitStrToInt(inputBitStr,prefixParserFun,prefixConverterFun,payloadConverterFun=(lambda payloadString: int("1"+payloadString,2))): #not tested thoroughly.
  #prefixRaw = prefixParserFun(inputBitStr)
  #prefixValue = prefixConverterFun(prefixRaw) #this duplicates work.
  #prefixValue = prefixParserFun(inputBitStr)
  return payloadConverterFun(inputBitStr[len(prefixRaw):len(prefixRaw)+prefixValue])






def intToFibcodeBitStr(inputInt,startPoint=None):
  return "".join(str(item) for item in intToFibcodeBitArr(inputInt,startPoint=startPoint))

def intToFibcodeBitArr(inputInt,startPoint=None):
  assert inputInt >= 1
  assert inputInt < fibNums[-1]
  if startPoint == None:
    startPoint = len(fibNums)-1
    """while fibNums[startPoint-1] > inputInt:
      startPoint -= 1"""
  index = startPoint
  currentInt = inputInt
  result = []
  while index >= 0:
    if fibNums[index] <= currentInt:
      currentInt -= fibNums[index]
      result.append(1)
    else:
      if len(result) > 0:
        result.append(0)
    index -= 1
  result.reverse()
  result.append(1)
  return result[1:] #I don't know why this is necessary.

def fibcodeBitStrToInt(inputBitStr,mode="parse"):
  #return fibcodeBitArrToInt([int(bitChr) for bitChr in inputBitStr],mode=mode)
  if mode == "convert":
    return fibcodeBitArrToInt([int(bitChr) for bitChr in inputBitStr])
  elif mode == "detailed_parse":
    for offset in range(0,len(inputBitStr)):
      if inputBitStr[offset:offset+2] == "11":
        return [inputBitStr[:offset+2],fibcodeBitStrToInt(inputBitStr[:offset+2],mode="convert")]
  elif mode == "parse":
    return fibcodeBitStrToInt(inputBitStr,mode="detailed_parse")[1] #maybe this is simpler.
  else:
    assert False, "bad mode."
      

def fibcodeBitArrToInt(inputBitArr,mode="parse"):
  return sum([fibNums[i+1]*inputBitArr[i] for i in range(len(inputBitArr)-1)])
  #for i in range(len(inputBitArr))


def intSeqToFibcodeSeqStr(inputIntSeq,addDebugCommas=False):
  return ("," if addDebugCommas else "").join(intToFibcodeBitStr(inputInt) for inputInt in inputIntSeq)

def fibcodeSeqStrToIntArr(inputFibcodeSeqStr):
  #the input isn't generator safe, but it could be. Or this entire method could be thrown away and its behavior handled by the UniversalCoding class.
  skipLastItem = inputFibcodeSeqStr.endswith("11")
  return [fibcodeBitStrToInt(item+"11") for item in (inputFibcodeSeqStr.split("11")[:-1] if skipLastItem else inputFibcodeSeqStr.split("11"))]



def intToUnaryBitStr(inputNum):
  return ("0"*inputNum)+"1"

def unaryBitStrToInt(inputBitStr,mode="parse"):
  assert mode in ["convert","parse","detailed_parse"]
  result = 0
  for char in inputBitStr:
    if char == "0":
      result += 1
    else:
      assert char == "1"
      break
  if mode=="convert":
    assert inputBitStr[result+1:]=="1"
  if mode == "detailed_parse":
    return [intToUnaryBitStr(result),result]
  return result

def validateUnaryBitStr(inputBitStr):
  if len(inputBitStr) < 1:
    return False
  if not "1" in inputBitStr:
    return False
  for item in inputBitStr[:-1]:
    if item!="0":
      return False
  if inputBitStr[-1] != "1":
    return False
  return True


def validateBinaryBitStr(inputBitStr):
  if len(inputBitStr.replace("0","").replace("1","")) > 0:
    return False
  return True
#def unaryBitStrFromStr(inputBitStr):
 # pass


def intToEliasGammaBitStr(inputNum):
  assert inputNum >= 1
  return (("0"*(inputNum.bit_length()-1))+bin(inputNum)[2:]) if inputNum > 1 else "1"

def eliasGammaBitStrToInt(inputBitStr,mode="parse"): #@ broken right now.
  assert mode in ["convert","parse","detailed_parse"]
  if mode == "convert":
    return int(inputBitStr,2) #special case of this format of method. Usually the convert branch would look like parsing and then making sure that the rest of the data is empty.
  elif mode in ["parse","detailed_parse"]:
    prefixValue = unaryBitStrToInt(inputBitStr,mode="parse")
    result = inputBitStr[prefixValue+1:prefixValue+prefixValue+1]
    if mode == "detailed_parse":
      return [inputBitStr[:prefixValue+prefixValue+1],int("1"+result,2)]
    return int("1"+result,2)
  else:
    assert False, "reality error."

"""
def validateEliasGammaBitStr(inputBitStr):
  if inputBitStr == "1":
    return True
  prefixLength = None
  for i in range(len(inputBitStr)):
    if validateUnaryBitStr(inputBitStr[:i]):
      prefixLength = i
      break
  if prefixLength == None:
    return False
  if len(inputBitStr)-prefixLength != unaryBitStrToInt(inputBitStr[:prefixLength]):
    return False
  return validateBinaryBitStr(inputBitStr[prefixLength:])"""

def validateEliasGammaBitStr(inputBitStr):
  if inputBitStr == "1":
    return True
  prefix = parsePrefix(inputBitStr,validateUnaryBitStr)
  if prefix == None:
    return False
  prefixLength = len(prefix)
  if len(inputBitStr)-prefixLength != unaryBitStrToInt(prefix):
    return False
  return validateBinaryBitStr(inputBitStr[prefixLength:])
  
def eliasGammaSeqStrToIntArr(inputBitStr):
  startIndex = 0
  result = []
  while startIndex < len(inputBitStr):
    prefix = parsePrefix(inputBitStr[startIndex:],validateEliasGammaBitStr) #could be faster by breaking down this task into finding the unary prefix and following steps.
    result.append(eliasGammaBitStrToInt(prefix))
    startIndex += len(prefix)
  return result

"""
def intToEliasDeltaBitStr(inputNum):
  assert inputNum >= 1
  return intToEliasGammaBitStr(inputNum.bit_length())+bin(inputNum)[3:] if inputNum > 1 else "1"
"""

"""def EliasDeltaBitStrToInt(inputBitStr):
  prefix = parsePrefix(inputBitStr,validateEliasGammaBitStr) #this causes slow and avoidable repeated failures.
  """
"""
def eliasDeltaBitStrToInt(inputBitStr,mode="parse"):
  assert mode in ["convert","parse","detailed_parse"]
  prefix = parsePrefix(inputBitStr,validateEliasGammaBitStr) #@ this causes slow and avoidable repeated failures.
  prefixLength = len(prefix)
  prefixValue = eliasGammaBitStrToInt(prefix)
  result = inputBitStr[prefixLength:prefixLength+prefixValue]
  #result = int("1"+result,2)
  #print([inputBitStr,prefix,prefixLength,prefixValue,result])
  if mode=="convert":
    assert prefixLength+prefixValue == len(inputBitStr)
  if mode == "detailed_parse":
    return [inputBitStr[:prefixLength+prefixValue],int("1"+result,2)]
  return int("1"+result,2)


def intSeqToEliasDeltaSeqStr(inputIntSeq):
  return "".join(intToEliasDeltaBitStr(inputInt) for inputInt in inputIntSeq)
"""






def intToEliasGammaIotaBitStr(inputInt,maxPayload):
  assert type(inputInt) == int
  maxPayloadLength = len(bin(maxPayload)[3:])
  #print("maxPayloadLength="+str(maxPayloadLength))
  prefixLength = len(bin(maxPayloadLength)[2:])
  #print("prefixLength="+str(prefixLength))
  return bin(len(bin(inputInt)[3:]))[2:].rjust(prefixLength,"0") + bin(inputInt)[3:]

def eliasGammaIotaBitStrToInt(inputBitStr,maxPayload,mode="parse"):
  assert type(inputBitStr) == str
  if not mode == "parse":
    print("WARNING: for eliasGammaIotaBitStrToInt, modes other than parse are not implemented, and parse mode be used in their stead. This might cause slower execution and incorrect results.")
  maxPayloadLength = len(bin(maxPayload)[3:])
  #print("maxPayloadLength="+str(maxPayloadLength))
  prefixLength = len(bin(maxPayloadLength)[2:])
  #print("prefixLength="+str(prefixLength))
  prefixValue = int(inputBitStr[:prefixLength],2)
  #print("prefixValue="+str(prefixValue))
  return int("1"+inputBitStr[prefixLength:prefixLength+prefixValue],2)



def intToEliasDeltaIotaBitStr(inputInt,maxPayload): #@ not yet proven optimal.
  assert type(inputInt) == int
  return intToHybridCodeBitStr(inputInt,(lambda x: intToEliasGammaIotaBitStr(x+1,len(bin(maxPayload)[3:])+1)))

def eliasDeltaIotaBitStrToInt(inputBitStr,maxPayload): #@ not yet proven optimal.
  assert type(inputBitStr) == str
  parseFun = (lambda x: eliasGammaIotaBitStrToInt(x,len(bin(maxPayload)[3:])+1,mode="parse")-1)
  convertFun = (lambda x: eliasGammaIotaBitStrToInt(x,len(bin(maxPayload)[3:])+1,mode="convert")-1)
  return hybridCodeBitStrToInt(inputBitStr,parseFun,convertFun)






class UniversalCoding:
  def __init__(self,intToBitStrFun,bitStrToIntFun,intSeqToBitStrFun,bitStrToIntSeqFun,zeroSafe=False):
    if intToBitStrFun:
      self.intToBitStr = intToBitStrFun
    if bitStrToIntFun:
      self.bitStrToInt = bitStrToIntFun
    if intSeqToBitStrFun:
      self.intSeqToBitStr = intSeqToBitStrFun
    if bitStrToIntSeqFun:
      self.bitStrToIntSeq = bitStrToIntSeqFun
    self.zeroSafe=zeroSafe
  def intToBitStr(self,inputInt):
    assert False, "intToBitStr has not been implemented."
  def bitStrToInt(self,inputBitStr):
    assert False, "bitStrToInt has not been implemented."
  def intSeqToBitStr(self,inputIntSeq):
    return "".join(self.intToBitStr(item) for item in inputIntSeq)
  def bitStrToIntSeq(self,inputBitStr):
    offset = 0
    parseResult = None
    while offset < len(inputBitStr):
      parseResult = self.bitStrToInt(inputBitStr[offset:],mode="detailed_parse")
      offset += len(parseResult[0])
      yield parseResult[1]
  

fibonacciCoding = UniversalCoding(intToFibcodeBitStr,fibcodeBitStrToInt,intSeqToFibcodeSeqStr,fibcodeSeqStrToIntArr)
unaryCoding = UniversalCoding(intToUnaryBitStr,unaryBitStrToInt,None,None)
eliasGammaCoding = UniversalCoding(intToEliasGammaBitStr,eliasGammaBitStrToInt,None,None)
#eliasDeltaCoding = UniversalCoding(intToEliasDeltaBitStr,eliasDeltaBitStrToInt,None,None)
#eliasGammaIotaCoding = UniversalCoding(intToEliasGammaIotaBitStr,eliasGammaIotaBitStrToInt,None,None)
#eliasDeltaIotaCoding = UniversalCoding(intToEliasDeltaIotaBitStr,eliasDeltaIotaBitStrToInt,None,None)


assert parsePrefix("00001Hello",validateUnaryBitStr)=="00001"
assert parsePrefix("101101101World",validateBinaryBitStr)=="101101101"

assert sum([validateEliasGammaBitStr(bin(item)[2:]) for item in range(1,100) if bin(item)[2:] not in [intToEliasGammaBitStr(i) for i in range(1,10)]]) == 0
assert sum([validateEliasGammaBitStr(item) for item in [intToEliasGammaBitStr(i) for i in range(1,100)]]) == 99

#assert [eliasDeltaBitStrToInt(intToEliasDeltaBitStr(i)) for i in range(1,32)] == [i for i in range(1,32)]

