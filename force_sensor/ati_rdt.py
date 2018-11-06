# coding=utf-8

"""
"""

__author__ = "Morten Lind"
__copyright__ = "SINTEF 2017"
__credits__ = ["Morten Lind"]
__license__ = "GPLv3"
__maintainer__ = "Morten Lind"
__email__ = "morten.lind@sintef.no"
__status__ = "Development"

import threading
import socket
import enum
import struct

import numpy as np


class Modes(enum.Enum):
    STREAM = 2
    SINGLE = 0


class ATIRDT(threading.Thread):
    """Class for sampling the ATI force sensor over UDP+RDT in both single
    shot and streaming mode.
    """

    REQ_STRUCT = struct.Struct('>HHI')
    FT_STRUCT = struct.Struct('>IIIiiiiii')

    def __init__(self, rdt_host, rdt_port=49152, bind_host='0.0.0.0'):
        threading.Thread.__init__(self)
        self.daemon = True
        self._rdt_addr = (rdt_host, rdt_port)
        self._bind_addr = (bind_host, rdt_port)
        self._sock = socket.socket(type=socket.SOCK_DGRAM)
        self._sock.settimeout(0.005)
        self._sock.bind(self._bind_addr)
        self._mode = Modes.SINGLE
        self._cycle_time = 0.0
        self._enc_to_si = np.array(6 * [1.0e-6])
        self._bias = np.zeros(6)
        self._latest_ft = None
        self._ft_lock = threading.Lock()
        self._stream_flag = threading.Event()
        self.__stop = False

    @property
    def is_streaming(self):
        return self._mode == Modes.STREAM

    @property
    def is_single(self):
        return self._mode == Modes.SINGLE

    def start_stream(self):
        if self._mode == Modes.STREAM:
            # Already in streaming mode
            return False
        self._sock.sendto(ATIRDT.REQ_STRUCT.pack(0x1234, 2, 0),
                          self._rdt_addr)
        self._mode = Modes.STREAM
        self._stream_flag.set()
        return True

    def stop_stream(self):
        if self._mode == Modes.SINGLE:
            # Already in single mode
            return False
        self._stream_flag.clear()
        self._sock.sendto(ATIRDT.REQ_STRUCT.pack(0x1234, 0, 0),
                          self._rdt_addr)
        self._mode = Modes.SINGLE
        # Empty the receive buffer
        while self._recv_ft() is not None:
            pass
        self._latest_ft = None

        return True

    def zero_bias(self):
        with self._ft_lock:
            self._bias = np.zeros(6)

    def sample_bias(self, N=100):
        with self._ft_lock:
            self._bias = np.zeros(6)
            for i in range(N):
                while self._req_single_ft() is None:
                    pass
                self._bias += self._raw_ft.copy()
            self._bias /= N

    def _recv_ft(self):
        try:
            data = ATIRDT.FT_STRUCT.unpack(self._sock.recv(1024))
        except socket.timeout:
            return None
        else:
            self._raw_ft = self._enc_to_si * np.array(data[3:])
            return self._raw_ft - self._bias

    def _req_single_ft(self):
        self._sock.sendto(ATIRDT.REQ_STRUCT.pack(0x1234, 2, 1),
                          self._rdt_addr)
        return self._recv_ft()

    def get_ft(self):
        if self._mode == Modes.STREAM:
            with self._ft_lock:
                return self._latest_ft
        else:
            # Request and return single measurement
            return self._req_single_ft()
            # Receive and return ft value
            ft = self._recv_ft()
            for i in range(5):
                new_ft = self._recv_ft()
                if new_ft is None:
                    break
                else:
                    ft = new_ft
            return ft

    ft = property(get_ft)

    def run(self):
        while not self.__stop:
            self._stream_flag.wait()
            with self._ft_lock:
                self._latest_ft = self._recv_ft()

    def stop(self):
        self.__stop = True
