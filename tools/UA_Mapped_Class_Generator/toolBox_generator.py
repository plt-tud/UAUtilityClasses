#!/usr/bin/env/python
# -*- coding: utf-8 -*-

###
### Author:  
### Version: rev 1
###
### This program was created for educational purposes and has been
### contributed to the open62541 project by the author. All licensing
### terms for this source is inherited by the terms and conditions
### specified for by the open62541 project (see the projects readme
### file for more information on the LGPL terms and restrictions).
###
### This program is not meant to be used in a production environment. The
### author is not liable for any complications arising due to the use of
### this program.
###


import re
import string
from logger import *

def getNodeCodeName(objectNode):
    name = objectNode.browseName()
    if len(objectNode.browseName().split(':')) > 1:
      name = name.split(":")[-1]
    re.sub("^[0-9]","",name)
    for SYM in "^.+: <>()[]":
      name=name.replace(SYM,"")
    return name

def getCPPTypeByUAType(ua_typestring):
  if ua_typestring.lower() == "string":
    return "std::string"
  elif ua_typestring.lower() in ["double", "float"]:
    return ua_typestring.lower()
  elif ua_typestring.lower() in ["int16", "uint16","int32", "uint32","int64", "uint64"]:
    return ua_typestring.lower() + "_t"
  elif ua_typestring.lower() == "nodeid":
    return "UA_NodeId"
  elif ua_typestring.lower() in ["bool", "boolean"]:
    return "bool"
  elif ua_typestring.lower() in ["byte"]:
    return "uint8_t"
  elif ua_typestring.lower() in ["sbyte"]:
    return "int8_t"
  elif ua_typestring.lower() == "datetime":
    return "time_t"
  elif ua_typestring.lower() == "localizedtext":
    return "std::tuple<std::string, std::string>"
  # FIXME: Lots of missing types here...
  else:
    return "NonMappableType_UAType_" + ua_typestring; 
    
def getProxyTypeByUAType(ua_typestring):
  if ua_typestring.lower() == "string":
    return "STRING"
  elif ua_typestring.lower() in ["double", "float"]:
    return ua_typestring.upper()
  elif ua_typestring.lower() in ["int16", "uint16","int32", "uint32","int64", "uint64", "byte", "sbyte"]:
    return ua_typestring.upper()
  elif ua_typestring.lower() == "datetime":
    return "DATETIME"
  elif ua_typestring.lower() in ["bool", "boolean"]:
    return "BOOL"
  elif ua_typestring.lower() == "localizedtext":
    return "LOCALIZEDTEXT"
  # FIXME: Lots of missing types here...
  else:
    return "NonMappableType_UAType_" + ua_typestring; 
        
# From "open62541_MacroHelper.py" littlebit changed
# now returns a single String with name of the DefineString
def getNodeIdDefineString(objectNode):
  
  extrNs = objectNode.browseName().split(":")
  symbolic_name = ""
  # strip all characters that would be illegal in C-Code
  if len(extrNs) > 1:
    nodename = extrNs[1]
  else:
    nodename = extrNs[0]
  
  symbolic_name = substitutePunctuationCharacters(nodename)
  if symbolic_name != nodename :
    log(self, "Subsituted characters in browsename for nodeid " + str(objectNode.id().i) + " while generating C-Code ", LOG_LEVEL_WARN)
      
  return "UA_NS"  + str(objectNode.id().ns) + "ID_" + symbolic_name.upper()
  
  
# From "open62541_MacroHelper.py" just copy&paste it
def substitutePunctuationCharacters(input):
  ''' 
    substitutePunctuationCharacters
  
    Replace punctuation characters in input. Part of this class because it is used by
    ua_namespace on occasion.
    returns: C-printable string representation of input
  '''
  # No punctuation characters <>!$
  illegal_chars = list(string.punctuation)
  # underscore is allowed
  illegal_chars.remove('_')

  illegal = "".join(illegal_chars)
  substitution = ""
  # Map all punctuation characters to underscore
  for illegal_char in illegal_chars:
    substitution = substitution + '_'

  return input.translate(string.maketrans(illegal, substitution), illegal)

def getNodeIdInitializer(node):
  if node.id().i != None:
      return "UA_NODEID_NUMERIC(" + str(node.id().ns) + ", " + str(node.id().i) + ")"
  elif node.id().s != None:
    return "UA_NODEID_STRING("  + str(node.id().ns) + ", " + node.id().s + ")"
  elif node.id().b != None:
    return ""
  elif node.id().g != None:
    return ""
  return "NODEID_NUMERIC(1,0)"
      