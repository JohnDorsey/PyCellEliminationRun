
import CodecTools



def bubbleSortSingleItemRight(inputArr,startIndex):
  #an O(N) method to modify a provided array to correct a single out-of-place item. It could have fewer compares if it relied on a O(log(N)) search, but it couldn't have fewer writes.
  inputArrLen = len(inputArr)
  assert startIndex >= 0
  while (startIndex < inputArrLen - 1) and inputArr[startIndex] > inputArr[startIndex+1]:
    inputArr[startIndex], inputArr[startIndex+1] = (inputArr[startIndex+1], inputArr[startIndex])
    startIndex += 1



def morphAscendingEntriesIntoHuffmanTree(entries):
  #modifies the input array and returns nothing.
  #input must be in the same format as is specified in HuffmanMath.makeHuffmanTreeFromAscendingEntries.
  #The tree ends up in last item of the input array as (sum of the chances of all items in the tree, tree).
  entriesStart = 0
  while entriesStart < len(entries)-1:
    #print("morphAscendingEntriesIntoHuffmanTree: entries is " + str(entries)+".")
    eB, eA = (entries[entriesStart], entries[entriesStart+1])
    entries[entriesStart+1] = (eB[0]+eA[0], (eB[1], eA[1]))
    #entries[entriesStart] = None
    entriesStart += 1
    bubbleSortSingleItemRight(entries,entriesStart)


def makeHuffmanTreeFromAscendingEntries(entries):
  #the input array must be in the format [(chance_0, item_0), (chance_1, item_1), ...].
  #the chances do not need to be probabilities, do not need to sum to 1.0, and do not need to be floats. They only need to be usable on either side of the '+' operator, and comparable on either side of the '>' operator (within HuffmanMath.bubbleSortSingleItemRight).
  workingArr = [item for item in entries]
  morphAscendingEntriesIntoHuffmanTree(workingArr)
  #print("makeHuffmanTreeFromAscendingEntries: workingArr is " + str(workingArr)+".")
  return workingArr[-1][1]

def makeHuffmanTreeFromEntries(entries):
  ascendingEntries = sorted(entries)
  #print("makeHuffmanTreeFromEntries: (entries,ascendingEntries) is " + str((entries,ascendingEntries))+".")
  return makeHuffmanTreeFromAscendingEntries(ascendingEntries)


def genLeafIDs(tree):
  #visit all paths to tree leaves as a generator.
  #yielded items are in the form of arrays of integers.
  if type(tree) == tuple:
    for i,item in enumerate(tree):
      for nextPath in genLeafIDs(item):
        yield [i] + nextPath
  else:
    yield []


def genLeafIDsAndItems(tree):
  #same as genLeafIDs(tree), but each yielded item is not just the leaf ID, but is a tuple bundling (leaf ID, leaf value).
  if type(tree) == tuple:
    for i,item in enumerate(tree):
      for nextResponse in genLeafIDsAndItems(item):
        yield ([i] + nextResponse[0],nextResponse[1])
  else:
    yield ([],tree)


def accessTreeLocation(tree,pathDefSeq,stopFun=None):
  #get a node from a tree at the location specified by pathDefSeq.
  if stopFun == None:
    stopFun = (lambda x: type(x) not in [list,tuple,dict])
  #pathDefSeq = makeGen(pathDefSeq)
  currentNode = tree
  for item in pathDefSeq:
    currentNode = currentNode[item]
    if stopFun(currentNode):
      break
  return currentNode


def treeToReverseDict(tree):
  #take an input tree and return a dictionary mapping tree leaves to their paths.
  result = dict()
  for entry in genLeafIDsAndItems(tree):
    result[entry[1]] = entry[0]
  return result




def makeHuffmanLimitedCodec(chanceFun,minInputInt,maxInputInt):
  entries = sorted((chanceFun(value),value) for value in range(minInputInt,maxInputInt+1))
  huffmanTree = makeHuffmanTreeFromEntries(entries)
  huffmanReverseDict = treeToReverseDict(huffmanTree)
  #print(huffmanTree)
  #print(huffmanReverseDict)
  return CodecTools.Codec((lambda x: huffmanReverseDict[x]),(lambda y: accessTreeLocation(huffmanTree,y)),zeroSafe=(minInputInt <= 0))


