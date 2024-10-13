import network
import time
from machine import Pin
from umqtt.robust2 import MQTTClient

# this version is for the alarm only pico
def set_io(pin_no):
    button = Pin(pin_no, Pin.IN, Pin.PULL_UP)
    return(button)

def switch_led(switch, pin_num):
    led = Pin(pin_num, Pin.OUT)
    if switch == 'alternate':
        if led.value():
            led.value(False)
        else:
            led.value(True)
    elif switch == 'off':
        led.value(False)
    elif switch == 'on':
        led.value(True)
        
def wlan_connect():
    switch_led('on','LED')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    while 1:
        wlan.connect("RT","wamozart")
        time.sleep(5)
        if(wlan.isconnected()):
            print("WiFi connected successfully")
            switch_led('off','LED')
            break
        else:
            print('Failed to connect to wifi')
        time.sleep(30)

def mqtt_connect(client_id, mqtt_server):
    client = MQTTClient(client_id, mqtt_server, keepalive=30)
    client.DEBUG = True
    client.MSG_QUEUE_MAX = 10
    client.connect()
    #client.subscribe('crash/alarm')
    print(f'Connected to {mqtt_server} MQTT Broker')#%(mqtt_server))
    return(client)

def reset_pico():
   print('Failed to connect to the MQTT Broker. Reconnecting...')
   time.sleep(5)
   machine.reset()

def ping_mqtt(client):
    try:
        client.ping()
        print(client.ping())
        print('mqtt conn tested')
        #client.check_msg()
        #print('mqtt checked msg')
    except OSError as e:
       reset_pico()

def check_button(button):
    if button.value() == 0:
        return(True)
    else:
        return(False)

def raise_alarm():
    switch_led('on','LED')
    #client.publish('crash/alarm','ALARM RAISED')

#def cancel_alarm(client):
#    client.publish('crash/alarm','ALARM CANCELLED')

def check_message(client):
    pass

def msg_received(topic, msg, s1, s2):
    print('oh tit wanks oh dear!!!')
    print(f"{topic} - {msg} - {s1} - {s2}")
    if msg == b'ALARM RAISED':
        raise_alarm()
        print('alarm raised')
        #client.check_msg()
        alarm_rung(client, time.ticks_ms())
        return('ahhhh')
        #
    elif msg == b'ALARM CANCELLED':
        cancel_alarm()
        print('cancelled')
    
def alarm_rung(client, start_tick):
    alarm = True
    #client.set_callback(msg_receive
    while alarm:
        tock = time.ticks_ms()
        client.check_msg()
        time.sleep(0.5)
        if(time.ticks_diff(tock, start_tick)/1000 > 60):
            print('alarm timeout - cancelling')
            cancel_alarm()
            alarm = False
        
def cancel_alarm():
    switch_led('off','LED')
    
def run(client, emergency_button, alarm_max_time):
    new_tick = True
    alarm_sounding = False
    alarm_timeout = False
    alarm_button_pressed = False
    while True:
        if new_tick:
            tick = time.ticks_ms()
            new_tick = False
        else:
            tock = time.ticks_ms()
            if(time.ticks_diff(tock, tick)/1000 > 10 and not alarm_button_pressed):
                if client.is_conn_issue():
                    print('its feked')
                    while client.is_conn_issue():
            # If the connection is successful, the is_conn_issue
            # method will not return a connection error.
                        client.reconnect()
                    if alarm_sounding:
                        cancel_alarm(client)
                ping_mqtt(client)
                #client.check_msg()
                #wlan = network.WLAN(network.STA_IF)
                #if(wlan.isconnected()):
                #    print("WiFi still connected")
                new_tick = True
        client.check_msg()
#        alarm_button_pressed = check_button(emergency_button)
#         if(alarm_button_pressed):
#             switch_led('alternate','LED')
#             print('Alarm button has been pressed')
#             if(alarm_sounding and not alarm_timeout):
#                 # If the alarm is currently ringing without timing out
#                 alarm_sounding_tock = time.ticks_ms()
#                 if(time.ticks_diff(alarm_sounding_tock, alarm_sounding_tick)/1000 > alarm_max_time): # alarm on for x seconds
#                     print('Alarm has been on for 60s, cancelling')
#                     alarm_timeout = True
#                     alarm_sounding = False
#                     cancel_alarm(client)
#                     # silence alarm
#             elif(not alarm_timeout):
#                 print('First notice of alarm, notify all')
#                 alarm_sounding = True
#                 alarm_sounding_tick = time.ticks_ms()
#                 raise_alarm(client)
#                 #continue #raise all hell!!!!!
#         elif(alarm_sounding and not alarm_button_pressed):
#             print('Alarm is on but button no longer pressed, cancelling')
#             alarm_sounding = False
#             cancel_alarm(client)
#             # silence alarm
#        else:
#            switch_led('off','LED')
            
        if alarm_timeout and not alarm_button_pressed: # Reset timeout once button reset
            print('Alarm timedout, and now button not pressed so resetting')
            alarm_timeout = False
        
        time.sleep(0.5)
        
if(__name__ == "__main__"):
    try:
        emergency_button = set_io(14)
        wlan_connect()
        mqtt_server = '10.50.10.66'
        client_id = 'pico-alarm-1'
        msg_start_topic = b'alarm/start'
        msg_stop_topic = b'alarm/stop'
        topic_msg = b'test'
        alarm_max_time = 60 # seconds
        client = mqtt_connect(client_id, mqtt_server)
        client.set_callback(msg_received)
        client.subscribe('crash/alarm')
        run(client, emergency_button, alarm_max_time)
    except Exception as e:
        print(e)
        reset_pico()
