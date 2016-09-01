# -- How to cross compile for Raspberry Pi (on a 32bit host) -- 
# 1) get the toolchain
# cd ~
# git clone https://github.com/raspberrypi/tools
# 2) export path to one of the compilers
# export PATH=$PATH:~/tools/arm-bcm2708/arm-none-linux-gnueabi/bin/
# 3) use this toolchain file 
# cmake -DCMAKE_TOOLCHAIN_FILE=../tools/cmake/Toolchain-rpi.cmake -DEXAMPLESERVER=ON ..
# make
SET(CMAKE_EXE_LINKER_FLAGS "-Wl,--no-as-needed ${THREADTEST_COMPILE_FLAG}")
set(CMAKE_C_COMPILER arm-none-linux-gnueabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-linux-gnueabi-g++)
set(CMAKE_STRIP arm-none-linux-gnueabi-strip)
