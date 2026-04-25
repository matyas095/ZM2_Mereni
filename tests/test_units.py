import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from objects.units import parse_unit, convert_factor, extract_name_unit, format_name_unit
from objects.measurement import Measurement


class TestParseUnit(unittest.TestCase):
    def test_base_unit_no_prefix(self):
        f, b = parse_unit("V")
        self.assertEqual((f, b), (1.0, "V"))

    def test_mA_to_A(self):
        f, b = parse_unit("mA")
        self.assertAlmostEqual(f, 1e-3)
        self.assertEqual(b, "A")

    def test_kV(self):
        f, b = parse_unit("kV")
        self.assertAlmostEqual(f, 1e3)
        self.assertEqual(b, "V")

    def test_MOhm(self):
        f, b = parse_unit("MOhm")
        self.assertAlmostEqual(f, 1e6)
        self.assertEqual(b, "Ω")

    def test_GHz(self):
        f, b = parse_unit("GHz")
        self.assertAlmostEqual(f, 1e9)
        self.assertEqual(b, "Hz")

    def test_micro_u(self):
        f, b = parse_unit("us")
        self.assertAlmostEqual(f, 1e-6)
        self.assertEqual(b, "s")

    def test_micro_greek(self):
        f, b = parse_unit("μs")
        self.assertAlmostEqual(f, 1e-6)
        self.assertEqual(b, "s")

    def test_da_prefix(self):
        f, b = parse_unit("dam")
        self.assertAlmostEqual(f, 10)
        self.assertEqual(b, "m")

    def test_unknown_unit(self):
        f, b = parse_unit("foo")
        self.assertEqual((f, b), (1.0, "foo"))

    def test_hz_not_hecto(self):
        # Hz by měla být hertz, ne hecto-z
        f, b = parse_unit("Hz")
        self.assertEqual((f, b), (1.0, "Hz"))

    def test_pa_not_pico_a(self):
        f, b = parse_unit("Pa")
        self.assertEqual((f, b), (1.0, "Pa"))

    def test_cd_not_centi(self):
        f, b = parse_unit("cd")
        self.assertEqual((f, b), (1.0, "cd"))


class TestConvertFactor(unittest.TestCase):
    def test_mA_to_A(self):
        self.assertAlmostEqual(convert_factor("mA", "A"), 1e-3)

    def test_A_to_mA(self):
        self.assertAlmostEqual(convert_factor("A", "mA"), 1e3)

    def test_kV_to_mV(self):
        self.assertAlmostEqual(convert_factor("kV", "mV"), 1e6)

    def test_km_to_cm(self):
        self.assertAlmostEqual(convert_factor("km", "cm"), 1e5)

    def test_incompatible_units(self):
        with self.assertRaises(ValueError):
            convert_factor("mA", "V")


class TestExtractName(unittest.TestCase):
    def test_with_unit(self):
        name, unit = extract_name_unit("I [mA]")
        self.assertEqual(name, "I")
        self.assertEqual(unit, "mA")

    def test_without_unit(self):
        name, unit = extract_name_unit("R")
        self.assertEqual(name, "R")
        self.assertIsNone(unit)

    def test_empty_unit(self):
        name, unit = extract_name_unit("U [ ]")
        self.assertEqual(name, "U")
        self.assertIsNone(unit)

    def test_format_name_unit(self):
        self.assertEqual(format_name_unit("I", "A"), "I [A]")
        self.assertEqual(format_name_unit("R"), "R")


class TestMeasurementSiNormalize(unittest.TestCase):
    def test_normalize_mA(self):
        m = Measurement("I [mA]", [1000, 2000, 3000])
        n = m.si_normalize()
        self.assertEqual(n.name, "I [A]")
        self.assertAlmostEqual(n.values[0], 1.0)

    def test_no_change_base_unit(self):
        m = Measurement("U [V]", [1, 2, 3])
        n = m.si_normalize()
        self.assertEqual(n.name, "U [V]")
        self.assertAlmostEqual(n.values[0], 1.0)

    def test_preserves_u_B(self):
        m = Measurement("I [mA]", [100, 200, 300], u_B=10.0)
        n = m.si_normalize()
        self.assertAlmostEqual(n.u_B, 0.01)

    def test_convert_to(self):
        m = Measurement("I [mA]", [1000, 2000])
        n = m.convert_to("A")
        self.assertAlmostEqual(n.values[0], 1.0)
        self.assertEqual(n.name, "I [A]")

    def test_convert_incompatible_raises(self):
        m = Measurement("I [mA]", [1, 2])
        with self.assertRaises(ValueError):
            m.convert_to("V")


class TestConvertStrValue(unittest.TestCase):
    def setUp(self):
        from objects.units import convert_str_value

        self.fn = convert_str_value

    def test_preserve_decimals_for_zero(self):
        self.assertEqual(self.fn("0,00", 1000), "0,00")
        self.assertEqual(self.fn("0,000", 1000), "0,000")
        self.assertEqual(self.fn("0", 1000), "0")

    def test_scaling_integer_result(self):
        self.assertEqual(self.fn("1,50", 1000), "1500")
        self.assertEqual(self.fn("0,056", 1000), "56")
        self.assertEqual(self.fn("2,34", 1000), "2340")

    def test_scaling_down(self):
        self.assertEqual(self.fn("1500", 0.001), "1,500")
        self.assertEqual(self.fn("56", 0.001), "0,056")

    def test_factor_one_preserves(self):
        self.assertEqual(self.fn("0,20", 1.0), "0,20")
        self.assertEqual(self.fn("0,24", 1.0), "0,24")
        self.assertEqual(self.fn("1,234", 1.0), "1,234")

    def test_dash_placeholder(self):
        self.assertEqual(self.fn("-", 1000), "-")

    def test_empty_string(self):
        self.assertEqual(self.fn("", 1000), "")

    def test_invalid_value(self):
        self.assertEqual(self.fn("foo", 1000), "foo")

    def test_decimal_separator_dot(self):
        self.assertEqual(self.fn("1,5", 1000, "."), "1500")
        self.assertEqual(self.fn("0,5", 0.001, "."), "0.0005")


class TestAutoScale(unittest.TestCase):
    def test_no_scale_needed(self):
        from objects.units import auto_scale_exponent

        self.assertEqual(auto_scale_exponent([1.0, 2.0, 3.0]), 0)

    def test_milli_range(self):
        from objects.units import auto_scale_exponent

        self.assertEqual(auto_scale_exponent([0.001, 0.002, 0.003]), -3)

    def test_kilo_range(self):
        from objects.units import auto_scale_exponent

        self.assertEqual(auto_scale_exponent([1500, 2000, 2500]), 3)

    def test_mega_range(self):
        from objects.units import auto_scale_exponent

        self.assertEqual(auto_scale_exponent([2e6, 5e6]), 6)

    def test_apply_auto_scale(self):
        from objects.units import apply_auto_scale

        vals, unit = apply_auto_scale([1500, 2000], "A")
        self.assertEqual(unit, "kA")
        self.assertAlmostEqual(vals[0], 1.5)


if __name__ == "__main__":
    unittest.main()
