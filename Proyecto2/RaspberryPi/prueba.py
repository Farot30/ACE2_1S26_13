import serial
import sys

puerto = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
baudrate = 115200

ser = serial.Serial(puerto, baudrate, timeout=1)
print(f"Recibiendo datos en {puerto} ...\n")

while True:
    line = ser.readline().decode("utf-8", errors="replace").strip()
    if line:
        print(line)