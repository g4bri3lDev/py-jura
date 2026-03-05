"""Tests for product enums and option spec types."""

import pytest

from py_jura.products import (
    Product,
    ProductDefinition,
    RangeOption,
    StrengthOption,
    Temperature,
    TemperatureOption,
)


class TestProduct:
    def test_codes_are_correct(self):
        assert Product.ESPRESSO.value == 0x02
        assert Product.COFFEE.value == 0x03
        assert Product.CAPPUCCINO.value == 0x04
        assert Product.RISTRETTO.value == 0x01
        assert Product.HOT_WATER.value == 0x0D

    def test_lookup_by_value(self):
        assert Product(0x02) is Product.ESPRESSO


class TestTemperature:
    def test_values(self):
        assert Temperature.LOW.value == 0x00
        assert Temperature.NORMAL.value == 0x01
        assert Temperature.HIGH.value == 0x02


class TestStrengthOption:
    def test_frozen(self):
        s = StrengthOption(arg=3, values=(1, 2, 3, 4), default=2)
        with pytest.raises(Exception):
            s.default = 3  # type: ignore[misc]

    def test_fields(self):
        s = StrengthOption(arg=3, values=(1, 2, 3, 4, 5, 6, 7, 8), default=4)
        assert s.arg == 3
        assert s.values == (1, 2, 3, 4, 5, 6, 7, 8)
        assert s.default == 4


class TestRangeOption:
    def test_fields(self):
        r = RangeOption(arg=4, min=15, max=80, step=5, default=45)
        assert r.arg == 4
        assert r.min == 15
        assert r.max == 80
        assert r.step == 5
        assert r.default == 45

    def test_wire_value_formula(self):
        r = RangeOption(arg=4, min=15, max=80, step=5, default=45)
        assert r.default // r.step == 9  # 45ml at step=5 → wire value 9


class TestTemperatureOption:
    def test_fields(self):
        t = TemperatureOption(
            arg=7,
            options=(Temperature.NORMAL, Temperature.HIGH),
            default=Temperature.HIGH,
        )
        assert t.arg == 7
        assert Temperature.NORMAL in t.options
        assert t.default == Temperature.HIGH


class TestProductDefinition:
    def test_minimal(self):
        pd = ProductDefinition(product=Product.MILK_PORTION, name="Milk Portion")
        assert pd.strength is None
        assert pd.water is None
        assert pd.temperature is None
        assert pd.milk is None

    def test_with_options(self):
        pd = ProductDefinition(
            product=Product.ESPRESSO,
            name="Espresso",
            strength=StrengthOption(arg=3, values=tuple(range(1, 9)), default=4),
            water=RangeOption(arg=4, min=15, max=80, step=5, default=45),
            temperature=TemperatureOption(
                arg=7,
                options=(Temperature.NORMAL, Temperature.HIGH),
                default=Temperature.HIGH,
            ),
        )
        assert pd.product is Product.ESPRESSO
        assert pd.strength is not None
        assert pd.water is not None
        assert pd.temperature is not None
        assert pd.milk is None
