import struct
import serial

class CollectDataShimmerEMG(object):
    def wait_for_ack(self):
        ddata = b""  # Use bytes type
        ack = struct.pack('B', 0xff)
        while ddata != ack:
            ddata = self.ser.read(1)

    def __init__(self):
        self._rate = 100.0  # Hz, adjust as needed for EMG
        self._plotemg = True
        self._emgstream = False
        self._emgsd = True

        self._emgsignal = [0.0] * 3

        print("EMG Setting up EMG+")
        self.ser = serial.Serial("/dev/rfcomm0", 115200)
        self.ser.flushInput()
        print("EMG port opening, done.")

        # Adjust command bytes for EMG configuration
        self.ser.write(struct.pack('BBBB', 0x08, 0x04, 0x01, 0x00))  # Change to EMG mode
        self.wait_for_ack()
        print("EMG sensor setting, done.")
        self.ser.write(struct.pack('BB', 0x5E, 0x01))
        self.wait_for_ack()
        self.ser.write(struct.pack('B', 0x03))
        self.wait_for_ack()
        ddata = b""  # Use bytes type
        numbytes = 0
        framesize = 3
        while numbytes < framesize:
            ddata += self.ser.read(framesize)
            numbytes = len(ddata)

        data = ddata[0:framesize]
        (samplingrate,) = struct.unpack('H', data[1:3])
        print("Current sampling rate: %d (%.2fHz)" % (samplingrate, (32768.0 / samplingrate)))

    def activate_thread(self):
        try:
            while True:
                self._dump_data()
        except KeyboardInterrupt:
            self.clean_shutdown()

    def _dump_data(self):
        # start writing data for EMG
        self.ser.write(struct.pack('B', 0x92))  # 0x70 Logging and streaming
        self.wait_for_ack()
        print("EMG start SD writing command sending, done.")

    def clean_shutdown(self):
        if self._plotemg:
            if self._emgstream:
                self._fileemg.close()
                self.ser.write(struct.pack('B', 0x20))
                print("EMG stop command sent, waiting for ACK_COMMAND")
                self.wait_for_ack()
            elif self._emgsd:
                self.ser.write(struct.pack('B', 0x93))  # 0x97 stop logging and streaming
                print("EMG SD stop command sent, waiting for ACK_COMMAND")
                self.wait_for_ack()
            # close serial port
            # self.ser.close()

def main():
    dumper = CollectDataShimmerEMG()
    dumper.activate_thread()


if __name__ == "__main__":
    main()

