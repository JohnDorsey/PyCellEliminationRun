



Usage:

  launch a python 3 or python 2 interpreter, preferrably Pypy (which executes PyCellEliminationRun about 4 to 8 times faster).
  

  initialize:

    >>> import Testing


  test that the project mostly works:

    >>> Testing.test()
    The printed output should include "test passed." after *most* of the tests, and the reported time taken should ideally be under a minute.


  compress the demo file "moo8bmono44100.txt":

    >>> Testing.compressFull("moo8bmono44100.txt","<your name for the output file>","linear",256,Testing.Codes.fibonacciCoding)
    
    The output file will be created in the same directory as the project, and will have the interpolation mode and block size appended to the end of its name.
    
    The output is full of the characters "1" and "0", each taking up a whole byte in UTF-8, so the output file will NOT be smaller than the original wave file until it is compressed using GZIP or better yet LZMA.


  decompress a compressed file:

    >>> reconstructedSound = Testing.decompressFull("<name of the compressed file>","linear",256,Testing.Codes.fibonacciCoding)


  verify that the reconstructed file matches the original "moo8bmono44100.txt":

    >>> reconstructedSound == Testing.CERWaves.sounds["moo8bmono44100.txt"][:len(reconstructedSound)]

        #The reconstructed sound will be cut slightly short just because partial blocks aren't allowed yet.
  

  prepare custom wave files to be compressed:

    >>> import PyWaveTest

    >>> PyWaveTest.convertAudio("source file name.wav","destination file name.wav")

        #This creates a destination file with 8-bit unsigned samples at 44.1kHz in mono, the default format that other parts of the project expect. But with some settings tweaks, the entire project should allow audio with any integer specified as the maximum value per sample.

    >>> import Testing

    >>> Testing.CERWaves.sounds["file name.wav"] = Testing.CERWaves.loadSound("file name.wav")

        #this loads the new sound into CERWaves. Also, CERWaves.py can be edited to add an empty entry to the sounds dictionary so that it will be loaded every time CERWaves is loaded.



explanation of compression settings:

  The interpolation mode chosen for the Spline affects how the Spline will estimate the values of the missing samples. Interpolation modes that are better at approximating audio signals generally result in better compression. Valid interpolationModes are "hold", "nearest-neighbor", "linear", "sinusoidal", and "finite difference cubic hermite", the last two of which contain unreliable float comparisons, making "linear" the best reliable mode.

  The block size (in samples) has a slight effect on compression ratio, and huge impact on performance. Block boundaries reduce the information available to the interpolator, so reducing the number of boundaries similarly reduces waste... but the time complexity to compress a block is about O((number of samples^1.5)*(number of possible values per sample)). a block size of 256 seems like a good balance.
  





Design notes:
  possible file format:
    -A plaintext header which includes:
      -sample rate.
      -sample value range start.
      -sample value range end.
      -missing sample value prediction mode.
      -cell probability prediction mode (vertical distance to Spline, direct distance to Spline, non-circular direct distance to spline (such as (log(horiz distance to nearest point)+log(vert distance to nearest point))**0.5) because this is less affected by the speed of the audio).
  possible block format:
    -Superblocks:
      -Superblocks might increase the effectiveness of some handwritten compression codecs which act on batches of blocks - e.g. palettization.
    -Blocks.

Todo:
  -make a fourier interpolation mode for the Spline.
  -make an integer-only linear interpolation mode for the Spline.
  -for performance reasons, make a mode where the CellElimRun catalogue has a lower vertical resolution than the Spline and audio data.
  -make an AI interpolation mode for the spline:
    -a mode where the NN is included in the file.
    -a mode where the NN learns as it goes.
  -Elias Delta Iota coding.
  -Haven bucket fibonacci coding with haven buckets that aren't embedded in the stream, to improve the effectiveness of Gzipping the output.
  -inclusion of gzip.
  -for performance:
    -numba.
    -spline caching.
    -move to another language.

distant future Todo:
  -more advanced versions might allow the prediction mode and cell scoring mode to dynamically change for certain ranges of samples, when the known samples at either end of the range both deserved a different prediction method than was used. This goes against the design goal of not searching through alternative representations of the same thing.
  -more advanced versions might allow file-globally defined custom mathematical functions.

done:
  -verify that the usage of CellCatalogue is perfectly correct in all situations in order to not leave any improvements to compression ratio on the table.
