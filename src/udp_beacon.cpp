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

#include "udp_beacon.h"
#include "config.h"
#include <thread>
#include <errno.h>
#include <fcntl.h>

udp_beacon::udp_beacon(uint16_t port, uint16_t ua_server_port, beacon_config config)
{
    this->ua_server_port        = ua_server_port;
    this->port                  = port;
    this->id.id                 = 0; // legacy; not used
    this->config                = config;
  
    this->callback_new          = nullptr;
    this->callback_missed       = nullptr;
    this->callback_down         = nullptr;
    this->callback_reconnect    = nullptr;
    
    this->rxthread = nullptr;
}

ipc_managed_object_type udp_beacon::getManagedObjectType() {
  return IPC_MANAGED_OBJECT_TYPE_UDPBEACON;
}

static void workerThreadrx_callproxy(udp_beacon *b) { 
  while(b->isRunning()) {
    b->workerThread_iterate_rx(); 
  }
}

void udp_beacon::workerThread_setup() 
{
  this->txsocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
  int txsocket_option = 1;
  setsockopt(this->txsocket, SOL_SOCKET, SO_BROADCAST, &txsocket_option, sizeof(txsocket_option));
  
  LOG_DEBUG("Setting up worker thread");
  
  if (this->config.options.listen_en)
    this->workerThread_setup_rx();
  
  #ifndef DISABLE_THREADING
  if (this->config.options.listen_en)
    this->rxthread = new std::thread(workerThreadrx_callproxy, this);
  #endif
}

void udp_beacon::workerThread_iterate()
{
  struct sockaddr_in txaddress;  // Bind to this for listening..
  memset((char *)&txaddress, 0, sizeof(struct sockaddr_in));
  txaddress.sin_family          = AF_INET;
  txaddress.sin_port            = htons(this->port);
  txaddress.sin_addr.s_addr     = INADDR_BROADCAST;
  
  beacon_packet packet;
  packet.id             = this->id;
  packet.interval       = this->config.interval;
  packet.ua_serverport  = htons(this->ua_server_port);
  
  size_t txsz;
  
  this->checkHosts();
  if (this->config.options.broadcast_en == 1)  {
    timeval t;
    gettimeofday(&t, NULL);
    packet.tv_sec  = htonl(t.tv_sec);
    packet.tv_usec = htonl(t.tv_usec);
    size_t sz = sizeof(beacon_packet);

    txsz = sendto(this->txsocket, (void*) &packet, sz, 0, (struct sockaddr *) &txaddress, sizeof(txaddress));
    if(txsz == -1) {
        std::string e = strerror(errno);
        LOG_DEBUG("Error: " + e);
    }
  }
  
  #ifdef DISABLE_THREADING
  if(this->config.options.listen_en == 1)
    this->workerThread_iterate_rx();
  #endif
    
  this->reschedule(this->config.interval);
}


void udp_beacon::workerThread_cleanup()
{
  #ifndef DISABLE_THREADING
  if(this->rxthread != nullptr && this->config.options.listen_en)
    this->rxthread->join();
  delete this->rxthread;
  #else
  this->workerThread_cleanup_rx();
  #endif
}

void udp_beacon::workerThread_setup_rx() 
{
  struct sockaddr_in rxaddress;  // Bind to this for listening..
  memset((char *)&rxaddress, 0, sizeof(struct sockaddr_in));
  rxaddress.sin_family = AF_INET;
  rxaddress.sin_port   = htons(this->port);
  rxaddress.sin_addr.s_addr = INADDR_ANY;
  
  if (( this->rxsocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) {
    std::string e = strerror(errno);  
    LOG_ERROR("UDP Beacon [RX]: Failed to bind RX Beacon port: " + e);
    return;
  }
  
  if (bind(this->rxsocket, (struct sockaddr *) &rxaddress, sizeof(struct sockaddr)) < 0) {
    std::string e = strerror(errno);
    LOG_DEBUG("UDP Beacon [RX]: Error binding RX Port: " + e);
    return;
  }  
  
  int rxsocket_option = 1;
  setsockopt(this->rxsocket, SOL_SOCKET, SO_BROADCAST, &rxsocket_option, sizeof(rxsocket_option));
  
#ifdef DISABLE_THREADING
  int ioctlFlags = fcntl(this->rxsocket, F_GETFL) | O_NONBLOCK ;
  fcntl(this->rxsocket, F_SETFL, ioctlFlags);
#endif
  return;
}

void udp_beacon::workerThread_iterate_rx()
{
  struct sockaddr_in srcaddress; // Put source ip/port here
  memset((char *)&srcaddress, 0, sizeof(struct sockaddr_in));
  socklen_t srcaddresssz = sizeof(struct sockaddr_in);
  
  size_t rxSz;
  beacon_packet rxPacket;

  rxSz = recvfrom(this->rxsocket, &rxPacket, sizeof(beacon_packet), 0, (struct sockaddr*) &srcaddress, &srcaddresssz);
  if(errno == EAGAIN || errno == EWOULDBLOCK) { // NonBlocking operations for non-threaded mode
    this->reschedule(0,250*1000000); //250 ms
    return;
  }
  
  if (srcaddress.sin_addr.s_addr != 0) {
      std::string uri =inet_ntoa(srcaddress.sin_addr);
      uri = "opc.tcp://" + uri + ":" + std::to_string(ntohs(rxPacket.ua_serverport));
      this->registerHost(uri, rxPacket.interval, ntohs(rxPacket.ua_serverport));
  }
  
  this->reschedule(0,250*1000000); //250 ms
  return;
}

void udp_beacon::workerThread_cleanup_rx()
{}

void udp_beacon::checkHosts() 
{
    struct timeval n;
    gettimeofday(&n, NULL);
    
    for(auto h : this->knownPeers) {
        if (not h->up() && h->state != STATE_DOWN) {
            if (h->state == STATE_MISSED_UPD) {
                h->state = STATE_DOWN;
                if (this->callback_down != nullptr)
                    this->callback_down(h->uri, h->interval, this->callback_down_handle);
            }
            else {
                h->state = STATE_MISSED_UPD;
                if (this->callback_missed != nullptr)
                    this->callback_missed(h->uri, h->interval, this->callback_missed_handle);
            }
        }
        else if (h->state == STATE_RECONNECT || h->state == STATE_NEW) {
            h->state = STATE_NOMINAL;
        }
    }
}

void udp_beacon::registerHost(std::string uri, uint8_t expectInterval, uint16_t port)
{
    struct timeval n;
    gettimeofday(&n, NULL);

    // Find out if this host is already known
    for(auto h : this->knownPeers) {
        if (h->uri == uri) {
            h->lastSeen = n;
            if (h->state == STATE_DOWN) {
                h->state = STATE_RECONNECT;
                if (this->callback_reconnect != nullptr)
                    this->callback_reconnect(h->uri, h->interval, this->callback_reconnect_handle);
            }
            else
                h->state = STATE_NOMINAL;
            return;
        }
    }
  
    peerlist_entry *p = new peerlist_entry;
    p->id = id;
    p->interval = expectInterval;
    std::string turi = uri;
    p->uri = turi;
    p->state = STATE_NEW;
    if (this->callback_new != nullptr)
        this->callback_new(p->uri, p->interval, this->callback_new_handle);
    this->knownPeers.push_back(p);
}

void udp_beacon::setCallback_new(beacon_event_callback callback, void *handle) 
{
    this->callback_new = callback;
}

void udp_beacon::setCallback_missed(beacon_event_callback callback, void *handle)
{
    this->callback_missed = callback;
}

void udp_beacon::setCallback_down(beacon_event_callback callback, void *handle)
{
    this->callback_down = callback;
}

void udp_beacon::setCallback_reconnect(beacon_event_callback callback, void *handle)
{
    this->callback_reconnect = callback;
}
