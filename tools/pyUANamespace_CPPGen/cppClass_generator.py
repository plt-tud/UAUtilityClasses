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
from ua_constants import *
import string
from ua_namespace import opcua_namespace
import re

logger = logging.getLogger(__name__)

__unique_item_id = 0

defined_typealiases = []

INDENT="    "

def getNodeCodeName(n):
    name = n.browseName()
    name = re.sub("^.+:","",name)
    name = re.sub(" ","",name)
    return name

def getCPPTypeByUAType(ua_typestring):
    if ua_typestring.lower() == "string":
        return "std::string"
    elif ua_typestring.lower() in ["double", "float"]:
        return ua_typestring.lower()
    elif ua_typestring.lower() in ["int16", "uint16","int32", "uint32","int64", "uint64"]:
        return ua_typestring.lower() + "_t"
    # FIXME: Lots of missing types here...
    else:
        return "NonMappableType"
    
class cppClass_generator():
    namespace = None # OPCUA namespace to be printed
    
    def __init__(self, namespace ):
        self.namespace = namespace
        self.ignoredNodes = []
   
    def addIgnoredNodes(self, ignoredNodesList):
        self.ignoredNodes += ignoredNodesList
    
    def generateImplementation(self, implementation, objectNode, methodList, variableList, objectList):
        classname = getNodeCodeName(objectNode);
        implementation.write("#include \"" + classname + ".hpp\"\n")
        implementation.write("#include \"ua_proxies.h\"\n\n")
        implementation.write("#include \"ua_proxies_callback.h\"\n")
        implementation.write("#include \"ua_proxies_typeconversion.h\"\n")
        implementation.write("\n\n")
        
        ## Create constructor
        implementation.write(classname+"::"+classname+"(UA_NodeId baseNodeId, UA_Server* server) : ua_mapped_class(server, baseNodeId) {\n")
        implementation.write("}\n\n")
        
        # Create destructor
        implementation.write(classname+"::~"+classname+"() {\n")
        implementation.write("}\n\n")
        
        # Variable Getters/Setters
        for vn in variableList:
            implementation.write(getCPPTypeByUAType(str(vn.dataType().target().browseName())) + " get_" + getNodeCodeName(vn) + "() {\n")
            implementation.write(INDENT +  "return this->" + getNodeCodeName(vn) + ";")
            implementation.write("}\n\n")
            implementation.write("void set_" + getNodeCodeName(vn) + "("+ getCPPTypeByUAType(str(vn.dataType().target().browseName()))+" value) {\n")
            implementation.write(INDENT +  "this->" + getNodeCodeName(vn) + " = value;")
            implementation.write("}\n\n")
            
        ## Lastly, always add mapSelfToNamespace
        implementation.write("UA_StatusCode "+classname+"::mapSelfToNamespace() {\n")      
        
        # Create base node
        implementation.write(INDENT + "UA_StatusCode retval = UA_STATUSCODE_GOOD;\n")
        implementation.write(INDENT + "UA_NodeId createdNodeId = UA_NODEID_NULL;\n")
        implementation.write("\n")      
        implementation.write(INDENT + "if (UA_NodeId_equal(&this->baseNodeId, &createdNodeId) == UA_TRUE) \n")
        implementation.write(INDENT + "return 0; // Something went UA_WRING (initializer should have set this!)\n")
        implementation.write("\n")
        implementation.write(INDENT + "UA_ObjectAttributes oAttr;\n")
        implementation.write(INDENT + "oAttr.displayName = UA_LOCALIZEDTEXT(\"en_US\", \"FIXME\");\n")
        implementation.write(INDENT + "oAttr.description = UA_LOCALIZEDTEXT(\"en_US\", \"FIXME\");\n")
        implementation.write("\n")      
        implementation.write(INDENT + "UA_INSTATIATIONCALLBACK(icb);\n")
        implementation.write(INDENT + "UA_Server_addObjectNode(this->mappedServer, UA_NODEID_NUMERIC(1,0),\n")
        implementation.write(INDENT + "                        UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER), UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES),\n")
        implementation.write(INDENT + "                        UA_QUALIFIEDNAME(1, \"BenchmarkSim\"), UA_NODEID_NUMERIC(2, \"FIXME\"), oAttr, &icb, &createdNodeId);\n")
        implementation.write(INDENT + "UA_NodeId_copy(&createdNodeId, \"FIXME\");\n")
        
        # Map function calls
        implementation.write(INDENT + "UA_FunctionCall_Map mapThis;\n")
        
        # Map DataSources
        implementation.write(INDENT + "UA_DataSource_Map mapDs;\n")
        implementation.write("}\n\n")
    
    def generateHeader(self, header, objectNode, methodList, variableList, objectList):
        classname = getNodeCodeName(objectNode);
        
        # Print Header Guards
        header.write("#ifdef HAVE_" + classname.capitalize() + "_H\n")
        header.write("#define HAVE_" + classname.capitalize() + "_H\n\n")
        
        header.write("#include \"ua_mapped_class.h\"\n\n")
        header.write("class " + classname + " : ua_mapped_class {\n")
        header.write("private:\n")
        for vn in variableList:
            header.write(INDENT + getCPPTypeByUAType(str(vn.dataType().target().browseName())) + " " + getNodeCodeName(vn) + ";\n")
        header.write("\n")
        for on in objectList:
            header.write(INDENT + "UA_NodeId " + getNodeCodeName(on) + ";\n")
        header.write("\n")
        header.write(INDENT + "UA_StatusCode mapSelfToNamespace();\n")
        header.write("\n")
        header.write("protected:\n")
        header.write("\n")
        header.write("public:\n")
        header.write(INDENT +classname+"(UA_NodeId baseNodeId, UA_Server* server);\n")
        header.write(INDENT + "~"+classname+"();\n")
        header.write("\n")
        header.write(INDENT + "// Getter and Setter functions \n")
        for vn in variableList:
            header.write(INDENT + getCPPTypeByUAType(str(vn.dataType().target().browseName())) + " get_" + getNodeCodeName(vn) + "();\n")
            header.write(INDENT + "void set_" + getNodeCodeName(vn) + "("+ getCPPTypeByUAType(str(vn.dataType().target().browseName()))+" value);\n")
            header.write("\n")
        header.write("\n")
        header.write("}\n")
        
        header.write("\n#endif // Header guard\n")
    
    def generateObject(self, objectNode, targetfiles):
        (header, implementation) = targetfiles
        classname = getNodeCodeName(objectNode)
        logger.debug("Generating ObjectType " + str(objectNode.id()) + " " + classname)
        
        methods=[]
        variables=[]
        objects=[]
        
        for r in objectNode.getReferences():
            if r.isForward() and r.target() != None:
                if((r.target().nodeClass() == NODE_CLASS_VARIABLE or  r.target().nodeClass() == NODE_CLASS_VARIABLETYPE)):
                    vn = r.target()
                    if (vn.dataType() != None):
                        variables.append(vn)
                if (r.target().nodeClass() == NODE_CLASS_OBJECT):
                    print("+-Object" + getNodeCodeName(r.target()))
                    objects.append(r.target())
                if(r.target().nodeClass() == NODE_CLASS_METHOD):
                    print("+-Method" + getNodeCodeName(r.target()))
                    methods.append(r.target())
                
        self.generateHeader(header, objectNode, methods, variables, objects)
        self.generateImplementation(implementation, objectNode, methods, variables, objects)
    
    def generateAll(self):
        for n in self.namespace.nodes:
            if n.nodeClass() == NODE_CLASS_OBJECTTYPE and not n in self.ignoredNodes:
                name = getNodeCodeName(n)
                print(name+".cpp, "+name+".hpp")
                codefile = open(name+".cpp", r"w+")
                headerfile = open(name+".hpp", r"w+")
                self.generateObject(n, (headerfile, codefile))
                headerfile.close()
                codefile.close()
        