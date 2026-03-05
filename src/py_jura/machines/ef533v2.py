"""Machine definition for JURA E8 - EF533V2."""

from __future__ import annotations

from py_jura._helpers import _milk, _milk_break, _water
from py_jura.models import Alert
from py_jura.products import Product, ProductDefinition, StrengthOption, Temperature, TemperatureOption

# ---------------------------------------------------------------------------
# Article numbers that map to this machine model
# ---------------------------------------------------------------------------

ARTICLE_NUMBERS: tuple[int, ...] = (
    14006,
    15235,
    15247,
    15250,
    15251,
    15266,
    15267,
    15268,
    15270,
    15271,
    15272,
    15279,
    15288,
    15295,
    15306,
    15307,
    15341,
)

ARTICLE_NAMES: dict[int, str] = {
    14006: "E8 60Hz",
    15235: "E8",
    15247: "E8",
    15250: "E800",
    15251: "E800",
    15266: "E801",
    15267: "E8",
    15268: "E8",
    15270: "E8",
    15271: "E8",
    15272: "E8",
    15279: "E800",
    15288: "E8",
    15295: "E80",
    15306: "E8",
    15307: "E800",
    15341: "E8",
}

# ---------------------------------------------------------------------------
# Product definitions
# ---------------------------------------------------------------------------

PRODUCTS: dict[Product, ProductDefinition] = {
    Product.RISTRETTO: ProductDefinition(
        product=Product.RISTRETTO,
        name="Ristretto",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=6,
        ),
        water=_water(15, 80, 25),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
    ),
    Product.ESPRESSO: ProductDefinition(
        product=Product.ESPRESSO,
        name="Espresso",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=6,
        ),
        water=_water(15, 80, 45),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
    ),
    Product.COFFEE: ProductDefinition(
        product=Product.COFFEE,
        name="Coffee",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=4,
        ),
        water=_water(25, 240, 100),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.NORMAL,
        ),
    ),
    Product.CAPPUCCINO: ProductDefinition(
        product=Product.CAPPUCCINO,
        name="Cappuccino",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=6,
        ),
        water=_water(25, 240, 60),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.NORMAL,
        ),
        milk=_milk(14),
    ),
    Product.ESPRESSO_MACCHIATO: ProductDefinition(
        product=Product.ESPRESSO_MACCHIATO,
        name="Espresso Macchiato",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=6,
        ),
        water=_water(15, 80, 25),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.NORMAL,
        ),
        milk=_milk(3),
        milk_break=_milk_break(0),
    ),
    Product.LATTE_MACCHIATO: ProductDefinition(
        product=Product.LATTE_MACCHIATO,
        name="Latte Macchiato",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=6,
        ),
        water=_water(25, 240, 45),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
        milk=_milk(22),
        milk_break=_milk_break(30),
    ),
    Product.TWO_RISTRETTI: ProductDefinition(
        product=Product.TWO_RISTRETTI,
        name="2 Ristretti",
        water=_water(15, 80, 25),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
    ),
    Product.TWO_ESPRESSI: ProductDefinition(
        product=Product.TWO_ESPRESSI,
        name="2 Espressi",
        water=_water(15, 80, 45),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
    ),
    Product.TWO_COFFEES: ProductDefinition(
        product=Product.TWO_COFFEES,
        name="2 Coffee",
        water=_water(25, 240, 100),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.NORMAL,
        ),
    ),
    Product.MILK_PORTION: ProductDefinition(
        product=Product.MILK_PORTION,
        name="Milk Portion",
        milk=_milk(20),
    ),
    Product.HOT_WATER: ProductDefinition(
        product=Product.HOT_WATER,
        name="Hotwater Portion(normal)",
        water=_water(25, 450, 220),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.LOW,
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.LOW,
        ),
    ),
    Product.HOT_WATER_GREEN_TEA: ProductDefinition(
        product=Product.HOT_WATER_GREEN_TEA,
        name="Hotwater Portion(Green tea)",
        water=_water(25, 450, 220),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.LOW,
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.NORMAL,
        ),
    ),
    Product.FLAT_WHITE: ProductDefinition(
        product=Product.FLAT_WHITE,
        name="1 Flat White",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=4,
        ),
        water=_water(25, 240, 60),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.NORMAL,
        ),
        milk=_milk(14),
    ),
    Product.LUNGO_BARISTA: ProductDefinition(
        product=Product.LUNGO_BARISTA,
        name="1 coffee special",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=6,
        ),
        water=_water(25, 240, 145),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.NORMAL,
        ),
    ),
    Product.ESPRESSO_DOPPIO: ProductDefinition(
        product=Product.ESPRESSO_DOPPIO,
        name="Espresso Doppio",
        strength=StrengthOption(
            arg=3,
            values=(
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
            ),
            default=6,
        ),
        water=_water(30, 160, 90),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.NORMAL,
        ),
    ),
    Product.TWO_LUNGO_BARISTAS: ProductDefinition(
        product=Product.TWO_LUNGO_BARISTAS,
        name="2 coffee special",
        water=_water(25, 240, 145),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
    ),
}

# ---------------------------------------------------------------------------
# Alert definitions
# ---------------------------------------------------------------------------

ALERTS: dict[int, Alert] = {
    0: Alert(bit=0, key="insert_tray", blocking=True),
    1: Alert(bit=1, key="fill_water", blocking=True),
    2: Alert(bit=2, key="empty_grounds", blocking=True),
    3: Alert(bit=3, key="empty_tray", blocking=True),
    4: Alert(bit=4, key="insert_coffee_bin", blocking=True),
    5: Alert(bit=5, key="outlet_missing", blocking=False),
    6: Alert(bit=6, key="rear_cover_missing", blocking=False),
    7: Alert(bit=7, key="milk_alert", blocking=False),
    8: Alert(bit=8, key="fill_system", blocking=True),
    9: Alert(bit=9, key="system_filling", blocking=False),
    10: Alert(bit=10, key="no_beans", blocking=False),
    11: Alert(bit=11, key="welcome", blocking=False),
    12: Alert(bit=12, key="heating_up", blocking=False),
    13: Alert(bit=13, key="coffee_ready", blocking=False),
    14: Alert(bit=14, key="no_milk_milk_sensor", blocking=False),
    15: Alert(bit=15, key="error_milk_milk_sensor", blocking=False),
    16: Alert(bit=16, key="no_signal_milk_sensor", blocking=False),
    17: Alert(bit=17, key="please_wait", blocking=True),
    18: Alert(bit=18, key="coffee_rinsing", blocking=False),
    19: Alert(bit=19, key="ventilation_closed", blocking=False),
    20: Alert(bit=20, key="close_powder_cover", blocking=False),
    21: Alert(bit=21, key="fill_powder", blocking=False),
    22: Alert(bit=22, key="system_emptying", blocking=False),
    23: Alert(bit=23, key="not_enough_powder", blocking=False),
    24: Alert(bit=24, key="remove_water_tank", blocking=False),
    25: Alert(bit=25, key="press_rinse", blocking=False),
    26: Alert(bit=26, key="goodbye", blocking=False),
    27: Alert(bit=27, key="periphery_alert", blocking=False),
    28: Alert(bit=28, key="powder_product", blocking=False),
    29: Alert(bit=29, key="program_mode_status", blocking=True),
    30: Alert(bit=30, key="error_status", blocking=True),
    31: Alert(bit=31, key="enjoy_product", blocking=False),
    32: Alert(bit=32, key="filter_alert", blocking=False),
    33: Alert(bit=33, key="decalc_alert", blocking=False),
    34: Alert(bit=34, key="cleaning_alert", blocking=False),
    35: Alert(bit=35, key="cappu_rinse_alert", blocking=False),
    36: Alert(bit=36, key="energy_safe", blocking=False),
    37: Alert(bit=37, key="active_rf_filter", blocking=False),
    38: Alert(bit=38, key="remotescreen", blocking=False),
    39: Alert(bit=39, key="lockedkeys", blocking=False),
    40: Alert(bit=40, key="close_tab", blocking=True),
    41: Alert(bit=41, key="cappu_clean_alert", blocking=False),
    42: Alert(bit=42, key="info_cappu_clean_alert", blocking=False),
    43: Alert(bit=43, key="info_coffee_clean_alert", blocking=False),
    44: Alert(bit=44, key="info_decalc_alert", blocking=False),
    45: Alert(bit=45, key="info_filter_used_up_alert", blocking=False),
    46: Alert(bit=46, key="steam_ready", blocking=False),
    47: Alert(bit=47, key="switchoff_delay_active", blocking=True),
}

# ---------------------------------------------------------------------------
# Maintenance slot ordering
# ---------------------------------------------------------------------------

MAINTENANCE_COUNTER_TYPES: tuple[str, ...] = (
    "cleaning",
    "filter_change",
    "decalc",
    "cappu_rinse",
    "coffee_rinse",
    "cappu_clean",
)

MAINTENANCE_PERCENT_TYPES: tuple[str, ...] = (
    "cleaning",
    "filter_change",
    "decalc",
)
