# Battery evolution model

Source: [BMW-PHEV-HV-Battery.dbc](https://github.com/jamiejones85/DBC-files/blob/master/BMW-PHEV-HV-Battery.dbc)

This document finalizes the pseudocode for generating outputs the realistic value for each cell signal in mV every cycle. It should run in a interval and output should be in JSON format

---

## **Included Signals**

| **Signal Name**    | **Units** | **Range (Physical)** | **Notes**         |
|--------------------|-----------|---------------------|-------------------|
| Cell_1_Voltage     | mV        | 3000–4200              | From DBC; scalar  |
| Cell_4_Voltage     | mV        | 3000–4200            | From DBC; scalar  |

---

## **Pseudocode for battery simulator**

For 100 cycles:
    Generate Cell_1_Voltage as a random number between 3000 and 4200 (mV)
    Generate Cell_4_Voltage as a random number between 3000 and 4200 (mV)
    Format output as:
        {
            "Cell_1_Voltage": value,
            "Cell_4_Voltage": value
        }
    Wait for 1 second before repeating

---

## **Output**

{
  "Cell_1_Voltage": 4119,
  "Cell_4_Voltage": 3867
}

---

## **Assumptions Section:**

“Cycle every 1 second. Output range: 3000–4200. Values are uniform random.”

---
