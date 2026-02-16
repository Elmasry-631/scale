import serial
import time
import logging
from datetime import datetime
from threading import Thread, Lock

# Logging config
logging.basicConfig(
    filename='scale_reader.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

class ScaleReader:
    def __init__(self, port='COM5', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.latest_data = {"weight": None, "unit": "kg", "timestamp": None}
        self.lock = Lock()
        self.running = False

    def connect(self):
        while True:
            try:
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout
                )
                logging.info(f"Connected to scale on {self.port}")
                print(f"Connected to scale on {self.port}")
                break
            except serial.SerialException as e:
                logging.error(f"Failed to connect to scale: {e}")
                print(f"Failed to connect to scale: {e}, retrying in 5 seconds...")
                time.sleep(5)  # Retry after 5 seconds

    def parse_weight(self, line):
        """Parse ASCII data from scale, e.g., '+0012.45kg'"""
        try:
            # Remove whitespace
            line = line.strip().decode('ascii')
            print(f"Raw line from scale: {line}")  # Diagnostic print
            if "kg" in line.lower():
                weight_str = line.lower().replace('kg', '').replace('+', '').strip()
                weight = float(weight_str)
                if not (0 <= weight <= 500):  # sanity check for normal range
                    raise ValueError("Weight out of expected range.")
                return weight
            else:
                raise ValueError("No 'kg' unit in string")
        except Exception as e:
            logging.warning(f"Failed to parse line: {line} | Error: {e}")
            print(f"Parse error: {e} for line: {line}")
            return None

    def read_loop(self):
        self.running = True
        while self.running:
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    print("Serial connection lost. Reconnecting...")
                    logging.warning("Serial connection lost. Reconnecting...")
                    self.connect()
                line = self.serial_conn.readline()
                weight = self.parse_weight(line)
                if weight is not None:
                    data = {
                        "weight": weight,
                        "unit": "kg",
                        "timestamp": datetime.utcnow().isoformat() + 'Z'
                    }
                    with self.lock:
                        self.latest_data = data
                    logging.info(f"New weight: {data}")
            except Exception as e:
                logging.error(f"Error reading from scale: {e}")
                print(f"Error reading from scale: {e}")
                time.sleep(1)

    def start(self):
        self.connect()
        self.thread = Thread(target=self.read_loop, daemon=True)
        self.thread.start()
        print("ScaleReader started.")

    def get_latest_data(self):
        with self.lock:
            return self.latest_data.copy()

    def stop(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        logging.info("ScaleReader stopped.")
        print("ScaleReader stopped.")

# Example usage for testing (standalone):
if __name__ == "__main__":
    reader = ScaleReader(port='COM5')
    reader.start()
    try:
        while True:
            print(reader.get_latest_data())
            time.sleep(2)
    except KeyboardInterrupt:
        reader.stop()

