#!/bin/bash
set -ex

# Convenience workspace directory for later use
WORKSPACE_DIR=$(pwd)

##
## Create some aliases
##
echo 'alias ll="ls -alF"' >> ${HOME}/.bashrc
echo 'alias la="ls -A"' >> ${HOME}/.bashrc
echo 'alias l="ls -CF"' >> ${HOME}/.bashrc

make -C ${WORKSPACE_DIR} dev

# Install CDK
npm i -g aws-cdk

echo "Done!"
