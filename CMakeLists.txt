cmake_minimum_required(VERSION 2.8.0)

project(UAUtility)


##########################################################################################################
## Compiler specific stuff
##########################################################################################################

if(CMAKE_COMPILER_IS_GNUCC OR "x${CMAKE_C_COMPILER_ID}" STREQUAL "xClang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
    #set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -static")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wl,--no-as-needed ${THREADTEST_COMPILE_FLAG}")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=c99 ")
    #set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -static")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3")
    set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
endif()

##########################################################################################################
## Includes, Link dirs und Quellcode
##########################################################################################################


include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${PROJECT_BINARY_DIR}/include
)

configure_file (
    "${PROJECT_SOURCE_DIR}/include/config.h.in"
    "${PROJECT_BINARY_DIR}/include/config.h"
)


set(ipcSources
    ${CMAKE_SOURCE_DIR}/src/ipc_managed_object.cpp
    ${CMAKE_SOURCE_DIR}/src/ipc_manager.cpp
    ${CMAKE_SOURCE_DIR}/src/ipc_task.cpp
)

set(udpBeaconSources
    ${CMAKE_SOURCE_DIR}/src/udp_beacon.cpp
)


#set(uaMappedClassSources
#     ${CMAKE_SOURCE_DIR}/src/ua_mapped_class.cpp
#     ${CMAKE_SOURCE_DIR}/src/ua_proxies.cpp
#     ${CMAKE_SOURCE_DIR}/src/ua_template.cpp
# )
#
# set(uaRemoteMapSources
#     ${CMAKE_SOURCE_DIR}/src/ua_remoteinstance_map.cpp
# )


##########################################################################################################
## Optionen
##########################################################################################################
set(IPC_MANAGER_TICKINTERVAL "10" CACHE STRING "Tick interval for the IPC Manager class (in ms)")
set(TIMETICK_INTERVAL "100" CACHE STRING "Tick interval for state machines (in ms)")

set(UA_SERVER_PORT "16664" CACHE STRING "Port for our Server to listen on")

set(UDP_BEACON_PORT "16664" CACHE STRING "Beacon group port")
set(UDP_BEACON_INTERVAL "1" CACHE STRING "UDP beacon interval in seconds")


##########################################################################################################
## Object and shared library compilation required by tests and examples
##########################################################################################################

## IPC
add_library(ipc SHARED ${ipcSources})

## UDP Beacon
add_library(udp_beacon SHARED ${udpBeaconSources})

# ## UA Mapped Class
# add_library(ua_mapped_class SHARED ${uaMappedClassSources})
#
# ## UA RemoteMap
# add_library(ua_remote_map SHARED ${uaRemoteMapSources})

##########################################################################################################
##  Installation
##########################################################################################################

install(TARGETS ipc udp_beacon #ua_mapped_class ua_remote_map
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
install(
    FILES
        ${CMAKE_SOURCE_DIR}/include/ipc_managed_object.h
        ${CMAKE_SOURCE_DIR}/include/ipc_manager.h
        ${CMAKE_SOURCE_DIR}/include/ipc_task.h
    DESTINATION include
)
