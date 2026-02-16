import logging
import os
import time
from datetime import datetime
from threading import Lock, Thread

import serial

logger = logging.getLogger(__name__)


class ScaleReader:
    def __init__(self, port: str = "COM5", baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.latest_data = {"weight": None, "unit": "kg", "timestamp": None}
        self.lock = Lock()
        self.running = False
        self.thread = None
        self.last_error = None

    def connect(self):
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )
            self.last_error = None
            logger.info("Connected to scale on %s", self.port)
            return True
        except serial.SerialException as exc:
            self.last_error = f"Failed to connect: {exc}"
            logger.error("%s", self.last_error)
            return False

    def parse_weight(self, line: bytes):
        """Parse ASCII data from scale, e.g., '+0012.45kg'."""
        raw_text = ""
        try:
            raw_text = line.strip().decode("ascii")
            if "kg" not in raw_text.lower():
                raise ValueError("Missing 'kg' unit")

            weight_str = raw_text.lower().replace("kg", "").replace("+", "").strip()
            weight = float(weight_str)

            if not (0 <= weight <= 500):
                raise ValueError("Weight out of expected range")
            return weight
        except (UnicodeDecodeError, ValueError) as exc:
            logger.warning("Failed to parse line '%s': %s", raw_text or line, exc)
            return None

    def read_loop(self):
        while self.running:
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    if not self.connect():
                        time.sleep(2)
                        continue

                line = self.serial_conn.readline()
                weight = self.parse_weight(line)

                if weight is not None:
                    data = {
                        "weight": weight,
                        "unit": "kg",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                    with self.lock:
                        self.latest_data = data
                    logger.info("New weight: %s", data)
            except serial.SerialException as exc:
                self.last_error = f"Serial read error: {exc}"
                logger.error("%s", self.last_error)
                time.sleep(1)
            except Exception as exc:
                self.last_error = f"Unexpected read error: {exc}"
                logger.exception("%s", self.last_error)
                time.sleep(1)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = Thread(target=self.read_loop, daemon=True)
        self.thread.start()
        logger.info("ScaleReader started")

    def get_latest_data(self):
        with self.lock:
            return self.latest_data.copy()

    def get_status(self):
        last_data = self.get_latest_data()
        return {
            "running": self.running,
            "serial_connected": bool(self.serial_conn and self.serial_conn.is_open),
            "port": self.port,
            "last_timestamp": last_data.get("timestamp"),
            "last_error": self.last_error,
        }

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        logger.info("ScaleReader stopped")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    reader = ScaleReader(port=os.getenv("SCALE_PORT", "COM5"))
    reader.start()
    try:
        while True:
            print(reader.get_latest_data())
            time.sleep(2)
    except KeyboardInterrupt:
        reader.stop()
