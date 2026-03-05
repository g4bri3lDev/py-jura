"""Tests for machine definitions and the MACHINES registry."""

import pytest

from py_jura.machines import ARTICLE_NAMES, MACHINES, MachineDefinition
from py_jura.machines.ef533 import ARTICLE_NUMBERS as EF533_ARTICLE_NUMBERS
from py_jura.machines.ef533v2 import ARTICLE_NUMBERS as EF533V2_ARTICLE_NUMBERS
from py_jura.products import Product, Temperature


class TestMachinesRegistry:
    def test_registry_size(self):
        assert len(MACHINES) == 671

    def test_ef533_article_numbers_present(self):
        for art in EF533_ARTICLE_NUMBERS:
            assert art in MACHINES, f"Article {art} missing from MACHINES"

    def test_ef533v2_article_numbers_present(self):
        for art in EF533V2_ARTICLE_NUMBERS:
            assert art in MACHINES, f"Article {art} missing from MACHINES"

    def test_no_overlap_between_ef533_and_ef533v2(self):
        overlap = set(EF533_ARTICLE_NUMBERS) & set(EF533V2_ARTICLE_NUMBERS)
        assert overlap == set()

    def test_all_values_are_machine_definitions(self):
        for art, m in MACHINES.items():
            assert isinstance(m, MachineDefinition), f"{art} -> {type(m)}"

    def test_unknown_article_number_not_present(self):
        assert 99999 not in MACHINES

    def test_article_names_size(self):
        assert len(ARTICLE_NAMES) == 671

    def test_article_names_e8(self):
        assert ARTICLE_NAMES[15084] == "E8"

    def test_article_names_e7(self):
        # Article 15234 is an E7 within the EF533 family
        assert ARTICLE_NAMES[15234] == "E7"

    def test_article_names_covers_all_machines(self):
        assert set(ARTICLE_NAMES) == set(MACHINES)


class TestEF533Machine:
    @pytest.fixture
    def machine(self):
        return MACHINES[15084]  # E8

    def test_name(self, machine):
        assert "EF533" in machine.name or "E8" in machine.name

    def test_has_espresso(self, machine):
        assert Product.ESPRESSO in machine.products

    def test_espresso_water_default(self, machine):
        assert machine.products[Product.ESPRESSO].water.default == 45

    def test_espresso_water_range(self, machine):
        water = machine.products[Product.ESPRESSO].water
        assert water.min == 15
        assert water.max == 80
        assert water.step == 5

    def test_espresso_strength_values(self, machine):
        strength = machine.products[Product.ESPRESSO].strength
        assert strength.values == (1, 2, 3, 4, 5, 6, 7, 8)
        assert strength.default == 4

    def test_espresso_temperature_default_high(self, machine):
        temp = machine.products[Product.ESPRESSO].temperature
        assert temp.default == Temperature.HIGH

    def test_cappuccino_has_milk(self, machine):
        milk = machine.products[Product.CAPPUCCINO].milk
        assert milk is not None
        assert milk.default == 14

    def test_milk_portion_no_strength(self, machine):
        pd = machine.products[Product.MILK_PORTION]
        assert pd.strength is None
        assert pd.water is None
        assert pd.temperature is None
        assert pd.milk is not None

    def test_latte_macchiato_has_milk_break(self, machine):
        pd = machine.products[Product.LATTE_MACCHIATO]
        assert pd.milk_break is not None
        assert pd.milk_break.arg == 11

    def test_hot_water_has_three_temperatures(self, machine):
        temp = machine.products[Product.HOT_WATER].temperature
        assert Temperature.LOW in temp.options
        assert Temperature.NORMAL in temp.options
        assert Temperature.HIGH in temp.options

    def test_no_espresso_macchiato(self, machine):
        assert Product.ESPRESSO_MACCHIATO not in machine.products

    def test_has_11_products(self, machine):
        assert len(machine.products) == 11

    def test_blocking_alerts(self, machine):
        blocking_keys = {a.key for a in machine.alerts.values() if a.blocking}
        assert "fill_water" in blocking_keys
        assert "insert_tray" in blocking_keys
        assert "empty_grounds" in blocking_keys

    def test_non_blocking_alert(self, machine):
        assert machine.alerts[12].key == "heating_up"
        assert machine.alerts[12].blocking is False

    def test_has_48_alerts(self, machine):
        assert len(machine.alerts) == 48


class TestEF533V2Machine:
    @pytest.fixture
    def machine(self):
        return MACHINES[15247]  # E8 V2

    def test_has_espresso_macchiato(self, machine):
        assert Product.ESPRESSO_MACCHIATO in machine.products

    def test_has_lungo_barista(self, machine):
        assert Product.LUNGO_BARISTA in machine.products

    def test_has_espresso_doppio(self, machine):
        assert Product.ESPRESSO_DOPPIO in machine.products

    def test_has_hot_water_green_tea(self, machine):
        assert Product.HOT_WATER_GREEN_TEA in machine.products

    def test_espresso_macchiato_has_milk(self, machine):
        pd = machine.products[Product.ESPRESSO_MACCHIATO]
        assert pd.milk is not None

    def test_espresso_macchiato_has_milk_break(self, machine):
        pd = machine.products[Product.ESPRESSO_MACCHIATO]
        assert pd.milk_break is not None

    def test_lungo_barista_strength_default(self, machine):
        strength = machine.products[Product.LUNGO_BARISTA].strength
        assert strength.default == 6

    def test_has_more_products_than_ef533(self, machine):
        ef533 = MACHINES[15084]
        assert len(machine.products) > len(ef533.products)

    def test_inherits_ef533_alerts(self, machine):
        assert machine.alerts[1].key == "fill_water"
        assert machine.alerts[1].blocking is True


# ---------------------------------------------------------------------------
# Maintenance types
# ---------------------------------------------------------------------------


class TestMaintenanceTypes:
    @pytest.fixture(params=[15084, 15247])  # EF533 and EF533V2 article numbers
    def machine(self, request):
        return MACHINES[request.param]

    def test_counter_types_not_empty(self, machine):
        assert len(machine.maintenance_counter_types) > 0

    def test_percent_types_not_empty(self, machine):
        assert len(machine.maintenance_percent_types) > 0

    def test_counter_types_includes_cleaning(self, machine):
        assert "cleaning" in machine.maintenance_counter_types

    def test_counter_types_includes_decalc(self, machine):
        assert "decalc" in machine.maintenance_counter_types

    def test_percent_types_subset_of_counter_types(self, machine):
        assert set(machine.maintenance_percent_types).issubset(set(machine.maintenance_counter_types))

    def test_ef533_has_six_counter_types(self):
        m = MACHINES[15084]
        assert len(m.maintenance_counter_types) == 6

    def test_ef533_has_three_percent_types(self):
        m = MACHINES[15084]
        assert len(m.maintenance_percent_types) == 3
