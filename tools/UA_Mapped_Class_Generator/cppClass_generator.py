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
        
        for r in objectNode.getReferences():
          if r.isForward() and r.target() != None:
            if((r.target().nodeClass() == NODE_CLASS_VARIABLE or  r.target().nodeClass() == NODE_CLASS_VARIABLETYPE)):
              vn = r.target()
              if (vn.dataType() != None):
                variables.append(vn)
            if (r.target().nodeClass() == NODE_CLASS_OBJECT):
              print("+-Object" + toolBox_generator.getNodeCodeName(r.target()))
              objects.append(r.target())
            if(r.target().nodeClass() == NODE_CLASS_METHOD):
              print("+-Method" + toolBox_generator.getNodeCodeName(r.target()))
              methods.append(r.target())
        
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
          print("Datei " + cppPath + classname + ".cpp existiert bereits")
          existingCodeFile = open(cppPath + classname + ".cpp")
          for line in existingCodeFile:
            if(string.find(line.rstrip(), "@generated") != -1) :
              codefile = open(cppPath + classname + ".cpp", r"w+")
              
              cppfile.generateImplementationFile(codefile, methods, variables, objects)
              codefile.close()  
              break;
          existingCodeFile.close()
          
        else:
          codefile = open(cppPath + classname + ".cpp", r"w+")
          cppfile.generateImplementationFile(codefile, methods, variables, objects)
          codefile.close()  
          
        if os.path.isfile(hppPath + classname + ".hpp"):
          print("Datei " + hppPath + classname + ".hpp existiert bereits")
          existingCodeFile = open(hppPath + classname + ".hpp")
          for line in existingCodeFile:
            if(string.find(line.rstrip(), "@generated") != -1) :
              headerfile = open(hppPath + classname + ".hpp", r"w+")
              hppfile.generateHeaderFile(headerfile, methods, variables, objects) 
              headerfile.close()  
              break;
          existingCodeFile.close()
        else:
          headerfile = open(hppPath + classname + ".hpp", r"w+")
          hppfile.generateHeaderFile(headerfile, methods, variables, objects)   
          headerfile.close()
