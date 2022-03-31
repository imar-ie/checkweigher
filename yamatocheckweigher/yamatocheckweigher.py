#!/usr/bin/env python3
"""
Enable data acquisition from CE3000/CE3100 Controller
Yamato Checkweighers
"""

__author__ = "Keith Phelan"
__version__ = "0.1.0"
__license__ = "MIT"


import argparse
import logging
import socket
import yaml
import sys
import os

class Checkweigher:

    def __init__(self, host, port, config_file, retry_attempts=5):

        self.host = host
        self.port = port
        self.retryAttempts = retry_attempts
        self.client = None
        self.config_file = config_file

        if not os.path.exists(self.config_file):
            logging.error('Config file does not exist...')
            sys.exit()

    """
    Connection methods
    """

    def connect(self, attempt=0):

        if attempt >= self.retryAttempts:
            logging.error(f'Failed to create socket after {self.retryAttempts} attempts')
            sys.exit()

        else:

            try:
                # create an INET, STREAMing socket (IPv4, TCP/IP)
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except socket.error:
                logging.error('Failed to create socket')
                sys.exit()

            try:
                # Connect the socket object to the yamatocheckweigher using IP address (string) and port (int)
                self.client.connect((self.host, self.port))
                logging.info('Socket created to {} on port {}'.format(self.host, self.port))

            except:
                logging.debug(f"Failed to connect try {attempt + 1}/{self.retryAttempts}...")
                self.connect(attempt + 1)

    def disconnect(self):
        logging.info("Closing connection")
        if self.client:
            self.client.close()
            self.client = None
        else:
            logging.info('No connection to close')

    """
    Command methods
    """

    def DC(self):

        logging.debug('Not tested (destructive command), but should work ')
        sys.exit()

        if not self.client:
            self.connect()

        if self.__command('DC'):
            logging.info('Data cleared')
            return

    def DS(self):

        if not self.client:
            self.connect()

        if self.__command('DS'):
            return self.__totalData()

    def DT(self):

        logging.debug('Not tested (destructive command), but should work ')
        sys.exit()

        if not self.client:
            self.connect()

        if self.__command('DT'):
            return self.__totalData()

    def AS(self):

        if not self.client:
            self.connect()

        if self.__command('AS'):
            return self.__fivehundredData()

    def PN(self):
        logging.debug('Not implemented')
        sys.exit()

        if not self.client:
            self.connect()

    """
    Command Cycle
    """

    def __command(self, command='DS'):

        if command not in ['DC', 'DS', 'DT', 'AS', 'PN']:
            logging.error('Error: Command not valid')
            sys.exit()

        # Convert the command string to hex
        cmd_hex = command.encode('utf-8').hex()

        logging.debug("Command 1")

        tx = bytes.fromhex('435705')
        xrx = bytes.fromhex('43571030')

        if not self.__txrxckrt(tx, 4, xrx):
            logging.error("BCC failed")
            # ???
            return False

        logging.debug('Command 2')

        tx = bytes.fromhex('435702{}3003{}'.format(cmd_hex, self.__bcc(bytes.fromhex('{}3003'.format(cmd_hex))).hex()))

        xrx = bytes.fromhex('43571031')

        if self.__txrxckrt(tx, 4, xrx):

            logging.debug("Command 3")

            tx = bytes.fromhex('435704')

            xrx = bytes.fromhex('435705')

            if not self.__txrxckrt(tx, 3, xrx):
                logging.error("BCC failed")
                sys.exit()

            else:
                logging.debug("command 3 sucessfull")
                return True

    """
    Data parsing methods
    """

    def __parseTotalData(self, data, data_number):

        d = dict()

        if not (isinstance(data_number, int) and data_number in set([1, 2])):

            logging.error("Not a valid data number...")

        else:

            with open(self.config_file, 'r') as file:
                config = yaml.load(file, Loader=yaml.FullLoader)

                items = config["dataFields"][data_number]

                pointer = 0

                for i in items:
                    logging.debug('{} - {}:{}'.format(i['name'], pointer, i['size']))

                    d[i['name']] = data[pointer:i['size'] + pointer].decode()

                    pointer += i['size']

            return d

    def __parseFivehundredData(self, data):

        chunkSize = 9

        for i in range(0, len(data), chunkSize):
            p = dict()

            p['Weight data'] = data[i:i + chunkSize][0:6].decode()
            p['pass flag'] = data[i:i + chunkSize][6:7].decode()
            p['Region'] = data[i:i + chunkSize][7:8].decode()
            p['Reserved'] = data[i:i + chunkSize][8:9].decode()

            yield p

    """
    main transmit method - tx rx check return
    """
    def __txrxckrt(self, tx, byte_size, xrx=None):


        logging.debug('=============================')
        logging.debug("sending: ")

        try:

            self.client.send(tx)
            rx = self.client.recv(byte_size)

            logging.debug("received {}".format(rx.decode('ascii')))

            if not xrx:
                return rx
            else:

                logging.debug("expected rx")
                logging.debug(xrx)

                if rx == xrx:  # expected res
                    return rx
                else:

                    if rx == bytes.fromhex('43571004'):  # DLEEOT
                        logging.error('DLEEOT')
                    elif rx == bytes.fromhex('435715'):  # NAK
                        logging.error('NAK')

                    return False

        except socket.error:
            logging.error('Failed to send data.')
            self.disconnect()
            sys.exit()

    # create an INET, STREAMing socket (IPv4, TCP/IP)
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logging.error('Failed to create socket')
        sys.exit()

    """
    Data getters / Response Cycle
    """

    def __totalData(self):

        """ request Total data """

        d = dict()

        logging.info("requesting totals")
        logging.debug("response 1")

        tx = bytes.fromhex('43571030')

        res = self.__txrxckrt(tx, 164)

        # Check the bcc
        if (res[-1:] == self.__bcc(res[3:-1])):
            logging.debug("bcc passed ! ")

            data = res[6:-2]

            d[1] = self.__parseTotalData(data, 1)

        else:
            logging.error("BCC failed")
            sys.exit()

        logging.debug("response 2")

        tx = bytes.fromhex('43571031')

        res = self.__txrxckrt(tx, 220)

        # Check the bcc
        if (res[-1:] == self.__bcc(res[3:-1])):
            logging.debug("bcc passed ! ")

            data = res[6:-2]

            d[2] = self.__parseTotalData(data, 2)

        else:
            logging.error("BCC failed")
            sys.exit()

        # Merge data 1 & 2
        return {**d[1], **d[2]}

    def __fivehundredData(self):

        """ request 500 data """

        d = dict()

        logging.debug("response 1 ... 20")

        for x in range(20):
            logging.debug(x)

            tx = bytes.fromhex('43571030')

            res = self.__txrxckrt(tx, 187)

            # Check the bcc
            if (res[-1:] == self.__bcc(res[3:-1])):
                logging.debug("bcc passed ! ")

                data = res[6:-2]

                d[len(d)] = list(self.__parseFivehundredData(data))

            else:
                logging.error("BCC failed")
                exit()

        return d

    @staticmethod
    def __bcc(packet):
        """Returns an XOR check for a hex
        :param packet:
        :return: bytes
        """

        if not isinstance(packet, bytes):
            logging.error("requires a bytes value")
            return False

        else:

            cs = 0
            for el in packet:
                cs ^= el

            return cs.to_bytes(1, 'big')


"""
Cli interface
"""

if __name__ == "__main__":
    """ Command Line interface """

    parser = argparse.ArgumentParser()

    # Handle args Command, IP & port
    parser.add_argument("ip", help="Device IP address")
    parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Device port", default=1001)
    parser.add_argument("-c", "--command", choices=['DC', 'DS', 'DT', 'AS'], help='Command', default="DS")
    parser.add_argument("-cf", "--config", help=" configuration location", default='{}/configs/yamatocheckweigher.yaml'.format(os.path.join(os.path.dirname(__file__))))

    # Specify output of "--version"
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()

    # New Checkweigher
    cw = Checkweigher(args.ip, args.port, args.config)

    # Handle Command
    if args.command == 'DC':
        logging.info("DC")
        cw.DC()

    elif args.command == 'DS':
        logging.info('DS')

        res = cw.DS()

        if res:

            print(res)

    elif args.command in 'DT':
        logging.info('DT')
        cw.DT()

    elif args.command in 'AS':
        logging.info('AS')
        print(cw.AS())

    cw.disconnect()
