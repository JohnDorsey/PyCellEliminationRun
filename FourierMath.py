
from math import e, pi, sin

j = 1.0j




def floatArrToShortStr(inputSeq,decimalPlaces=3):
  return "["+",".join(str(item)[:str(item).index(".")+1+decimalPlaces] for item in inputSeq)+"]"

def absOverArr(inputSeq):
  return [abs(item) for item in inputSeq]

def realOverArr(inputSeq):
  return [item.real for item in inputSeq]

def imagOverArr(inputSeq):
  return [item.real for item in inputSeq]

def combine(arr1,arr2):
  result = []
  for i in range(max(len(arr1),len(arr2))):
    result.append((arr1[i], arr2[i]))
  return result



def DFT(x):
  N = len(x)
  return [DFT_at_k(x,k) for k in range(N)]

def IDFT(x):
  N = len(x)
  return [item/float(N) for item in DFT(x)]

def DFT_at_k(x,k):
  N = len(x)
  return sum(x[n]*e**(-2.0*pi*j*n*k/float(N)) for n in range(0,N))

def IDFT_at_k(x,k): 
  #return float(k)/float(DFT_with_k(x,k)) #?????????
  N = len(x)
  return DFT_at_k(x,k)/float(N)


def DFT_over_kSeq(x,kSeq):
  return [DFT_at_k(x,k) for k in kSeq]

def IDFT_over_kSeq(x,kSeq):
  return [item/float(len(x)) for item in DFT_over_kSeq(x,kSeq)]

#oh no. This method shows that fourier interpolation might not work well.
def DFTDoubleRate(x):
  doubleKGen = (i/2.0 for i in range(len(x)*2-1))
  doubleKArr = [item for item in doubleKGen]
  print(doubleKArr)
  return absOverArr(IDFT_over_kSeq(DFT(x),doubleKArr))


"""
#the following functions might not work for interpolation.

def uncertainDFT_with_k(x,k):
  N = len(x)
  currentSum = 0.0
  currentDenominator = 0.0
  for n in range(0,N):
    localValue = e**(-2.0*pi*j*n*k/float(N))
    currentSum += x[n][0]*localValue
    #assert abs(x[n][1]) <= 1.0001
    currentDenominator += x[n][1]*localValue
  return (currentSum, currentDenominator)

def uncertainIDFT_with_k(x,k):
  N = len(x)
  pair = DFT_with_k(x,k)
  return (pair[0]/pair[1],pair[1]/float(N))

def uncertainDFT(x):
  N = len(x)
  return [uncertainDFT_with_k(x,k) for k in range(N)]

def uncertainIDFT(x):
  N = len(x)
  return [(item[0]/item[1],item[1]/float(N)) for item in uncertainDFT(x)]
"""


SAMPLEWAVELEN = 1024

sampleWaves = [[sin(t*pi*2/100.0) for t in range(SAMPLEWAVELEN)],[sin(t*pi*2/10.0)+sin(t*pi*2/50.0) for t in range(SAMPLEWAVELEN)],[0.75 for i in range(SAMPLEWAVELEN)],([1.0]*100)+([0.0]*10)+([1.0]*(SAMPLEWAVELEN-110))]


