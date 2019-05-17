#! /bin/bash

set -x
set -e

cd /root
if [ ! -d "tcf.agent" ]; then
git clone https://github.com/eclipse/tcf.agent
cd tcf.agent/agent
cmake .
make -j4
make install

systemctl enable tcf.agent
fi

exit 0

cd /home/xilinx
if [ ! -d "gstreamer" ]; then
git clone https://gitlab.freedesktop.org/gstreamer/gstreamer
cd gstreamer
./autogen.sh
make -j4
make install
cd ..
chown -R xilinx:xilinx gstreamer
fi

cd /home/xilinx
if [ ! -d "gst-plugins-base" ]; then
git clone https://github.com/GStreamer/gst-plugins-base
cd gst-plugins-base
./autogen.sh
make -j4
cd ..
chown -R xilinx:xilinx gst-plugins-base
fi

cd /home/xilinx
if [ ! -d "gst-plugins-good" ]; then
git clone https://github.com/GStreamer/gst-plugins-good
cd gst-plugins-good
./autogen.sh
make -j4
cd ..
chown -R xilinx:xilinx gst-plugins-good
fi

cd /home/xilinx

rm -rf gst-rtsp-server

if [ ! -d "gst-rtsp-server" ]; then
git clone https://github.com/GStreamer/gst-rtsp-server
cd gst-rtsp-server
./autogen.sh
make -j4
cd ..
chown -R xilinx:xilinx gst-rtsp-server
fi

