
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
