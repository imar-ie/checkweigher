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


#logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

log = logging.getLogger(__name__)


class Checkweigher:

    def __init__(self, host, port, retry_attempts=5, config_file='./configs/checkweigher.yaml'):

        self.host = host
        self.port = port
        self.retryAttempts = retry_attempts
        self.client = None
        self.config_file = config_file

        if not os.path.exists(self.config_file):
            log.error('Config file does not exist...')
            sys.exit()

    """
    Connection methods
    """

    def connect(self, attempt=0):

        if attempt >= self.retryAttempts:
            log.error(f'Failed to create socket after {self.retryAttempts} attempts')
            sys.exit()

        else:

            try:
                # create an INET, STREAMing socket (IPv4, TCP/IP)
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except socket.error:
                log.error('Failed to create socket')
                sys.exit()

            try:
                # Connect the socket object to the checkweigher using IP address (string) and port (int)
                self.client.connect((self.host, self.port))
                log.info('Socket created to {} on port {}'.format(self.host, self.port))

            except:
                log.debug(f"Failed to connect try {attempt + 1}/{self.retryAttempts}...")
                self.connect(attempt + 1)

    def disconnect(self):
        log.info("Closing connection")
        if self.client:
            self.client.close()
            self.client = None
        else:
            log.info('No connection to close')

    """
    Command methods
    """

    def DC(self):

        log.debug('Not tested (destructive command), but should work ')
        sys.exit()

        if not self.client:
            self.connect()

        if self.__command('DC'):
            log.info('Data cleared')
            return

    def DS(self):

        if not self.client:
            self.connect()

        if self.__command('DS'):
            return self.__totalData()

    def DT(self):

        log.debug('Not tested (destructive command), but should work ')
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
        log.debug('Not implemented')
        sys.exit()

        if not self.client:
            self.connect()

    """
    Command Cycle
    """

    def __command(self, command='DS'):

        if command not in ['DC', 'DS', 'DT', 'AS', 'PN']:
            log.error('Error: Command not valid')
            sys.exit()

        # Convert the command string to hex
        cmd_hex = command.encode('utf-8').hex()

        log.debug("Command 1")

        tx = bytes.fromhex('435705')
        xrx = bytes.fromhex('43571030')

        if not self.__foo(tx, 4, xrx):
            log.error("BCC failed")
            # ???
            return False

        log.debug('Command 2')

        tx = bytes.fromhex('435702{}3003{}'.format(cmd_hex, self.__bcc(bytes.fromhex('{}3003'.format(cmd_hex))).hex()))

        xrx = bytes.fromhex('43571031')

        if self.__foo(tx, 4, xrx):

            log.debug("Command 3")

            tx = bytes.fromhex('435704')

            xrx = bytes.fromhex('435705')

            if not self.__foo(tx, 3, xrx):
                log.error("BCC failed")
                sys.exit()

            else:
                log.debug("command 3 sucessfull")
                return True

    """
    Data parsing methods
    """

    def __parseTotalData(self, data, data_number):

        d = dict()

        if not (isinstance(data_number, int) and data_number in set([1, 2])):

            log.error("Not a valid data number...")

        else:

            with open(self.config_file, 'r') as file:
                config = yaml.load(file, Loader=yaml.FullLoader)

                items = config["dataFields"][data_number]

                pointer = 0

                for i in items:
                    log.debug('{} - {}:{}'.format(i['name'], pointer, i['size']))

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

    def __foo(self, tx, byte_size, xrx=None):
        # TODO name this method

        log.debug('=============================')
        log.debug("sending: ")

        try:

            self.client.send(tx)
            rx = self.client.recv(byte_size)

            log.debug("received {}".format(rx.decode('ascii')))

            if not xrx:
                return rx
            else:

                logging.debug("expected rx")
                logging.debug(xrx)

                if rx == xrx:  # expected res
                    return rx
                else:

                    if rx == bytes.fromhex('43571004'):  # DLEEOT
                        log.error('DLEEOT')
                    elif rx == bytes.fromhex('435715'):  # NAK
                        log.error('NAK')

                    return False

        except socket.error:
            log.error('Failed to send data.')
            self.disconnect()
            sys.exit()

    # create an INET, STREAMing socket (IPv4, TCP/IP)
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        log.error('Failed to create socket')
        sys.exit()

    """
    Data getters / Response Cycle
    """

    def __totalData(self):

        """ request Total data """

        d = dict()

        log.info("requesting totals")
        log.debug("response 1")

        tx = bytes.fromhex('43571030')

        res = self.__foo(tx, 164)

        # Check the bcc
        if (res[-1:] == self.__bcc(res[3:-1])):
            log.debug("bcc passed ! ")

            data = res[6:-2]

            d[1] = self.__parseTotalData(data, 1)

        else:
            log.error("BCC failed")
            sys.exit()

        log.debug("response 2")

        tx = bytes.fromhex('43571031')

        res = self.__foo(tx, 220)

        # Check the bcc
        if (res[-1:] == self.__bcc(res[3:-1])):
            log.debug("bcc passed ! ")

            data = res[6:-2]

            d[2] = self.__parseTotalData(data, 2)

        else:
            log.error("BCC failed")
            sys.exit()

        # Merge data 1 & 2
        return {**d[1], **d[2]}

    def __fivehundredData(self):

        """ request 500 data """

        d = dict()

        log.debug("response 1 ... 20")

        for x in range(20):
            log.debug(x)

            tx = bytes.fromhex('43571030')

            res = self.__foo(tx, 187)

            # Check the bcc
            if (res[-1:] == self.__bcc(res[3:-1])):
                log.debug("bcc passed ! ")

                data = res[6:-2]

                d[len(d)] = list(self.__parseFivehundredData(data))

            else:
                log.error("BCC failed")
                exit()

        return d

    @staticmethod
    def __bcc(packet):
        """Returns an XOR check for a hex
        :param packet:
        :return: bytes
        """

        if not isinstance(packet, bytes):
            log.error("requires a bytes value")
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

    # Specify output of "--version"
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()

    # New Checkweigher
    cw = Checkweigher(args.ip, args.port)

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