# pikiln
Raspberry Pi Kiln Controller by William Olson

Tested on RaspberryPI Zero W

Prereqs:
sudo apt install python-gpiozero
sudo apt-get install build-essential python-dev python-pip python-smbus git
sudo pip install RPi.GPIO
git clone https://github.com/adafruit/Adafruit_Python_MAX31855.git
cd Adafruit_Python_MAX31855/
sudo python setup.py install

Download this code:
git clone https://github.com/williamolyolson/pikiln

python kiln.py <TEMP> <RISETIME(s)> <SOAKTIME(s)> <LOWTEMPTOLERANCE(degc)> <HIGHTEMPTOLERANCE(degc)> <REPORTINGINTERVAL(s)>
