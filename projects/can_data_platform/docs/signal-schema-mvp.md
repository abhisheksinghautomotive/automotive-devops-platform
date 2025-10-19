# BMW Battery MVP Signal List

Source: [BMW-PHEV-HV-Battery.dbc](https://github.com/jamiejones85/DBC-files/blob/master/BMW-PHEV-HV-Battery.dbc)

This document finalizes the minimal, actionable signal subset required for MVP simulation and telemetry. Only cell voltages with confirmed unit and format are included.

---

## **Included Signals**

| **Signal Name**    | **Units** | **Range (Physical)** | **Notes**         |
|--------------------|-----------|---------------------|-------------------|
| Cell_1_Voltage     | mV        | 0-5000              | From DBC; scalar  |
| Cell_4_Voltage     | mV        | 0-5000              | From DBC; scalar  |

---

## **Excluded Signals**

- **Cell_16**
  - Missing unit, offset value unverified, possible anomaly
- **BMW_Module_1_P3**
  - No signal defined in DBC

---

## **Derived Stats**

- **min_voltage**: minimum value among included cell voltages
  - `min([Cell_1_Voltage, Cell_4_Voltage])`
- **max_voltage**: maximum value among included cell voltages
  - `max([Cell_1_Voltage, Cell_4_Voltage])`
- **avg_voltage**: average value among included cell voltages
  - `avg([Cell_1_Voltage, Cell_4_Voltage])`

*Constraint:*
- `min_voltage ≤ avg_voltage ≤ max_voltage`

---

## **Assumptions**

- All cell voltages in millivolts (mV)
- Acceptable range for simulation: 0–5000 mV
- Only explicitly listed signals are available and reliable

---

## **Reflection**

Finalizing a minimal signal schema ensures a lean MVP, by using only well-defined, unit-confirmed voltages and deferring ambiguous fields for future analysis.

---

_Time Spent: 30 mins
_Blocked Days: None_
