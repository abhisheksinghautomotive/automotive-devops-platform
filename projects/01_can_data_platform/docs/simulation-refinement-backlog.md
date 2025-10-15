# Simulation Realism Refinement Backlog

| Refinement Idea                      | Value/Why?                                                    | Effort | Priority | Doing Now?   |
|--------------------------------------|---------------------------------------------------------------|--------|----------|--------------|
| 1. Module-to-module variance         | Makes simulation more realistic, helps test analytics.        | S      | P1       | Yes          |
| 2. Use Gaussian noise for voltages   | Matches real-world sensor readings for better pipeline QA.    | S      | P1       | Yes          |
| 3. Simulate temperature effects      | Real batteries’ voltage shifts with temperature; needed for advanced fault testing. | M | P2 | Not now      |
| 4. Add degradation over cycles       | Models aging battery behavior, enables lifetime/statistics analytics. | M | P2 | Not now      |
| 5. Inject anomaly spikes             | Stress-tests event detection; models faults and spikes.       | S-M    | P2       | Not now      |
| 6. Simulate message dropouts         | Tests pipeline robustness against real-world CAN losses.      | S      | P2       | Not now      |

---

## Reflection

Focusing first on module variance and Gaussian noise will quickly add realism and de-risk analytics without overcomplicating the MVP. Advanced effects (temperature, aging, anomaly injection) are valuable but deferred to keep the scope lean and milestones achievable.

---

Time spent: **~10 min for backlog review**  
Blocked days: **None**
