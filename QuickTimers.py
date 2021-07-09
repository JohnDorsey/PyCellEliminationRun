"""

QuickTimers.py by John Dorsey.

QuickTimers.py offers very simple low-overhead timers to track the time taken between a call to create and start a named timer and a second call to stop and destroy a timer by name. It is not better than the features of python 3's time module, but it works identically in both python 3 and python 2 (and therefore pypy).

"""


import time


timerStartTimes = {"load_module":time.time()}


def startTimer(name): #create a timer with a name, which starts immediately.
  if name in timerStartTimes.keys():
    print("QuickTimers.startTimer: overwriting timer with name " + str(name) + ".")
  timerStartTimes[name] = time.time()

def stopTimer(name): #destroy a timer by name and return the amount of time it existed.
  assert name in timerStartTimes.keys()
  return time.time() - timerStartTimes.pop(name,None)

