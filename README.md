# Network Flow Anomaly Detection Plan

**Dataset:** [UNSW-NB15 (Cleaned)](https://www.kaggle.com/datasets/krish4n/unsw-nb15-cleaned)
This dataset will be easiest to use and focus on

**Idea:** Take one network flow and answer two questions:
1. **Normal or attack?**
2. **If attack, what kind?**

## Steps

1. Get the data, prep it, split it into train / validation / test.
2. **Tier 1:** detect normal vs attack; pick a cutoff that limits false alarms.
3. **Tier 2:** classify the 9 attack families.
4. Measure each tier honestly and see if both got it right.
5. Build a GUI gradio demo and write report.

## Measure

- Tier 1: precision, recall, false positive rate, F1, PR-AUC.
- Tier 2: per-family precision/recall/F1.
- Rare attacks and false alarms are what matter.