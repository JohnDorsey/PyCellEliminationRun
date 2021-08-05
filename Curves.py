"""

Curves.py by John Dorsey.

Curves.py contains tools like the Spline class for creating curves and doing calculations related to them. The Spline class is mainly used by the Cell Elimination Run codec in PyCellElimRun.py for predicting missing samples of audio.

"""

import math
import itertools
import PyDeepArrTools
import SpiralMath
import PyGenTools
from PyGenTools import arrTakeOnly, seqsAreEqual

try:
  range = xrange
except NameError:
  pass
  

DODBGPRINT = False #print debug info.
DOVIS = False #show pretty printing, mostly for debugging.

def dbgPrint(text,end="\n"): #only print if DODBGPRINT.
  if DODBGPRINT:
    print(text)
    print("custom line endings disabled for python2 compatibility.")




def forceMonotonicSlopes(sur,slopes): #completely untested.
  #sur stands for surroundings.
  surRises = [sur[i+1][1] - sur[i][1] for i in range(len(sur)-1)] #changes in y between each pair of points.
  surMonotonicSlope = -1 if all(((item <= 0) for item in surRises)) else 1 if all(((item >= 0) for item in surRises)) else 0 #the sign of every surRise if those are all the same sign, else 0.
  if surMonotonicSlope == 1:
    for i in range(len(slopes)):
      slopes[i] = max(0,slopes[i])
  elif surMonotonicSlope == -1:
    for i in range(len(slopes)):
      slopes[i] = min(0,slopes[i])
#these functions are used in constructing cubic hermite splines.
def hermite_h00(t):
  return 2*t**3 - 3*t**2 + 1
def hermite_h10(t):
  return t**3 - 2*t**2 + t
def hermite_h01(t):
  return -2*t**3 + 3*t**2
def hermite_h11(t):
  return t**3-t**2


distance_2d_funs = {
  "absolute_distance":(lambda x, y: (x**2 + y**2)**0.5),
  "bilog_distance":(lambda x, y: (math.log(x+1)**2 + math.log(y+1)**2)**0.5), #don't use this name anymore.
  "axial_log_distance":(lambda x, y: (math.log(x+1)**2 + math.log(y+1)**2)**0.5),
  "manhattan_distance":(lambda x, y: x + y)
}

point_distance_2d_funs = {
  "absolute_distance":(lambda p0, p1: ((p0[0]-p1[0])**2 + (p0[1]-p1[1])**2)**0.5),
  "bilog_distance":(lambda p0, p1: (math.log(abs(p0[0]-p1[0])+1)**2 + math.log(abs(p0[1]-p1[1])+1)**2)**0.5), #don't use this name anymore.
  "axial_log_distance":(lambda p0, p1: (math.log(abs(p0[0]-p1[0])+1)**2 + math.log(abs(p0[1]-p1[1])+1)**2)**0.5),
  "manhattan_distance":(lambda p0, p1: abs(p0[0]-p1[0]) + abs(p0[1]-p1[1]))
}

point_distance_nd_funs = {
  "absolute_distance":(lambda p0, p1: sum((p0[dimi]-p1[dimi])**2 for dimi in range(len(p0)))**0.5),
  "axial_log_distance":(lambda p0, p1: sum(math.log(abs(p0[dimi]-p1[dimi])+1)**2 for dimi in range(len(p0)))**0.5),
  "manhattan_distance":(lambda p0, p1: sum(abs(p0[dimi]-p1[dimi]) for dimi in range(len(p0))))
}



def flatten_point(point_to_flatten, world_size):
  #assert point_to_flatten != None
  #assert None not in point_to_flatten
  assert len(point_to_flatten) == len(world_size)
  result = 0
  for pointElement,measure in itertools.izip_longest(point_to_flatten,world_size):
    result = result * measure + pointElement
  return result

def hash_point_list(point_list_to_hash, world_size):
  if len(point_list_to_hash) == 0: #avoid index error.
    return 0
  uniform_base = flatten_point([element-1 for element in world_size], world_size) + 2 #the +2 accomodates Nones.
  flattened_points = sorted(((0 if point==None else flatten_point(point,world_size)+1) for point in point_list_to_hash)) #sorting is performed after hashing because sorting integers is much faster than sorting tuples or lists.
  if sum(flattened_points) == 0: #avoid possible index error.
    return 0
  assert flattened_points[-1] < uniform_base
  result = 0
  for flattened_point in flattened_points:
    result = result * uniform_base + flattened_point
  return result

def lookup_if_str(lookup_dict, potential_key, default=None):
  if type(potential_key) == str:
    if default != None:
      return lookup_dict.get(potential_key,default=defalut)
    else:
      return lookup_dict[potential_key]
  else:
    return potential_key
    
    
def genFindNearest2d(startPoint,triggerFun,timeout=None):
  for i in (range(0,timeout) if timeout != None else itertools.count(0)):
    currentCoord = SpiralMath.spiralCoordDecode(i,startPoint,0,1)
    if triggerFun(currentCoord):
      yield currentCoord
    
    


class Spline:
  #the Spline is what holds sparse or complete records of all the samples of a wave, and uses whichever interpolation mode was chosen upon its creation to provide guesses about the values of missing samples. It is what will inform decisions about how likely a cell (combination of a sample location and sample value) is to be filled/true. 


  SUPPORTED_INTERPOLATION_METHOD_NAMES = ["hold","nearest_neighbor","linear","sinusoidal","finite_difference_cubic_hermite","inverse_distance_weighted"]
  SUPPORTED_OUTPUT_FILTERS = ["span_clip","global_clip","round","monotonic"]
  
  CACHE_VALUES_2D = False #enabling offers a Testing.test() speedup from 16.8 to 14.0 seconds, not considering time spent on numberCodecs and other tasks.
  CACHE_VALUES_BY_SUR_HASH = True
  
  CACHE_BONE_DISTANCE_ABS = False #only applies when valueCache misses.
  CACHE_NEARBY_BONE_LOCATION = True #an alternative to caching bone distance abs.
  
  #in the following dictionary, integers represent points relative to the new point 0. 1 is the next anchor point to the right of the new point, 2 is the point to the right of that one, and the points -1 and -2 are similar. a tuple of two ints represents the span between those two points. Future interpolation methods might require more than this notation can offer, such as trig (fourier) requiring a keyword like "ENTIRE".
  VALUE_CACHE_UPDATE_TYPES = {
    "hold":[(0,1)],
    "nearest_neighbor":[(-1,0),(0,1)],
    "linear":[(-1,0),(0,1)],
    "sinusoidal":[(-1,0),(0,1)],
    "finite_difference_cubic_hermite":[(-2,-1),(-1,0),(0,1),(1,2)],
    "inverse_distance_weighted":[(-2,-1),(-1,0),(0,1),(1,2)]
  }
  
  SURROUNDINGS_REQUIREMENTS = {
    "hold":[0,1,0,0],
    "nearest_neighbor":[0,1,1,0],
    "linear":[0,1,1,0],
    "sinusoidal":[0,1,1,0],
    "finite_difference_cubic_hermite":[1,1,1,1],
    "inverse_distance_weighted":[1,1,1,1],
    "unspecified":[0,0,0,0] #this exists to make it easier to set endpoints.
  }
  
  OUTPUT_FILTER_TEMPLATES = {
    "span_clip":"max(min({},max(sur_for_filter[1][1],sur_for_filter[2][1])),min(sur_for_filter[1][1],sur_for_filter[2][1]))",
    "global_clip":"max(min({},self.size[1]),0)",
    "round":"int(round({}))"
  }

  def __init__(self, interpolation_mode="unspecified", size=None, endpointInitMode=None, default_value=None):
    
    self.initialize_by_default()
    
    self.set_interpolation_mode(interpolation_mode)
    self.set_size_and_endpoints(size,endpointInitMode)
    self.set_default_value(default_value)

    self.data = PyDeepArrTools.noneInitializer(self.size[:-1])

    self.initialize_caches()
      
    self.finalize_endpoints()
    
    assert seqsAreEqual(PyDeepArrTools.shape(self.data), self.size[:-1])


  def initialize_caches(self):
    if Spline.CACHE_BONE_DISTANCE_ABS:
      self.boneDistanceAbs = [None for i in range(len(self.data))]
    if Spline.CACHE_NEARBY_BONE_LOCATION:
      assert not Spline.CACHE_BONE_DISTANCE_ABS, "these caching modes can't be used simultaneously!"
      self.nearbyBoneLocation = [None for i in range(len(self.data))]
    if Spline.CACHE_VALUES_BY_SUR_HASH:
      self.value_cache_by_surroundings_hash = dict()
    if Spline.CACHE_VALUES_2D:
      assert not Spline.CACHE_VALUES_BY_SUR_HASH, "these caching modes can't be used simultaneously!"
      self.valueCache = [None for i in range(len(self.data))]

  def initialize_by_default(self):
    self.forceMonotonicSlopes = forceMonotonicSlopes
    self.hermite_h00 = hermite_h00
    self.hermite_h10 = hermite_h10
    self.hermite_h01 = hermite_h01
    self.hermite_h11 = hermite_h11
    
  def finalize_endpoints(self):
    if self.dimensions == 2:
      self.__setitem__(0,self.endpoints[0][1])
      self.__setitem__(-1,self.endpoints[1][1])

  def set_size_and_endpoints(self,size,endpointInitMode):
    self.size = size
    self.dimensions = len(self.size)
    self.volume = PyGenTools.accumulate(self.size,"*")
    assert type(endpointInitMode) in [list,str]
    if type(endpointInitMode) == str:
      endpointInitMode = [str(endpointInitMode) for i in range(2)]
    assert len(endpointInitMode) == 2 #1 for each endpoint.
    tempEndpoints = [[0,None],[self.size[0]-1,None]]
    for i in [0,1]:
      if self.size[1] == None:
        tempEndpoints[i][1] = 0
        print("Curves.Spline.setSizeAndEndpoints: size[1]==None sets endpoint height to zero.")
        continue
        
      try:
        tempEndpoints[i][1] = self.resolve_init_value_keyword(endpointInitMode[i])
      except KeyError:
        raise KeyError("The endpointInitMode value {} at i={} is invalid!".format(repr(endpointInitMode[i]),i))

    self.endpoints = ((tempEndpoints[0][0],tempEndpoints[0][1]),(tempEndpoints[1][0],tempEndpoints[1][1]))
    if self.size == None:
      print("Curves.Spline.setSizeAndEndpoints: Size should not be empty, and this branch should not be running!")
      self.size = [self.endpoints[1][0] - self.endpoints[0][0] + 1,None]
      print("Curves.Spline.setSizeAndEndpoints: self.size is incomplete.")
    assert len(self.endpoints) == 2
    assert self.endpoints[0][0] == 0, "sample ranges not starting at zero are not yet supported."
    assert self.endpoints[1][0] == size[0]-1, "sample ranges not ending at their second endpoint are not supported."
    
    
  def set_default_value(self,default_value):
    if type(default_value) == str:
      self.default_value = self.resolve_init_value_keyword(default_value)
    else:
      self.default_value = default_value
      
    
  def resolve_init_value_keyword(self, keyword):
      if keyword == "middle":
        return self.size[1]>>1
      elif keyword == "zero":
        return 0
      elif keyword == "maximum":
        return self.size[1]-1
      else:
        raise KeyError("The init value keyword is invalid!")


  def set_interpolation_mode(self,interpolationMode):
    if type(interpolationMode) == str:
      self.interpolation_method_name = interpolationMode.split("&")[0]
      self.output_filters = []
      if "&" in interpolationMode:
        self.output_filters.extend(interpolationMode.split("&")[1].split(";")) #@ this is not ideal but it saves complexity in testing. It lets every configuration I want to test be described by a single string.
      if not self.interpolation_method_name in Spline.SUPPORTED_INTERPOLATION_METHOD_NAMES:
        if self.interpolation_method_name != "unspecified":
          raise ValueError("The interpolation_method_name " + self.interpolation_method_name + " is not supported.")
      for outputFilter in self.output_filters:
        if not outputFilter in Spline.SUPPORTED_OUTPUT_FILTERS:
          raise ValueError("The outputFilter " + outputFilter + " is not supported.")
    elif isinstance(interpolationMode,dict):
      self.interpolation_method_name = interpolationMode.get("method_name","unspecified163")
      self.interpolation_power = interpolationMode.get("power",2)
      self.output_filters = interpolationMode.get("output_filters",[])
      #self.interpolation_distance_2d_fun = lookup_if_str(distance_2d_funs,interpolationMode.get("distance_fun","absolute_distance"))
      self.interpolation_point_distance_nd_fun = lookup_if_str(point_distance_nd_funs,interpolationMode.get("distance_fun","absolute_distance"))
    #print("setInterpolationMode set outputFilters to {}.".format(self.outputFilters))
    self.find_performance_warnings()
    self.initialize_output_filter()
    
    
  def find_performance_warnings(self):
    def warn(filterName,modeName):
      print("Curves.Spline.findPerformanceWarnings: outputFilter \"" + filterName + "\" and interpolationMode \"" + modeName + "\" are both enabled, but that filter doesn't affect the results of that method of interpolation.")
    for outputFilter in ["span_clip","global_clip","monotonic"]:
      if outputFilter in self.output_filters:
        if self.interpolation_method_name in ["hold","nearest_neighbor","linear","sinusoidal"]:
          warn(outputFilter,self.interpolation_method_name)
    for outputFilter in ["round"]:
      if outputFilter in self.output_filters:
        if self.interpolation_method_name in ["hold","nearest_neighbor"]:
          warn(outputFilter,self.interpolation_method_name)
    if "span_clip" in self.output_filters and "global_clip" in self.output_filters:
      print("Curves.Spline.findPerformanceWarnings: global_clip and span_clip are both enabled, but span_clip always does the job of global_clip, assuming no Spline bones are outside of the size of the spline.")


  def initialize_output_filter(self):
    if "global_clip" in self.output_filters:
      print("Curves.Spline: warning: global clip incorrectly uses size. boundaries should be added to spline to properly support global clipping.")
    ORIGINAL_OUTPUT_FILTER_TEMPLATE = "lambda value_to_filter, sur_for_filter: {}"
    outputFilterTemplate = ORIGINAL_OUTPUT_FILTER_TEMPLATE
    
    #print("Curves.Spline.initializeOutputFilter: self.outputFilters is now {}.".format(self.outputFilters))
    for outputFilterName in self.output_filters:
      if outputFilterName in Spline.OUTPUT_FILTER_TEMPLATES.keys():
        outputFilterTemplate = outputFilterTemplate.format(Spline.OUTPUT_FILTER_TEMPLATES[outputFilterName])
      else:
        print("output filter {} is not in OUTPUT_FILTER_TEMPLATES, but that's probably fine.".format(outputFilterName))
    outputFilterTemplate = outputFilterTemplate.format("value_to_filter")
    self._output_filter_fun = eval(outputFilterTemplate)
    #print("initializeOutputFilter finally evaluated {}.".format(repr(outputFilterTemplate)))



  def toPrettyStr(self):
    alphabet = [["~","-"],["%","#"]] #access like alphabet[known?][exact?]
    result = "Curves.Spline.toPrettyStr generated string representation."
    assert self.endpoints[0][0] == 0
    tempValues = [self.__getitem__(index) for index in range(self.endpoints[1][0]+1)]
    roundedTempValues = [int(round(value)) for value in tempValues]
    valueRange = (min(roundedTempValues),max(roundedTempValues))
    for y in range(valueRange[1],valueRange[0]-1,-1):
      if not y in roundedTempValues: #@ slow.
        if not result.endswith("\n..."):
          result += "\n..."
        continue
      result += "\n"+str(y).rjust(10," ")+": "
      #print("Curves.Spline.prettyPrint: prettyPrinting disabled for python2 compatibility.")
      for index in range(self.size[0]):
        if not roundedTempValues[index] == y:
          result += " "
          continue
        known = (self.data[index] != None)
        exact = (tempValues[index] == y)
        addition = alphabet[known][exact]
        result += addition
    result += "\nend of generated string representation."
    return result


  def getPointInDirection(self,location,direction,skipStart=True):
    assert len(self.size) == 2, "this is a 2d only method."
    #dbgPrint("Curves.Spline.getPointInDirection: "+str((location,direction,skipStart)))
    #assert type(direction) == int
    #assert direction in [-1,1]
    #assert 0 <= location < len(self.data)
    #print(direction)
    if Spline.CACHE_NEARBY_BONE_LOCATION:
      location += skipStart*direction
      while 0 <= location < len(self.data):
        nearbyBoneLocation = self.nearbyBoneLocation[location]
        if nearbyBoneLocation == location:
          return (location,self.data[location])
        nearbyBoneDisplacement = nearbyBoneLocation - location
        if nearbyBoneDisplacement*direction > 0: #if they have the same sign:
          return (nearbyBoneLocation,self.data[nearbyBoneLocation])
        location -= nearbyBoneDisplacement
      return None
    elif Spline.CACHE_BONE_DISTANCE_ABS:
      location += skipStart*direction
      while 0 <= location < len(self.data):
        if self.data[location] != None:
          return (location,self.data[location])
        location += direction * self.boneDistanceAbs[location]
      return None
    else:
      location += skipStart*direction
      if not 0 <= location < len(self.data):
        return None
      for i in range(len(self.data)*2):
        if self.data[location] != None:
          return (location,self.data[location])
        location += direction
        if location < 0 or location >= len(self.data):
          return None
    assert False
    
  def get_enclosing_surroundings(self,location):
    assert isinstance(location,list) or isinstance(location,tuple)
    assert len(location) + 1 == self.dimensions
    if self.dimensions == 2:
      return self.get_surroundings_2d(location[0],[0,1,1,0])
    elif self.dimensions == 3:
      triggerFun = (lambda testLocation: PyDeepArrTools.isInShape(testLocation,self.size[:-1]) and PyDeepArrTools.getValueUsingPath(self.data, testLocation) != None)
      surLocations = arrTakeOnly(genFindNearest2d(location,triggerFun,timeout=self.volume),4)
      return [list(surLocation) + [PyDeepArrTools.getValueUsingPath(self.data,surLocation)] for surLocation in surLocations]
    elif self.dimensions > 3:
      raise NotImplementedError("above 3d")
    else:
      assert False, "Invalid dimensions."
  
  def get_necessary_surroundings_2d(self,index):
    """
    creates a surroundings list [second item to left, item to left, item to right, second item to right] populated with only the values needed by the current interpolation mode. Values not needed will be None.
    """
    surroundings_request = Spline.SURROUNDINGS_REQUIREMENTS[self.interpolation_method_name]
    return self.get_surroundings_2d(index,surroundings_request)
    

  def get_surroundings_2d(self,index,surroundings_request):
    """
    creates a surroundings list [second item to left, item to left, item to right, second item to right] populated with only the values requested. Values not requested will be None.
    """
    surroundings = [None,None,None,None]
    if surroundings_request[1]:
      surroundings[1] = self.getPointInDirection(index,-1)
      if surroundings_request[0]:
        if surroundings[1] == None:
          print("Curves.Spline.get_necessary_surroundings_2d: at index {}, surroundings[1] was empty, and surroundings[0] won't be filled in.".format(index))
        else:
          surroundings[0] = self.getPointInDirection(surroundings[1][0],-1)
    if surroundings_request[2]:
      surroundings[2] = self.getPointInDirection(index,1)
      if surroundings_request[3]:
        if surroundings[2] == None:
          print("Curves.Spline.get_necessary_surroundings_2d: at index {}, surroundings[2] was empty, and surroundings[3] won't be filled in.".format(index))
        else:
          surroundings[3] = self.getPointInDirection(surroundings[2][0],1)
    return surroundings
    


  def __len__(self): #this is to make Spline iterable.
    assert self.dimensions == 2, "this is a 2d only method."
    return self.size[0]

  
  def __getitem__(self,index):
    assert self.dimensions == 2, "this is a 2d only method."
    index = index%len(self.data)
    location = (index,)
    return self.get_at_location_cached(location)
      
  
  def __setitem__(self,index,value):
    assert self.dimensions == 2, "this is a 2d only method."
    index = index%len(self.data)
    location = (index,)
    self.set_at_location_cached(location,value)
    
      
  def get_value_using_path(self,path):
    assert len(path) + 1 == self.dimensions
    return self.get_at_location_cached(path)
      
      
  def set_value_using_cell(self,cell):
    assert len(cell) == self.dimensions
    self.set_at_location_cached(cell[:-1],cell[-1])
      

    
      
  def get_at_location_cached(self,location):
    assert len(location) + 1 == self.dimensions
    
    if self.dimensions == 2:
      index = location[0]
      directAccessResult = self.data[index]
      if directAccessResult != None: #no interpolation is ever done when the index in question has a known value.
        return directAccessResult
        
      if Spline.CACHE_VALUES_2D:
        if self.valueCache[index] != None:
          return self.valueCache[index]
        else:
          sur = self.get_necessary_surroundings_2d(index)
          result = self.solve_location(location,sur)
          self.valueCache[index] = result
          return result
    elif self.dimensions > 2:
      directAccessResult = PyDeepArrTools.getValueUsingPath(self.data,location)
      if directAccessResult != None:
        return directAccessResult
    else:
      assert False, "invalid dimension count."
      
    if Spline.CACHE_VALUES_BY_SUR_HASH:
      sur = None
      if self.dimensions == 2:
        sur = self.get_necessary_surroundings_2d(location[0])
      elif self.dimensions > 2:
        sur = self.get_enclosing_surroundings(location)
      else:
        assert False, "Invalid dimension count."
      surHash = hash_point_list(sur, self.size) #include cell heights.
      if surHash in self.value_cache_by_surroundings_hash:
        surHashEntryDict = self.value_cache_by_surroundings_hash[surHash]
      else: #if no point with these surroundings has ever been calculated and cached before:
        surHashEntryDict = dict() #make a new entry.
        self.value_cache_by_surroundings_hash[surHash] = surHashEntryDict #register the new entry.
      locationHash = flatten_point(location,self.size[:-1])
      if locationHash in surHashEntryDict:
        return surHashEntryDict[locationHash]
      else:
        result = self.solve_location(location,sur)
        surHashEntryDict[locationHash] = result
        return result

    return self.solve_location(location)
      
        
  def solve_location(self,location,sur):
    #print("solve_location: location is {}. sur is {}.".format(location,sur))
    assert isinstance(location,list) or isinstance(location,tuple)
    result = None
    interpolation_method_name = self.interpolation_method_name
    
    if interpolation_method_name == "hold":
      resultPoint = sur[1]
      result = resultPoint[1]
    elif interpolation_method_name == "nearest_neighbor":
      #when two neighbors are equal distances away, the one on the left will be chosen.
      t = float(location[0]-sur[1][0])/float(sur[2][0]-sur[1][0])
      resultPoint = sur[1] if (t <= 0.5) else sur[2]
      result = resultPoint[1]
    elif interpolation_method_name in ["linear","sinusoidal"]:
      t = float(location[0]-sur[1][0])/float(sur[2][0]-sur[1][0])
      leftBone,rightBone = sur[1], sur[2]
      if interpolation_method_name == "linear":
        result = leftBone[1]+((rightBone[1]-leftBone[1])*t)
      elif interpolation_method_name == "sinusoidal":
        result = leftBone[1]+((rightBone[1]-leftBone[1])*0.5*(1-math.cos(math.pi*t)))
    elif interpolation_method_name == "finite_difference_cubic_hermite":
      t = float(location[0]-sur[1][0])/float(sur[2][0]-sur[1][0])
      if None in sur[1:3]:
        assert False, "an important (inner) item is missing from the surroundings."
      slopes = [None,None]
      if sur[0] == None:
        slopes[0] = float(sur[2][1]-sur[1][1])/float(sur[2][0]-sur[1][0])
      else:
        slopes[0] = 0.5*(float(sur[2][1]-sur[1][1])/float(sur[2][0]-sur[1][0])+float(sur[1][1]-sur[0][1])/float(sur[1][0]-sur[0][0]))
      if sur[3] == None:
        slopes[1] = (sur[2][1]-sur[1][1])/(sur[2][0]-sur[1][0])
      else:
        slopes[1] = 0.5*(float(sur[3][1]-sur[2][1])/float(sur[3][0]-sur[2][0])+float(sur[2][1]-sur[1][1])/float(sur[2][0]-sur[1][0]))
      if "monotonic" in self.output_filters:
        self.forceMonotonicSlopes(sur,slopes) #might not have any effect anyway.
      result = self.hermite_h00(t)*sur[1][1]+self.hermite_h10(t)*slopes[0]+self.hermite_h01(t)*sur[2][1]+self.hermite_h11(t)*slopes[1]
    elif interpolation_method_name == "inverse_distance_weighted":
      weightSum = 0.0
      workingResult = 0.0
      for surPoint in sur:
        if surPoint == None:
          continue
        surPointValue = surPoint[-1]
        #surPointWeight = float(abs(location - surPoint[0]))**(-self.interpolation_power)
        surPointDistance = self.interpolation_point_distance_nd_fun(location, surPoint)
        assert surPointDistance > 0, "this should have been detected earlier!"
        surPointWeight = surPointDistance**(-self.interpolation_power)
        workingResult += surPointValue*surPointWeight
        weightSum += surPointWeight
      if weightSum > 0: #avoid zero division error.
        workingResult /= weightSum
        result = workingResult
      else:
        result = self.default_value
    else:
      raise KeyError("The interpolation_method_name {} isn't supported.".format(interpolation_method_name))
    
    result = self._output_filter_fun(result,sur)
    return result
    
    
  def set_at_location_cached(self,location,value):
    assert len(location) + 1 == self.dimensions
      
    if Spline.CACHE_VALUES_BY_SUR_HASH:
      sur = None
      if self.dimensions == 2:
        sur = self.get_necessary_surroundings_2d(location[0])
      elif self.dimensions > 2:
        raise NotImplementedError("some cache handling isn't ready for this number of dimensions.")
      else:
        assert False, "invalid dimension count."
      self.clear_cache_entry_for_surroundings(sur)
      
    if self.dimensions == 2:
      index = location[0]
      
      self.data[index] = value
      
      if Spline.CACHE_NEARBY_BONE_LOCATION:
        assert value != None, "None values can't be set while bone location caching is enabled."
        self.nearbyBoneLocation[index] = index
        for direction in [-1,1]:
          for x in (range(index-1,-1,-1) if direction==-1 else range(index+1,len(self.data))):
            oldNearestBoneLocation = self.nearbyBoneLocation[x]
            if oldNearestBoneLocation == None:
              self.nearbyBoneLocation[x] = index
            else:
              oldDist = abs(x-oldNearestBoneLocation)
              newDist = abs(x - index)
              if newDist >= oldDist:
                break
              self.nearbyBoneLocation[x] = index
      elif Spline.CACHE_BONE_DISTANCE_ABS:
        assert value != None, "None values can't be set while bone distance abs caching is enabled."
        self.boneDistanceAbs[index] = 0
        for direction in [-1,1]:
          #x = index + direction
          #while x < len(self.data):
          for x in (range(index-1,-1,-1) if direction==-1 else range(index+1,len(self.data))):
            oldDist = self.boneDistanceAbs[x]
            newDist = abs(x - index)
            if oldDist != None:
              if newDist >= oldDist:
                break
            self.boneDistanceAbs[x] = newDist

      if Spline.CACHE_VALUES_2D:
        #the following fast update version works by processing runs of non-None values. It is too simple to handle clearing a far region without a closer one first. The benefit of doing it this way is that bone distances don't need to be determined before work starts.
        if self.interpolation_method_name == "unspecified":
          return
        updateType = Spline.VALUE_CACHE_UPDATE_TYPES[self.interpolation_method_name]
        if type(updateType) != list:
          raise ValueError("updateType definitions of types other than list are not supported yet.")
        self.valueCache[index] = None
        if (0,1) in updateType:
          self.clearCacheInDirection(index, 1, times=(2 if (1,2) in updateType else 1))
        if (-1,0) in updateType:
          self.clearCacheInDirection(index, -1, times=(2 if (-2,-1) in updateType else 1))
    elif self.dimensions > 2:
      
      PyDeepArrTools.setValueUsingPath(self.data, location, value)
    
      if Spline.CACHE_NEARBY_BONE_LOCATION:
        print("Spline.set_at_location_cached: warning: can't cache nearby bone location when dimensions > 2.")
      if Spline.CACHE_BONE_DISTANCE_ABS:
        print("Spline.set_at_location_cached: warning: can't cache bone distance abs when dimensions > 2.")
    else:
      assert False, "invalid dimension count."


  def clearCacheInDirection(self,index,direction,times=1):
    """
    skips clearing the value at index. The arg _times_ indicates the number of times to skip over a value of None and continue.
    If interpolation with endpoint wrapping is added, this method will need to be changed to wrap as well.
    """
    clearingIndex = index
    try:
      for i in range(times):
        clearingIndex += direction
        while self.valueCache[clearingIndex] != None:
          self.valueCache[clearingIndex] = None
          clearingIndex += direction
    except IndexError:
      pass
      

  def clear_cache_entry_for_surroundings(self,sur):
    assert all(len(item) == len(self.size) for item in sur if item != None)
    surHash = hash_point_list(sur,self.size)
    if surHash in self.value_cache_by_surroundings_hash:
      del self.value_cache_by_surroundings_hash[surHash] #the old surroundings are now not a valid thing to search by. Any points who used to have values chached in the dict stored here now need to be regenerated.





