
## 1. Wiring
For wiring, see [NeoPIO: Drive lots of LEDs with Raspberry Pi Pico](https://learn.adafruit.com/neopio-drive-lots-of-leds-with-raspberry-pi-pico/wiring-and-code).

## 2. Software
### CircuitPython
Tested with CircuitPython 9.x.
See [Installing CircuitPython](https://learn.adafruit.com/neopio-drive-lots-of-leds-with-raspberry-pi-pico/installing-circuitpython) in the above guide.

### Libraries
Uses NeoPIO library from Adafruit and the following dependencies. Put them under `/lib` on your pico:

![image](https://github.com/user-attachments/assets/5d62e221-c5bb-45b3-bf53-dc1af161fef6)

You can get them [precompiled for CircuitPython](https://circuitpython.org/libraries).

### Wifi Configuration
The code pulls WiFi SSID and password from a separate file, `settings.toml`. It is a plain text file. Create one in the root folder, with the following contents:

```
CIRCUITPY_WIFI_SSID="your-wifi-ssid"
CIRCUITPY_WIFI_PASSWORD="your-wifi-password"
```
(replace with your own SSID and password)

### Receiver code
Copy the Python files from this repository into the root folder of your Pi Pico, and reboot.

The Pico will attempt to connect to WiFi, update time from NTP, and wait for incoming packets on UDP port `5705`.


