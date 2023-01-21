cd ev3-robotic-arm
code .
sudo apt install python3-venv
python3 -m venv .venv
. .venv/bin/activate
pip3 install --upgrade pip
pip3 install python-ev3dev2
pip3 install rpyc
pip3 install paho-mqtt
pip3 install msgpack