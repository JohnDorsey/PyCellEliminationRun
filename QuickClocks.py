"""

QuickClocks.py by John Dorsey.

QuickClocks.py offers very simple low-overhead clocks to track the time taken between a call to create and start a named clock and a second call to stop and destroy a clock by name. It is not better than the features of python 3's time module, but it works identically in both python 3 and python 2 (and therefore pypy).

"""

import time



class Clock:
  def __init__(self, name=None, start=False):
    self.memory = 0.0
    self.startTime = time.time() if start else None
    self.name = name
  def resume(self):
    assert self.startTime is None
    self.startTime = time.time()
  def pause(self):
    self.memory = self.time()
    self.startTime = None
  def time(self):
    if self.startTime is not None:
      return (time.time() - self.startTime) + self.memory
    else:
      return self.memory
  def __repr__(self):
    return "Clock(name={}, memory={}, time={})".format(self.name, self.memory, self.time())
  #def running(self):
  #  return self.startTime is not None
  
clockDict = dict()

def overwriteCheck(name):
  if name in clockDict:
    print("QuickClocks.overwriteCheck: warning: clock {} will be overwritten.".format(repr(clockDict[name])))

def create(name):
  overwriteCheck(name)
  clockDict[name] = Clock(name=name, start=False)

def start(name): #create a clock with a name, which starts immediately.
  overwriteCheck(name)
  clockDict[name] = Clock(name=name, start=True)
  
def resume(name):
  clockDict[name].resume()

def stop(name): #destroy a clock by name and return the amount of time it ran.
  result = clockDict[name].time()
  del clockDict[name]
  return result
  
def pause(name):
  clockDict[name].pause()

def peek(name): #by name, check how long a clock has existed.
  return clockDict[name].time()

