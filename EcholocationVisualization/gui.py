import argparse
import random
import sys
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow
from msg.messaging import StreamMessageConsumer
from widget.radar import RadarWidget


def create_test_data(filename, step_size=5, distance_range=range(30, 150)):
    """Writes some test data to file 'testdata.txt'"""
    input_data_tmpl = """{"measurements": [{"angle": %f,"distance": %d},{"angle": %f,"distance": %d}]}"""
    bla_data_tmpl = "SomeLog ... aaa {   }"

    with open(filename, "w") as test_data_file:
        for angle1 in range(0, 180, step_size):
            other_angle = (angle1 + 180) % 360
            value1, value2 = random.choice(distance_range), random.choice(distance_range)
            test_data_file.write(input_data_tmpl % (angle1, value1, other_angle, value2))
            test_data_file.write("\n")
            test_data_file.write(bla_data_tmpl)
            test_data_file.write("\n")



class RadarGui(QMainWindow):
    """
    The main window.
    """

    def __init__(self):
        super().__init__()
        self.radar_widget = RadarWidget(self)
        self.setCentralWidget(self.radar_widget)
        self.setWindowTitle("Echolocation")


if __name__ == "__main__":
    LOG_TAG = '[Radar] '
    print(LOG_TAG + "Starting Radar.")

    parser = argparse.ArgumentParser(description='Shows a visualization for the radar hardware.')
    parser.add_argument('--mocked', dest='mocked', action='store_true', help="runs the radar with mocked test data by writing some data into the given input file and reading it with some delay.")
    parser.add_argument("-f", "--input-file", type=str, dest="input_file", help="The file to read from. If called with --mocked, test data will be written to this file first.")
    parser.add_argument("-s", "--serial-device", type=str, dest="serial_device", help="If given, will try to read input data from the given serial interface. Note: You can define the baud rate using --baud")
    parser.add_argument("-b", "--baud", type=int, dest="baud_rate", help="The baud rate to be used. Only used in conjuction with -s/--serial-device")
    args = parser.parse_args()

    if args.serial_device is None and args.input_file is None:
        print("ERROR: Please choose an input file or input serial device (-f, or -b).")
        sys.exit(1)
    if args.serial_device is not None and args.input_file is not None:
        print("ERROR: -f and -s are XOR")
        sys.exit(1)
    if args.mocked and args.input_file is None:
        print("ERROR: -f has to be defined if using --mocked")
        sys.exit(1)
    if args.serial_device is not None and args.baud_rate is None:
        print("WARN: No baud rate was set (-b), using 9600 as fallback.")
        args.baud_rate = 9600

    app = QApplication(sys.argv)
    gui = RadarGui()
    gui.show()

    if args.mocked:
        create_test_data(args.input_file)

    # get the input stream based on our options
    input_stream = serial.Serial(args.serial_device, args.baud_rate) if args.serial_device is not None else open(args.input_file, "r")

    # start the stream consumer
    consumer = StreamMessageConsumer(input_stream, delay=0.05 if args.mocked else 0)
    consumer.SIGNAL_NEW_MEASUREMENT.connect(gui.radar_widget.on_new_measurement)
    consumer.start()

    # TODO: terminate app on EOF, close resources

    status = app.exec_()
    print(LOG_TAG + "Radar stopped.")
    sys.exit(status)
