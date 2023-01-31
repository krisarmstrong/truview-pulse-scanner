Revision: 2017-01-23
Original: 2016-11-03

Author: Kevin Loftin
Platform: TruViewPulse-Ubuntu-14.04.1 (VMware Workstation 10.0.3)

** Need version 0.29 of websocket-client, may need version 0.7.14 of netaddr **

RUN: sudo pip install "websocket-client==0.29"
RUN: sudo pip install netaddr

$ cat /etc/issue
Ubuntu 14.04.5 LTS

$ python --version
Python 2.7.6

./BigRedWebSocketClient.py > discover_pulse_live.txt

