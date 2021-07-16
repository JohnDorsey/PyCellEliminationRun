"""

CodecTools.py by John Dorsey.

CodecTools.py contains classes and other tools that might help make it easier to rapidly create and test codecs made
from smaller codecs applied in stages.

"""

from PyGenTools import isGen, makeArr


def measureIntArray(inputIntArr):
    rectBitSize = (len(inputIntArr), len(bin(max(inputIntArr))[2:]))
    return {
        "length": rectBitSize[0],
        "bit_depth": rectBitSize[1],
        "bit_area": rectBitSize[0] * rectBitSize[1],
    }


def printComparison(plainData, pressData):
    plainDataMeasures, pressDataMeasures = (
        measureIntArray(plainData),
        measureIntArray(pressData),
    )
    estimatedCR = float(plainDataMeasures["bit_area"]) / float(pressDataMeasures["bit_area"])
    estimatedSaving = 1.0 - 1.0 / estimatedCR
    print(
        "CodecTools.printComparison: plainData measures "
        + str(plainDataMeasures)
        + ". pressData measures "
        + str(pressDataMeasures)
        + ". Estimated CR is "
        + str(estimatedCR)[:8]
        + ". Estimated saving rate is "
        + str(estimatedSaving * 100.0)[:8]
        + "%."
    )


def countTrailingZeroes(inputArr):
    i = 0
    while inputArr[-1 - i] == 0:
        i += 1
    return i


def roundTripTest(testCodec, plainData, showDetails=False):
    # test the input testCodec on testData to make sure that it is capable of reconstructing its original input. If it
    # isn't, print additional information before returning False.
    if isGen(plainData):
        plainData = makeArr(plainData)
    if type(plainData) == list and len(plainData) == 0:
        print("CodecTools.roundTripTest: warning: plainData is empty.")
    pressData = testCodec.encode(plainData)
    if isGen(pressData):
        pressData = makeArr(pressData)
    if type(pressData) == list and len(pressData) == 0:
        print("CodecTools.roundTripTest: warning: pressData is empty.")
    if showDetails:
        printComparison(plainData, pressData)
    reconstPlainData = testCodec.decode(pressData)
    if isGen(reconstPlainData):
        reconstPlainData = makeArr(reconstPlainData)
    if type(reconstPlainData) == list and len(reconstPlainData) == 0:
        print("CodecTools.roundTripTest: warning: reconstPlainData is empty.")
    result = reconstPlainData == plainData
    if not result:
        print("CodecTools.roundTripTest: Test failed.")
        print(
            "CodecTools.roundTripTest: testData is "
            + str(plainData)
            + " and reconstData is "
            + str(reconstPlainData)
            + ". pressData is "
            + str(pressData)
            + "."
        )
        if type(plainData) == list and type(reconstPlainData) == list:
            print(
                "CodecTools.roundTripTest: Lengths "
                + ("do not" if len(reconstPlainData) == len(plainData) else "")
                + " differ."
            )
    return result


def makePlatformCodec(platCodec, mainCodec):
    return Codec(
        (lambda x: platCodec.encode(mainCodec.encode(platCodec.decode(x)))),
        (lambda x: platCodec.encode(mainCodec.decode(platCodec.decode(x)))),
    )


def makeChainedPairCodec(codec1, codec2):
    return Codec(
        (lambda x: codec2.encode(codec1.encode(x))),
        (lambda x: codec1.decode(codec2.decode(x))),
    )


class Codec:
    def __init__(
        self,
        encodeFun,
        decodeFun,
        transcodeFun=None,
        zeroSafe=None,
        extraArgs=None,
        extraKwargs=None,
    ):
        self.encodeFun, self.decodeFun, self.transcodeFun, self.zeroSafe = (
            encodeFun,
            decodeFun,
            transcodeFun,
            zeroSafe,
        )
        if not (self.encodeFun or self.decodeFun or self.transcodeFun):
            raise ValueError("No functions for encoding, decoding, or transcoding were specified!")
        self.extraArgs, self.extraKwargs = extraArgs or [], extraKwargs or {}

    def encode(self, data, *args, **kwargs):
        if not (self.encodeFun or self.transcodeFun):
            raise AttributeError("Either encodeFun or transcodeFun must be defined to decode.")
        argsToUse = (
            args or self.extraArgs
        )  # an extra argument specified when calling Codec.encode will override ALL stored values in Codec.extraArgs.
        kwargsToUse = (
            kwargs or self.extraKwargs
        )  # an extra argument specified when calling Codec.encode will override ALL stored values in Codec.extraKwargs.
        if self.encodeFun:
            return self.encodeFun(data, *argsToUse, **kwargsToUse)
        else:
            return self.transcodeFun(data, "encode", *argsToUse, **kwargsToUse)

    def decode(self, data, *args, **kwargs):
        if not (self.decodeFun or self.transcodeFun):
            raise AttributeError("Either decodeFun or transcodeFun must be defined to decode.")
        argsToUse = args or self.extraArgs
        kwargsToUse = kwargs or self.extraKwargs
        if self.decodeFun:
            return self.decodeFun(data, *argsToUse, **kwargsToUse)
        else:
            return self.transcodeFun(data, "decode", *argsToUse, **kwargsToUse)

    def clone(self, extraArgs=None, extraKwargs=None):
        if self.extraArgs != [] and extraArgs is not None:
            print("CodecTools.Codec.clone: warning: some existing extraArgs will not be cloned.")
        if self.extraKwargs != {} and extraKwargs is not None:
            print("CodecTools.Codec.clone: warning: some existing extraKwargs will not be cloned.")
        argsToUse = extraArgs or self.extraArgs
        kwargsToUse = extraKwargs or self.extraKwargs
        return Codec(
            self.encodeFun,
            self.decodeFun,
            transcodeFun=self.transcodeFun,
            zeroSafe=self.zeroSafe,
            extraArgs=argsToUse,
            extraKwargs=kwargsToUse,
        )


bitSeqToStrCodec = Codec((lambda x: "".join(str(item) for item in x)), (lambda x: [int(char) for char in x]))

# tests:


def get_delimited_str_codec(delimiter):
    return Codec((lambda x: delimiter.join(x)), (lambda x: x.split(delimiter)))


assert get_delimited_str_codec("&").encode(["hello", "world!"]) == "hello&world!"
assert get_delimited_str_codec("&").decode("hello&world!") == ["hello", "world!"]
