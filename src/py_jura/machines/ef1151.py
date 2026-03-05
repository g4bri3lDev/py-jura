"""Machine definition for JURA S8 (NAB) - EF1151."""

from __future__ import annotations

from py_jura._helpers import _milk_break, _water
from py_jura.models import Alert
from py_jura.products import Product, ProductDefinition, RangeOption, StrengthOption, Temperature, TemperatureOption

# ---------------------------------------------------------------------------
# Article numbers that map to this machine model
# ---------------------------------------------------------------------------

ARTICLE_NUMBERS: tuple[int, ...] = (
    15482,
    15483,
    15486,
    15487,
    15651,
    15652,
    15653,
    15694,
    15755,
)

ARTICLE_NAMES: dict[int, str] = {
    15482: "S8 (EB)",
    15483: "S8 (EB)",
    15486: "S8 (SB)",
    15487: "S8 (SB)",
    15651: "S8 (INTB)",
    15652: "S8 (NAB)",
    15653: "S8 (NAB)",
    15694: "S8 (KRB)",
    15755: "S8 (NAB)",
}

# ---------------------------------------------------------------------------
# Product definitions
# ---------------------------------------------------------------------------

PRODUCTS: dict[Product, ProductDefinition] = {
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
                9,
                10,
            ),
            default=8,
        ),
        water=_water(15, 80, 45),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.LOW,
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
                9,
                10,
            ),
            default=7,
        ),
        water=_water(25, 240, 100),
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
                9,
                10,
            ),
            default=8,
        ),
        water=_water(25, 240, 60),
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
                9,
                10,
            ),
            default=8,
        ),
        water=_water(15, 80, 25),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.LOW,
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
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
                9,
                10,
            ),
            default=8,
        ),
        water=_water(25, 240, 45),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.LOW,
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
        milk_break=_milk_break(20),
    ),
    Product.MILK_FOAM: ProductDefinition(
        product=Product.MILK_FOAM,
        name="Milk Foam",
    ),
    Product.MILK_PORTION: ProductDefinition(
        product=Product.MILK_PORTION,
        name="Milk",
        milk=RangeOption(arg=5, min=1, max=45, step=1, default=30),
    ),
    Product.HOT_WATER: ProductDefinition(
        product=Product.HOT_WATER,
        name="Hotwater Portion",
        water=_water(25, 300, 220),
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
    Product.CAFE_BARISTA: ProductDefinition(
        product=Product.CAFE_BARISTA,
        name="Cafe Barista",
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
                9,
                10,
            ),
            default=7,
        ),
        water=_water(25, 240, 45),
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
    Product.AMERICANO: ProductDefinition(
        product=Product.AMERICANO,
        name="Barista Lungo",
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
                9,
                10,
            ),
            default=7,
        ),
        water=_water(25, 240, 120),
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
    Product.CORTADO: ProductDefinition(
        product=Product.CORTADO,
        name="Cortado",
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
                9,
                10,
            ),
            default=8,
        ),
        water=_water(15, 80, 25),
        temperature=TemperatureOption(
            arg=7,
            options=(
                Temperature.LOW,
                Temperature.NORMAL,
                Temperature.HIGH,
            ),
            default=Temperature.HIGH,
        ),
    ),
    Product.RAF_COFFEE: ProductDefinition(
        product=Product.RAF_COFFEE,
        name="Sweet Latte",
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
                9,
                10,
            ),
            default=5,
        ),
        water=_water(25, 240, 60),
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
        name="Flat White",
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
                9,
                10,
            ),
            default=5,
        ),
        water=_water(25, 240, 60),
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
                9,
                10,
            ),
            default=8,
        ),
        water=_water(30, 160, 90),
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
    5: Alert(bit=5, key="outlet_missing", blocking=True),
    6: Alert(bit=6, key="rear_cover_missing", blocking=True),
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
    20: Alert(bit=20, key="close_powder_cover", blocking=True),
    21: Alert(bit=21, key="fill_powder", blocking=True),
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
    48: Alert(bit=48, key="close_front_cover", blocking=True),
    49: Alert(bit=49, key="left_bean_alert", blocking=False),
    50: Alert(bit=50, key="right_bean_alert", blocking=False),
    53: Alert(bit=53, key="empty_grounds_rtc", blocking=False),
    54: Alert(bit=54, key="ml_oz_status", blocking=False),
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
