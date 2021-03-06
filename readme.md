



Usage:

  launch a python 2 or python 3 interpreter, preferably Pypy (which executes PyCellEliminationRun about 4 to 8 times faster).
  

  initialize:

    import Testing


  test that the project mostly works:

    Testing.test()
  
  The printed output should include "test passed." after *most* of the tests, and the reported time taken should ideally be under a minute (for pypy). The saving rate should *never* be negative.
  

  compress the demo file "samples/moo8bmono44100.txt":

    Testing.compressFull(
      "samples/moo8bmono44100.txt",
      "<your name for the output file>",
      settings=None,
      blockSize=[512,256],
      numberSeqCodec=Testing.Codes.codecs["inSeq_fibonacci"]
      )
    
  The output file(s) will be created in a new folder inside testingOutputs/.
    
  The output includes separate files for each output format. Only the less practical _bitStr_ format (with each bit represented by a full UTF-8 character "1" or "0") is currently accepted by Testing.decompressFull. When the _bitStr_ format output file is compressed further using LZMA or GZIP, it is similar in size to the _bytes_ format output file.
  

  decompress a compressed file:

    reconstructedSound = Testing.decompressFull(
      "<name of the compressed file>",
      settings=None,
      blockSize=[512,256],
      numberSeqCodec=Testing.Codes.codecs["inSeq_fibonacci"]
      )
  

  verify that the reconstructed file matches the original "samples/moo8bmono44100.txt":

    testLen = min(
      len(reconstructedSound),
      len(Testing.WaveIO.sounds["samples/moo8bmono44100.txt"])
      )

    assert reconstructedSound[:testLen] == Testing.WaveIO.sounds["samples/moo8bmono44100.txt"][:testLen]
    
  or more breifly:
    
    assert all(item[0]==item[1] for item in zip(reconstructedSound, Testing.WaveIO.sounds["samples/moo8bmono44100.txt"]))

  The reconstructed sound could be cut slightly shorter or longer than the original, so only directly compare as many items as the shortest of them has.
  
  Both of the above tests are coincidentally passed when the reconstructedSound is an empty list, so maybe print out its contents, too.
  

  prepare custom wave files to be compressed:

    import WavePrep

    WavePrep.convertAudio(
      "<source file name>.wav",
      "<destination file name>",
      sourceFramerate=44100,
      resamplingInterval=1
      )

  The above takes an int16 44.1kHz stereo .wav source file and creates a uint8 44.1kHz mono destination file (in two formats: .wav, and .txt containing a python list literal). Preparing a file is necessary because some parts of the project, particularly in Testing.py, assume that audio samples have values under 256 (although the Cell Elimination Run codec supports any integer as the maximum sample value), and also because no parts of the project operate on more than one audio channel.
  
  The .txt format for sample files is helpful because it means that sample file loading can be done in any version of python without regard for how python's wave module has changed between python 2 and python 3.


    import Testing

    Testing.WaveIO.sounds["<file name>.wav"] = Testing.WaveIO.loadSound("<file name>.wav")

  The above loads the new sound into WaveIO. Also, WaveIO.py can be edited to add an empty entry to the sounds dictionary so that it will be loaded every time WaveIO.py is loaded.

---

Explanation of compression settings:

  The interpolation mode chosen for the Spline affects how the Spline will estimate the values of the missing samples. Interpolation modes that are better at approximating audio signals ought to result in better compression. Valid interpolationModes are "hold", "nearest_neighbor", "linear", "sinusoidal", "finite_difference_cubic_hermite", and "inverse_distance_weighted". Of these, "linear" seems to give the best compression for the sample file moo8bmono44100.txt.

  The block size (in samples) has a slight effect on compression ratio, and huge impact on performance. Block boundaries reduce the information available to the interpolator, so reducing the number of boundaries similarly reduces waste... but the time complexity to compress a block is about O((number of samples^1.5)*(number of possible values per sample)). a block size of 512 seems like a good balance.
  
  Other considerations for choosing block sizes:
    -At 64 samples per block, at 44.1kHz, there are 689 blocks per second - blocks so small that a single wavelength of the note middle C can't fit within them, and a frequency-analyzing interpolation method would not be able to identify those frequencies and use them to improve its estimations.
    -At 2205 samples per block, at 44.1kHz, a 20Hz wave can fit one cycle per block, so the saving rate might finally plateau there.
    -in the future, interpolation may happen on a larger scale than Cell Elimination Run block space, making large block sizes less necessary for high saving rates.
  
  
  
Explanation of compression settings in higher than 2 dimensions:

  The block size may be a 2-element list where size[0] is the block length in plaindata values and size[-1] is greater than the largest plaindata value. The block size may be a 3-element list, allowing images to be compressed in the same way as sound. In this case, the last element of size is always the range of valid plaindata values. "inverse_distance_weighted" works with 3d (image) data, but most other methods don't yet.

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

  misc:
    When critical cell or critical column routines handle the resolution of the last few cells in a board, there is no hit. So what is stored as a last pressnum or expected as one?

  possible file format:

    -A plaintext header which includes:

      -sample rate.

    -Superblocks, which might increase the effectiveness of some compression codecs which act on the batches of encoded blocks - e.g. palettization.

  Todo:
  
    -external features:
      
      -add a sample image.

      -inclusion of LZMA and/or GZIP.
      
    -maintenance:
    
      -move most Spline caching code to new classes to simplify the core of Spline.
        
      -improve structure of Spline init args.
    
      -simplify the CellElimRunCodecState:
      
        -factor out all CERCS header interpretation and usage into a new class.
        
        -consider moving the entry point for execution into the CellTargeter, making it more like the player of a one-player game.
        
      -make CERCS test for more incompatible settings.
        
      -fix unnecessary calls to dict.keys().
  
      -reduce file count.
    
      -increase testing.
  
      -choose a language version (python 2 for pypy, or python 3 for numba and numpy) and commit to it.
      
    -capability goals:
    
      -add support for splitting one Cell Elimination Run across any number of _Cell Elim Run Step_-capable objects.
      
      -add support for using a single spline across multiple CER blocks.
      
    -internal features:
    
      -make a Cell class that caches its own score, and knows when that cache is outdated.
      
      -modify Spline and ColumnCellCatalogue to make them both use the same list to store known plaindata values.
    
      -Shrink the interface of the CellCatalogue.
      
      -Make a CellCatalogueColumn with more state information (like tracked live cell count, persistent extreme cell info, and strict automatic validation of live cell count.).
    
      -add compression mode where local extrema are first stored and then the spaces between them are compressed as CER blocks.
        
      -add real _lower and upper bounds_ to Spline instead of imposeMinimum/imposeMaximum. This will fix global clipping.
      
      -add real _lower and upper bounds_ to CellCatalogue.
    
      -fix potential bugs related to rankings not being updated by crit cell callback in CER.
    
      -add lower bound and upper bound shape hints for CER in higher dimensions (e.g. the minimum z for x=5 and y in range(size[1])).
        
      -make the CER block seq codec reuse a CERCS.
        
      -add automatic cellCatalogue edits / editing functions for different situations like monotonic data.
      
      -modify EmbedCode class to allow original values for settings to be embedded.
      
      -add optional filters to genCellCheckOrder and/or scoreFun.
    
      -complete and test grid mode for CellCatalogue.
        
      -allow Spline cache settings to be chosen automatically.
    
      -implement cellCatalogue-based spline clipping, or spline value overrides, or temporary spline bones, or a spline bones that are ranges instead of points.
      
      -make it possible to define a structure for the storage of header pressNums.
      
    -minor details:
    
      -store CellTargeter rankings as a heap for performance reasons.
      
    -variety features:
    
      -make a strict most-aligned-axes-first interpolation mode for higher dimensions.

      -convolution-based weighted spline interpolation.
      
      -arithmetic coding.
      
    -tools:

      -make a better way to make numberSeqCodecs from numberCodecs.
      
      -come up with a good way to transparently apply a column-aware sequence sequence codec to another sequence sequence codec's data.
      
      -come up with a good way to treat sequence codecs like they are not sequence codecs / use them like a stateful function.
      
      -make better preset storage tools:
    
        -memory management and memory warnings.
      
        -make a helpful database.
      
        -pickling?
      
      -time complexity:
      
        -list-like objects that track their own sortedness for bisection searches, performance warnings when falling back to linear searches, etc.

  Feature wish list (CR = compression ratio):
  
    -make a dynamically learning markov-model-like cell scoring tool.
      -this might score cells based on their paired (x, y) displacement from each endpoint individually, as well as their absolute height, and an additional chart for approximate location scaled to the rectangle formed by the start and end points.
      (complexity: medium, maintenance: high, CR impact: positive, performance impact: very negative).
      
    -make a parallel-grid variant Cell Elimination Run, where cell elimination runs are split between two or more grids representing a wave and its derivitive(s).
      (complexity: nightmare, maintenance: high, CR impact: positive, performance impact: none).

    -for performance reasons, make a mode where the CellElimRun catalogue has a lower vertical resolution than the Spline and audio data.
      (complexity: medium, maintenance: medium, CR impact: negative, performance impact: very positive - dissociates time complexity from audio bit depth, maybe avoiding a 256x slowdown when jumping from 8bit to 16bit samples.).

    -make an integer-only or fraction-based linear interpolation mode for the Spline, to prove it can be done easily for better compatibility between different implementations of the codec.
      (complexity: low, maintenance: low, CR impact: slightly negative, performance impact: none).

    -make a static AI interpolation mode for the spline.
      (complexity: high, maintenance: low, CR impact: positive, performance impact: very negative).

    -make a fourier interpolation mode for the Spline.
      (complexity: medium, maintenance: zero, CR impact: positive, performance impact: negative).
      
  will not do:
    
    -change the structure of CellElimRunCodecState to make it easier for other data predictors to be used instead of Curves.Spline.
    
    -simplify Spline:
    
      -separate into 2d and nd.
      
      -move caching to new classes - compose cachedSpline2d(Spline) and cachedSplineND(Spline).

  done:

    -verify that the usage of CellCatalogue is perfectly correct in all situations in order to not leave any improvements to compression ratio on the table.

    -move havenBucketFibonacciCoding from Testing.py to IntSeqStore.py.

    -Elias Delta Iota coding.

    -fully self-delimiting Cell Elimination Run blocks, based on CER's natural potential ability to know when it is finished decoding.
      (complexity: low, maintenance: low, CR impact: slightly positive, performance impact: none).

    -Haven bucket fibonacci coding with haven buckets that aren't embedded in the stream, to improve the effectiveness of Gzipping the output.
    
    -in genDynamicMarkovTranscode, move each possible item into the search sequence so that the search directly decides the probability of that item being the next item, instead of needing a separate singleUsageHistogram.
    
    -add huffman coding to markov tools.
    
    -replace CodecTools.Codec.zeroSafe with easier-to-use CodecTools.Codec.getDomain().
      
    -make it so that most CellCatalogue methods don't need to know whether it is in grid mode or limits mode.
      
    -implement efficient spline value caching based on the knowledge of how much of a spline can be affected by a modification for each interpolationMode.

    -add bound-touch header features.
      
    -accelerate Spline value cache rebuilding by caching bone locations.
        
    -speed up CERCS logging by splitting lines.
  
    -move more header tools out of CellElimRunCodecState.
    
    -move logging tools out of CellElimRunCodecState.
      
    -simplify Spline:
    
      -ensure that self.data isn't accessed multiple times.
    
      -give __getitem__ and __setitem__ no responsibilities to other methods in Spline.
      
      -rename most Spline methods to reflect whether or not they deal with a cache.
    
    -add more customizable endpoint handling to Curves.Spline to prepare the CellElimRun block Codec for more use cases other than raw audio waves, especially compressing sorted data such as palettes, or reducing waste when compressing nearly-sorted data such as very small segments of audio.
      
    -make CellElimRunCodecState unaware of how many dimensions the plaindata has.
    
    -add image compression with a 3d spline.        
    
    -make circular spiral for searches.

    -finish higher-order fibonacci coding.
      
    -combine lewis truncation with haven bucket fibonacci coding.
        
    -add Shannon-Fano coding as a faster alternative to huffman coding.
    
    -add a full-length sample song.
      
    -add more output file formats, including plaintext python integer lists.
    
    -add 15-second 48kHz sample song.
      
    -rename QuickTimers to QuickClocks.
    
    -isolate enbocode code.
      
    -move ParseError to CodecTools.
        
    -add bound corner touch header features to make the CER codec easily able to compress its own output.
      
    -improve logging techniques, possibly using the logging module.
        
    -separate (cross out: everything) _several_ things but the header processing into functions outside of the class. (cell targeter created.)