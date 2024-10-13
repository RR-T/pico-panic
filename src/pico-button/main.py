import network
import time
from machine import Pin
from umqtt.robust2 import MQTTClient
import requests
import usocket as socket
import ujson as json

# this version is for the button pico
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


def switch_external_led(switch, led_type):
    print('ext called', switch, led_type)
    led_types = {'red':18, 'orange':8, 'green':9}
    pin_num = led_types.get(led_type,18)
    print(pin_num)
    led = Pin(pin_num, Pin.OUT)
    #led.toggle()
    if switch == 'alternate':
        if led.value():
            led.value(False)
        else:
            led.value(True)
    elif switch == 'off':
        led.value(False)
    elif switch == 'on':
        led.value(True)
        
def wlan_connect(params):
    switch_external_led('on', 'red')
    switch_led('on','LED')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    count = 0
    while 1:
        count +=1
        wlan.connect(params['ssid'],params['ssid_password'])
        time.sleep(5)
        if(wlan.isconnected()):
            print("WiFi connected successfully")
            switch_external_led('off', 'red')
            switch_led('off','LED')
            break
        elif count > 3:
            reset_pico()
        else:
            print('Failed to connect to wifi')
        time.sleep(30)


def mqtt_connect(client_id, mqtt_server):
    client = MQTTClient(client_id, mqtt_server, keepalive=30)
    client.DEBUG = True
    client.MSG_QUEUE_MAX = 10
    client.connect()
    
    print(f'Connected to {mqtt_server} MQTT Broker')#%(mqtt_server))
    return(client)


def reset_pico():
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

def raise_alarm(client):
    client.publish('crash/alarm','ALARM RAISED', retain=True)

def cancel_alarm(client):
    client.publish('crash/alarm','ALARM CANCELLED', retain=True)
    switch_led('off','LED')
    switch_external_led('off', 'orange')

def web_page():
    html = '''
<html>
    <head>
        <title>JVV alarm config</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <h1>JVV pi pico alarm setup (with button)</h1>
    
    <form action="./saveparams" method="get">
        <h3>Wifi details</h2>
        <input type="text" name="ssid" placeholder="ssid name" size="30" required>&nbsp;&nbsp;
        <input type="password" name="ssid_password" placeholder="ssid password" size="20" required><br><br>
        <h3>IP address of MQTT server</h3>
        <input type="text" name="mqtt_server" placeholder="10.0.0.0" size="15" required><br><br>
        <h3>Physical location of pico</h3>
        <input type="text" name="location" placeholder="cat-clinic-lab" size="15" required><br><br>
        <h3>Alarm max time (s)</h3>
        <input type="number" name="alarm_time" step="1" value="60" min="10" max="500" required><br><br><br><br>
        <button type="submit" name="Submit params">
            Submit params
        </button>
    </form>
    </body>
</html>
    '''
    return(html)


def confirmed_page(ssid, mqtt_id, mqtt_server):
    html = f'''
<html>
    <head>
        <title>JVV alarm (button) config</title>
    </head>
    <body>
        <h1>Details submitted</h1>
        <p>Rebooting and connecting to SSID: {ssid} in 10 seconds</p>
        <p>ID of pi for mqtt: {mqtt_id}</p>
        <p>IP of mqtt server: {mqtt_server}</p>
    </body>
</html>
    '''
    return(html)


def ap_mode(ssid, password):
    # Create an AP
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    switch_external_led('off', 'green')
    switch_external_led('on', 'orange')

    while ap.active() == False:
        pass
    print('AP Mode Is Active, You can Now Connect')
    print('IP Address To Connect to:: ' + ap.ifconfig()[0])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creating socket object
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)

    new_tick = True
    while True:
        if new_tick:
            tick = time.ticks_ms()
            new_tick = False
        tock = time.ticks_ms()
        if(time.ticks_diff(tock, tick)/1000 > 2):
            switch_external_led('alternate', 'orange')
            print('tocked')
        conn, addr = s.accept()
        submitted = False
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        try:
            print(request.GET.get('ssid'))
        except:
            print('oh')
        print('Content = %s' % str(request))
        decoded_request = request.decode('UTF-8')
        request_list=decoded_request.split()
        for part in request_list:
            print(part)
            if "?" and "Submit" in part:
                params = parse_params(part)
                print(params)
                submitted = True
                
            #if params:
            #    print(f"Params: {params}\n")
        print(request_list, 'reqeust list')
        if submitted:
            ssid = params['ssid']
            mqtt_server = params['mqtt_server']
            params = save_data(params)
            mqtt_id = params['mqtt_id']
            response = confirmed_page(ssid, mqtt_id, mqtt_server)
            time.sleep(5)
        else:
            
            response = web_page()
        conn.send(response)
        conn.close()
        if submitted:
            break
        #time.sleep(0.1)


def parse_params(part):
    parameters = {}
    part = part[part.find('?')+1:]
    for piece in part.split("&"):
        amp_split = piece.split("&")
        for param_set in amp_split:
            eq_split = param_set.split("=")
            parameters[eq_split[0]] = eq_split[1]
    return parameters
        
    
def check_data():
    try:
        with open('params.json', 'r') as f:
            data = json.load(f)
            return(data, True)
    except:
        print("Params file not found or error opening")
        return('', False)
        

def save_data(params):
    try:
        params['mqtt_id'] = f"pico-button-{params['location']}"
        with open('params.json', 'w') as f:
            json.dump(params, f)
        return(params)
    except:
        print("Could not save the button state variable.")
    
    
def run(client, emergency_button, config_button, alarm_max_time):
    new_tick = True
    alarm_sounding = False
    alarm_timeout = False
    alarm_button_pressed = False
    cancel_alarm(client)
    switch_external_led('on', 'green')
    while True:
        if new_tick:
            tick = time.ticks_ms()
            new_tick = False
        else:
            tock = time.ticks_ms()
            #print('not ready')
            if(time.ticks_diff(tock, tick)/1000 > 15):
                while client.is_conn_issue():
                    print('there is an issue')
                    switch_external_led('off', 'green')
                    switch_external_led('alternate', 'red')
                    client.reconnect()
                    print(f'{client.is_conn_issue()} conn issue now, counter: {issue_counter}')
                    time.sleep(1)
                    issue_counter += 1
                    if issue_counter > 5:
                        reset_pico()
                    if not client.is_conn_issue():
                        switch_external_led('on', 'green')
                        switch_external_led('off', 'red')
                client.ping()
                client.check_msg()
                #print(client.is_keepalive())
                issue_counter = 0
                wlan = network.WLAN(network.STA_IF)
                if not wlan.isconnected():
                    switch_external_led('on', 'red')
                    print("WiFi conn issue!")
                    time.sleep(5)
                    reset_pico()
                new_tick = True
            
            
        alarm_button_pressed = check_button(emergency_button)
        setup_button_pressed = check_button(config_button)
        if(alarm_button_pressed):
            switch_led('alternate','LED')
            switch_external_led('alternate', 'orange')
            print('Alarm button has been pressed')
            if(alarm_sounding and not alarm_timeout):
                # If the alarm is currently ringing without timing out
                alarm_sounding_tock = time.ticks_ms()
                if(time.ticks_diff(alarm_sounding_tock, alarm_sounding_tick)/1000 > alarm_max_time): # alarm on for x seconds
                    print(f'Alarm has been on for {alarm_max_time}s, cancelling')
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
        elif(alarm_sounding and not alarm_button_pressed):
            print('Alarm is on but button no longer pressed, cancelling')
            alarm_sounding = False
            switch_led('off','LED')
            switch_external_led('off', 'orange')
            cancel_alarm(client)
            # silence alarm
            
        if alarm_timeout and not alarm_button_pressed: # Reset timeout once button reset
            print('Alarm timedout, and now button not pressed so resetting')
            alarm_timeout = False

        if setup_button_pressed:
            ap_mode('sos-button','mgct1234')
            time.sleep(5)
            reset_pico()
            
        
        time.sleep(0.25)
        
if(__name__ == "__main__"):
    try:
        switch_external_led('off', 'green')
        switch_external_led('off', 'red')
        switch_external_led('off', 'orange')
        params, params_collected = check_data()
        config_button = set_io(15)
        setup_button_pressed = check_button(config_button)
        if setup_button_pressed:
            params_collected = False
        if not params_collected:
            # start ap mode
            ap_mode('sos-button','mgct1234')
            time.sleep(5)
            reset_pico()
        else:
            print(params)
        last_msg=b""
        emergency_button = set_io(14)
        wlan_connect(params)
        mqtt_server = params['mqtt_server']
        client_id = params['mqtt_id']
        msg_start_topic = b'alarm/start'
        msg_stop_topic = b'alarm/stop'
        topic_msg = b'test'
        alarm_max_time = int(params['alarm_time']) # seconds
        client = mqtt_connect(client_id, mqtt_server)
        run(client, emergency_button, config_button, alarm_max_time)
    except Exception as e:
        print(e)
        reset_pico()
