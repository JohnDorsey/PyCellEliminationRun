import CERWaves
import Codes
import PyCellElimRun as pcer

def test():
  for interpolationMode in ["hold","nearest-neighbor","linear","sinusoidal","finite distance cubic hermite"]:
    print("interpolation mode: " + interpolationMode + ": ")
    if pcer.functionalTest(pcer.functionalTest(CERWaves.sounds["sampleNoise"],"encode",interpolationMode,[128,256]),"decode",interpolationMode,[128,256]) == CERWaves.sounds["sampleNoise"]:
      print("test passed.")
    else:
      print("test failed.")

def autoBenchmark():
  pass
