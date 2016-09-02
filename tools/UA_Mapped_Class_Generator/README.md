## UA Mapped Class Generator

(Quick and dirty...)

Python Generator that creates UA mapped class prototypes derived from OPC UA XML Descriptions.

How to use:

1. For general purpose you have to define server classes in a xml file. This kind of class will be able to init a OPCUA Server.
	a) Example:
	<?xml version="1.0" encoding="UTF-8"?>
	<serverClass>
		<name>mtcaModule</name>
		<name>ModuleType</name>
	</serverClass>
	
	The example define two server classes "mtcaModule" and "ModuleType".

2. Lets start
	python ./generate_cppClasses.py 			-> Main file
	-i ../../model/NodeID_Blacklist_FullNS0.txt 
	-b ../../model/NodeID_Blacklist.txt 
	../../model/Opc.Ua.NodeSet2.xml 
	../../model/moduleim.xml 
	../../build/src_generated/ 				-> Output directory
	-l ../../model/serverList.xml 				-> path to the server class definition
	-ns mtpmodule_namespaceinit_generated			-> file name of the output from namespaceCompiler



