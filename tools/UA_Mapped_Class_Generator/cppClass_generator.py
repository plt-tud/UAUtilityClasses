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
import os
from headerfile_generator import headerfile_generator
from cppfile_generator import cppfile_generator
import toolBox_generator

logger = logging.getLogger(__name__)

__unique_item_id = 0

defined_typealiases = []

INDENT="    "
  
class serverHostClassConfig():
  name = ""
  
  def __init__(self, name):
    self.name = name

class clientHostClassConfig():
  name = ""
  
  def __init__(self, name):
    self.name = name
    
class cppClass_generator():
  namespace = None # OPCUA namespace to be printed
  serverHostList = None
  generatedNamspaceFileName = None
  
    
  def __init__(self, namespace, serverHostList, generatedNamspaceFileName):
    self.namespace = namespace
    self.serverHostList = serverHostList
    self.generatedNamspaceFileName = generatedNamspaceFileName
    self.ignoredNodes = []
    
    self.namespace.linkOpenPointers
  
   
  def addIgnoredNodes(self, ignoredNodesList):
    self.ignoredNodes += ignoredNodesList    
  
  
  def getMembersOfType(self, objectNode):
    variables=[]
    objects=[]
    methods=[]
    
    # Return a Triple of (varibales, objects, methods) for a given type definition
    for r in objectNode.getReferences():
      if r.isForward() and r.target() != None:
        # FIXME: We are only checking hasProperty & hasComponent, but we should be checking any derived refType as well...
        if((r.target().nodeClass() == NODE_CLASS_VARIABLE or r.target().nodeClass() == NODE_CLASS_VARIABLETYPE)) and \
        (r.referenceType().id().ns == 0 and r.referenceType().id().i == 46 or 
         r.referenceType().id().ns == 0 and r.referenceType().id().i == 47 ):
          vn = r.target()
          if (vn.dataType() != None):
            print("+-Variable" + toolBox_generator.getNodeCodeName(r.target()))
            # Only create encodable types!
            if not "NonMappableType" in toolBox_generator.getCPPTypeByUAType(str(vn.dataType().target().browseName())):
              variables.append(vn)
            if not r.target() in self.ignoredNodes:
              t = self.getMembersOfType(r.target())
              variables += t[0]
              objects += t[1]
              methods += t[2]
        # FIXME: We are only checking hasProperty & hasComponent, but we should be checking any derived refType as well...
        if (r.target().nodeClass() == NODE_CLASS_OBJECT)  and \
        (r.referenceType().id().ns == 0 and r.referenceType().id().i == 46 or 
         r.referenceType().id().ns == 0 and r.referenceType().id().i == 47 ):
          print("+-Object" + toolBox_generator.getNodeCodeName(r.target()))
          if not r.target() in self.ignoredNodes:
            print("-- contains -->" + toolBox_generator.getNodeCodeName(r.target()))
            t = self.getMembersOfType(r.target())
            variables += t[0]
            objects += t[1]
            methods += t[2]
          objects.append(r.target())
        if(r.target().nodeClass() == NODE_CLASS_METHOD)  and \
        (r.referenceType().id().ns == 0 and r.referenceType().id().i == 46 or 
         r.referenceType().id().ns == 0 and r.referenceType().id().i == 47 ):
          print("+-Method" + toolBox_generator.getNodeCodeName(r.target()))
          methods.append(r.target())
      ## If this type inherits attributes from its parent, we need to add these to this objects list of variables/objects/methods
      # FIXME: We are only checking hasSubtype, but we should be checking any derived refType as well...
      if not r.isForward() and r.target() != None and r.referenceType().id().ns == 0 and r.referenceType().id().i == 45:
        if not r.target() in self.ignoredNodes:
          print("-- supertype -->" + toolBox_generator.getNodeCodeName(r.target()))
          t = self.getMembersOfType(r.target())
          variables += t[0]
          objects += t[1]
          methods += t[2]
    return (variables,objects, methods)
  
  def generateAll(self, outputPath):
    for objectNode in self.namespace.nodes:
      # TODO: clientReflection classes
      if objectNode.nodeClass() == NODE_CLASS_OBJECTTYPE and not objectNode in self.ignoredNodes:
        classname = toolBox_generator.getNodeCodeName(objectNode)
        print(classname+".cpp, " + classname+".hpp")
        cppPath = outputPath + "/serverReflection/"
        hppPath = cppPath
        if not os.path.exists(cppPath):
          os.makedirs(cppPath)
        if not os.path.exists(hppPath):
          os.makedirs(hppPath)    
          
        logger.debug("Generating ObjectType " + str(objectNode.id()) + " " + classname)
        methods=[]
        variables=[]
        objects=[]
        print("Discovering generatable subnodes")
        (variables,objects, methods) = self.getMembersOfType(objectNode)
        
        ## create all files    
        classname = toolBox_generator.getNodeCodeName(objectNode);
        config = None
        for serverConfig in self.serverHostList:
          if serverConfig.name == classname:
            config = serverConfig
        cppfile = cppfile_generator(self.generatedNamspaceFileName, objectNode, config)
        hppfile = headerfile_generator(self.namespace, objectNode, config)

        '''
        ' Check if file still exist.
        ' If there is a "@generated" string in the first lines of code, the file can be reprinted
        ' if not, the file was changed by an human or somethink like a human... hence we dont touch it with the generator
        '''
        if os.path.isfile(cppPath + classname + ".cpp"):
          existingCodeFile = open(cppPath + classname + ".cpp")
          for line in existingCodeFile:
            if(string.find(line.rstrip(), "@generated") != -1) :
              codefile = open(cppPath + classname + ".cpp", r"w+")
              cppfile.generateImplementationFile(codefile, methods, variables, objects)
              codefile.close()  
              break;
            else:
              logger.warn(cppPath + classname + ".cpp has been modified (is missing the @generated comment). Skipping code generation for this class")
          existingCodeFile.close()
          
        else:
          codefile = open(cppPath + classname + ".cpp", r"w+")
          cppfile.generateImplementationFile(codefile, methods, variables, objects)
          codefile.close()  
          
        if os.path.isfile(hppPath + classname + ".hpp"):
          existingCodeFile = open(hppPath + classname + ".hpp")
          for line in existingCodeFile:
            if(string.find(line.rstrip(), "@generated") != -1) :
              headerfile = open(hppPath + classname + ".hpp", r"w+")
              hppfile.generateHeaderFile(headerfile, methods, variables, objects) 
              headerfile.close()  
              break;
            else:
              logger.warn(cppPath + classname + ".hpp has been modified (is missing the @generated comment). Skipping code generation for this class")
          existingCodeFile.close()
        else:
          headerfile = open(hppPath + classname + ".hpp", r"w+")
          hppfile.generateHeaderFile(headerfile, methods, variables, objects)   
          headerfile.close()
