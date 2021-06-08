import sys
import Adafruit_MAX31855.MAX31855 as MAX31855

from gpiozero import OutputDevice
from time import sleep

#global variable init
#GPIO HW interface stuff
CLK = 22
CS  = 27
DO  = 17
sensor = MAX31855.MAX31855(CLK, CS, DO)
element = OutputDevice(23)

#misc globals

runTime = 1
currentTemp = 0
stepTemp = 0
riseInterval = 1
sleepInterval = 1
reportCounter = 0
rising = 1
soaking = 1
elementState = 0
startingTemp = 0

#varibles used to control the ramp up duty cycle
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
elementToggle=1

#read the current temp and save the starting temp
currentTemp = sensor.readTempC()
startingTemp = currentTemp


argcnt = len(sys.argv)
if argcnt == 9:
    setTemp = float(sys.argv[1])
    riseTime = float(sys.argv[2])
    soakTime = float(sys.argv[3])
    lowTolerance = float(sys.argv[4])
    highTolerance = float(sys.argv[5])
    reportInterval = int(sys.argv[6])
    onDutyTime= int(sys.argv[7])
    offDutyTime = int(sys.argv[8])
else:
    #command line arguments appear invalid
    sys.exit("Invalid Argument: kiln.py <settemp> <risetime> <soaktime> <lowtemptolerance> <hightemptolerance> <reportinterval> <onDutyTime> <offDutyTime>")
    #end of program

#define the incremental temp rise for ramp settings
riseInterval = round((setTemp -currentTemp)/riseTime,4)

#clamp interval
if riseInterval < 0.0001:
    riseInterval = 0.0001

#set speed limit for temp rise in deg/minute
tempRiseRateLimit = riseInterval * 60

#set next temp target for ramp up
stepTemp = currentTemp + riseInterval

totalTime = soakTime + riseTime

#cmd line arguments appear valid, all variable set, report parameters and begin
print('Fire Parameters: SetTemp:' + str(setTemp) + 'c RiseTime:' + str(riseTime) + 's SoakTime:' + str(soakTime) + 's')
print('Starting Temp:' + str(startingTemp))
print('Temp Rise Limit(deg/min):' + str(tempRiseRateLimit))
print('Temp Rise Interval(deg/s):' + str(riseInterval))
print('Element Duty Cycle(on/off)(s):' + str(onDutyTime) + '/' + str(offDutyTime))


#Define a few functions
#degc to degf
def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0
      
#Checks the Rise Rate and adjusts the element's on/off duty cycle to maintain a smooth temp rise.
def check_rates():
    global tempRiseRate
    global onDutyTime
    global offDutyTime
    global stepTemp

    #Calculate the current rise rate for the entire ramp thus far
    tempRiseRate = ((currentTemp - startingTemp)/runTime)*60
    tempDifferential = abs(currentTemp - stepTemp)
    #Set the duty cycle modifier value to be the rounded absolute value of Rise Rate - the Rise Rate Limit
    cycleMod = abs(tempRiseRate-tempRiseRateLimit)
    
    #Rise Rate is too SLOW
    if tempRiseRate < tempRiseRateLimit:
        #increase onDutyTime/decrease offDutyTime
        if onDutyTime < maxElementOnTime:
	    #onDutyTime can be increased
            onDutyTime += cycleMod
        else:
	    #onDutyTime is maximum, attempt to decrease offDutyTime
            if offDutyTime > minElementOffTime:
	        #offDutyTime can be decreased
                offDutyTime -= cycleMod
    
    #Rise Rate is too FAST        
    if tempRiseRate > tempRiseRateLimit:
        #decrease onDutyTime/increase offDutytime
        if onDutyTime > minElementOnTime:
            #onDutyTime can be decreased
            onDutyTime -= cycleMod
        else:
	    #onDutyTime is at minimum, attempt to increase offDutyTime
            if offDutyTime < maxElementOffTime:
		#offDutyTime can be increased
                offDutyTime += cycleMod

    if offDutyTime > minElememtOffTime:
        if tempDifferential > 5:
            offDutyTime -= cycleMod

    #report rise rate and limit
    print('Current Rise Rate/Limit:' + str(tempRiseRate) + '/' + str(tempRiseRateLimit))
    #Report Duty Cycle adjustments
    print('Element Duty Cycle(on/off)(s):' + str(onDutyTime) + '/' + str(offDutyTime))

#Toggles the element accourding to the duty cycle settings during ramp up.
def element_control():
    global onDutyCnt
    global offDutyCnt
    global elementToggle
    
    #increment cycle counters
    onDutyCnt += 1
    offDutyCnt +=1
    
    #Toggle element on / off
    if elementToggle == 1:
	#element should be on
        if onDutyCnt < onDutyTime:
	    #turn it on
            element.on()
        else:
	    #on cycle has ended
            elementToggle=0
            #reset the off duty cycle counter
            offDutyCnt = 0
    else:            
	#element should be off
        if offDutyCnt < offDutyTime:
	    #turn it off
            element.off()
        else:
	    #off cycle has ended
            elementToggle=1
            #reset the on duty cycle counter
            onDutyCnt = 0
            
            #check and adjust the duty cycle settings based on the Rise Rate and the Rise Rate Limit
            check_rates()

#rising
while rising == 1:
	#read the current temp from the thermocouple
	currentTemp = sensor.readTempC()
	
	#set this iteration's target temp
	stepTemp += riseInterval
	
	#Clamp the stepTemp to the Target Soak Temp
	if stepTemp > setTemp:
		stepTemp = setTemp
	
	#Check if we've reached the Target Soak Temp
	if currentTemp >= setTemp:
		rising = 0
	
	#Status report
	reportCounter += 1
        if reportCounter >= reportInterval:
            print('Rising - ' + str(elementToggle) + '... Current temp:' + str(currentTemp) + 'C Set Temp:' + str(stepTemp) + 'C RiseTime:' + str(runTime) + 's of ' + str(riseTime) + 's')
            reportCounter = 0
        
        #Adjust Element
        element_control()
	
	#Sleep for a sec
	sleep(sleepInterval)
	
	#Increment the cook time counter
	runTime += sleepInterval
	
#soak
startSoak = runTime
while soaking == 1:
	#Soak cycle
        #read current temp
        currentTemp = sensor.readTempC()
        
        #Switch element on or off depending on temp and tolerance settings
        if currentTemp < setTemp-lowTolerance:
		#temp too LOW, turn on element
                element.on()
                elementState=1
                
        if currentTemp > setTemp+highTolerance:
		#temp too HIGH, turn off element
                element.off()
                elementState=0
        
        if runTime - startSoak >= soakTime:
        	#Firing complete
        	soaking = 0
		print('Firing Completed in ' + str(runTime) + 's of ' + str(totalTime) + 's')
		element.off()
		#End of program
	else:
		#Soak still in progress
		#Status Report
		reportCounter += 1
                if reportCounter >= reportInterval:
        	        print('Soaking - '+ str(elementState) + '... Current temp:' + str(currentTemp) + 'C Set Temp:' + str(setTemp) + 'C SoakTime:' + str(runTime-startSoak) + 's of ' + str(soakTime) + 's')
                        reportCounter = 0
		#Sleep for a sec
		sleep(sleepInterval)
	
		#Increment the cook time counter
		runTime += sleepInterval
