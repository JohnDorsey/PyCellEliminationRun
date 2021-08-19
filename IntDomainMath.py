"""

IntDomainMath.py by John Dorsey.

IntDomainMath.py contains tools for remapping integer values. It may be used to transform items of a number sequence into a format that is easier to compress.

P = domain (0, inf).
OP = domain [0, inf).
NOP = domain (-inf, inf).
I used the letter O for zero instead of the letter Z because NZP may look like it stood for non-zero positive.

"""


def NOP_to_OP(inputInt):
  """ map (-inf, inf) to [0, inf). """
  return (inputInt * 2) if inputInt >= 0 else (inputInt * -2) -1

def OP_to_NOP(inputInt):
  """ map [0, infinity) to (-inf, inf). """
  assert inputInt >= 0
  return ((inputInt+1)>>1)*((-2*(inputInt%2))+1)
  
  
def OP_to_focusedNOP(inputInt, focus):
  """ map [0, inf) to _(-inf, inf) centered around focus_. """
  return OP_to_NOP(inputInt) + focus
  
def focusedNOP_to_OP(inputInt, focus):
  """ map _(-inf, inf) centered around focus_ to [0, inf). """
  return NOP_to_OP(inputInt - focus)
  

def unfocusedOP_to_focusedOP(inputInt,focus):
  """ map an input integer in [0, inf) to an output integer [0, inf) that is smaller whenever the input int is close to some expected value or _focus_ which is in [0, inf). """
  if inputInt > focus*2:
    return inputInt
  return NOP_to_OP(inputInt-focus)

def focusedOP_to_unfocusedOP(inputInt,focus):
  """ inverse of unfocusedOP_to_focusedOP. """
  if inputInt > focus*2:
    return inputInt
  return OP_to_NOP(inputInt) + focus


#tests:
assert [OP_to_NOP(NOP_to_OP(item)) for item in [5,99,32,1,0]] == [5,99,32,1,0]
assert [focusedOP_to_unfocusedOP(i,6) for i in range(20)] == [6,5,7,4,8,3,9,2,10,1,11,0,12,13,14,15,16,17,18,19]
assert [unfocusedOP_to_focusedOP(i,6) for i in [6,5,7,4,8,3,9,2,10,1,11,0,12,13,14,15,16,17,18,19]] == [i for i in range(20)]
