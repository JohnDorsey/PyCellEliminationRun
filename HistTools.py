"""

HistTools.py by John Dorsey.

HistTools.py provides Histogram classes for tracking frequencies of occurrence of values in data.

"""




class SimpleListHist:
  def __init__(self,fillItem=0):
    self.data = list()
    self.oddballData = SimpleDictHist()
    self.fillItem = fillItem
  
  def __setitem__(self,key,value):
    if not key >= 0:
      raise IndexError("negative keys are not allowed.")
    while len(self.data) <= key:
      self.data.append(self.fillItem)
    self.data[key] = value

  def __getitem__(self,key):
    try:
      return self.data[key]
    except IndexError:
      return self.fillItem

  def register(self,key):
    self.registerMany(key,1)

  def registerMany(self,key,amount):
    if type(key) != int:
      self.oddballData.registerMany(key,amount)
      return
    #add more than 1 to the frequency of any item, but only increase the write count by 1. This is for making some occurences more valuable than others.
    currentValue = self.__getitem__(key)
    if currentValue == None: #it doesn't matter what self.fillItem is, any None must still be replaced with 0 before addition.
      currentValue = 0
    self.__setitem__(key,currentValue+amount)

  def registerFrom(self,keySeq):
    for key in keySeq:
      self.register(key)


class SimpleDictHist:
  def __init__(self):
    self.data = dict()
  
  def __setitem__(self,key,value):
    self.data[key] = value

  def __getitem__(self,key):
    try:
      return self.data[key]
    except KeyError:
      return None

  def register(self,key):
    self.registerMany(key,1)

  def registerMany(self,key,amount):
    #add more than 1 to the frequency of any item, but only increase the write count by 1. This is for making some occurences more valuable than others.
    currentValue = self.__getitem__(key)
    if currentValue == None:
      currentValue = 0
    self.data[key] = currentValue+amount

  def registerFrom(self,keySeq):
    for key in keySeq:
      self.register(key)


class OrderlyHist:
  #OrderlyHist is a histogram tool to track frequency, order first encountered, and order last encountered.
  def __init__(self,registrationShape=None):
    self.data = dict()
    self.writeCount = 0
    self.registeredAmount = 0
    self.registrationShape = registrationShape if (registrationShape != None) else [1]
    if sum(self.registrationShape) != 1:
      print("Hist.__init__: Warning: registrationShape sum differs from 1 by " + str(abs(1-sum(registrationShape))) + ".")

  def __setitem__(self,key,value):
    print("Hist.__setitem__ should not be used. totalAmount will not be updated.")
    assert len(value) == 3
    self.writeCount += 1
    self.data[key] = value

  def __getitem__(self,key):
    try:
      return self.data[key]
    except KeyError:
      return (None,None,None)

  def register(self,key):
    #add 1 to the frequency of any item.
    self.registerMany(key,1.0)

  def registerMany(self,key,amount):
    #add more than 1 to the frequency of any item, but only increase the write count by 1. This is for making some occurences more valuable than others.
    self.writeCount += 1
    self.registeredAmount += amount
    if type(key) == int:
      startKey = key-(len(self.registrationShape)>>1)
      for i,columnAmount in enumerate(self.registrationShape):
        self.editItem(startKey+i,columnAmount*amount)
    else:
      self.editItem(key,amount)

  def editItem(self,key,amount):
    currentValue = self.__getitem__(key)
    if None in currentValue:
      currentValue = (0.0,self.writeCount,self.writeCount)
    self.data[key] = (currentValue[0]+amount,currentValue[1],self.writeCount)
    assert len(self.data[key]) == 3

  def registerFrom(self,keySeq):
    for key in keySeq:
      self.register(key)

  def keysInDescendingFreqOrder(self):
    return [itemC[0] for itemC in sorted([item for item in self.data.iteritems()],key=(lambda itemB: itemB[1]))[::-1]]

  def keysInDescendingRelevanceOrder(self):
    #it is important that this method sorts first by frequency and then sorts by recentness within identical frequencies.
    keyFun = (lambda itemB: itemB[1][0]*(self.writeCount+1)+itemB[1][2])
    for value in self.data.values():
      assert len(value) == 3
    return [itemC[0] for itemC in sorted([item for item in self.data.iteritems()],key=keyFun)[::-1]]

