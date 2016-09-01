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

#ifndef UDP_BEACON_H
#define UDP_BEACON_H

#ifdef WIN32
  #include <winsock2.h>
  #include <windows.h>
#else
  #include <sys/types.h>
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
#endif

#include <unistd.h>
#include <stdlib.h>
#include <list>

#include "ipc_managed_object.h"
#include "sys/time.h"

#include "config.h"

typedef struct beacon_config_t {
  struct {
    unsigned listen_en    : 1;
    unsigned broadcast_en : 1;
    unsigned unused       : 6;
  } options;
  uint8_t interval;
} beacon_config;

typedef struct udp_beacon_id_t {
    uint8_t id;
} udp_beacon_id;


typedef struct beacon_packet_t {
    udp_beacon_id id; // Leave for back compat
    uint32_t      tv_sec;
    uint32_t      tv_usec;
    uint8_t       interval;
    uint16_t      ua_serverport;
} beacon_packet;

typedef enum peer_state_t {
    STATE_UNKNOWN,
    STATE_NEW,
    STATE_NOMINAL,
    STATE_MISSED_UPD,
    STATE_DOWN,
    STATE_RECONNECT
} peer_state;

class peerlist_entry {
public:
    udp_beacon_id      id;
    unsigned int       interval;
    struct timeval     lastSeen;
    std::string        uri;
    peer_state         state;
  
    bool up() {
        struct timeval n;
        gettimeofday(&n, NULL);
        if (this->lastSeen.tv_sec + this->interval + 1.5*UDP_BEACON_INTERVAL < n.tv_sec)
            return false;
        return true;
    };
};

typedef void (*beacon_event_callback) (std::string hostUri, uint8_t interval, void *handle);

/* ua_server(ua_serverport) <===============>|
 *                                           |
 * bind(0.0.0.0:16664) <-- inbound beacons --+
 *                                           |
 * sendto(ANY:16664) ----- tx beacons ------>+
 *                                           |
 */
class udp_beacon : public ipc_managed_object
{
private:
    udp_beacon_id id;
    uint16_t      port;
    uint16_t      ua_server_port;
    beacon_config config;
    
    int txsocket;
    int rxsocket;
    std::thread *rxthread;
    
    beacon_event_callback callback_new;
    void *callback_new_handle;
    beacon_event_callback callback_missed;
    void *callback_missed_handle;
    beacon_event_callback callback_down;
    void *callback_down_handle;
    beacon_event_callback callback_reconnect;
    void *callback_reconnect_handle;
    
    std::list<peerlist_entry *> knownPeers;
    void registerHost(std::string uri, uint8_t expectInterval, uint16_t port);
    void deleteKnownHost(udp_beacon_id id);
public:
    udp_beacon(uint16_t port, uint16_t ua_server_port, beacon_config config);

    ipc_managed_object_type getManagedObjectType();
    void workerThread();
    void workerThreadrx();
    
    void workerThread_setup();
    void workerThread_iterate();
    void workerThread_cleanup();
    
    void workerThread_setup_rx();
    void workerThread_iterate_rx();
    void workerThread_cleanup_rx();
    
    peerlist_entry *getKnownHostById(udp_beacon_id id);
    peerlist_entry *getKnownHostByUri(std::string uri);
    std::list<peerlist_entry *> *getAliveKnownHosts();
    std::list<peerlist_entry *> *getDeadKnownHosts();
    void checkHosts();
    
    void setCallback_new(beacon_event_callback callback, void *handle);
    void setCallback_missed(beacon_event_callback callback, void *handle);
    void setCallback_down(beacon_event_callback callback, void *handle);
    void setCallback_reconnect(beacon_event_callback callback, void *handle);
};

#endif // UDP_BEACON_H
