#! /bin/bash

target=$1
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cp $script_dir/.bashrc $target/home/xilinx/
cp $script_dir/startvnc.sh $target/home/xilinx/
sudo cp $script_dir/tcf.agent.service $target/lib/systemd/system

