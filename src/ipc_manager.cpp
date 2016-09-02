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
#include "config.h"

#include "ipc_manager.h"
#include "ipc_managed_object.h"

extern "C" {
#ifdef WIN32
  #include <windows.h>
#else
  #include <unistd.h>
#endif
}

#include <time.h>

ipc_manager::ipc_manager()
{
  this->nxtId = 0;
}

ipc_manager::~ipc_manager()
{
  // FIXME: Stop, then terminate managed objects.
}

static void call_periodiclyKickWorkerThread(ipc_manager *mgr) {mgr->periodiclyKickWorkerThread();}
void ipc_manager::periodiclyKickWorkerThread()
{
  //timespec t_periodic = (const struct timespec) {.tv_sec=0, .tv_nsec=IPC_MANAGER_PERIODIC_IDLEUPATEINTERVAL*1000000};
  
  while(this->thread_run) {
    this->notifier.notify_all();
    this->reschedule(1);
  }
}

void ipc_manager::workerThread_setup()   
{
  #ifndef DISABLE_THREADING
  this->kicker = new std::thread(call_periodiclyKickWorkerThread, this);
  this->lock   = new std::unique_lock<std::mutex>(this->mtx_threadOperations);
  #endif
}

void ipc_manager::workerThread_iterate() 
{
  #ifndef DISABLE_THREADING
  this->notifier.wait(*(this->lock));
  #endif
  
  // Check Tasks
  for (std::list<ipc_task*>::reverse_iterator i = this->taskList.rbegin(); i != this->taskList.rend(); ++i) 
  {
    if((*(i))->hasCompleted()) 
      this->taskList.remove((*(i)));
    else 
      if (! (*(i))->isRunning())
        (*(i))->doStart();
  }  
  #ifdef DISABLE_THREADING
  this->reschedule(0, IPC_MANAGER_TICKINTERVAL);
  #endif
}

void ipc_manager::workerThread_cleanup() 
{
  #ifndef DISABLE_THREADING
  // Kicker is only required in multithreaded scenarios to periodically lift the event lock
  // In single-threading, the main loop can safely be run in each iteration
  if (this->kicker->joinable()) {
    this->kicker->join();
    delete this->kicker;
    this->kicker = nullptr;
  }
  #endif
}

uint32_t ipc_manager::addObject(ipc_managed_object *object) 
{
  #ifndef DISABLE_THREADING
  std::unique_lock<std::mutex> lock(this->mtx_threadOperations);
  #endif
  
  if (object==nullptr) return 0; //Used to kick the worker thread for shutdown;
  
  object->setIpcId(this->getUniqueIpcId());
  object->assignManager(this);
  this->objects.push_back(object);
  object->doStart();
  
  this->notifier.notify_all();
  
  return object->getIpcId();
}

uint32_t ipc_manager::deleteObject(uint32_t rpc_id) 
{
  std::list<ipc_managed_object *> deleteThese;
  
  for(list<ipc_managed_object*>::iterator j = this->objects.begin(); j != this->objects.end(); j++) {
    ipc_managed_object *obj = *j;
    if (obj->getIpcId() == rpc_id) {
      deleteThese.push_back(obj);
    }
  }
  
  list<ipc_managed_object*>::iterator j ;
  j = deleteThese.begin();
  while (j != deleteThese.end()) {
    ipc_managed_object *obj = *j;
    obj->doStop();
    this->objects.remove(obj);
    deleteThese.remove(obj);
    delete obj;
    j = deleteThese.begin();
  }
  return 0;
}

uint32_t ipc_manager::getUniqueIpcId() 
{
  return ++nxtId;
}

uint32_t ipc_manager::addTask(ipc_task *task) {
  #ifndef DISABLE_THREADING
  std::unique_lock<std::mutex> lock(this->mtx_threadOperations);
  #endif
  
  if (task == NULL)
    return 0;
  task->setIpcId(this->getUniqueIpcId());
  task->assignManager(this);
  this->taskList.push_back(task);
  task->doStart();
  
  this->notifier.notify_all();
  
  return task->getIpcId();
}

void ipc_manager::startAll() {
  for (auto j : this->objects) {
    j->doStart();
  }
  this->doStart();
  return;
}

void ipc_manager::iterate() {
  struct timespec now;
  
  struct timespec delta_min;
  clock_gettime(CLOCK_REALTIME, &delta_min);
  for (auto j : this->objects) {
    clock_gettime(CLOCK_REALTIME, &now);
    long int delta_sec = j->nxt_scheduled.tv_sec - now.tv_sec;
    long int delta_usec = j->nxt_scheduled.tv_nsec - now.tv_nsec;
    if ( delta_sec < 0 || (delta_sec == 0 &&  delta_usec <= 0 )) {
      // run now
      j->workerThread_iterate();
      long int delta_sec = j->nxt_scheduled.tv_sec - now.tv_sec;
      long int delta_usec = j->nxt_scheduled.tv_nsec - now.tv_nsec;
      if (delta_usec < 0) {
        delta_sec --;
        delta_usec = 1000000000 + delta_usec ;
      }
    }
    if (delta_sec < delta_min.tv_sec || (delta_sec == delta_min.tv_sec  && delta_usec < delta_min.tv_nsec)) {
      delta_min.tv_sec = delta_sec;
      delta_min.tv_nsec = delta_usec;
    }
  }
  
  //LOG_DEBUG("Running " + std::to_string(delta_min.tv_sec) + "s, " + std::to_string(delta_min.tv_nsec) + "ns");
  nanosleep((const timespec *) &delta_min, NULL);
  return;
}

void ipc_manager::stopAll() {
  for(list<ipc_managed_object*>::iterator j = this->objects.begin(); j != this->objects.end(); j++) {
    ipc_managed_object *obj = *j;
    (*obj).doStop();
  }
  
  // Stop our own thread
  this->thread_run = false;
  this->reschedule(1);
  this->notifier.notify_all();
  this->reschedule(1);
  this->notifier.notify_all();
  this->doStop();
  
  return;
}

list<ipc_managed_object*> *ipc_manager::getAllObjectsByType(ipc_managed_object_type typeMask) 
{
  list<ipc_managed_object*> *objLst = new list<ipc_managed_object*>;
  
  // cppcheck-suppress postfixOperator                REASON: List iterator cannot be prefixed
  for(list<ipc_managed_object*>::iterator j = this->objects.begin(); j != this->objects.end(); j++) {
    ipc_managed_object *obj = *j;
    if (obj->getManagedObjectType() & typeMask) {
      objLst->push_back(obj);
    }
  }
  
  return objLst;
}

ipc_managed_object* ipc_manager::getObjectById(uint32_t id) {return nullptr; }