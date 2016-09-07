/*
 * Copyright (c) 2016 Chris Iatrou <Chris_Paul.Iatrou@tu-dresden.de>
 * Chair for Process Systems Engineering
 * Technical University of Dresden
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

#include "ua_remoteinstance_map.h"


extern "C" {
  #include <unistd.h>
  #include "open62541.h"
}

#include "logger.h"
#include "ua_proxies_typeconversion.h"

ua_remoteInstance_map::ua_remoteInstance_map(std::string targetUri) 
{
    this->targetUri = targetUri;
    this->rootNode.nodeClass = UA_NODECLASS_OBJECT;
    this->rootNode.nodeId = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER);
    this->rootNode.typeDefinition = UA_NODEID_NUMERIC(0, UA_NS0ID_FOLDERTYPE);
    this->rootNode.browseName  = "Objects";
    this->rootNode.displayName = "Objects";
    this->rootNode.description = "Objects";
    this->client    = UA_Client_new(UA_ClientConfig_standard);
}

ua_remoteInstance_map::ua_remoteInstance_map(std::string targetUri, UA_Client *client) 
{
    this->targetUri = targetUri;
    this->rootNode.nodeClass = UA_NODECLASS_OBJECT;
    this->rootNode.nodeId = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER);
    this->rootNode.typeDefinition = UA_NODEID_NUMERIC(0, UA_NS0ID_FOLDERTYPE);
    this->rootNode.browseName  = "Root";
    this->rootNode.displayName = "Root";
    this->rootNode.description = "Root";
    this->client    = client;
}

ua_remoteInstance_map::~ua_remoteInstance_map()
{
    UA_Client_disconnect(this->client);
    UA_Client_reset(this->client);
    UA_Client_delete(this->client);
}

static UA_StatusCode nodeIter(UA_NodeId childId, UA_Boolean isInverse, UA_NodeId referenceTypeId, void *handle) {
    ua_iterator_handle *hhandle = static_cast<ua_iterator_handle*>(handle);
    
    /* Only follow forwad refs */
    if(isInverse == UA_TRUE)
        return UA_STATUSCODE_GOOD;
    
    /* Make sure the reference type for the child is of interest to us */
    UA_NodeId matchIds[4];
    matchIds[0] = UA_NODEID_NUMERIC(0, UA_NS0ID_HASCOMPONENT);
    matchIds[1] = UA_NODEID_NUMERIC(0, UA_NS0ID_HASPROPERTY);
    matchIds[1] = UA_NODEID_NUMERIC(0, UA_NS0ID_ORGANIZES);
    matchIds[2] = UA_NODEID_NUMERIC(0, UA_NS0ID_HASTYPEDEFINITION);
    bool match = false;
    for (int i =0; i < sizeof(matchIds); i++) {
        if (UA_NodeId_equal(&matchIds[i], &referenceTypeId) == UA_TRUE) {
            match = true;
            break;
        }
    }
    if(!match)
        return UA_STATUSCODE_GOOD;
    
    /* Forward referenced child /w references of interest, but only its ID is known
     * In 90% of cases, we want to know a bit more about the child... 
     */
    UA_ReadRequest *rReq = UA_ReadRequest_new();
    
    rReq->nodesToReadSize = 3;
    rReq->nodesToRead = (UA_ReadValueId *) malloc(sizeof(UA_ReadValueId) * rReq->nodesToReadSize );
    for(int i=0; i<rReq->nodesToReadSize; i++) {
        UA_ReadValueId_init(&rReq->nodesToRead[i]);
        UA_NodeId_copy(&childId, &rReq->nodesToRead[i].nodeId);
    }
    
    rReq->nodesToRead[0].attributeId = UA_ATTRIBUTEID_BROWSENAME;
    rReq->nodesToRead[1].attributeId = UA_ATTRIBUTEID_DISPLAYNAME;
    rReq->nodesToRead[2].attributeId = UA_ATTRIBUTEID_NODECLASS;

    UA_ReadResponse rRes = UA_Client_Service_read(hhandle->client, *rReq);
    if(rRes.results->status != UA_STATUSCODE_GOOD or rRes.resultsSize == 0) {
        UA_ReadResponse_deleteMembers(&rRes);
        UA_ReadRequest_delete(rReq);
        return UA_STATUSCODE_GOOD;
    }
    
    ua_remoteNode *thisChild = new ua_remoteNode();
    UA_NodeId_copy(&childId, &thisChild->nodeId);
    
    if (rRes.responseHeader.serviceResult == UA_STATUSCODE_GOOD) {
        if (rRes.resultsSize > 0 && rRes.results[0].value.data != nullptr) {
            UA_QualifiedName *bName = (UA_QualifiedName *) rRes.results[0].value.data;
            UASTRING_TO_CPPSTRING(bName->name, thisChild->browseName);
        }
        if (rRes.resultsSize > 1 && rRes.results[1].value.data != nullptr) {
            UA_LocalizedText *dName = (UA_LocalizedText *) rRes.results[1].value.data;
            UASTRING_TO_CPPSTRING(dName->text, thisChild->displayName);
        }
        if (rRes.resultsSize > 2 && rRes.results[2].value.data != nullptr) {
            thisChild->nodeClass = *((UA_NodeClass *) rRes.results[2].value.data);
        }
    }
    
    // Store child
    switch (thisChild->nodeClass) {
        case UA_NODECLASS_OBJECT:
            hhandle->parent->objects.push_back(thisChild);
        break;
        case UA_NODECLASS_VARIABLE:
            hhandle->parent->variables.push_back(thisChild);
        break;
        case UA_NODECLASS_METHOD:
            hhandle->parent->methods.push_back(thisChild);
        break;
        default:
            if (thisChild->nodeClass == UA_NODECLASS_DATATYPE ||
                thisChild->nodeClass == UA_NODECLASS_OBJECTTYPE ||
                thisChild->nodeClass == UA_NODECLASS_REFERENCETYPE ||
                thisChild->nodeClass == UA_NODECLASS_VARIABLETYPE) 
            {
                if(UA_NodeId_equal(&hhandle->parent->typeDefinition , &UA_NODEID_NULL) == UA_STATUSCODE_GOOD)
                    UA_NodeId_copy(&thisChild->nodeId, &hhandle->parent->typeDefinition);
            }
            delete thisChild;
            thisChild = nullptr;
    }
    
    UA_ReadResponse_deleteMembers(&rRes);
    UA_ReadRequest_delete(rReq);
    
    if (thisChild != nullptr) {
        /* If max depth is reached, just abort */
        if (hhandle->depthLimit > 0 && hhandle->iterationDepth >= hhandle->depthLimit) {
           return UA_STATUSCODE_GOOD;
        }
        /* Modify handle, then recurse */
        ua_remoteNode *oldParent = hhandle->parent;
        hhandle->parent = thisChild;
        hhandle->iterationDepth++;
        UA_Client_forEachChildNodeCall(hhandle->client, childId, nodeIter, (void *) hhandle);
        hhandle->iterationDepth--;
        hhandle->parent = oldParent;
    }
    
    return UA_STATUSCODE_GOOD;
}

int32_t ua_remoteInstance_map::mapRemoteSystemInstances(uint32_t mappingDepthLimit) {
  UA_ClientState orgClientState;
  if ((orgClientState = UA_Client_getState(this->client)) != UA_CLIENTSTATE_CONNECTED) {
    LOG_DEBUG("Connecting client for mapping purposes...");
    if (UA_Client_connect(this->client, this->targetUri.c_str()) != UA_STATUSCODE_GOOD) {
      return -1;
    }
  }
  
  UA_NodeId nullId = UA_NODEID_NUMERIC(0, UA_NS0ID_OBJECTSFOLDER);
  ua_iterator_handle iterhandle(this->client, &this->rootNode, this);
  UA_Client_forEachChildNodeCall(this->client, nullId, nodeIter, (void *) &iterhandle);
  
  if (orgClientState != UA_CLIENTSTATE_CONNECTED) {
    LOG_DEBUG("Disconnecting client from mapping purposes...");
    UA_Client_disconnect(this->client);
  }
  return 0;
}

int32_t ua_remoteInstance_map::mapRemoteSystemInstances()
{
    this->mapRemoteSystemInstances(0);
}

ua_remoteNode * ua_remoteInstance_map::findNodeByName(ua_remoteNode *node, std::string name) {
    ua_remoteNode *search;
    if (node->browseName == name)
        return node;
    
    for (auto n : node->objects) {
        search = this->findNodeByName(n, name);
        if (search != nullptr)
            return search;
    }
    for (auto n : node->variables) {
        search = this->findNodeByName(n, name);
        if (search != nullptr)
            return search;
    }
    for (auto n : node->methods) {
        search = this->findNodeByName(n, name);
        if (search != nullptr)
            return search;
    }
    return nullptr;
}

void ua_remoteInstance_map::printNamespace(ua_remoteNode *node, uint32_t depth) 
{
    std::string indent = "";
    for (int i = 0; i<depth; i++)
        indent += "  ";
    std::string t;
    if(node->nodeClass == UA_NODECLASS_OBJECT)
        t="[O]";
    else if(node->nodeClass == UA_NODECLASS_VARIABLE)
        t="[V]";
    else if(node->nodeClass == UA_NODECLASS_METHOD)
        t="[M]";
    else
        t="[?]";
    
    cout << indent << "+ " + t + " " << node->browseName << endl ;
    for (auto n : node->objects) {
        this->printNamespace(n, depth+1);
    }
    for (auto n : node->variables) {
        this->printNamespace(n, depth+1);
    }
    for (auto n : node->methods) {
        this->printNamespace(n, depth+1);
    }
}

void ua_remoteInstance_map::printNamespace() 
{
    uint32_t d = 0;
    this->printNamespace(&this->rootNode, d);
}

ua_remoteNode* ua_remoteNode::getVariableByBrowseName(string name)
{
    for (auto v : this->variables) {
        if (v->browseName == name) {
            return v;
        }
    }
    return nullptr;
}

