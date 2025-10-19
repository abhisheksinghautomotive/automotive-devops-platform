| **Message Name**      | **Message ID** | **Signal Name**    | **Start Bit / Length** | **Factor / Offset** | **Units** | **Range** | **Anomalies / Notes**                     |
|-----------------------|----------------|--------------------|------------------------|---------------------|-----------|-----------|-------------------------------------------|
| BMW_Module_4_P6       | 371            | Cell_16            | 1 \| 14                | (1, 1000)           | Unknown   | [0 \| 0]   | Missing unit, offset=1000—needs review     |
| BMW_Module_1_P1       | 129            | Cell_1_Voltage     | 0 \| 14                | (1, 0)              | mV        | [0 \| 0]   |                                           |
| BMW_Module_1_P2       | 130            | Cell_4_Voltage     | 0 \| 14                | (1, 0)              | mV        | [0 \| 0]   |                                           |
| BMW_Module_1_P3       | 131            | N/A                | N/A                    | N/A                 | N/A       | N/A       | Signal missing—excluded from MVP          |

---

Reflection:
Created normalized DBC signal table; flagged missing fields and ambiguous signals for future refinement.

Time spent: ~20 minutes
Blockers: None

---
