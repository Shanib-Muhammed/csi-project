# Hardware setup

## Parts

- Two ESP32-WROOM-32D development boards.
- Two USB data cables (not charge-only cables).
- Windows laptop with two available USB ports, or one USB port plus a reliable USB power source for the transmitter.
- A clear table/room area for testing.

No jumper wires are required between the ESP32 boards. They communicate over their own 2.4 GHz Wi-Fi link. USB is used for power and programming; the receiver's USB cable also carries CSI records to the laptop.

## Board roles

| Board | Firmware | Connection |
|---|---|---|
| Board 1 | firmware/transmitter/transmitter.ino | USB power; creates CSI-RADAR-LINK access point |
| Board 2 | firmware/receiver/receiver.ino | USB data to laptop; joins the transmitter and streams CSI over serial |

## Physical placement

1. Place both boards on non-metallic stands or table surfaces.
2. Begin with about 1 metre between the boards, with their PCB antenna ends facing into the test area.
3. Keep both boards at roughly the same height.
4. Keep the boards and USB cables still during calibration.
5. Test with a hand or object moving through the middle of the link.
6. Avoid placing either antenna directly beside metal, a laptop chassis, a large power supply, or another 2.4 GHz transmitter.

The 1 metre starting distance is a practical initial experiment, not a guaranteed sensing range. Test other distances only after confirming stable packet reception.

## USB and COM port

1. Upload transmitter firmware to board 1.
2. Upload receiver firmware to board 2.
3. Connect board 2 to the laptop using a data-capable USB cable.
4. Open Windows Device Manager → Ports (COM & LPT).
5. Identify the COM port that appears/disappears when board 2 is unplugged.
6. Use that port in start.ps1, for example: .\start.ps1 -Port COM6.
7. Close Arduino Serial Monitor before launching Python.

The transmitter's serial port is not needed by the Python app. It can be connected to a USB power source after firmware upload.

## First power-on sequence

1. Power board 1 and wait about 5 seconds for its SoftAP to start.
2. Power board 2 and wait for it to join CSI-RADAR-LINK.
3. Start the Python app with the receiver COM port.
4. Confirm that the dashboard changes to RECEIVER ONLINE and the CSI packet count increases.
5. Only then begin calibration.

## Radio settings

Both sketches must use matching SSID, password, channel, and UDP port. Defaults:

- SSID: CSI-RADAR-LINK
- Password: radar-demo-32
- Channel: 6 (2.437 GHz centre frequency)
- UDP port: 3333
- Receiver serial baud: 921600

This is a private local SoftAP link. It does not provide internet access. The laptop does not need to join this network; it reads the receiver through USB serial.
