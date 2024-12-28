# SPDX-FileCopyrightText: 2021 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

from adafruit_led_animation.helper import PixelMap
#from adafruit_led_animation.group import AnimationGroup
#from adafruit_led_animation.sequence import AnimationSequence


from neopio import NeoPIO
from ringbuffer import RingBuffer
from micropython import const
import board
import microcontroller
import gc
import time
import os
import rtc
import socketpool
import wifi
import struct
import errno

import adafruit_ntp

# Customize for your strands here
_NUM_STRANDS = const(4)
_STRAND_LENGTH = const(50)
_NS_PER_MS = const(1000000)

print( "Available memory after imports: {} bytes".format(gc.mem_free()) )

# Make the object to control the pixels
pixels = NeoPIO(
    board.GP0,
    board.GP1,
    board.GP2,
    _NUM_STRANDS * _STRAND_LENGTH,
    num_strands=_NUM_STRANDS,
    auto_write=False,
    brightness=0.5,
    pixel_order="RGB"
)

print( "Available memory after neopio: {} bytes".format(gc.mem_free()) )

one_long_strip = PixelMap(pixels, range(_STRAND_LENGTH * _NUM_STRANDS), individual_pixels=True)

rb = RingBuffer(30*2)   # 30fps *2 secs


class RpiPicoTime:
    def __init__(self, pool):
        self.ntp = adafruit_ntp.NTP(pool, server="time.windows.com", tz_offset=0, cache_seconds=3600)
        self.utc_epoch_ns = self.ntp.utc_ns
        self.ts_ref_ns = time.monotonic_ns()
        self.iter = 0
        rtc.RTC().datetime = self.ntp.datetime
        print("RpiPicoTime: self.utc_epoch_ns=" + str(self.utc_epoch_ns) + ", self.ts_ref_ns=" + str(self.ts_ref_ns) + ".")

    def ns_since_epoch(self) -> int:
        self.iter += 1
        now = time.monotonic_ns()
        if self.iter == 200 or self.iter == 201:
            print("now - self.ts_ref_ns = " + str(now - self.ts_ref_ns))
            print("self.utc_epoch_ns + (now - self.ts_ref_ns) = " + str(self.utc_epoch_ns + (now - self.ts_ref_ns)))
            print("int(self.utc_epoch_ns + (now - self.ts_ref_ns)) = " + str(int(self.utc_epoch_ns + (now - self.ts_ref_ns))))
            print("int(self.utc_epoch_ns + (now - self.ts_ref_ns)) / 1000000 = " + str(int(self.utc_epoch_ns + (now - self.ts_ref_ns)) / 1000000))
            pass
            #print("now=" + str(now))
        return int(self.utc_epoch_ns + (now - self.ts_ref_ns))



wifi_ssid = os.getenv("CIRCUITPY_WIFI_SSID")
wifi_password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
if wifi_ssid is None:
    print("WiFi credentials are kept in settings.toml, please add them there!")
    raise ValueError("SSID not found in environment variables")

try:
    wifi.radio.connect(wifi_ssid, wifi_password)
except ConnectionError:
    print("Failed to connect to WiFi with provided credentials")
    raise

print("Connected to Wifi "+ str(wifi_ssid))

pool = socketpool.SocketPool(wifi.radio)

pt = RpiPicoTime(pool)

print("Local time is: " + str(time.localtime()))

udp_socket = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
udp_socket.bind(('', 5705))
udp_socket.setblocking(False)
print("Bound to UDP port 5705")

ts_start = time.monotonic_ns()
#while True:
    #if (time.monotonic_ns() - ts_start) > 3600000000000:
    #    # After an hour passes, reset the board (time.monotonic() becomes factor 2, 4, etc inaccurate)
    #    microcontroller.reset()

print("Started cycle")
print( "Available memory before free: {} bytes".format(gc.mem_free()) )
gc.collect()
print( "Available memory after free: {} bytes".format(gc.mem_free()) )

buf = bytearray(2000)
num_rx = 0
#while (time.monotonic_ns() - ts_start) < 3600000000000:
while True:
    try:
        nfds = 0
        # Poll max 30 packets at a time
        while nfds < 30:
            n, address = udp_socket.recvfrom_into(buf)
            # 2 uint64's (8B) followed by num pixels * uint32 (4B)
            if n < 2 * 8 + _STRAND_LENGTH * _NUM_STRANDS * 4:
                print("Err: Packet too small (" + str(n) + ")")
                continue
            #ts_sink = time.mktime(ntp.datetime) * 1000  # ms since epoch
            ts_sink_ns = pt.ns_since_epoch()
            ts_tree = struct.unpack_from('!Q', buf, 8)[0]
            rb.enqueue((ts_tree, buf))

            # Often enough (1-2 times per second)
            if num_rx % 30 == 0:
                # Return packet format:
                # int64 (source timestamp)
                # int64 (sink timestamp in ns)
                ts_source = struct.unpack_from('<Q', buf, 0)[0]
                response = bytearray(struct.pack('Q', ts_source))
                response.extend(bytearray(struct.pack('!Q', ts_sink_ns)))
                udp_socket.sendto(response, address)
            if num_rx % 200 == 0:
                pass
                print(str(rb.num_frames()) + " frames in ringbuf")

            nfds += 1
            num_rx += 1
    except OSError as e:
        if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
            # no more packets
            if nfds > 0:
                pass
                #print("nfds=" + str(nfds))
            pass

    num_iters = 0
    if not rb.is_empty():
        #print(str(rb.peek()[0]))
        while rb.peek()[0]*1000000 < pt.ns_since_epoch():
            (ts, frame) = rb.dequeue()
            for i in range(_STRAND_LENGTH * _NUM_STRANDS):
                #print("len(frame) = " + str(len(frame)))
                pixels[i] = int(struct.unpack_from('!I', frame, i*4)[0])

            pixels.show()
            time.sleep(0.010)
            num_iters += 1
            if rb.is_empty():
                break
    if num_iters > 0: 
        pass
        #print("num_iters=" + str(num_iters))
    time.sleep(0.001)
time.sleep(10)
