"""Client for the SnapAV Binary-brand MoIP telnet control protocol.

Vendored and fixed from pybinarymoip 0.0.8 (github.com/gjbadros/pybinarymoip).
The upstream library conflates a receiver/transmitter's position in its
internal list with its real device index as reported by the controller.
Those two numbers differ whenever devices aren't numbered contiguously
starting at 1 (the common case), which crashes _update_inputs() with an
IndexError and would otherwise silently target the wrong physical port on
every source switch. This version tracks the real device index separately
via an index lookup, instead of assuming index-1 is a valid list position.
"""
import logging
import select
import socket
import threading

_LOGGER = logging.getLogger(__name__)


class MoIPError(Exception):
    """Raised when the controller rejects a command or doesn't respond."""


class MoIP(object):
    """Main SnapAV Binary Media Over IP (MoIP) class."""

    def __init__(self, host, username, password, area='', noop_set_state=False):
        """Initializes the MoIP object. No connection is made to the device."""
        self._host = host
        self._port = 23
        self._username = username
        self._password = password
        self._firmware_version = None
        self._receivers = []
        self._transmitters = []
        self._receivers_by_index = {}
        self._transmitters_by_index = {}
        self._sock = None
        self._timeout = 8
        self._socket_lock = threading.Lock()

    def connect(self):
        """Begin connection to the device and get its status."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self._timeout)
        try:
            self._sock.connect((self._host, self._port))
        except socket.error as err:
            _LOGGER.error(
                "Unable to connect to %s on port %s: %s",
                self._host, self._port, err)
            return

        try:
            self._send("?Firmware\n")
            self._firmware_version = self._read_after_equals()
            _LOGGER.info("MoIP firmware version = %s", self._firmware_version)
            self._send("?Devices\n")
            devices = self._read_after_equals()
            (tx, rx) = devices.split(",", 1)
            (num_tx, num_rx) = (int(tx), int(rx))
            _LOGGER.info("# Transmitters = %s, # Receivers = %s", num_tx, num_rx)

            self._send("?Name=0\n")  # receivers
            rx_names = self._read_full()
            rx_lines = rx_names.split("\n")
            for rl in rx_lines[0:len(rx_lines) - 1]:
                (_, a) = rl.split("=", 1)
                (_, index, name) = a.split(",", 2)
                receiver = MoIP_Receiver(self, int(index), name)
                self._receivers.append(receiver)
                self._receivers_by_index[int(index)] = receiver

            self._send("?Name=1\n")  # transmitters
            tx_names = self._read_full()
            tx_lines = tx_names.split("\n")
            for tl in tx_lines[0:len(tx_lines) - 1]:
                (_, a) = tl.split("=", 1)
                (_, index, name) = a.split(",", 2)
                transmitter = MoIP_Transmitter(self, int(index), name)
                self._transmitters.append(transmitter)
                self._transmitters_by_index[int(index)] = transmitter

            self._update_inputs()
            _LOGGER.info("Transmitters = %s", self._transmitters)
            _LOGGER.info("Receivers = %s", self._receivers)
        except Exception as err:
            _LOGGER.error("Failed to initialize connection: %s", err)

    def _update_inputs(self):
        with self._socket_lock:
            extra_text = self._read_full()
            if extra_text:
                _LOGGER.warning("Ignoring extra text: %r", extra_text)
            self._send("?Receivers\n")
            answer = self._read_after_equals()
            if answer is None:
                _LOGGER.error("Got bad response from ?Receivers "
                               "-- cannot _update_inputs")
                return
            inputs = answer.split(",")
            for i in inputs:
                (tx, rx) = i.split(":", 1)
                rx_obj = self._receivers_by_index.get(int(rx))
                if rx_obj is None:
                    _LOGGER.warning(
                        "Unknown receiver index %s in ?Receivers reply", rx)
                    continue
                tx_obj = self._transmitters_by_index.get(int(tx))
                rx_obj._set_input(tx_obj)

    def _send(self, str):
        self._last_send = str
        self._sock.send(str.encode())

    def _send_check(self, str, timeout=None):
        """Appends newline to str before sending. Raises MoIPError if the
        controller doesn't acknowledge with OK (including on timeout)."""
        if timeout is None:
            timeout = self._timeout
        with self._socket_lock:
            self._send(str + "\n")
            response = self._read(timeout)
            _LOGGER.debug("sent %r, got response = %r", str, response)
            if response is None:
                raise MoIPError(
                    "No response from controller after sending: %s" % str)
            if not response.startswith("OK"):
                raise MoIPError(
                    "Controller rejected '%s': %s" % (str, response))

    def _read_raw(self, timeout=None):
        if timeout is None:
            timeout = self._timeout
        readable, _, _ = select.select([self._sock], [], [], timeout)
        if not readable:
            return None
        answer = self._sock.recv(16384).decode()
        return answer

    def _read(self, timeout=None):
        if timeout is None:
            timeout = self._timeout
        answer = self._read_raw(timeout)
        if not answer:
            _LOGGER.warning(
                "Timeout (%s second(s)) waiting for a response after "
                "sending %r to %s on port %s.",
                self._timeout, self._last_send,
                self._host, self._port)
            return None
        if answer.endswith("\n"):
            answer = answer[0:len(answer) - 1]
        _LOGGER.debug("read text: %s", answer)
        return answer

    def _read_full(self):
        answer = ""
        while True:
            line = self._read_raw(timeout=0.1)
            if line is None:
                _LOGGER.debug("read: %s", answer)
                return answer
            answer += line

    def _read_after_equals(self):
        answer = self._read()
        split_answer = answer.split("=", 1)
        if len(split_answer) > 1:
            return split_answer[1]
        else:
            return None

    @property
    def receivers(self):
        """Return the full list of receivers."""
        return self._receivers

    @property
    def transmitters(self):
        """Return the full list of transmitters."""
        return self._transmitters

    def __str__(self):
        return "MoIP Controller @ %s [%s]" % (
            self._host, self._firmware_version)

    def __repr__(self):
        return str({'host': self._host,
                     'firmware_version': self._firmware_version})


class MoIP_Receiver(object):
    def __init__(self, mc, num, name, input=None):
        self._mc = mc
        self._num = num  # the receiver's real device index on the controller
        self._name = name
        self._input = input  # a MoIP_Transmitter object

    @property
    def num(self):
        return self._num

    @property
    def name(self):
        return self._name

    @property
    def input(self):
        return self._input

    def _set_input(self, input):
        self._input = input

    def _send_check(self, str, timeout=5):
        return self._mc._send_check(str, timeout)

    def switch_to_tx(self, tx):
        """Switch to a given transmitter.

        Can specify either as a position in the transmitters list (int) or
        by passing the MoIP_Transmitter object directly.
        """
        if isinstance(tx, int):
            if 0 <= tx < len(self._mc._transmitters):
                tx = self._mc._transmitters[tx]
            else:
                _LOGGER.error("tx = %s is out of range", tx)
                return
        self._input = tx
        self._send_check("!Switch=%s,%s" % (tx.num, self._num), 12)
        self._mc._update_inputs()

    def set_resolution(self, resolution):
        """Use resolution int in [0,4]::
        0 == Pass thru
        1 == 1080p 60Hz
        2 == 1080p 50Hz
        3 == 2160p 30Hz
        4 == 2160p 25Hz
        """
        self._send_check("!Resolution=%s,%d" % (self._num, resolution))

    def show_osd_message(self, msg):
        self._send_check("!OSD=%s,%s" % (self._num, msg))

    def reboot_device(self):
        self._send_check("!Reboot")

    def set_cec(self, cec_on):
        self._send_check("!CEC=%s,%d" % (self._num, 1 if cec_on else 0))

    def send_ir(self, pronto_code):
        """Send an IR command (Pronto Hex format) out this receiver's IR
        flasher output, e.g. to power a TV on/off."""
        self._send_check("!IR=0,%s,%s" % (self._num, pronto_code))

    def __str__(self):
        return "{MoIP Rx#%d \"%s\" from %s}" % (self._num,
                                                  self._name,
                                                  self._input)

    def __repr__(self):
        return str({'name': self._name,
                     'num': self._num,
                     'input': self._input,
                     'input_num': self._input and self._input.num,
                     'mc': self._mc})


class MoIP_Transmitter(object):
    def __init__(self, mc, num, name):
        self._mc = mc
        self._num = num
        self._name = name

    @property
    def num(self):
        return self._num

    @property
    def name(self):
        return self._name

    def __str__(self):
        return "{MoIP Tx#%d \"%s\"}" % (self._num, self._name)

    def __repr__(self):
        return str({'name': self._name,
                     'num': self._num,
                     'mc': self._mc})
