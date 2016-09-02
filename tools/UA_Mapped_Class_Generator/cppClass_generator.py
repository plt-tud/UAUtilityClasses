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
    
  def generateObject(self, objectNode, targetfiles):
    (header, implementation) = targetfiles
    classname = toolBox_generator.getNodeCodeName(objectNode)
    logger.debug("Generating ObjectType " + str(objectNode.id()) + " " + classname)
    print("Generating ObjectType " + str(objectNode.id()) + " " + classname)
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
    # 
    cppfile = cppfile_generator(self.generatedNamspaceFileName, self.serverHostList)
    headerfile = headerfile_generator(self.namespace, self.serverHostList)
    
    cppfile.generateImplementationFile(implementation, objectNode, methods, variables, objects)
    headerfile.generateHeaderFile(header, objectNode, methods, variables, objects)    
    
  def generateAll(self, outputPath):
    for n in self.namespace.nodes:
      if n.nodeClass() == NODE_CLASS_OBJECTTYPE and not n in self.ignoredNodes:
        name = toolBox_generator.getNodeCodeName(n)
        print(name+".cpp, "+name+".hpp")
        cppPath = outputPath + "/cpp/"
        hppPath = outputPath + "/hpp/"
        if not os.path.exists(cppPath):
          os.makedirs(cppPath)
        if not os.path.exists(hppPath):
          os.makedirs(hppPath)    
          
        #if os.path.isfile(cppPath + name + ".cpp"):
        #  print("Datei " + cppPath + name + ".cpp existiert bereits")
        codefile = open(cppPath + name + ".cpp", r"w+")
          
        #if os.path.isfile(hppPath + name + ".hpp"):
        #  print("Datei " + hppPath + name + ".cpp existiert bereits")
        headerfile = open(hppPath + name + ".hpp", r"w+")
          
        self.generateObject(n, (headerfile, codefile))
        headerfile.close()
        codefile.close()  
