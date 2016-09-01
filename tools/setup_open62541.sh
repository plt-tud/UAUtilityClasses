SETUP_COMMAND="$1"
CMAKE_PROJECT_DIRECTORY="$2"
SUBPROJECT_BUILD_DIRERCTORY="$3"

function usage() {
    echo "setup script usage: setup_<depName> [install|uninstall] CMAKE_PROJECT_DIRECTORY SUBPROJECT_BUILD_DIRERCTORY"
    echo ""
}

function log() {
    echo $@
}

## Check Options
if [ $# -lt 3 ];then
  exit 1
fi

if [ ! -d "$CMAKE_PROJECT_DIRECTORY/include/open62541" ]; then
    mkdir "$CMAKE_PROJECT_DIRECTORY/include/open62541"
fi

case $SETUP_COMMAND in
install)
  if [ ! -d "$CMAKE_PROJECT_DIRECTORY/include/open62541" ]; then
      mkdir "$CMAKE_PROJECT_DIRECTORY/include/open62541"
  fi
  if [ ! -d "$CMAKE_PROJECT_DIRECTORY/src/open62541" ]; then
      mkdir "$CMAKE_PROJECT_DIRECTORY/src/open62541"
  fi
  
  log "Installing headers"
  
  # Pretend we don't have amalgamation (use bootstrapping code in model): Copy all header files
  ( cd "$SUBPROJECT_BUILD_DIRERCTORY"/..
  find ./ -name *.h | while read HEADER; do 
    DIR=`dirname $HEADER`; 
    mkdir -p ../../../include/open62541/$DIR; 
    cp $HEADER ../../../include/open62541/$DIR; 
  done
  )
  # Since we are actually using open62541.c, we will still need this one...
  cp "$SUBPROJECT_BUILD_DIRERCTORY"/open62541.h "$CMAKE_PROJECT_DIRECTORY/include/open62541"
  
  cp "$SUBPROJECT_BUILD_DIRERCTORY"/open62541.c "$CMAKE_PROJECT_DIRECTORY/src/open62541"
  log "Installing libraries"
  cp "$SUBPROJECT_BUILD_DIRERCTORY"/libopen62541* "$CMAKE_PROJECT_DIRECTORY/lib"

  cp -r "$SUBPROJECT_BUILD_DIRERCTORY/../tools/pyUANamespace" "$CMAKE_PROJECT_DIRECTORY/tools"
  rm "$CMAKE_PROJECT_DIRECTORY"/tools/pyUANamespace/*txt
  ;;
uninstall)
  rm -r "$CMAKE_PROJECT_DIRECTORY/include/open62541"
  rm -r "$CMAKE_PROJECT_DIRECTORY/src/open62541"
  rm -r "$CMAKE_PROJECT_DIRECTORY/lib"/libopen62541*
  rm -r "$CMAKE_PROJECT_DIRECTORY/tools/pyUANamespace"
;;
*) 
  echo "Invalid script command \"$1\""
  usage
  exit 1
;;
esac

exit 0
