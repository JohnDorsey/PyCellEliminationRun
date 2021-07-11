


def bubbleSortSingleItemRight(inputArr,startIndex):
  inputArrLen = len(inputArr)
  assert startIndex >= 0
  while (startIndex < inputArrLen - 1) and inputArr[startIndex] > inputArr[startIndex+1]:
    inputArr[startIndex], inputArr[startIndex+1] = (inputArr[startIndex+1], inputArr[startIndex])
    startIndex += 1


def makeHuffmanTreeFromAscendingEntries(entries): #in-place, ends up in last item of input array as (total probability of any item in tree, tree).
  entriesStart = 0
  while entriesStart < len(entries)-1:
    eB, eA = (entries[entriesStart], entries[entriesStart+1])
    entries[entriesStart+1] = (eB[0]+eA[0], (eB[1], eA[1]))
    #entries[entriesStart] = None
    entriesStart += 1
    bubbleSortSingleItemRight(entries,entriesStart)

def getHuffmanTreeFromAscendingEntries(entries):
  workingArr = [item for item in entries]
  makeHuffmanTreeFromAscendingEntries(workingArr)
  return workingArr[-1][1]

def genLeafIDs(tree): #visit all paths to tree leaves as a generator.
  if type(tree) == tuple:
    for i,item in enumerate(tree):
      for nextPath in genLeafIDs(item):
        yield [i] + nextPath
  else:
    yield []

def genLeafIDsAndItems(tree):
  if type(tree) == tuple:
    for i,item in enumerate(tree):
      for nextResponse in genLeafIDsAndItems(item):
        yield ([i] + nextResponse[0],nextResponse[1])
  else:
    yield ([],tree)

def accessTree(tree,pathDefinition):
  currentNode = tree
  for item in pathDefinition:
    currentNode = currentNode[item]
  return currentNode

def treeToReverseDict(tree):
  result = dict()
  for entry in genLeafIDsAndItems(tree):
    result[entry[1]] = entry[0]
  return result
