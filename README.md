# UAUtilityClasses
OPC UA Mapping and utility classes for C++

This project serves as a development base for classes and tools that are frequently reused in a variety of projects. The source code is united in this repository for better maintainability.

Subprojects include:

## UA Mapped Classes

A set of classes facilitating the UA based reflection.

## UA Mapped Class Generator

Python Generator that creates UA mapped class prototypes derived from OPC UA XML Descriptions.

## IPC Managed Classes & Manager

A framework for creating parallelizable objects.

## UA RemoteMap

A Server scanner that assists in searching and mapping remote nodes.

## UDP Beacon

A UDP Broadcast Beacon class that assists search/discovery of servers in a subnet.

# Writeback Policy

Different projects using these utility classes are likely to generate both new features and bugfixes. For consistency, the following applies:

  * Changes introduced by projects shall always be written into a new branch dedicated to that project. 
  * Merging of features into the master branch will occur once a conflict-free and non project specific port has been verified.