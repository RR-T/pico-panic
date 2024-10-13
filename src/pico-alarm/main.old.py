import network
import time
from machine import Pin
from umqtt.simple import MQTTClient

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
        time.sleep(30)

def mqtt_connect(client_id, mqtt_server):
    client = MQTTClient(client_id, mqtt_server, keepalive=3600)
    client.connect()
    print(f'Connected to {mqtt_server} MQTT Broker')#%(mqtt_server))
    mqttClient.set_callback(sound_alarm)
    return(client)

def sound_alarm(topic, msg):
    

def reset_pico():
   print('Failed to connect to the MQTT Broker. Reconnecting...')
   time.sleep(5)
   machine.reset()

def ping_mqtt(client):
    try:
        client.ping()
        print(client.ping())
        print('mqtt conn tested')
    except OSError as e:
       reset_pico()

def read_mqtt_stream(client):
    try:
    except OSError as e:
        ping_mqtt(client)
        
def check_button(button):
    if button.value() == 0:
        return(True)
    else:
        return(False)

def raise_alarm(client):
    client.publish('crash/alarm','ALARM RAISED')

def cancel_alarm(client):
    client.publish('crash/alarm','ALARM CANCELLED')

def run(client, emergency_button, alarm_max_time):
    new_tick = True
    alarm_sounding = False
    alarm_timeout = False
    #alarm_button_pressed = False
    while True:
        if new_tick:
            tick = time.ticks_ms()
            new_tick = False
        else:
            tock = time.ticks_ms()
            if(time.ticks_diff(tock, tick)/1000 > 10 and not alarm_sounding):
                ping_mqtt(client)
                new_tick = True
        
        alarm_called = check_messages(client) #check_button(emergency_button)
        if(alarm_called):
            switch_led('alternate','LED')
            print('Alarm called by button pico')
            if(alarm_sounding and not alarm_timeout):
                # If the alarm is currently ringing without timing out
                alarm_sounding_tock = time.ticks_ms()
                if(time.ticks_diff(alarm_sounding_tock, alarm_sounding_tick)/1000 > alarm_max_time): # alarm on for x seconds
                    print('Alarm has been on for 60s, cancelling')
                    alarm_timeout = True
                    alarm_sounding = False
                    cancel_alarm(client)
                    # silence alarm
            elif(not alarm_timeout):
                print('First notice of alarm, notify all')
                alarm_sounding = True
                alarm_sounding_tick = time.ticks_ms()
                raise_alarm(client)
                #continue #raise all hell!!!!!
        elif(alarm_sounding and not alarm_called):
            print('Alarm is on but button no longer pressed, cancelling')
            alarm_sounding = False
            cancel_alarm(client)
            # silence alarm
        else:
            switch_led('off','LED')
            
        if alarm_timeout and not alarm_button_pressed: # Reset timeout once button reset
            print('Alarm timedout, and now button not pressed so resetting')
            alarm_timeout = False
        
        time.sleep(0.1)
        
if(__name__ == "__main__"):
    try:
        #emergency_button = set_io(14)
        wlan_connect()
        mqtt_server = '10.50.10.124'
        client_id = 'pico-alarm1'
        msg_subscription = b'crash/alarm'
        #msg_stop_topic = b'alarm/stop'
        #topic_msg = b'test'
        alarm_max_time = 60 # seconds
        client = mqtt_connect(client_id, mqtt_server)
        run(client, msg_subscription, alarm_max_time)
    except Exception as e:
        print(e)
        reset_pico()

