#! /bin/bash

set -x
set -e

cd /root

git clone https://github.com/eclipse/tcf.agent
cd tcf.agent/agent
cmake .
make -j4
make install

