/*
 * Copyright (c) 2016 <copyright holder> <email>
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 */

#ifndef UA_REMOTEINSTANCE_MAP_H
#define UA_REMOTEINSTANCE_MAP_H

extern "C" {
  #include "open62541/open62541.h"
}

#include <string>
#include <list>
#include "ipc_managed_object.h"

class ua_remoteNode
{
public:
    UA_NodeId    nodeId;
    UA_NodeClass nodeClass;
    std::string  browseName;
    std::string  displayName;
    std::string  description;
    UA_NodeId    typeDefinition;
    
    std::list<ua_remoteNode *> variables;
    std::list<ua_remoteNode *> objects;
    std::list<ua_remoteNode *> methods;
    
    ua_remoteNode() {
        UA_NodeId_init(&this->nodeId);
        UA_NodeId_init(&this->typeDefinition);
        this->nodeClass = UA_NODECLASS_UNSPECIFIED;
    };
    ~ua_remoteNode() {
        UA_NodeId_deleteMembers(&this->nodeId);
        UA_NodeId_deleteMembers(&this->typeDefinition);
    };
    
    ua_remoteNode *getVariableByBrowseName(std::string name);
};



class ua_remoteInstance_map
{
private:
    std::string targetUri;
    UA_Client *client;
public:
    ua_remoteNode rootNode;
    
    ua_remoteInstance_map(std::string targetUri); // Create new/own client 
    ua_remoteInstance_map(std::string targetUri, UA_Client *client);     // Reuse existing client
    ~ua_remoteInstance_map();
    
    int32_t mapRemoteSystemInstances();
    int32_t mapRemoteSystemInstances(uint32_t mappingDepthLimit);
    ua_remoteNode *findNodeByName(ua_remoteNode *node, std::string name);
    void printNamespace();
    void printNamespace(ua_remoteNode *rootNode, uint32_t depth);
};

class ua_iterator_handle
{
public:
    UA_Client             *client;
    ua_remoteNode         *parent;
    ua_remoteInstance_map *caller;
    uint32_t               iterationDepth;
    int32_t                depthLimit;
    ua_iterator_handle(UA_Client *client, ua_remoteNode *parentNode, ua_remoteInstance_map *caller) : client(client), parent(parentNode), caller(caller), depthLimit(-1), iterationDepth(0) {};
};
#endif // UA_REMOTEINSTANCE_MAP_H
