# pico-panic
Networked panic button via Pi Picos over MQTT

Two seperate versions for
1) Pi Pico with latching emergency switch 
2) Pi Pico with relay and alarm siren setup


## Both Picos

- Start an internal AP if configuration file not found on the Pico, or if 'reset' button pressed on `GPIO15`
- Upon form submission (NOT SECURED), submits WiFi credentials, MQTT server/client details & alarm timeout & reboots Pico
- Updates users visibly via external LEDs on wifi connection status, MQTT status & current alarm status through `GPIO8, GPIO9, GPIO18`
- Pings MQTT every 15 seconds, attempts to reconnect to MQTT/Wifi upon issue, last restort reboot if this is not successful


## Button Pico

- Checks for closed circuit on `GPIO14`
- Posts 'Raise alarm' MQTT message after detected button pushed on `GPIO14`
- Posts 'Cancel alarm' MQTT message after 60s or button detected reset (whichever is first)

## Alarm Pico

- Checks for messages on MQTT server
- If alarm raised message found, switch on relay via `GPIO7`
- If alarm cancelled message found or elapsed alarm time 60s, switch off relay via `GPIO7`
