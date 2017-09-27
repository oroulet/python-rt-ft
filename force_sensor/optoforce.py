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

from .ati_rdt import ATIRDT

class OptoForce(ATIRDT):
    """Class for sampling the OptoForce force sensor over UDP+RDT in both single
    shot and streaming mode.
    """

    def __init__(self, rdt_host, rdt_port=49152, bind_host='0.0.0.0'):
        ATIRDT.__init__(self, rdt_host, rdt_port, bind_host)
        self._enc_to_si = np.array(3*[1.0e-4] + 3*[1.0e-5])
        self._sock.settimeout(0.05)
