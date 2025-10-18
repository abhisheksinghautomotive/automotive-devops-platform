# BMW Battery DBC Signal Survey

This document summarizes key signals from the BMW high-voltage battery DBC (source: [BMW-PHEV-HV-Battery.dbc](https://github.com/jamiejones85/DBC-files/blob/master/BMW-PHEV-HV-Battery.dbc)), to enable a minimal MVP for simulation and telemetry. Only actionable cell voltage signals (no ambiguous data or pack-level signals) are included.

| **Message Name**      | **Message ID** | **Signal Name**    | **Start Bit / Length** | **Factor / Offset** | **Units** | **Range** | **Anomalies / Notes**                     |
|-----------------------|----------------|--------------------|------------------------|---------------------|-----------|-----------|-------------------------------------------|
| BMW_Module_4_P6       | 371            | Cell_16            | 1 \| 14                | (1, 1000)           | N/A       | [0 \| 0]   | Missing unit, offset=1000—needs review     |
| BMW_Module_1_P1       | 129            | Cell_1_Voltage     | 0 \| 14                | (1, 0)              | mV        | [0 \| 0]   |                                           |
| BMW_Module_1_P2       | 130            | Cell_4_voltage     | 0 \| 14                | (1, 0)              | mV        | [0 \| 0]   |                                           |
| BMW_Module_1_P3       | 131            | N/A                | N/A                    | N/A                 | N/A       | N/A       | Signal missing—excluded from MVP          |

---

## **Anomalies & Gaps**
- Most signals have range values [0 \| 0]; unsure if this is a DBC excerpt artifact.
- Units missing for Cell_16—cannot be included in MVP until clarified.
- BMW_Module_1_P3 has a missing signal; excluded for MVP.
- No pack-level state-of-charge, current, or temperature found in excerpt.

---

## **MVP Subset Decision**
- Include only signals with clear names, factor/offset, and units (Cell_1_Voltage and Cell_4_voltage).
- Exclude ambiguous signals (Cell_16 with offset anomaly, missing unit; all missing signals).

## **Assumptions**
- Cell voltages in millivolts (mV) where stated.
- All ambiguous or incomplete signals deferred until more DBC info is available.
- No new dependencies, parsers, or cloud costs introduced.

---

## **Open Questions**
- Is Cell_16’s offset of 1000 correct? What are the real units?
- Why are all ranges set to [0 \| 0]? Is real-world voltage range available elsewhere?
- Are there other module/cell voltage signals in the full DBC?

---

## **Reflection**
Manual DBC signal inspection is sufficient to ship a cell-voltage MVP, while deferring pack-level signals and ambiguous fields for future refinement.

---
