"""

FourierMath.py by John Dorsey.

FourierMath.py contains tools for creating fourier transforms and manipulating audio. In the future, these functions may be used by the Spline class in Curves.py for better interpolation to predict missing samples of audio.

"""



from math import e, pi, sin

j = 1.0j



def compare(arr1,arr2):
  if len(arr1) != len(arr2):
    print("the arrays are different lengths.")
    return
  difference = subtractArrs(arr1,arr2)
  print(str(len([item for item in difference if item != 0])) + " of " + str(len(arr1)) + " item pairs differ.")
  print("The sum of the differences is " + str(sum(differences)) + " and the sum of their absolute values is " + str(sum(absOverArr(differences))) + ".")
  print("The most extreme differences are " + str(min(differences)) + " and " + str(max(differences)) + ".")
  return


def floatArrToShortStr(inputSeq,decimalPlaces=3):
  return "["+",".join(str(item)[:str(item).index(".")+1+decimalPlaces] for item in inputSeq)+"]"

def absOverArr(inputSeq):
  return [abs(item) for item in inputSeq]

def realOverArr(inputSeq):
  return [item.real for item in inputSeq]

def imagOverArr(inputSeq):
  return [item.real for item in inputSeq]

def combineArrs(arr1,arr2):
  result = []
  for i in range(max(len(arr1),len(arr2))):
    result.append((arr1[i], arr2[i]))
  return result

def subtractArrs(arr1, arr2):
  return [arr1[i]-arr2[i] for i in range(max(len(arr1),len(arr2)))]

def genDoubleSeqRateLinear(inputSeq):
  #double the sampling rate of a sequence using linear interpolation.
  lastItem = None
  justStarted = True
  for item in inputSeq:
    if justStarted:
      lastItem = item
      justStarted = False
      yield lastItem
      continue
    yield (lastItem+item)/2.0
    yield item
    lastItem = item



def slowDFT(x):
  N = len(x)
  return [slowDFT_at_k(x,k) for k in range(N)]

def slowIDFT(X):
  N = len(X)
  return [slowIDFT_at_n(X,n) for n in range(N)]

def slowDFT_at_k(x,k):
  N = len(x)
  return sum(x[n]*e**(-2.0*pi*j*k*n/float(N)) for n in range(0,N))

def slowIDFT_at_n(X,n):
  N = len(X)
  scale = 1.0/float(N)
  return scale * sum(X[k]*e**(2.0*pi*j*k*n/float(N)) for k in range(0,N))



#change these if faster equivalent methods are introduced.
DFT = slowDFT
IDFT = slowIDFT
DFT_at_k = slowDFT_at_k
IDFT_at_n = slowIDFT_at_n



def DFT_over_kSeq(x,kSeq):
  return [DFT_at_k(x,k) for k in kSeq]

def IDFT_over_nSeq(X,nSeq):
  #return [item/float(len(X)) for item in DFT_over_kSeq(X,nSeq)]
  return [IDFT_at_n(X,n) for n in nSeq]


"""
def DFTDoubleRate(x):
  #this method works by roughly doubling the size of the input's fourier transform using linear interpolation and then using IDFT to create a reconstruction of the input at the new sample rate.
  #scale = len(x)/float(len(x)*2.0-1.0)
  scale = 1.0
  doubleRateFTOfInput = [item*scale for item in genDoubleSeqRateLinear(DFT(x))]
  assert len(doubleRateFTOfInput) == len(x)*2-1
  return IDFT(doubleRateFTOfInput)


#oh no. This method shows that fourier interpolation might not work well.
def DFTDoubleRateDumb(x):
  #this function simply inserts calculations for non-integer values of k between the normal result items for integer values of k.
  doubleKGen = (i/2.0 for i in range(len(x)*2-1))
  doubleKArr = [item for item in doubleKGen]
  #print(doubleKArr)
  return absOverArr(IDFT_over_kSeq(DFT(x),doubleKArr))
"""


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

sampleWaves = [[sin(t*pi*2/100.0) for t in range(SAMPLEWAVELEN)], [sin(t*pi*2/10.0)+sin(t*pi*2/50.0) for t in range(SAMPLEWAVELEN)], [0.75 for i in range(SAMPLEWAVELEN)],([1.0]*100)+([0.0]*10)+([1.0]*(SAMPLEWAVELEN-110)), [6,7,7.5,7,6,5,4.5,5]*2]


