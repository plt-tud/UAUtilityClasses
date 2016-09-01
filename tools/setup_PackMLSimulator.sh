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
  cp "$SUBPROJECT_BUILD_DIRERCTORY/../AutomatonSTL"  "$CMAKE_PROJECT_DIRECTORY/src/" -r
  cp "$SUBPROJECT_BUILD_DIRERCTORY/../MTPServiceModel"  "$CMAKE_PROJECT_DIRECTORY/src/" -r
  ;;
uninstall)
  rm "$CMAKE_PROJECT_DIRECTORY/src/AutomatonSTL" -r
  rm "$CMAKE_PROJECT_DIRECTORY/src/MTPServiceModel" -r
;;
*) 
  echo "Invalid script command \"$1\""
  usage
  exit 1
;;
esac

exit 0
