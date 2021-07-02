"""

IntMath.py by John Dorsey.

IntMath.py contains tools for remapping integer values. It may be used to transform items of a number sequence into a format that is easier to compress.

"""


def NOP_to_OP(inputInt):
  return (inputInt * 2) if inputInt >= 0 else (inputInt * -2) -1

def OP_to_NOP(inputInt):
  return ((inputInt+1)>>1)*((-2*(inputInt%2))+1)


assert [OP_to_NOP(NOP_to_OP(item)) for item in [5,99,32,1,0]] == [5,99,32,1,0]
