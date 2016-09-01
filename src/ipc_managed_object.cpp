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

#include "ipc_managed_object.h"
#include <iostream>
#include <sys/time.h>

void ipc_managed_object_callWorker(ipc_managed_object *theClass)
{
  try {
    while (theClass->isRunning()) {
      theClass->workerThread_iterate();
    }
  }
  catch (...) {
    cout << "IPC: Managed Object; thread threw exception" << endl;
  }
}

ipc_managed_object::ipc_managed_object()
{
  this->ipc_id = 0;
  #ifndef DISABLE_THREADING
    this->threadTask = nullptr;
  #endif
  this->manager    = nullptr;
  this->thread_run = false;
  clock_gettime(CLOCK_REALTIME, &this->nxt_scheduled);
}

ipc_managed_object::ipc_managed_object(uint32_t ipc_id)
{
  this->ipc_id = ipc_id;
  #ifndef DISABLE_THREADING
    this->threadTask = nullptr;
  #endif
  this->manager    = nullptr;
  this->thread_run = false;
}

ipc_managed_object::~ipc_managed_object()
{
  if (this->isRunning()) 
  {
    this->doStop();
  }
  this->terminate();
}

ipc_manager *ipc_managed_object::getIpcManager()
{
  return this->manager;
}

void ipc_managed_object::reschedule(time_t tv_sec_delta, long int tv_nsec_delta) 
{
  #ifndef DISABLE_THREADING
    struct timespec delta;
    delta.tv_sec = tv_sec_delta;
    delta.tv_nsec = tv_nsec_delta;
    nanosleep((const timespec *) &delta, NULL);
  #else
    clock_gettime(CLOCK_REALTIME, &this->nxt_scheduled);
    this->nxt_scheduled.tv_sec  += tv_sec_delta;
    this->nxt_scheduled.tv_nsec += tv_nsec_delta;
  #endif
}

void ipc_managed_object::reschedule(time_t tv_sec_delta) 
{
  #ifndef DISABLE_THREADING
    struct timespec delta;
    delta.tv_sec = tv_sec_delta;
    delta.tv_nsec = 0;
    nanosleep((const timespec *) &delta, NULL);
  #else
    clock_gettime(CLOCK_REALTIME, &this->nxt_scheduled);
    this->nxt_scheduled.tv_sec += tv_sec_delta;
  #endif
}

bool ipc_managed_object::isManaged() {
  if (this->manager != nullptr)
    return true;
  return false;
}

bool ipc_managed_object::assignManager(ipc_manager *manager) {
  if (manager == nullptr)
    return false;
  this->manager = manager;
  return true;
}

void ipc_managed_object::setIpcId(uint32_t ipc_id)
{
  this->ipc_id = ipc_id;
}

uint32_t ipc_managed_object::getIpcId()
{
  return this->ipc_id;
}

bool ipc_managed_object::isRunning() 
{
  return this->thread_run;
}

bool ipc_managed_object::taskRunningAttached() 
{
#ifndef DISABLE_THREADING
  return this->threadTask->joinable();
#else
  return true;
#endif
}

uint32_t ipc_managed_object::doStop()
{
  cout << "ipc_managed_object being stopped" << endl;
  this->thread_run = false;
#ifndef DISABLE_THREADING
  if (this->threadTask->joinable()) {
    this->threadTask->join();
  }
#else
  this->workerThread_iterate(); // Make thread note the thread_run change
  this->workerThread_cleanup();
#endif
  cout << "ipc_managed_object was stopped" << endl;
  return 0;
}

uint32_t ipc_managed_object::doStart()
{
#ifndef DISABLE_THREADING
  this->mtx_threadOperations.lock();
  if (this->isRunning()) {
    this->mtx_threadOperations.unlock();
    return 0;
  }
#endif
  if(!this->isRunning())
    this->workerThread_setup();
  this->thread_run = true; 
#ifndef DISABLE_THREADING
  this->threadTask = new std::thread(ipc_managed_object_callWorker, this);
  this->mtx_threadOperations.unlock();  
#endif
  return 0;
}

int32_t ipc_managed_object::terminate() 
{
  return 0;
}

ipc_manager *ipc_managed_object::getManager() 
{
  return this->manager;
}

ipc_managed_object_type ipc_managed_object::getManagedObjectType() {
  return IPC_MANAGED_OBJECT_TYPE_GENERICOBJECT;
}