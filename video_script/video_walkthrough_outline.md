# 3–5 Minute Video Walkthrough

## 0:00–0:45 — Problem
- Explain the stockout vs. overstocking problem.
- Explain why bars need a dynamic inventory policy.
- Show the project objective.

## 0:45–1:45 — Data & Modeling
- Show the raw transaction fields.
- Explain conservation validation.
- Explain conversion to daily Bar + Brand consumption.
- Show EDA: top items and weekday pattern.
- Explain the temporal train/test split.
- Mention the baseline, Holt-Winters, and Random Forest models.

## 1:45–3:00 — Par Level & Simulation
- Explain:
  Par Level = Lead-Time Demand + Safety Stock
- Explain the service-level Z value.
- Show forecasted demand and inventory simulation.
- Explain stockout days, lost volume, average inventory, and turnover.

## 3:00–4:00 — Business Impact & Production
- Explain that the numerical impact depends on the actual dataset.
- Show model KPI table.
- Explain how daily recommendations could be delivered to bar managers.
- Mention production risks: lead-time variability, holidays/promotions, pouring waste and data drift.

## 4:00–5:00 — Conclusion
- Summarize the pipeline.
- Explain how the solution converts historical inventory records into an operational reorder recommendation.
- Show the final folder structure and README.
