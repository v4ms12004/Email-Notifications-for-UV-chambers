import time
from datetime import datetime
from pymodbus.client import ModbusSerialClient

#where script will write data
LOG_FILE = "uv_log.txt"

# Create clients for both sensors
left_client = ModbusSerialClient(
    port='COM4',
    baudrate=9600,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=1
)

right_client = ModbusSerialClient(
    port='COM3',
    baudrate=9600,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=1
)

left_connected = left_client.connect()
right_connected = right_client.connect()


def main():
    if left_connected or right_connected:
        print("Connected. Logging UV radiation data every 10 minutes...")
        if left_connected:
            print("Left box connected.")
        if right_connected:
            print("Right box connected.")

        try:
            while True:
                timestamp = datetime.now()
                date_str = f"{timestamp.month}/{timestamp.day}/{timestamp.year}"
                time_str = timestamp.strftime("%I:%M:%S %p")

                # Read left sensor
                if left_connected:
                    result_left = left_client.read_holding_registers(address=0x0000, count=1, slave=47)
                    left_uv = result_left.registers[0] if not result_left.isError() else "ERROR"
                else:
                    #reads not connected
                    left_uv = "NC"

                # Read right sensor
                if right_connected:
                    result_right = right_client.read_holding_registers(address=0x0000, count=1, slave=47)
                    right_uv = result_right.registers[0] if not result_right.isError() else "ERROR"
                else:
                    #reads not connected
                    right_uv = "NC"

                # Write to file
                with open(LOG_FILE, "a") as f:
                    f.write(f"{date_str}\t{time_str}\t{left_uv}\t{right_uv}\n")

                # Terminal output
                print(f"Logged at {date_str} {time_str} — Left: {left_uv} W/m², Right: {right_uv} W/m²")

                time.sleep(5)  # 10 minutes (change to 1 for quick testing, 600 for 10 minute)
        except KeyboardInterrupt:
            print("\nLogging stopped by user.")
        finally:
            if left_connected:
                left_client.close()
            if right_connected:
                right_client.close()
    else:
        print("Failed to connect to either Modbus RTU sensor.")

main()