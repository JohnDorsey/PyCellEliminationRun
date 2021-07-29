



Usage:

  launch a python 2 or python 3 interpreter, preferably Pypy (which executes PyCellEliminationRun about 4 to 8 times faster).
  

  initialize:

    import Testing


  test that the project mostly works:

    Testing.test()
  
  The printed output should include "test passed." after *most* of the tests, and the reported time taken should ideally be under a minute.


  compress the demo file "samples/moo8bmono44100.txt":

    Testing.compressFull("samples/moo8bmono44100.txt","<your name for the output file>","linear",256,Testing.Codes.codecs["inSeq_fibonacci"])
    
  The output file will be created in the same directory as the project, and will have the interpolation mode and block size appended to the end of its name.
    
  The output is full of the characters "1" and "0", each taking up a whole byte in UTF-8, so the output file will NOT be smaller than the original wave file until it is compressed using GZIP or LZMA.


  decompress a compressed file:

    reconstructedSound = Testing.decompressFull("<name of the compressed file>","linear",256,Testing.Codes.codecs["inSeq_fibonacci"])


  verify that the reconstructed file matches the original "samples/moo8bmono44100.txt":

    testLen = min(len(reconstructedSound),len(Testing.WaveIO.sounds["samples/moo8bmono44100.txt"]))

    reconstructedSound[:testLen] == Testing.WaveIO.sounds["samples/moo8bmono44100.txt"][:testLen]

  The reconstructed sound could be slightly shorter or longer than the original.
  

  prepare custom wave files to be compressed:

    import WavePrep

    WavePrep.convertAudio("source file name.wav","destination file name.wav")

  The above takes an int16 44.1kHz stereo source file and creates a uint8 44.1kHz mono destination file, the default format that other parts of the project expect. This is not a limitation of the Cell Elimination Run algorithm, which supports any integer as the maximum sample value,

    import Testing

    Testing.WaveIO.sounds["file name.wav"] = Testing.WaveIO.loadSound("file name.wav")

  The above loads the new sound into WaveIO. Also, WaveIO.py can be edited to add an empty entry to the sounds dictionary so that it will be loaded every time WaveIO.py is loaded.

---

Explanation of compression settings:

  The interpolation mode chosen for the Spline affects how the Spline will estimate the values of the missing samples. Interpolation modes that are better at approximating audio signals generally result in better compression. Valid interpolationModes are "hold", "nearest-neighbor", "linear", "sinusoidal", and "finite difference cubic hermite", the last two of which contain unreliable float comparisons, making "linear" the best reliable mode.

  The block size (in samples) has a slight effect on compression ratio, and huge impact on performance. Block boundaries reduce the information available to the interpolator, so reducing the number of boundaries similarly reduces waste... but the time complexity to compress a block is about O((number of samples^1.5)*(number of possible values per sample)). a block size of 256 or 512 seems like a good balance.

---

Project terminology and naming rules:
  
  -The prefixes plain- and press- are analogous to plain- and cypher- as used in plaintext and ciphertext, but they instead refer to whether something is compressed or not.

  -Anything called a "Codec" is an instance of CodecTools.Codec.
  
  -Any transcoding function (a function for encoding data, decoding data, or capable of doing either as instructed by its arguments) is always identified by its name suffixed with -Encode, -Decode, or -Transcode, respectively.
  
  -A transcoding function always has the data source as its first argument.
  
  -The direction of transcoding for a -Transcode function or other function handling both encoding and decoding actions is called its "opMode". An opMode is officially always either "encode" or "decode" and when it is given as an argument to a -Transcode function, it must always be the second argument.

  -generator functions have names prefixed with gen-. Generator arguments have names suffixed with -Gen. A common reason for an argument to need to be a generator is that the function using it may take only a certain number of items, and then the generator that was passed in should remain in that condition, with that many items missing from the beginning. This completely replaces the need for a parse function that includes information about how much data it needed from an input array in its own output.
  
  -an argument with a name suffixed with -Seq must at least be iterable. An argument which only needs to be iterable for the function to work internally should usually be named with the suffix -Seq. Functions that are designed with the goal of transforming one generator into another should usually have their data argument's name suffixed with -Gen, with one exception: transcoding functions designed specifically for powering a CodecTools.Codec that transcodes sequences. Such Sequence Codec transcoding functions should have their data argument names end in -Seq, because they should accept either Lists or generators as inputs, and should ALSO act like generator transformers whenever possible - taking only as many items from their generator-type input data arguments as are taken from their generator-type outputs. In fact, if a Codec can't follow these rules, it shouldn't be called a Sequence Codec at all.
  
  -A function's taking items from a generator-type argument is sometimes called eating. Taking more items from the input than are absolutely necessary to produce as many output items as it yields is called over-eating, and it is a serious bug. It is guaranteed to happen whenever a generator tranformer function has a for-in loop directly iterating over its input argument's items and also has the possibility of exiting from the loop body before yielding the current item. Avoiding this bug is why many functions like genFunctionalDynamicMarkovTranscode have while loops and use "try: currentItem = next(inputGen) except StopIteration: break" at some point within them.

---

Design notes:

  possible file format:

    -A plaintext header which includes:

      -sample rate.

      -missing sample value prediction mode.

      -cell probability prediction mode (vertical distance to Spline, direct distance to Spline, non-circular direct distance to spline (such as (log(horiz distance to nearest point)+log(vert distance to nearest point))**0.5) because this is less affected by the speed of the audio).

  possible block format:

    -Superblocks:

      -Superblocks might increase the effectiveness of some compression codecs which act on the batches of encoded blocks - e.g. palettization.

    -Blocks.

  Todo:
    
    -make a good way to transparently apply a column-aware sequence sequence codec to another sequence sequence codec's data.

    -rename QuickTimers to QuickClocks.

    -replace CodecTools.Codec.zeroSafe with easier-to-use CodecTools.Codec.minStorable.
 
    -complete and test grid mode for CellCatalogue.
    
    -move more header tools out of CellElimRunBlockState.

    -add more customizable endpoint handling to Curves.Spline to prepare the CellElimRun block Codec for more use cases other than raw audio waves, especially compressing sorted data such as palettes, or reducing waste when compressing nearly-sorted data such as very small segments of audio.
    
    -change the structure of CellElimRunCodecState to make it easier for other data predictors to be used instead of Curves.Spline.

    -add more output file formats, including plaintext python integer lists.

    -inclusion of GZIP and/or LZMA.
  
    -make a better way to make numberSeqCodecs from numberCodecs.
  
    -make CER easier to understand and modify.

    -finish higher-order fibonacci coding.

  Feature wish list (CR = compression ratio):

    -for performance reasons, make a mode where the CellElimRun catalogue has a lower vertical resolution than the Spline and audio data.
      (complexity: medium, maintenance: medium, CR impact: negative, performance impact: very positive - dissociates time complexity from audio bit depth, maybe avoiding a 256x slowdown when jumping from 8bit to 16bit samples.).

    -make a fourier interpolation mode for the Spline.
      (complexity: medium, maintenance: zero, CR impact: positive, performance impact: very negative).

    -make an integer-only or fraction-based linear interpolation mode for the Spline, to prove it can be done easily for better compatibility between different implementations of the codec.
      (complexity: low, maintenance: low, CR impact: slightly negative, performance impact: none).

    -make a static AI interpolation mode for the spline.
      (complexity: high, maintenance: low, CR impact: positive, performance impact: very negative).

    -make a parallel-grid variant Cell Elimination Run, where cell elimination runs are split between two or more grids representing a wave and its derivitive(s).
      (complexity: nightmare, maintenance: high, CR impact: positive, performance impact: none).

    -make a dynamically learning markov-model-like cell scoring tool.
      -this might score cells based on their paired (x, y) displacement from each endpoint individually, as well as their absolute height, and an additional chart for approximate location scaled to the rectangle formed by the start and end points.
      (complexity: medium, maintenance: high, CR impact: positive, performance impact: very negative).

  done:

    -verify that the usage of CellCatalogue is perfectly correct in all situations in order to not leave any improvements to compression ratio on the table.

    -move havenBucketFibonacciCoding from Testing.py to IntSeqStore.py.

    -Elias Delta Iota coding.

    -fully self-delimiting Cell Elimination Run blocks, based on CER's natural potential ability to know when it is finished decoding.
      (complexity: low, maintenance: low, CR impact: slightly positive, performance impact: none).

    -Haven bucket fibonacci coding with haven buckets that aren't embedded in the stream, to improve the effectiveness of Gzipping the output.
    
    -in genDynamicMarkovTranscode, move each possible item into the search sequence so that the search directly decides the probability of that item being the next item, instead of needing a separate singleUsageHistogram.
    
    -add huffman coding to markov tools.
