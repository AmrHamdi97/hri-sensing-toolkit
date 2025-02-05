import argparse
import struct
import serial
import signal

# Global flag to control the execution
running = True

# Signal handler function
def signal_handler(sig, frame):
    global running
    print("Signal received, shutting down...")
    running = False

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

class CollectDataShimmer(object):
    def wait_for_ack(self):
        ddata = b""
        ack = struct.pack('B', 0xff)
        while ddata != ack and running:  # Check the running flag
            ddata = self.ser.read(1)

    def __init__(self):
        self._rate = 128.0  # Hz
        self._plotgsr = True
        self._gsrstream = False
        self._gsrsd = True

        self._gsrsignal = [0.0] * 3

        print("GSR Setting up GSR+")
        # Note: Added a timeout to prevent indefinite blocking
        self.ser = serial.Serial("/dev/rfcomm0", 115200, timeout=1)
        self.ser.flushInput()
        print("GSR port opening, done.")
        self.ser.write(struct.pack('BBBB', 0x08, 0x04, 0x01, 0x00))  # GSR and PPG
        self.wait_for_ack()
        print("GSR sensor setting, done.")
        self.ser.write(struct.pack('BB', 0x5E, 0x01))
        self.wait_for_ack()
        self.ser.write(struct.pack('B', 0x03))
        self.wait_for_ack()

    def activate_thread(self):
        while running:
            self._dump_data()
        self.clean_shutdown()

    def _dump_data(self):
        if running:  # Check before attempting to dump data
            self.ser.write(struct.pack('B', 0x92))  # Logging and streaming command
            self.wait_for_ack()
            print("GSR data dumping initiated.")

    def clean_shutdown(self):
        if self._plotgsr:
            if self._gsrstream:
                self._filegsr.close()
                self.ser.write(struct.pack('B', 0x20))
                print ("GSR stop command sent, waiting for ACK_COMMAND")
                self.wait_for_ack()
            elif self._gsrsd:
                self.ser.write(struct.pack('B', 0x93)) #0x97 stop logging and streaming
                print ("GSR SD stop command sent, waiting for ACK_COMMAND")
                self.wait_for_ack()

def main():
    dumper = CollectDataShimmer()
    dumper.activate_thread()

if __name__ == "__main__":
    main()

