## UA Mapped Class Generator

(Quick and dirty...)

Python Generator that creates UA mapped class prototypes derived from OPC UA XML Descriptions.

How to use:

1. For general purpose you have to define server classes in a xml file. This kind of class will be able to init a OPCUA Server.
	a) Example:
	```xml
      <?xml version="1.0" encoding="UTF-8"?>
      <classannotations>
        <serverClass classname="mtcaModule">
          <!-- Future concept: Allow configuration of generation parameters like so: 
          -->
          <publishingIntervalLimitMin>10.0</publishingIntervalLimitMin>
          <publishingIntervalLimitMax>3600.0 * 1000.0</publishingIntervalLimitMax>
          <samplingIntervalLimitMin>10.0</samplingIntervalLimitMin>
          <samplingIntervalLimitMax>3600.0 * 1000.0</samplingIntervalLimitMax>
          <!-- But right now only the classname is evaluated -->
        </serverClass>
        <serverClass classname="ModuleType" />
        <clientClass classname="magicClientXY" />
      </classannotations>
	```
	The example define two server classes "mtcaModule" and "ModuleType" as well as one client class.

2. Lets start

| Command | Description |
|--- | --- |
|`python ./generate_cppClasses.py` | `Main file` |
| `-i ../../model/NodeID_Blacklist_FullNS0.txt` | | 
| `-b ../../model/NodeID_Blacklist.txt` | |  
| `../../model/Opc.Ua.NodeSet2.xml` |  |
| `../../model/moduleim.xml` |  |
| `../../build/src_generated/` | `Output directory` |
| `-a ../../model/serverList.xml` | `path to the server class definition` |
| `-n mtpmodule_namespaceinit_generated` | `file name of the output from namespaceCompiler` |

Complet command:
`python ./generate_cppClasses.p y -i ../../model/NodeID_Blacklist_FullNS0.txt -b ../../model/NodeID_Blacklist.txt ../../model/Opc.Ua.NodeSet2.xml ../../model/moduleim.xml ../../build/src_generated/ -a ../../model/serverList.xml -n mtpmodule_namespaceinit_generated`


