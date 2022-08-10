# Author: Haiwen Zhang
# Created at: 2021/12/2

from machine import Pin
from machine import Timer
from machine import I2C
import machine
from machine import Pin, SoftI2C
import urequests as requests
import json
import ustruct

green = Pin(26, Pin.OUT)
red = Pin(25, Pin.OUT)

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('FiveStarFlag404', 'Alita@527')
        while not wlan.isconnected():
            pass
    
    print('Connected to FiveStarFlag404\nIP Adress: ' +  str(wlan.ifconfig()[0]))

do_connect()

############################################################################################################
def http_get(url):
    import socket
    _, _, host, path = url.split('/', 3)
    addr = socket.getaddrinfo(host, 80)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    data_str = ''
    while True:
        data = s.recv(100)
        if data:
            data_str = data_str + (str(data, 'utf8'))
        else:
            break
    s.close()
    return data_str
############################################################################################################
# Read sensor state from ThingSpeak every 30s
tim0 = Timer(0)
tim3 = Timer(3)
def turn_off(timer):
    if sensor_state != 0:
            print("Sensor is deavtivated.")
    sensor_state = 0
    green.off()
    red.off()
    
sensor_state = 0
def read_data(timer):    
    data_str = http_get('https://api.thingspeak.com/channels/1587078/status?api_key=SQBX91NE2T2J9196&results=1')
    global sensor_state
    if data_str.find('deactivate') != -1:
        if sensor_state != 0:
            print("Sensor is deavtivated.")
        sensor_state = 0
        green.off()
        red.off()
    elif data_str.find('activate') != -1:
        if (sensor_state != 1):
            print("Sensor is activated.")
        sensor_state = 1
        tim3.init(period=60000, mode=Timer.ONE_SHOT, callback=turn_off) #turn off the sensor after 60s if not get activate status during this period
        green.on()
        
read_data(tim0)        
tim0.init(period=30000, mode=Timer.PERIODIC, callback=read_data)
###############################################################################################################

def twosCom_binDec(bin, digit): # function converting from bianry to 2's complement in decimal
        while len(bin)<digit :
                bin = '0'+bin
        if bin[0] == '0':
                return int(bin, 2)
        else:
                return -1 * (int(''.join('1' if x == '0' else '0' for x in bin), 2) + 1)

################################################################################################################

i2c = SoftI2C(scl=Pin(22), sda=Pin(23), freq=4000)

i2c.scan()      

address = 83 # This is the I2C adress of motion sensor

i2c.writeto_mem(address, 0x2D, b'\x08') # turn on measure
i2c.writeto_mem(address, 49, b'\x08')
i2c.writeto_mem(address, 0x2c, b'\x0c')
i2c.writeto_mem(address, 30, b'\x00')
i2c.writeto_mem(address, 31, b'\x00')
i2c.writeto_mem(address, 32, b'\x00')


x_data = int.from_bytes(i2c.readfrom_mem(address, 0X32, 2), "little", False)
y_data = int.from_bytes(i2c.readfrom_mem(address, 0X34, 2), "little", False)
z_data = int.from_bytes(i2c.readfrom_mem(address, 0X36, 2), "little", False)

x_binary = str(bin(x_data))
x_trim = x_binary.replace('0b', '')
y_binary = str(bin(y_data))
y_trim = y_binary.replace('0b', '')
z_binary = str(bin(z_data))
z_trim = z_binary.replace('0b', '')

x_value = twosCom_binDec(x_trim, 16)
y_value = twosCom_binDec(y_trim, 16)
z_value = twosCom_binDec(z_trim, 16)

x_off = -round((x_value*1000)/3993)
y_off = -round((y_value*1000)/3993)
z_off = -round(((z_value-256)*1000)/3993)

if (x_off < 255 and y_off < 255 and z_off < 255):
    i2c.writeto_mem(address, 30, bytes([x_off])) 
    i2c.writeto_mem(address, 31, bytes([y_off]))
    i2c.writeto_mem(address, 32, bytes([z_off]))

print("Sensor initialization and Calibration completed!!")

###########################################################################
# After turning on red light, let it on for 5 sec and turn it off
tim1 = Timer(1)
def red_control(timer):
    red.off()
     
###########################################################################
# After sending a notification time will be set to 1, after 5 sec reset to 0, only send notificatio when time is 0
# This is for preventing sending message to often
do_not_send = 0
tim2 = Timer(2)
def reset(timer):
    global do_not_send
    do_not_send = 0
############################################################################

while True:
    if sensor_state == 1:
        
        x_data = int.from_bytes(i2c.readfrom_mem(address, 0X32, 2), "little", False)
        y_data = int.from_bytes(i2c.readfrom_mem(address, 0X34, 2), "little", False)
        z_data = int.from_bytes(i2c.readfrom_mem(address, 0X36, 2), "little", False)

        x_binary = str(bin(x_data))
        x_trim = x_binary.replace('0b', '')
        y_binary = str(bin(y_data))
        y_trim = y_binary.replace('0b', '')
        z_binary = str(bin(z_data))
        z_trim = z_binary.replace('0b', '')

        x_value = twosCom_binDec(x_trim, 16) / 256
        y_value = twosCom_binDec(y_trim, 16) /256
        z_value = twosCom_binDec(z_trim, 16) / 256
        
        if x_value >= 0.1 or x_value <= -0.1 or y_value >= 0.1 or y_value <= -0.1 or z_value >= 1.1 or z_value <= 0.9:
                red.on()
                tim1.init(period=5000, mode=Timer.ONE_SHOT, callback=red_control)
                if do_not_send == 0:
                    print("Motion detected, sending notification")
                    url = "https://maker.ifttt.com/trigger/motion_detected/with/key/dli9MaBYZlkrrg8rMG3OBc"
                    json = {"value1": str(round(x_value,1)), "value2": str(round(y_value,1)), "value3": str(round(z_value,1))}
                    r = requests.post(url,json=json)
                    r.close()
                    do_not_send = 1
                    tim2.init(period=5000, mode=Timer.ONE_SHOT, callback=reset)
                
        
        #print('x: ' + str(round(x_value,1))  + 'y: ' + str(round(y_value,1)) + ' ' + 'z: ' + str(round(z_value,1)))






























