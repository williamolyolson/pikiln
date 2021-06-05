from gpiozero import OutputDevice
from time import sleep

element = OutputDevice(23)

while True:
	element.on()
	sleep(5)
	element.off()
	sleep(1)
