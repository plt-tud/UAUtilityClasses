#
# Copyright (c) 2016 <copyright holder> <email>
#
# Autor:
# Version: rev 1
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# 
#

import logging
from ua_constants import *
import string
from ua_namespace import opcua_namespace
import re
import os
import toolBox_generator

logger = logging.getLogger(__name__)

__unique_item_id = 0

defined_typealiases = []

INDENT="    "
        
class headerfile_generator:
  
  namespace = None # OPCUA namespace to be printed
  serverList = None
  
  #header = None
  #objectNode = None
  #methods = None
  #variables = None
  #objects = None
  
  def __init__(self, namespace, objectNode, serverList=None):
    self.namespace = namespace
    self.ignoredNodes = []
    self.objectNode = objectNode
    if serverList != None and serverList.name == toolBox_generator.getNodeCodeName(self.objectNode):
      self.serverList = serverList
    else:
      self.serverList = None
  
  def isServerClass(self, classname):
    if self.serverList == None:
      return False
    return True
  
  def generateHeaderFile(self, header, methodList, variableList, objectList):
    classname = toolBox_generator.getNodeCodeName(self.objectNode);
        
    header.write("/*\n")
    header.write("* @generated \n")
    header.write("*/ \n\n")
    
    # Print Header Guards
    header.write("#ifndef HAVE_" + classname.capitalize() + "_H\n")
    header.write("#define HAVE_" + classname.capitalize() + "_H\n\n")
        
    if self.isServerClass(classname):
      header.write("#include <ipc_managed_object.h>\n")
    header.write("#include \"ua_mapped_class.h\"\n\n")
    
    if self.isServerClass(classname):
      header.write("class " + classname + " : public ipc_managed_object, ua_mapped_class {\n")
      header.write("private:\n")
      header.write(INDENT + "UA_Boolean runUAServer;\n")
      header.write(INDENT + "std::thread *serverThread;\n")
    else:
      header.write("class " + classname + " : ua_mapped_class {\n")
      header.write("private:\n")
    header.write(INDENT + "std::string name;\n")
    header.write(INDENT + "UA_NodeId rootNodeId;\n")
    
    if self.isServerClass(classname):
      self.generateHeaderServerVariables(header, variableList)
      for vn in variableList:
        header.write(INDENT + toolBox_generator.getCPPTypeByUAType(str(vn.dataType().target().browseName())) + " " + toolBox_generator.getNodeCodeName(vn) + ";\n")
      self.generateHeaderServerMethoden(header)
      print("generate server header file")
    else:
      for vn in variableList:
        header.write(INDENT + toolBox_generator.getCPPTypeByUAType(str(vn.dataType().target().browseName())) + " " + toolBox_generator.getNodeCodeName(vn) + ";\n")
      print("generate standard header file")
    
    '''
    ' Do we need this kind of object?! You should think about...
    '
    '''
    '''#objectList
    ' for on in objectList:
    '  header.write(INDENT + "//FIXME " + toolBox_generator.getCPPTypeByUAType(str(on.id())) + " " + toolBox_generator.getNodeCodeName(on) + ";\n")
    '''
    
    header.write("\n")
    for on in objectList:
      header.write(INDENT + "UA_NodeId " + toolBox_generator.getNodeCodeName(on) + ";\n")
    header.write("\n")
    header.write(INDENT + "UA_StatusCode mapSelfToNamespace();\n")
    header.write("\n")
    header.write("protected:\n")
    header.write("\n")
    header.write("public:\n")
    
    if self.isServerClass(classname):
      header.write(INDENT + classname + "(std::string name, uint16_t opcuaPort);\n")
      header.write(INDENT + "void workerThread_setup();\n")
      header.write(INDENT + "void workerThread_iterate();\n")
      header.write(INDENT + "void workerThread_cleanup();\n")
    else:
      header.write(INDENT + classname + "(std::string name, UA_NodeId baseNodeId, UA_Server* server);\n")
    header.write(INDENT + "~" + classname + "();\n")
    header.write("\n")
    header.write(INDENT + "// Getter and Setter functions \n")
    for vn in variableList:
      header.write(INDENT + toolBox_generator.getCPPTypeByUAType(str(vn.dataType().target().browseName())) + " get_" + toolBox_generator.getNodeCodeName(vn) + "();\n")
      header.write(INDENT + "void set_" + toolBox_generator.getNodeCodeName(vn) + "("+ toolBox_generator.getCPPTypeByUAType(str(vn.dataType().target().browseName()))+" value);\n")
      header.write("\n")
    
    self.generateHeaderMethods(header, methodList)
    
    header.write("\n")
    header.write("};\n")
    header.write("\n#endif // Header guard\n")
    
  def generateHeaderMethods(self, header, methodList):     
    # Method header   
    for mn in methodList:
      header.write("UA_StatusCode " + toolBox_generator.getNodeCodeName(mn) + "(size_t inputSize, const UA_Variant *input, size_t outputSize, UA_Variant *output);\n") 
    
  def generateHeaderServerVariables(self, header, variableList):
    header.write(INDENT + "UA_ServerConfig server_config;\n")
    header.write(INDENT + "UA_ServerNetworkLayer server_nl;\n")
    
  def generateHeaderServerMethoden(self, header):
    header.write(INDENT + "void constructserver(uint16_t opcuaPort);\n")
