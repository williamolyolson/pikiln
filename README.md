# pikiln
Raspberry Pi Kiln Controller by William Olson

Tested on: 

RaspberryPI Zero W: https://www.adafruit.com/product/3400

Thermocouple Amplifier MAX31855 breakout board: https://www.adafruit.com/product/269

Prereqs:

sudo apt install python-gpiozero

sudo apt-get install build-essential python-dev python-pip python-smbus git

sudo pip install RPi.GPIO

git clone https://github.com/adafruit/Adafruit_Python_MAX31855.git

cd Adafruit_Python_MAX31855/

sudo python setup.py install

Download this code:
git clone https://github.com/williamolyolson/pikiln

python kiln.py <TEMP> <RISETIME(sec)> <SOAKTIME(sec)> <LOWTEMPTOLERANCE(degc)> <HIGHTEMPTOLERANCE(degc)> <REPORTINGINTERVAL(sec)>
