#!/bin/bash

CMAKE_PROJECT_DIRECTORY="$1"

## Directory configs
PROJECT_DEPENDENCIES_DIR="$CMAKE_PROJECT_DIRECTORY/tools/dependencies"

if [  ! -d "$PROJECT_DEPENDENCIES_DIR" ]; then
    mkdir -p "$PROJECT_DEPENDENCIES_DIR"
fi

## Subproject targets
SUBPROJECT=0

SUBPROJECTS_NAMES[$SUBPROJECT]="open62541"
SUBPROJECTS_VCS[$SUBPROJECT]="git"
SUBPROJECTS_BUILD[$SUBPROJECT]="cmake"
SUBPROJECTS_URI[$SUBPROJECT]="https://github.com/open62541/open62541.git"
SUBPROJECTS_CMAKEOPTIONS[$SUBPROJECT]="-DUA_ENABLE_AMALGAMATION=On -DBUILD_SHARED_LIBS=On -DUA_ENABLE_GENERATE_NAMESPACE0=On -DUA_ENABLE_METHODCALLS=ON -DUA_ENABLE_NODEMANAGEMENT=ON -DUA_ENABLE_SUBSCRIPTIONS=ON"
SUBPROJECT=$((SUBPROJECT+1))

SUBPROJECTS_NAMES[$SUBPROJECT]="PackMLSimulator"
SUBPROJECTS_VCS[$SUBPROJECT]="git"
SUBPROJECTS_BUILD[$SUBPROJECT]=""
SUBPROJECTS_URI[$SUBPROJECT]="https://github.com/plt-tud/PackML-Simulator.git"
SUBPROJECTS_CMAKEOPTIONS[$SUBPROJECT]=""
SUBPROJECT=$((SUBPROJECT+1))

SUBPROJECTS_NAMES[$SUBPROJECT]="ModuleIM"
SUBPROJECTS_VCS[$SUBPROJECT]="git"
SUBPROJECTS_BUILD[$SUBPROJECT]=""
SUBPROJECTS_URI[$SUBPROJECT]="https://github.com/plt-tud/OPC_UA_Module_IM.git"
SUBPROJECTS_CMAKEOPTIONS[$SUBPROJECT]=""
SUBPROJECT=$((SUBPROJECT+1))

#No of subprojects
SUBPROJECTS=$((SUBPROJECT-1))

function vcs_getProject() {
    VCS="$1"
    URI="$2"
    TGTDIR="$3"
    
    if [ $VCS == "git" -o $VCS="GIT" ]; then
        git $OPTIONS clone "$URI" "$TGTDIR"
    elif  [ $VCS == "svn" -o $VCS="SVN" ]; then
        svn $OPTIONS checkout "$URI" "$TGTDIR"
    fi
}

function vcs_updateProject() {
    VCS="$1"
    URI="$2"
    TGTDIR="$3"
    
    if [ $VCS == "git" -o $VCS="GIT" ]; then
        git -C "$TGTDIR" pull 
    elif  [ $VCS == "svn" -o $VCS="SVN" ]; then
        svn $OPTIONS update "$TGTDIR"
    fi
}

function log() {
    echo $@
}

function installAll() {
  ## Stage 1: Clone/Fetch all subprojects
  I=0
  while [ $I -lt $SUBPROJECTS ]; do
    log "Fetching/Updating subproject $I ${SUBPROJECTS_NAMES[$I]}"
    # Decide whether to clone or pull 
    if [ -d "$PROJECT_DEPENDENCIES_DIR/${SUBPROJECTS_NAMES[$I]}" ]; then
        vcs_updateProject "${SUBPROJECTS_VCS[$I]}" "${SUBPROJECTS_URI[$I]}" "$PROJECT_DEPENDENCIES_DIR/${SUBPROJECTS_NAMES[$I]}"
    else
        vcs_getProject "${SUBPROJECTS_VCS[$I]}" "${SUBPROJECTS_URI[$I]}" "$PROJECT_DEPENDENCIES_DIR/${SUBPROJECTS_NAMES[$I]}"
    fi
    
    I=$((I+1))
  done

  ## Stage 2: Patch all subprojects

  ## Stage 3: Build all subprojects
  I=0
  while [ $I -lt $SUBPROJECTS ]; do
    log "Building subproject ${SUBPROJECTS_NAMES[$I]}"
    # Decide whether to clone or pull 
    if [ ! -d "$PROJECT_DEPENDENCIES_DIR/${SUBPROJECTS_NAMES[$I]}/build" ]; then
        mkdir "$PROJECT_DEPENDENCIES_DIR/${SUBPROJECTS_NAMES[$I]}/build"
    fi
    
    OLDD=`pwd`
    cd "$PROJECT_DEPENDENCIES_DIR/${SUBPROJECTS_NAMES[$I]}/build"
    
    if [ "${SUBPROJECTS_BUILD[$I]}" == "cmake" ]; then
        (cmake ${SUBPROJECTS_CMAKEOPTIONS[$I]} .. && make) || exit 1
    fi
    cd $OLDD
    
    log "Installing subproject"
    if [ ! -f "$CMAKE_PROJECT_DIRECTORY/tools/setup_${SUBPROJECTS_NAMES[$I]}.sh" ]; then
        log "Installscript does not exist... creating template"
        echo -e "#!/bin/bash\nCMAKE_PROJECT_DIRECTORY=\"\$1\"\nSUBPROJECT_BUILD_DIRERCTORY=\"\$2\"\n\nfunction log() {\n    echo \$@\n}\n\n## Check Options\nif [ \$# -lt 2 ];then\n  exit 1\nfi\n\n\nexit 0" >  "$PROJECT_DEPENDENCIES_DIR/setup_${SUBPROJECTS_NAMES[$I]}.sh"
    fi
    
    /bin/bash "$CMAKE_PROJECT_DIRECTORY/tools/setup_${SUBPROJECTS_NAMES[$I]}.sh" install "$CMAKE_PROJECT_DIRECTORY" "$PROJECT_DEPENDENCIES_DIR/${SUBPROJECTS_NAMES[$I]}/build"
    
    I=$((I+1))
  done
}

function uninstallAll() {
  ## Call setup script to uninstall all installed files
  I=0
  while [ $I -lt $SUBPROJECTS ]; do
    log "Unistalling subproject $I ${SUBPROJECTS_NAMES[$I]}"
    
    /bin/bash "$CMAKE_PROJECT_DIRECTORY/tools/setup_${SUBPROJECTS_NAMES[$I]}.sh" uninstall "$CMAKE_PROJECT_DIRECTORY" "$PROJECT_DEPENDENCIES_DIR/${SUBPROJECTS_NAMES[$I]}/build"
    
    I=$((I+1))
  done
  
  log "Removing dependencies build directory"
  rm -rf "$PROJECT_DEPENDENCIES_DIR"
}

## Check Options
if [ $# -lt 1 ]; then
    log "Invalid number of arguments"
    exit 1
fi

if [ ! -d $CMAKE_PROJECT_DIRECTORY -o ! -d $PROJECT_DEPENDENCIES_DIR ]; then
    log "Invalid Project folder"
    exit 1
fi

if [ ! -z "$2" -a "$2"="uninstall" ]; then
  uninstallAll
else
  installAll
fi

exit 0
