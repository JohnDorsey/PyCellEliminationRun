
import time


timerStartTimes = {"load_module":time.time()}


def startTimer(name):
  if timerStartTimes.has_key(name):
    print("QuickTimers.startTimer: overwriting timer with name " + str(name) + ".")
  timerStartTimes[name] = time.time()

def stopTimer(name):
  assert timerStartTimes.has_key(name)
  return time.time() - timerStartTimes.pop(name,None)
  
