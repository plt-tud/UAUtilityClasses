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
	
	def __init__(self, serverList, namespace):
		self.namespace = namespace
		self.serverList = serverList
		self.ignoredNodes = []
		#self.header = header
		#self.objectNode = objectNode
		#self.methods = methods
		#self.variables = variables
		#self.objects = objects

       
       
	def generateHeaderFile(self, header, objectNode, methodList, variableList, objectList):
		classname = toolBox_generator.getNodeCodeName(objectNode);
		
		isServerClass = False;
		## Check kind of class
		## normal class oder root class     
		for server in self.serverList:
			if server.firstChild.nodeValue == classname:
				isServerClass = True;
				
		# Print Header Guards
		header.write("#ifndef HAVE_" + classname.capitalize() + "_H\n")
		header.write("#define HAVE_" + classname.capitalize() + "_H\n\n")
        
        
		if	isServerClass:
			header.write("#include <ipc_managed_object.h>\n")
			
		header.write("#include \"ua_mapped_class.h\"\n\n")
		
		
		if	isServerClass:
			header.write("class " + classname + " : public ipc_managed_object, ua_mapped_class {\n")
		else:
			header.write("class " + classname + " : ua_mapped_class {\n")
	
		header.write("private:\n")
				
		if	isServerClass:
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
		'	header.write(INDENT + "//FIXME " + toolBox_generator.getCPPTypeByUAType(str(on.id())) + " " + toolBox_generator.getNodeCodeName(on) + ";\n")
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
		
		if	isServerClass:
			header.write(INDENT + classname + "(std::string moduleName, uint16_t opcuaPort);\n")
			header.write(INDENT + "~" + classname + "();\n")
			header.write(INDENT + "void workerThread();\n")
		else:
			header.write(INDENT + classname + "(UA_NodeId baseNodeId, UA_Server* server);\n")
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
		
		#header.write(INDENT + "std::string name;\n\n")
		#header.write(INDENT + "UA_NodeId rootNodeId;\n")
		#header.write(INDENT + "UA_NodeId HMIId;\n")
		#header.write(INDENT + "UA_NodeId PhysicalPortsListId;\n")
		#header.write(INDENT + "UA_NodeId ServiceListId;\n")
		#header.write(INDENT + "UA_NodeId SignalListId;\n\n")
		
		header.write(INDENT + "UA_ServerConfig server_config;\n")
		header.write(INDENT + "UA_ServerNetworkLayer server_nl;\n")
		#header.write(INDENT + "UA_Logger logger;\n")
		#header.write(INDENT + "UA_NodeId simulatorsNodeId;\n\n")
		
	def generateHeaderServerMethoden(self, header):
		header.write(INDENT + "void constructserver(uint16_t opcuaPort);\n")
