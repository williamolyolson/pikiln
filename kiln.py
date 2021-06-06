import sys
import Adafruit_MAX31855.MAX31855 as MAX31855

from gpiozero import OutputDevice
from time import sleep

# Define a function to convert celsius to fahrenheit.
def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0

# Raspberry Pi software SPI configuration.
CLK = 22
CS  = 27
DO  = 17
sensor = MAX31855.MAX31855(CLK, CS, DO)

argcnt = len(sys.argv)
if argcnt == 7:
    setTemp = float(sys.argv[1])
    riseTime = float(sys.argv[2])
    soakTime = float(sys.argv[3])
    lowTolerance = float(sys.argv[4])
    highTolerance = float(sys.argv[5])
    reportInterval = int(sys.argv[6])
else:
    sys.exit("Invalid Argument: kiln.py <settemp> <risetime> <soaktime> <lowtemptolerance> <hightemptolerance> <reportinterval>")
    #print('Invalid Arguments: kiln.py <settemp> <risetime> <soaktime> <reportinterval>')
    #print('Setting test firing defaults... (30, 180, 60, 1)')
    #setTemp = 30
    #soakTime = 180
    #riseTime = 60
    #reportInterval = 1

print('Fire Parameters: SetTemp:' + str(setTemp) + 'c RiseTime:' + str(riseTime) + 's SoakTime:' + str(soakTime) + 's')
totalTime = soakTime+riseTime
runTime = 1
currentTemp = 0
stepTemp = 0
riseInterval = 1
sleepInterval = 1
reportCounter = 0
rising = 1
soaking = 1
element = OutputDevice(23)
elementState =0
onDutyCnt=0
offDutyCnt=5
onDutyTime=5
offDutyTime=60
tempRiseRateLimit=0
tempRiseRate=0
maxElementOnTime=60
minElementOnTime=5
maxElementOffTime=60
minElementOffTime=5
startingTemp=0
checkFreq=20
checkCnt=0
elementToggle=1

def check_rates():
    global tempRiseRate
    global onDutyTime
    global offDutyTime
    tempRiseRate = ((currentTemp - startingTemp)/runTime)*60
    if tempRiseRate < tempRiseRateLimit:
        #increase onDutyTime/decrease offDutyTime
        if onDutyTime < maxElementOnTime:
            onDutyTime+=round(abs(tempRiseRate-tempRiseRateLimit),1)
        else:
            if offDutyTime > minElementOffTime:
                offDutyTime -= round(abs(tempRiseRate-tempRiseRateLimit),1)
            
    if tempRiseRate > tempRiseRateLimit:
        #decrease onDutyTime/increase offDutytime
        if onDutyTime > minElementOnTime:
            onDutyTime -=round(abs(tempRiseRate-tempRiseRateLimit),1)
        else:
            if offDutyTime < maxElementOffTime:
                offDutyTime += round(abs(tempRiseRate-tempRiseRateLimit),1)

    print('Current Rise Rate/Limit:' + str(tempRiseRate) + '/' + str(tempRiseRateLimit))
    print('Element Duty Cycle(on/off)(s):' + str(onDutyTime) + '/' + str(offDutyTime))

def element_control():
    global checkCnt
    global onDutyCnt
    global offDutyCnt
    global elementToggle
    checkCnt += 1
    onDutyCnt += 1
    offDutyCnt +=1
    #if checkCnt >= checkFreq:
    #    if elementState == 1:
    #        check_rates()

    #    checkCnt = 0

    if elementState == 1:
        #on mode5
        if elementToggle == 1:
            if onDutyCnt < onDutyTime:
                #onDutyCnt += 1
                element.on()
            else:
                offDutyCnt = 0
                elementToggle=0
        else:            
            if offDutyCnt < offDutyTime:
                #offDutyCnt += 1
                element.off()
            else:
                onDutyCnt = 0
                elementToggle=1
                check_rates()
    else:
        #off mode
        element.off()
        
currentTemp = sensor.readTempC()
startingTemp = currentTemp
riseInterval = round((setTemp -currentTemp)/riseTime,4)
tempRiseRateLimit = riseInterval * 60
if riseInterval < 0.0001:
    riseInterval = 0.0001
stepTemp = currentTemp + riseInterval

print('Starting Temp:' + str(startingTemp))
print('Target Temp:' + str(setTemp))
print('Temp Rise Limit(deg/min):' + str(tempRiseRateLimit))
print('Temp Rise Interval(deg/s):' + str(riseInterval))
print('Element Duty Cycle(on/off)(s):' + str(onDutyTime) + '/' + str(offDutyTime))

#rising
while rising == 1:
        #print('On:'+str(onDutyCnt)+'--Off:'+str(offDutyCnt))
	reportCounter += 1
	currentTemp = sensor.readTempC()
        #if currentTemp < stepTemp:
	#	#element.on()
        #        elementState=1
	#if currentTemp > stepTemp+highTolerance:
	#	#element.off()
        #        elementState =0
        elementState=1
	stepTemp += riseInterval
	if stepTemp > setTemp:
		stepTemp = setTemp
	if currentTemp >= setTemp:
		rising = 0
        if reportCounter >= reportInterval:
            print('Rising' + str(elementState) + '... Current temp:' + str(currentTemp) + 'C Set Temp:' + str(stepTemp) + 'C RiseTime:' + str(runTime) + 's of ' + str(riseTime) + 's')
            reportCounter = 0
        element_control()
	sleep(sleepInterval)
	runTime += sleepInterval
#soak
startSoak = runTime
while soaking == 1:
        reportCounter += 1
        currentTemp = sensor.readTempC()
        if currentTemp < setTemp-lowTolerance:
                element.on()
                elementState=1
        if currentTemp > setTemp+highTolerance:
                element.off()
                elementState=0
        
        if runTime - startSoak >= soakTime:
        	soaking = 0
		print('Firing Completed in ' + str(runTime) + 's of ' + str(totalTime) + 's')
		element.off()
	else:
                if reportCounter >= reportInterval:
        	        print('Soaking'+ str(elementState) + '... Current temp:' + str(currentTemp) + 'C Set Temp:' + str(setTemp) + 'C SoakTime:' + str(runTime-startSoak) + 's of ' + str(soakTime) + 's')
                        reportCounter = 0
                #element_control()
        	sleep(sleepInterval)
		runTime += sleepInterval
