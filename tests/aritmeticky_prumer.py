import unittest;
import os;
from statisticke_vypracovani.aritmeticky_prumer.logic import try_convert;

# TO RUN TEST DO: python -m unittest discover tests

class TestMathLogic(unittest.TestCase):

    def test_conversion_int(self):
        """Tests if '10' becomes 10"""
        self.assertEqual(try_convert("10"), 10)

    def test_conversion_float(self):
        """Tests if '10.5' becomes 10.5"""
        self.assertEqual(try_convert("10.5"), 10.5)

    def test_conversion_string(self):
        """Tests if text stays text"""
        self.assertEqual(try_convert("chyba"), "chyba")

    # You can also test the math here if you separate 
    # the calculation logic from the file reading!