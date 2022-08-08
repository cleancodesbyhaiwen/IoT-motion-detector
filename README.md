# IoT motion detector
 
## This program is written for ESP32

Hardware connection:
green led is connected to Pin26
red led is connected to Pin25

Work Flow:
The program first connect to the wifi..
then get the desired state of the sensor (activate/deavtivate) from ThingSpeak every 30s
then change sensor_state variable to 0/1 correspondingly and turn on/off green led
the sensor turn off automatically after its turned on for 60s is didn't get activate state during the 60s
if deactivating sensor and red led is on, turn off red led along with green led

connect to motion sensor through I2C protocal 
through testing, we already know that the slave address of motion sensor is 83
turn on the measuring of motion and calibrate x,y,z axis acceleration
then is sensor_state is 1, under a while loop constantly measuring x,y,z acceleration
if acceleration is out of range meaning there is a suspicious movement
then turn on red led (red led will turn off automatically 5 sec after it's turned on)
send notification with x,y,z acceleration to IFTTT app
there is a timer that prevent sending another message after sending one message
this is preventing message overflow on the app

Link to the video:
https://www.youtube.com/watch?v=LPqw6yXNlpE
