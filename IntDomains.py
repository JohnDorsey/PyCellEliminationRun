"""

IntDomains.py by John Dorsey.

IntDomains.py contains classes used to test whether a value received by a Codec is in the domain of values the Codec is able to process.

"""
import itertools

import IntDomainMath



class InfiniteIntSeq:
  def __len__(self,testValue):
    print("CodecTools.InfiniteIntSeq.__len__: Warning: this method should not be called, because no correct integer response is possible. returning 2**32.")
    return 2**32


class IntRay(InfiniteIntSeq):
  def __init__(self,startValue,direction=1):
    if not direction in [1,-1]:
      raise ValueError("direction must be 1 or -1.")
    self.startValue, self.direction = (startValue, direction)
    
  def __contains__(self,testValue):
    if type(testValue) != int:
      return False
    if self.direction > 0:
      return testValue >= self.startValue
    else:
      return testValue <= self.startValue
      
  def __getitem__(self,index):
    return self.startValue + index*self.direction
    
  def index(self,value):
    if value != self.startValue:
      if type(value) != int:
        raise TypeError("Value not found, because it is not possible for a value of type {} to be found.".format(type(value)))
      if (value - self.startValue)*self.direction < 0:
        raise ValueError("Value not found.")
    result = abs(value - self.startValue)
    return result
    
  def __iter__(self):
    return itertools.count(self.startValue, self.direction)
    
    
class IntStaggering(InfiniteIntSeq):
  def __init__(self,startValue,direction=1):
    if not direction in [1,-1]:
      raise ValueError("direction must be 1 or -1.")
    self.startValue, self.direction = (startValue, direction)
    
  def __contains__(self,testValue):
    if type(testValue) != int:
      return False
    return True
    
  def __getitem__(self,index):
    return IntDomainMath.OP_to_focusedNOP(index, self.startValue)
    
  def index(self,value):
    return IntDomainMath.focusedNOP_to_OP(value, self.startValue)
    
  def __iter__(self):
    return itertools.imap((lambda lindex: IntDomainMath.OP_to_focusedNOP(lindex, self.startValue)), itertools.count(0))
    

simpleIntDomains = {"UNSIGNED":IntRay(0),"UNSIGNED_NONZERO":IntRay(1),"SIGNED":IntStaggering(0)}



for testDomainName, testDomain in simpleIntDomains.items():
  if not 1 in testDomain:
    raise AssertionError(testDomain)
assert 0 in simpleIntDomains["UNSIGNED"]
assert 0 in simpleIntDomains["SIGNED"]
assert 0 not in simpleIntDomains["UNSIGNED_NONZERO"]
assert -1 not in simpleIntDomains["UNSIGNED"]
assert -1 not in simpleIntDomains["UNSIGNED_NONZERO"]
assert -1 in simpleIntDomains["SIGNED"]


assert [simpleIntDomains["SIGNED"].index(simpleIntDomains["SIGNED"][testIndex]) for testIndex in range(50)] == [testIndex for testIndex in range(50)]