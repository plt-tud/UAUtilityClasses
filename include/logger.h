/*
 * Copyright (c) 2016 Chris Iatrou <Chris_Paul.Iatrou@tu-dresden.de>
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

#ifndef COSIM_LOGGER_H
#define COSIM_LOGGER_H

#include <string>
#include <list>

extern "C" {
  #ifdef WIN32
  #include <Windows.h>
  #include <Winsock2.h>
  #else
  #include <unistd.h>
  #endif
}

#include <sys/time.h>
#include <fstream>
#include <mutex>


/* Global log mechaninsm... needs to be instantiated in externally (see main)
 * globalLog->logAppend() is the default target of COSIM_LOG(msg)
 */
class logger;
extern logger *globalLog;

// Mini-Logging
#include "time.h"
static double timeval2double(struct timeval n) {
  double s = n.tv_sec;
  double u = n.tv_usec;
  u /= 1000000;
  return s + u;
}

typedef enum log_category_t 
{
  LOG_CATEGORY_NONE     = 0,
  LOG_CATEGORY_DEBUG    = 10,
  LOG_CATEGORY_INFO     = 20,
  LOG_CATEGORY_WARNING  = 30,
  LOG_CATEGORY_ERROR    = 40,
  LOG_CATEGORY_FATAL    = 50
} log_category;


typedef struct log_entry_t {
  struct timeval n;
  log_category   category;
  std::string    message;
} log_entry;

class logger
{
private:
  /* FIXME: Making logs an in-memory-struct only dumped regular program 
   * termination would make this far more efficient... 
   */
  std::list<log_entry *> logentries; // unused
  std::ofstream logFile;
  std::mutex     mtx_output;
public:
  logger();
  logger(std::string filename);
  ~logger();
  
  void logAppend(std::string logline);
  void logAppend(std::string logline, log_category log_category);
  
  void dumpLogToFile(std::string filename); // unimplemented/unused
  
  void debug(std::string logline) {this->logAppend(logline, LOG_CATEGORY_DEBUG);}
  void info(std::string logline)  {this->logAppend(logline, LOG_CATEGORY_INFO);}
  void warn(std::string logline)  {this->logAppend(logline, LOG_CATEGORY_WARNING);}
  void error(std::string logline) {this->logAppend(logline, LOG_CATEGORY_ERROR);}
  void fatal(std::string logline) {this->logAppend(logline, LOG_CATEGORY_FATAL);}
};

static inline void LOG_DEBUG(std::string logline) { if (globalLog != nullptr) globalLog->debug(logline); }
static inline void LOG_INFO(std::string logline) { if (globalLog != nullptr) globalLog->info(logline); }
static inline void LOG_WARN(std::string logline) { if (globalLog != nullptr) globalLog->warn(logline); }
static inline void LOG_ERROR(std::string logline) { if (globalLog != nullptr) globalLog->error(logline); }
static inline void LOG_FATAL(std::string logline) { if (globalLog != nullptr) globalLog->fatal(logline); }

#endif // COSIM_LOGGER_H
