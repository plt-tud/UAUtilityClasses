#!/usr/bin/env/python
# -*- coding: utf-8 -*-

###
### Author:  Chris Iatrou (ichrispa@core-vector.net)
### Version: rev 13
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

import logging
from logger import *
from ua_constants import *
import string
from ua_namespace import opcua_namespace
import re
import os
import toolBox_generator
import open62541_MacroHelper

logger = logging.getLogger(__name__)

__unique_item_id = 0

defined_typealiases = []

INDENT="    "
  
class cppfile_generator():
  namespace = None # OPCUA namespace to be printed
  serverList = None
  generatedNamspaceFileName = None
  
  #implementation = None
  #objectNode = None
  #methods = None
  #variables = None
  #objects = None
      
  def __init__(self, generatedNamspaceFileName, objectNode, serverList = None):
    self.objectNode = objectNode
    self.ignoredNodes = []
    self.serverList = serverList
    self.generatedNamspaceFileName = generatedNamspaceFileName  
   
  def addIgnoredNodes(self, ignoredNodesList):
    self.ignoredNodes += ignoredNodesList
    
  def isServerClass(self, classname):
    if self.serverList == None:
      return False
    return True
  
  def generateImplementationFile(self, implementation, methodList, variableList, objectList):
    classname = toolBox_generator.getNodeCodeName(self.objectNode);
      
    implementation.write("/*\n")
    implementation.write("* @generated \n")
    implementation.write("*/ \n\n")

    implementation.write("#include \"" + classname + ".hpp\"\n")
    implementation.write("extern \"C\" {\n")
    implementation.write(INDENT + "#include \"open62541.h\"\n")
    implementation.write(INDENT + "#include \"" + self.generatedNamspaceFileName + ".h\"\n")
    implementation.write("}\n")
    implementation.write("#include \"ua_proxies.h\"\n")
    implementation.write("#include \"ua_proxies_callback.h\"\n")
    implementation.write("#include \"ua_proxies_typeconversion.h\"\n\n")
    
    if  self.isServerClass(classname):
      self.generateServerClass(implementation, methodList, variableList, objectList)
    else:
      ## binding lib's
      self.generateClass(implementation, methodList, variableList, objectList)
      
    self.generateDestructor(implementation, classname)
    self.generateVariable(implementation, variableList, classname)
    self.generateMethods(implementation, methodList, classname)
    self.generateClassMapSelfToNS(implementation, classname, variableList, methodList)


  def generateServerClass(self, implementation, methodList, variableList, objectList):
    classname = toolBox_generator.getNodeCodeName(self.objectNode);
    
    ## hard coded value "name" and "port" -> maybe bad?
    # -> needed? implementation.write("#include \"string.h\"\n\n")
    implementation.write(classname + "::" + classname + "(std::string name, uint16_t opcuaPort) : ua_mapped_class(nullptr, UA_NODEID_NULL) {\n")
    implementation.write(INDENT + "this->name = name;\n")
    implementation.write(INDENT + "this->runUAServer=UA_FALSE; // Needs workerThread_setup\n");
    implementation.write(INDENT + "this->constructserver(opcuaPort);\n")
    implementation.write("}\n\n")
      
    ## Method "constructserver" (special ServerClass methode
    implementation.write("void "+classname+"::constructserver(uint16_t opcuaPort) {\n")
    implementation.write(INDENT + "this->server_config = UA_ServerConfig_standard;\n")
    implementation.write(INDENT + "this->server_nl = UA_ServerNetworkLayerTCP(UA_ConnectionConfig_standard, opcuaPort);\n")
    implementation.write(INDENT + "this->server_config.logger = UA_Log_Stdout;\n")
    implementation.write(INDENT + "this->server_config.networkLayers = &this->server_nl;\n");
    implementation.write(INDENT + "this->server_config.networkLayersSize = 1;\n")
    
    ## Suck -> fix values!!!!
    ## FIXME
    implementation.write(INDENT + "this->server_config.publishingIntervalLimits = { .min = 10.0, .max = 3600.0 * 1000.0 };\n")
    implementation.write(INDENT + "this->server_config.samplingIntervalLimits   = { .min = 10.0, .max = 24.0 * 3600.0 * 1000.0 };\n")
    
    implementation.write(INDENT + "this->mappedServer = UA_Server_new(this->server_config);\n")
    implementation.write(INDENT + "this->baseNodeId = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER);\n")
    implementation.write(INDENT + "//MODEL_INITIALIZER_FUNCTION(this->mappedServer);\n")
    implementation.write(INDENT + self.generatedNamspaceFileName + "(this->mappedServer);\n");
    implementation.write(INDENT + "this->mapSelfToNamespace();\n")
    implementation.write("}\n\n")
    
    self.generateWorkerMethode(implementation, classname)
    
    
  def generateClass(self, implementation, methodList, variableList, objectList):
    classname = toolBox_generator.getNodeCodeName(self.objectNode);
    
    implementation.write(classname + "::" + classname + "(std::string name, UA_NodeId baseNodeId, UA_Server* server) : ua_mapped_class(server, baseNodeId) {\n")
    implementation.write(INDENT + "this->name = name;\n")
    implementation.write(INDENT + "this->mapSelfToNamespace();\n")
    implementation.write("}\n\n")
            
    
  def generateDestructor(self, implementation, classname):
    # Create destructor
    implementation.write(classname+"::~"+classname+"() {\n")
    if (self.isServerClass(classname)) :
      implementation.write(INDENT + "if (this->isRunning()) {\n")
      implementation.write(INDENT + INDENT + "this->doStop();\n")
      implementation.write(INDENT + "}\n")
      implementation.write(INDENT + "UA_Server_delete(this->mappedServer);\n")
    
    implementation.write("}\n\n")
    
    
  def generateVariable(self, implementation, variableList, classname):        
    # Variable Getters/Setters
    for vn in variableList:
      # Reader Proxy
      implementation.write("UA_RDPROXY_" + toolBox_generator.getProxyTypeByUAType(str(vn.dataType().target().browseName())) + "(" + classname + ", get_" + toolBox_generator.getNodeCodeName(vn) + ")\n")
      # Getter
      implementation.write(toolBox_generator.getCPPTypeByUAType(str(vn.dataType().target().browseName())) + " " + classname + "::get_" + toolBox_generator.getNodeCodeName(vn) + "() {\n")
      implementation.write(INDENT +  "return this->" + toolBox_generator.getNodeCodeName(vn) + ";\n")
      implementation.write("}\n\n")
      # Writer Proxy
      implementation.write("UA_WRPROXY_" + toolBox_generator.getProxyTypeByUAType(str(vn.dataType().target().browseName())) + "(" + classname + ", set_" + toolBox_generator.getNodeCodeName(vn) + ")\n")
      # Setter
      implementation.write("void " + classname + "::set_" + toolBox_generator.getNodeCodeName(vn) + "("+ toolBox_generator.getCPPTypeByUAType(str(vn.dataType().target().browseName()))+" value) {\n")
      implementation.write(INDENT +  "this->" + toolBox_generator.getNodeCodeName(vn) + " = value;\n")
      implementation.write("}\n\n")
      
  def generateMethods(self, implementation, methodList, classname):        
    # Variable Getters/Setters
    for mn in methodList:
      # Methde Proxy
      implementation.write("UA_CALLPROXY(" + classname + ", " + toolBox_generator.getNodeCodeName(mn) + ")\n")
      # Method header
      implementation.write("UA_StatusCode " + classname + "::" + toolBox_generator.getNodeCodeName(mn) + "(size_t inputSize, const UA_Variant *input, size_t outputSize, UA_Variant *output) {\n") 
      implementation.write(INDENT + "if (input == nullptr && inputSize > 0 )\n")
      implementation.write(INDENT + INDENT + "return UA_STATUSCODE_BADINVALIDARGUMENT;\n")
      implementation.write(INDENT + "if (inputSize != 0)\n")
      implementation.write(INDENT + INDENT + "return UA_STATUSCODE_BADINVALIDARGUMENT;\n")
      implementation.write(INDENT + "Do crazy shit and start methode... \n")
      implementation.write(INDENT + "this->parentService->service_cmd_execute(\"run\");\n")
      implementation.write(INDENT + "return UA_STATUSCODE_GOOD;\n")
      implementation.write("}\n\n")  
            
        
    ## Methode "mapSelfToNamespace"
  def generateClassMapSelfToNS(self, implementation, classname, variableList, methodList):
    ## Lastly, always add mapSelfToNamespace
    implementation.write("UA_StatusCode " + classname + "::mapSelfToNamespace() {\n")        

    # Create base node
    implementation.write(INDENT + "UA_StatusCode retval = UA_STATUSCODE_GOOD;\n")
    implementation.write(INDENT + "UA_NodeId createdNodeId = UA_NODEID_NULL;\n")
    implementation.write("\n")      
    implementation.write(INDENT + "if (UA_NodeId_equal(&this->baseNodeId, &createdNodeId) == UA_TRUE) { \n")
    implementation.write(INDENT + INDENT + "return 0; // Something went UA_WRING (initializer should have set this!)\n")
    implementation.write(INDENT + "}\n\n")
    implementation.write("\n")
    implementation.write(INDENT + "UA_ObjectAttributes oAttr;\n")
    implementation.write(INDENT + "oAttr.displayName = UA_LOCALIZEDTEXT_ALLOC((char*)\"en_US\", this->name.c_str());\n")
    implementation.write(INDENT + "oAttr.description = UA_LOCALIZEDTEXT_ALLOC((char*)\"en_US\", this->name.c_str());\n")
    implementation.write("\n")      
    implementation.write(INDENT + "UA_INSTATIATIONCALLBACK(icb);\n")
    implementation.write(INDENT + "UA_Server_addObjectNode(this->mappedServer, UA_NODEID_NUMERIC(1,0),\n")
    implementation.write(INDENT + INDENT + INDENT + "UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER), UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES),\n")
    implementation.write(INDENT + INDENT + INDENT + "UA_QUALIFIEDNAME_ALLOC(1, this->name.c_str()), UA_NODEID_NUMERIC(" + str(self.objectNode.id().ns) + ", " + toolBox_generator.getNodeIdDefineString(self.objectNode) + "), oAttr, &icb, &createdNodeId);\n")
    
    
    #Something like this should be printed
    #implementation.write(INDENT + "UA_NodeId_copy(&createdNodeId, \"FIXME\");\n")
    # really needed?
    implementation.write(INDENT + "UA_NodeId_copy(&createdNodeId, &this->rootNodeId);\n\n")
    # Or like this...
    # UA_NodeId_copy(nodePairList_getTargetIdBySourceId(this->ownedNodes, UA_NODEID_NUMERIC(IMMODULE_NSID, MODULE_TYPE_SIGNALIST_ID)), &this->SignalListId);
    
    # Map function calls
    implementation.write(INDENT + "UA_FunctionCall_Map mapThis;\n")
    for mn in methodList:
      implementation.write(INDENT + "mapThis.push_back((UA_FunctionCall_Map_Element) {.typeTemplateId = UA_NODEID_NUMERIC(\"FIXME_IMMODULE_NSID\", \"FIXME_COMMANDSET_61512_" + toolBox_generator.getNodeCodeName(mn) + "\"), .lookupTable = UA_CALLPROXY_TABLE(" + classname + ", " + toolBox_generator.getNodeCodeName(mn) + "), .callback = UA_CALLPROXY_NAME(" + classname + ", " + toolBox_generator.getNodeCodeName(mn) + ") }); \n")
  
    
    implementation.write(INDENT + "this->ua_mapFunctions(this, &mapThis, createdNodeId);\n\n")
    # Map DataSources
    implementation.write(INDENT + "UA_DataSource_Map mapDs;\n")
    # create for every var setter/getter proxys
    
    for vn in variableList:
      implementation.write(INDENT + "mapDs.push_back((UA_DataSource_Map_Element) { .typeTemplateId = UA_NODEID_NUMERIC(" + str(vn.id().ns) + ", " + str(vn.id().i) + "), .read=UA_RDPROXY_NAME(" + classname + ", get_" + toolBox_generator.getNodeCodeName(vn) + "), .write=UA_WRPROXY_NAME(" + classname + ", set_" + toolBox_generator.getNodeCodeName(vn) + ")});\n")
    
    implementation.write(INDENT + "ua_callProxy_mapDataSources(this->mappedServer, this->ownedNodes, &mapDs, (void *) this);\n")
    
    implementation.write(INDENT + "return UA_STATUSCODE_GOOD;\n")
    implementation.write("}\n\n")
  
    
  def generateWorkerMethode(self, implementation, classname):
    implementation.write("void " + classname + "::workerThread_setup() {\n")
    implementation.write(INDENT + "if (this->mappedServer == nullptr) {\n")
    implementation.write(INDENT + INDENT + "return;\n")
    implementation.write(INDENT + "}\n\n")
    implementation.write(INDENT + "#ifdef DISABLE_THREADING\n")
    implementation.write(INDENT + INDENT + "UA_Server_run_startup(this->mappedServer);\n")
    implementation.write(INDENT + "#else\n")
    implementation.write(INDENT + "this->thread_run = true;\n")
    implementation.write(INDENT + "this->runUAServer = UA_TRUE;\n")
    implementation.write(INDENT + "this->serverThread = new std::thread(UA_Server_run, this->mappedServer, &runUAServer);\n")
    implementation.write(INDENT + "#endif\n")
    implementation.write("}\n\n")
    
    implementation.write("void " + classname + "::workerThread_iterate() {\n")
    implementation.write(INDENT + "if (this->mappedServer == nullptr) {\n")
    implementation.write(INDENT + INDENT + "return;\n")
    implementation.write(INDENT + "}\n\n")
    implementation.write(INDENT + "if (! this->isRunning()) {\n")
    implementation.write(INDENT + INDENT + "this->runUAServer = UA_FALSE;\n")
    implementation.write(INDENT + "}\n")
    implementation.write(INDENT + "#ifdef DISABLE_THREADING\n")
    implementation.write(INDENT + "uint16_t timeout = UA_Server_run_iterate(this->mappedServer, UA_TRUE);\n")
    implementation.write(INDENT + "#endif\n")
    implementation.write(INDENT + "this->reschedule(0, TIMETICK_INTERVAL * 1000000);\n")
  
    implementation.write("}\n\n")
    
    implementation.write("void " + classname + "::workerThread_cleanup() {\n")
    implementation.write(INDENT + "if (this->mappedServer == nullptr) {\n")
    implementation.write(INDENT + INDENT + "return;\n")
    implementation.write(INDENT + "}\n\n")
    implementation.write(INDENT + "this->runUAServer == UA_FALSE;\n")
    implementation.write(INDENT + "#ifndef DISABLE_THREADING\n")
    implementation.write(INDENT + "if (this->serverThread->joinable()) {\n")
    implementation.write(INDENT + INDENT + "this->serverThread->join();\n")
    implementation.write(INDENT + "}\n")
    implementation.write(INDENT + "delete this->serverThread;\n")
    implementation.write(INDENT + "#endif\n")
    implementation.write(INDENT + "this->serverThread = nullptr;\n")
    implementation.write("}\n\n")
