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
  
  log "Installing headers"
  cp "$SUBPROJECT_BUILD_DIRERCTORY"/../UAModeler/* "$CMAKE_PROJECT_DIRECTORY/model"
  ;;
uninstall)
  
;;
*) 
  echo "Invalid script command \"$1\""
  usage
  exit 1
;;
esac

exit 0
