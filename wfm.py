#from __future__ import print_function

import collections
import struct
import array
import sys
import os

def printf(str, *args):
    print str % args,

def printScaleraw(value, unit, scale):
	value_scaled = value * scale;
	printf("\t\t%6.3f %s\n", value_scaled, unit);
	
def printScale(label, value, unit, scale):
	value_scaled = value * scale;
	printf("%25s: %6.3f %s\n", label, value_scaled, unit);

def probeScale(scale):
	base = ord(scale)
	
	if base == 6:
		return 1
	if base == 7:
		return 2
	if base == 8:
		return 5
	if base == 9:
		return 10
	if base == 12:
		return 100

class FormatError(Exception):
  pass
    
def _parseFile(f, description, leading="<", strict = True):
  """
  Parse a binary file according to the provided description.
  
  The description is a list of triples, which contain the fieldname, datatype
  and a test condition.
  """
  
  data = collections.OrderedDict()
  
  for field, t, test in description:
    if t == "nested":
      data[field] = _parseFile(f, test, leading)
    else:
      binary_format = leading+t
      tmp = f.read(struct.calcsize(binary_format))
      printf("POS %X\n", f.tell());
      value = struct.unpack(binary_format, tmp)[0]
      data[field] = value
      
      if test:
        scope, condition, match = test
        
        assert scope in ("expect", "require")
        assert condition  in ("==", ">=", "<=", "<", ">", "in")
        matches = eval("value %s match" % condition)
        
        if not matches and scope == "require":
          raise FormatError("Field %s %s %s not met, got %s" % (field, condition, match, value))
        
        if strict and not matches and scope == "expect":
          raise FormatError("Field %s %s %s not met, got %s" % (field, condition, match, value))
        
  return data

def parseRigolWFM(f, strict=True):
  chan_header  = (
  	("padding1",	"14s",	None),
  	("enabled",		"B",		None),
  	("padding2",	"14s",	None),
    ("probeAtt",	"c",		None),
    ("padding3",	"3s",		None),
    ("scaleV",		"q",		None),
    ("padding4",	"16s",	None),
    ("name",			"3s",		None),
  )
  time_header  = (
  	("scale",			"c",			None),
  	("padding1",	"8s",	None),
  )
  
  wfm_header = (
    ("magic",    	"H",			("require", "==", 0xFF01)),
    ("padding1", 	"2013s",  None),
    #("padding1", 	"1980s",  None), DS1104Z
    ("time1", 		"nested", time_header),
    ("channel4", 	"nested", chan_header),
    ("channel3", 	"nested", chan_header),
    ("channel2", 	"nested", chan_header),
    ("channel1", 	"nested", chan_header),
    ("padding2", 	"54s",  	None),
    ("off_ch1",		"q",			None),
    ("off_ch2",		"q",			None),
    ("off_ch3",		"q",			None),
    ("off_ch4",		"q",			None),
  )
  
  fileHdr = _parseFile(f, wfm_header, strict=strict)
  
  #import pprint
  #pprint.pprint(fileHdr["channel1"])
  fileHdr["channels"] = (	fileHdr["channel1"],
  												fileHdr["channel2"],
  												fileHdr["channel3"],
  												fileHdr["channel4"] )
  
  fileHdr["offset"] = (	fileHdr["off_ch1"],
  											fileHdr["off_ch2"],
  											fileHdr["off_ch3"],
  											fileHdr["off_ch4"] )
  """
  The time divisions has 3 possible values 10, 20 and 50
  All other values are always multiples (100ns, 200ns, 500ns, 1000ns)
  
  Take the scale value, calculate where it is (base) and add as 
  many zeros as indicated by scale_real
  
  """
  scale = ord(fileHdr["time1"]["scale"])
  scale_real = round(float(scale) / 3);
  base = scale - ( (scale_real - 1) * 3 )
    
  if base == 2:
  	scale_ns = 10
  if base == 3:
  	scale_ns = 20
  if base == 4:
  	scale_ns = 50
  
  #Number of zeros to add
  scale_d = pow(10, scale_real - 1)
  scale_ns *= scale_d
	
	
  fileHdr["timeDiv"] = scale_ns
  
  
  for i in range(4):
  	printf("%s %i\n", fileHdr["channels"][i]["name"], fileHdr["channels"][i]["enabled"]);
  	fileHdr["channels"][i]["probeScale"] = probeScale(fileHdr["channels"][i]["probeAtt"])
  	fileHdr["channels"][i]["offsetScaled"] = fileHdr["offset"][i] * fileHdr["channels"][i]["probeScale"];
  	#printf("Probe attenuation \t\t%0.1f\n", fileHdr["channels"][i]["probeScale"]);
  	printScale("Probe attenuation", fileHdr["channels"][i]["probeScale"], "X", 1)
  	printScale("Y grid scale", fileHdr["channels"][i]["scaleV"], "V/div", 1e-9);
  	printScale("Y shift", fileHdr["channels"][i]["offsetScaled"], "V", 1e-6);
  	printf("\n");
  
  printScale("Time grid scale", fileHdr["timeDiv"], "ns/div", 1)
  
  filePosition = f.tell() + 848
  f.seek(0, os.SEEK_END)
  fileSize = f.tell()
  f.seek(filePosition)
  
  printf("%x\n", f.tell());
  
  nBytes = (fileSize - filePosition)
  sampleData = array.array('B')
  sampleData.fromfile(f, nBytes)
  fileHdr["channels"][0]['data'] = sampleData
  samples = len(fileHdr["channels"][0]['data'])
  
  scale_time = float(fileHdr["timeDiv"] * 1e-9) * 12
  scale_time = scale_time / (samples - 512)

  #scale_time = 1./(float(fileHdr["timeDiv"]) * 1e-6)
  #scale_time = float(samples)/scale_time
  printf("samples: %i %6.3e\n", samples, scale_time);
  #fileHdr["time"] = [(t - samples/2) * 1 for t in range(samples)]
  fileHdr["time"] = [(t) * scale_time for t in range(samples)]

  return fileHdr
  
def describeScopeData(scopeData):
  def describeDict(d, description, ljust=0):
    tmp = ""
    for item, desc in description:
      if item in d:
        tmp = tmp + "%s: %s\n" % (desc[0].ljust(ljust), desc[1] % d[item])
    return tmp

  def header(header_name, sep = '='):
    return "\n%s\n%s\n" % (header_name, sep*len(header_name))
  
  channelDsc = (
    ('probeAtt'		, ("Probe attenuation", "%c")),
    ('scaleV'			, ("Y grid scale", "%0.3e V/div")),
    )

  tmp = ""
  
  tmp = tmp + header("Channel")
  data = scopeData["channel1"]
  tmp = tmp + describeDict(data, channelDsc, ljust=25)
  
  return tmp