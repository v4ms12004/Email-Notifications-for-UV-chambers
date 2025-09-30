from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException

# Configure the serial connection
client = ModbusSerialClient(
    port='COM4',       # Replace with your actual serial port
    baudrate=9600,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=0.5
)

# Connect to the serial port
if not client.connect():
    print("Failed to connect to the serial port.")
else:
    print("Scanning for active Modbus RTU addresses on COM3...")
    active_addresses = []

    for address in range(1, 248):  # Valid Modbus addresses: 1–247
        try:
            result = client.read_holding_registers(address=0x0000, count=1, slave=address)
            if not isinstance(result, ModbusIOException) and not result.isError():
                print(f"✅ Device found at address: {address}")
                active_addresses.append(address)
        except Exception:
            pass  # Ignore errors and continue scanning

    client.close()

    if active_addresses:
        print(f"\nActive Modbus addresses found: {active_addresses}")
    else:
        print("\nNo active Modbus devices found on the bus.")
