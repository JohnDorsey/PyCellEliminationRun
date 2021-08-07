
def rjustedArr(inputArr,length,fillItem=0,crop=False):
  if length < 0:
    raise ValueError("length cannot be negative.")
  return [fillItem for i in range(length-len(inputArr))] + (([] if length == 0 else ([inputArr[-1]] if length == 1 else inputArr[-length:])) if crop else inputArr)


def ljustedArr(inputArr,length,fillItem=0,crop=False):
  if length < 0:
    raise ValueError("length cannot be negative.")
  return (([] if length == 0 else inputArr[:length]) if crop else inputArr) + [fillItem for i in range(length-len(inputArr))]


def arrEndsWith(inputArr,testArr):
  testStartIndex = len(inputArr)-len(testArr)
  if testStartIndex < 0:
    raise ValueError("This test can't be performed because testArr is longer than inputArr.")
  return all((inputArr[testStartIndex+i]==testArr[i]) for i in range(len(testArr)))

  
  
  

def linearInsort(sortedList, newItem, keyFun=(lambda x: x)): #insert sorted with linear search.
  keyFunOfNewItem = keyFun(newItem) #caching this probably improves performance a lot.
  for i,item in enumerate(sortedList):
    #print("insort: " + str(item) + " versus " + str(newItem)) #debug.
    if keyFun(item) > keyFunOfNewItem:
      sortedList.insert(i,newItem)
      return
  sortedList.append(newItem) #because it didn't go before any item, it goes after the last one.
  return


def directBisectInsort(sortedList, newItem, startPoint=0, endPoint=None, keyFun=(lambda x: x)):
  if len(sortedList) == 0:
    sortedList.append(newItem)
    return
  keyFunOfNewItem = keyFun(newItem) #@ cache this for probably a tiny performance gain, but not as much as rewriting the method to take a key instead of a keyFun would give.
  if endPoint == None:
    endPoint = len(sortedList)-1
  if endPoint - startPoint == 1:
    if keyFun(sortedList[endPoint]) < keyFunOfNewItem:
      sortedList.insert(endPoint+1,newItem)
    else:
      if keyFun(sortedList[startPoint]) < keyFunOfNewItem:
        sortedList.insert(endPoint,newItem)
      else:
        sortedList.insert(startPoint,newItem)
    return
  elif endPoint - startPoint == 0:
    if keyFun(sortedList[endPoint]) < keyFunOfNewItem:
      sortedList.insert(endPoint+1,newItem)
    else:
      sortedList.insert(endPoint,newItem)
    return
  testPoint = int((startPoint+endPoint)/2)
  testItem = sortedList[testPoint]
  testResult = keyFun(testItem) - keyFunOfNewItem
  if testResult > 0: #if we should search lower...
    bisectInsort(sortedList, newItem, startPoint=startPoint, endPoint=testPoint, keyFun=keyFun)
  elif testResult < 0: #if we should search higher...
    bisectInsort(sortedList, newItem, startPoint=testPoint, endPoint=endPoint, keyFun=keyFun)
  else:
    sortedList.insert(testPoint,newItem)
    
    
def iterativeBisectionSearch(sortedList, searchItem, keyFun=(lambda x: x)):
  sortedListLength = len(sortedList)
  if sortedListLength == 0:
    #print("PyArrTools.iterativeBisectionSearch: returning before anything.")
    return 0
  searchItemKey = keyFun(searchItem)
  startPoint = 0
  startItemKey = keyFun(sortedList[startPoint])
  endPoint = sortedListLength-1
  endItemKey = keyFun(sortedList[endPoint])
  while True:
    if endPoint - startPoint < 2:
      if endPoint == startPoint:
        if endItemKey < searchItemKey:
          #print("PyArrTools.iterativeBisectionSearch: returning at AA.")
          return endPoint+1
        else:
          #print("PyArrTools.iterativeBisectionSearch: returning at AB.")
          return endPoint
      else: #if endPoint - startPoint == 1...
        if endItemKey < searchItemKey:
          #print("PyArrTools.iterativeBisectionSearch: returning at BA.")
          return endPoint+1
        else:
          if startItemKey < searchItemKey:
            #print("PyArrTools.iterativeBisectionSearch: returning at BBA.")
            return endPoint
          else:
            #print("PyArrTools.iterativeBisectionSearch: returning at BBB.")
            return startPoint
    else:
      testPoint = (startPoint+endPoint)>>1
      testItemKey = keyFun(sortedList[testPoint])
      if testItemKey > searchItemKey: #if we should search lower...
        endPoint, endItemKey = (testPoint, testItemKey)
      elif testItemKey < searchItemKey: #if we should search higher...
        startPoint, startItemKey = (testPoint, testItemKey)
      else:
        return testPoint
    
def bisectInsort(sortedList, newItem, stable=False, keyFun=(lambda x: x)):
  """
  when stable=True, any item which would normally be inserted in a random place in a run of items with the same key will instead be inserted at the end of it.
  """
  searchResultLocation = iterativeBisectionSearch(sortedList, newItem, keyFun=keyFun)
  
  insertionLocation = searchResultLocation
  
  if stable:
    insertionLocation = len(sortedList)
    newItemKey = keyFun(newItem)
    for stabilityTestPoint in range(searchResultLocation,len(sortedList)):
      if keyFun(sortedList[stabilityTestPoint]) != newItemKey:
        insertionLocation = stabilityTestPoint
        break
  
  sortedList.insert(insertionLocation, newItem)
    
    
#insert sorted:
insort = bisectInsort
    
    
    

    
def bubbleSortSingleItemRight(inputArr,startIndex):
  #an O(N) method to modify a provided array to correct a single out-of-place item. It could have fewer compares if it relied on a O(log(N)) search, but it couldn't have fewer writes.
  inputArrLen = len(inputArr)
  assert startIndex >= 0
  while (startIndex < inputArrLen - 1) and inputArr[startIndex] > inputArr[startIndex+1]:
    inputArr[startIndex], inputArr[startIndex+1] = (inputArr[startIndex+1], inputArr[startIndex])
    startIndex += 1
