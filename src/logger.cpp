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

#include "logger.h"
#include "config.h"

#include <iostream>
logger::logger() {}

logger::logger(std::string filename)
{
  try {
    this->logFile.open(filename);
  }
  catch(...) {
    std::cout << "Failed to open log file, using stdout instead." << std::endl;
  }
}

logger::~logger() 
{
  // FIXME: If in-memory logging is used, make sure we dump its contents now
  if (this->logFile.is_open())
    this->logFile.close();
}

void logger::logAppend(std::string logline)
{
  struct timeval n; 
  gettimeofday(&n, NULL);
  this->mtx_output.lock();
  if (this->logFile.is_open()) {
    this->logFile << std::to_string(timeval2double(n)) << ": " << std::to_string(LOG_CATEGORY_NONE) + ": " << logline << std::endl;
    this->logFile.flush();
  }
  // FIXME: else? The silent treatment means we cannot diagnose the running server... leaving it in for now
  std::cout << std::to_string(timeval2double(n)) << ": " << std::to_string(LOG_CATEGORY_NONE) + ": " << logline << std::endl; 
  std::cout.flush();
  this->mtx_output.unlock();
}

void logger::logAppend(std::string logline, log_category category)
{
  struct timeval n; 
  gettimeofday(&n, NULL);
  this->mtx_output.lock();
  if (this->logFile.is_open()) {
    this->logFile <<  std::to_string(timeval2double(n)) << ": " <<  std::to_string(category) + ": " << logline << std::endl; 
    this->logFile.flush();
  }
  // FIXME: else? The silent treatment means we cannot diagnose the running server...
  std::cout << std::to_string(timeval2double(n)) << ": " <<  std::to_string(category) + ": " << logline << std::endl; 
  std::cout.flush();
  this->mtx_output.unlock();
}
