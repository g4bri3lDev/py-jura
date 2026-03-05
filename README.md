# py-jura

> Python library for controlling JURA coffee machines over Bluetooth

[![Tests](https://github.com/OpenDisplay-org/py-jura/actions/workflows/test.yml/badge.svg)](https://github.com/OpenDisplay-org/py-jura/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/py-jura)](https://pypi.org/project/py-jura/)
[![Python Version](https://img.shields.io/pypi/pyversions/py-jura)](https://pypi.org/project/py-jura/)

Brew drinks, check machine status, read maintenance counters, and track live brew progress - all from Python, over Bluetooth, with a simple async API.

> [!NOTE]
> Hardware testing has only been performed on a **JURA E8 (EF533, firmware EF533M V01.18)**. All other machine families should work, but are untested. Feedback and bug reports from other models are very welcome.

## Installation

```bash
pip install py-jura
# or with uv
uv add py-jura
```

Requires Python 3.11+ and a Bluetooth adapter supported by [bleak](https://github.com/hbldh/bleak).

## Quick start

```python
import asyncio
from py_jura import JuraMachine, MachineBlockedError, Product

async def main():
    async with JuraMachine("AA:BB:CC:DD:EE:FF") as machine:
        print(f"Connected to {machine.display_name}")  # e.g. "E8"

        try:
            await machine.brew(Product.ESPRESSO, strength=6, water_ml=40)
        except MachineBlockedError as e:
            print("Machine not ready:", [a.key for a in e.alerts])

asyncio.run(main())
```

`JuraMachine` is an async context manager. On entry it scans for the device, reads the BLE advertisement to identify the machine model and extract the encryption key, then connects and starts a background heartbeat. On exit it sends a graceful disconnect.

## Supported machines

| Series       | Models                                    |
|--------------|-------------------------------------------|
| E-line       | E4, E6, E7, E8                            |
| S-line       | S8                                        |
| Z-line       | Z6, Z8, Z10                               |
| J-line       | J6, J8, J10, J8 twin, J10 twin            |
| X-line       | X4, X6, X8, X10, X4c, X8c, X10c           |
| W-line       | W4, W8                                    |
| C-line       | C3, C8, C9                                |
| ENA          | ENA 4, ENA 5, ENA 8                       |
| GIGA         | GIGA 5, GIGA 6, GIGA X3/X7/X8/X9/X10, W10 |
| Professional | GIGA X3/X7/X8/X9 Professional, W3         |
| D-line       | D4, D6                                    |
| WE-line      | WE6, WE8                                  |



## API reference

### `JuraMachine(address, max_retries=3)`

| Parameter     | Description                                                                   |
|---------------|-------------------------------------------------------------------------------|
| `address`     | BLE address - `"AA:BB:CC:DD:EE:FF"` on Linux/Windows, UUID string on macOS    |
| `max_retries` | Reconnection attempts before raising `MachineDisconnectedError` (default `3`) |

**Identity properties** - available immediately after connecting:

| Property          | Type  | Description                                            |
|-------------------|-------|--------------------------------------------------------|
| `.address`        | `str` | BLE address passed at construction                     |
| `.article_number` | `int` | Article number from BLE advertisement                  |
| `.display_name`   | `str` | Customer-facing model name, e.g. `"E8"` or `"GIGA X8"` |

```python
async with JuraMachine("AA:BB:CC:DD:EE:FF") as machine:
    print(machine.article_number)  # 15084
    print(machine.display_name)    # "E8"
```

---

**Method summary**

| Method                | Returns            | Description                     |
|-----------------------|--------------------|---------------------------------|
| `get_status()`        | `MachineStatus`    | Active alerts and ready state   |
| `brew(product, ...)`  | -                  | Start brewing a product         |
| `cancel_brew()`       | -                  | Cancel the current brew         |
| `get_progress()`      | `BrewProgress`     | Real-time brew state            |
| `get_stats()`         | `MachineStats`     | Lifetime brew counts            |
| `get_daily_stats()`   | `MachineStats`     | Today's brew counts             |
| `get_maintenance()`   | `MaintenanceStats` | Maintenance counters and wear   |
| `get_about()`         | `MachineInfo`      | Firmware version strings        |
| `lock()` / `unlock()` | -                  | Barista mode (touchscreen lock) |
| `shutdown()`          | -                  | Power off the machine           |

---

### `get_status() → MachineStatus`

Reads the machine's current alert state.

```python
status = await machine.get_status()
print(status.is_ready)
for alert in status.alerts:
    print(alert.key, "blocking" if alert.blocking else "info")
```

| Field       | Type          | Description                                                          |
|-------------|---------------|----------------------------------------------------------------------|
| `.is_ready` | `bool`        | `True` when no blocking alerts are active                            |
| `.alerts`   | `list[Alert]` | Active alerts; each has `.key` (e.g. `"fill_water"`) and `.blocking` |

---

### `brew(product, *, strength, water_ml, temperature, milk_ml, milk_break_ml) → None`

Starts brewing. All option parameters are optional - omitted values use the machine's defaults.

```python
await machine.brew(Product.ESPRESSO)
await machine.brew(Product.ESPRESSO, strength=8, water_ml=35, temperature=Temperature.HIGH)
await machine.brew(Product.CAPPUCCINO, milk_ml=120)
```

| Parameter       | Type          | Description                                                 |
|-----------------|---------------|-------------------------------------------------------------|
| `product`       | `Product`     | Product to brew                                             |
| `strength`      | `int`         | Strength level (valid range is product- and model-specific) |
| `water_ml`      | `int`         | Water volume in ml                                          |
| `temperature`   | `Temperature` | `LOW`, `NORMAL`, or `HIGH`                                  |
| `milk_ml`       | `int`         | Milk volume in ml                                           |
| `milk_break_ml` | `int`         | Milk break duration in ml-equivalent                        |

**Raises:** `UnsupportedProductError`, `ValueError` (option out of range), `MachineBlockedError`

---

### `cancel_brew() → None`

Cancels the in-progress brew.

---

### `get_progress() → BrewProgress`

Reads the real-time brewing state.

```python
progress = await machine.get_progress()
print(progress.is_idle)   # True when idle
print(progress.is_done)   # True when product is ready
print(progress.product)   # Product enum member, or None
```

| Field      | Description                                                              |
|------------|--------------------------------------------------------------------------|
| `.is_idle` | `True` when state is `0x00`                                              |
| `.is_done` | `True` when state is `0x24` (ready) or `0x3E` (enjoy)                    |
| `.product` | Resolved `Product` enum member, or `None`                                |
| `.state`   | Raw state byte (`0x00` idle, `0x21` heating, `0x24` ready, `0x3E` enjoy) |

---

### `get_stats() → MachineStats`

Reads lifetime brew counts.

```python
stats = await machine.get_stats()
print(stats.total_count)
print(stats.product_counts[Product.ESPRESSO])
```

| Field             | Description                                                |
|-------------------|------------------------------------------------------------|
| `.total_count`    | Total brews across all products                            |
| `.product_counts` | `dict[Product, int]`; products with zero brews are omitted |

`get_daily_stats()` returns the same structure for today's counts only.

---

### `get_maintenance() → MaintenanceStats`

Reads maintenance counters and wear percentages.

```python
maint = await machine.get_maintenance()
print(maint.counters["cleaning"])    # times performed
print(maint.percentages["decalc"])  # remaining capacity 0–100
```

| Field          | Description                                                                |
|----------------|----------------------------------------------------------------------------|
| `.counters`    | `dict[str, int]` - how many times each maintenance was performed           |
| `.percentages` | `dict[str, int]` - remaining capacity 0–100 (0 = overdue, 100 = just done) |

Keys: `"cleaning"`, `"decalc"`, `"filter_change"`, `"cappu_rinse"`, `"coffee_rinse"`, `"cappu_clean"` (model-dependent).

---

### `get_about() → MachineInfo`

Reads firmware version strings.

```python
info = await machine.get_about()
print(info.machine_version)    # e.g. "J-EF533-V02.04"
print(info.bluefrog_version)   # BLE module firmware
```

---

### `lock() / unlock() → None`

Locks or unlocks the touchscreen (Barista mode).

---

### `shutdown() → None`

Sends the machine shutdown command.

---

## Products

<details>
<summary>Full product list (46 products)</summary>

| `Product`                | Drink                      |
|--------------------------|----------------------------|
| `RISTRETTO`              | Ristretto                  |
| `ESPRESSO`               | Espresso                   |
| `ESPRESSO_DOPPIO`        | Espresso Doppio            |
| `COFFEE`                 | Coffee                     |
| `CAPPUCCINO`             | Cappuccino                 |
| `ESPRESSO_MACCHIATO`     | Espresso Macchiato         |
| `LATTE_MACCHIATO`        | Latte Macchiato            |
| `MILK_COFFEE`            | Milk Coffee                |
| `MILK_PORTION`           | Milk Portion               |
| `MILK_FOAM`              | Milk Foam                  |
| `FLAT_WHITE`             | Flat White                 |
| `CAFE_BARISTA`           | Café Barista               |
| `LUNGO_BARISTA`          | Lungo Barista              |
| `CORTADO`                | Cortado                    |
| `LONG_BLACK`             | Long Black                 |
| `AMERICANO`              | Americano                  |
| `XL_LUNGO`               | XL Lungo                   |
| `MOCACCINO`              | Mocaccino                  |
| `RAF_COFFEE`             | Raf Coffee                 |
| `CHOCOLATE_MILK_FOAM`    | Chocolate Milk Foam        |
| `HOT_WATER`              | Hot Water                  |
| `HOT_WATER_GREEN_TEA`    | Hot Water (green tea temp) |
| `POT`                    | Pot                        |
| `POT_SPEED`              | Pot (Speed)                |
| `COFFEE_BIG`             | Coffee (large)             |
| `CAPPUCCINO_BIG`         | Cappuccino (large)         |
| `MILK_COFFEE_BIG`        | Milk Coffee (large)        |
| `LATTE_MACCHIATO_BIG`    | Latte Macchiato (large)    |
| `MILK_BIG`               | Milk (large)               |
| `HOT_WATER_BIG`          | Hot Water (large)          |
| `TWO_RISTRETTI`          | 2× Ristretto               |
| `TWO_ESPRESSI`           | 2× Espresso                |
| `TWO_COFFEES`            | 2× Coffee                  |
| `TWO_CAPPUCCINI`         | 2× Cappuccino              |
| `TWO_MILK_COFFEES`       | 2× Milk Coffee             |
| `TWO_ESPRESSO_MACCHIATI` | 2× Espresso Macchiato      |
| `TWO_LATTE_MACCHIATI`    | 2× Latte Macchiato         |
| `TWO_MILK_FOAM`          | 2× Milk Foam               |
| `TWO_MILK_PORTIONS`      | 2× Milk Portion            |
| `TWO_CAFE_BARISTAS`      | 2× Café Barista            |
| `TWO_LUNGO_BARISTAS`     | 2× Lungo Barista           |
| `TWO_LUNGOS`             | 2× Lungo                   |
| `TWO_CORTADOS`           | 2× Cortado                 |
| `TWO_ESPRESSI_ENA`       | 2× Espresso (ENA)          |
| `TWO_COFFEES_ENA`        | 2× Coffee (ENA)            |
| `TWO_FLAT_WHITES`        | 2× Flat White              |

</details>

Which products are available depends on the machine model. Attempting to brew an unsupported product raises `UnsupportedProductError`.

## `ARTICLE_NAMES`

A `dict[int, str]` mapping every article number to its customer-facing model name. Useful for scanning and discovery flows where you don't connect to the machine yet.

```python
from py_jura import ARTICLE_NAMES

ARTICLE_NAMES[15084]  # "E8"
ARTICLE_NAMES[15234]  # "E7"
```

## Exceptions

| Exception                  | When raised                                                |
|----------------------------|------------------------------------------------------------|
| `MachineNotFoundError`     | Device not found, or unrecognised article number           |
| `MachineDisconnectedError` | Not connected, or reconnection failed after `max_retries`  |
| `MachineBlockedError`      | Blocking alerts active; brew not started - check `.alerts` |
| `UnsupportedProductError`  | Product not available on this machine model                |
| `JuraError`                | Base class for all py-jura exceptions                      |

## Development

```bash
git clone https://github.com/OpenDisplay-org/py-jura.git
cd py-jura
uv sync --all-extras

uv run pytest tests/                    # unit tests
uv run pytest tests/ --cov=src/py_jura  # with coverage
uv run pytest -m hardware               # hardware tests (real machine required)
uv run ruff check .
uv run mypy src/py_jura
```

## Contributing

Contributions are welcome. Please open an issue before starting significant work so we can align on approach. Run tests and linting before submitting a PR.

## Acknowledgements

The BLE protocol implementation is based on reverse-engineering work by the [Jutta-Proto](https://github.com/Jutta-Proto) project, specifically [protocol-bt-cpp](https://github.com/Jutta-Proto/protocol-bt-cpp) - a C++ JURA protocol implementation released under GPL-3.0.
