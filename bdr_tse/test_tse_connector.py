from unittest import TestCase

TSE_PATH = "/media/leon/304C-D627"

from bdr_tse import tse_connector

class TestTseConnector(TestCase):

    def setUp(self):
        self.tse = tse_connector.TseConnector(TSE_PATH)

    def test_get_pin_status(self):
        print(self.tse.start())
        print(self.tse.get_pin_status())
