MODULE 3 — SYNTHETIC FRAUD INTELLIGENCE DATASET
=================================================

This dataset is artificial and created for educational/testing purposes.
It does not contain real people, bank accounts, or financial transactions.

Files
-----
synthetic_cases.csv
  One row per synthetic complaint/case. Includes reported date, fraud category,
  reported loss, victim account, initial recipient, and case status.

synthetic_accounts.csv
  Synthetic account directory. Account IDs and bank IDs are invented.

synthetic_transactions.csv
  Synthetic transfer records linked to cases. Successful transfers may include
  reported initial transfers, onward transfers, and observed transfers.

scenario_truth.csv
  Test-only labels describing planted scenario types and expected pattern flags.
  Use this file to evaluate detection after implementing the intelligence engine.
  Do NOT use these labels as input features in the detection logic.

Scenario types planted
----------------------
shared_account: recipient accounts are intended to recur across cases.
multi_hop_chain: cases include sequential onward transfers.
repeat_activity: recipient accounts have multiple onward transfers.
ordinary_control: simpler cases without intentionally planted pattern flags.
mixed_pattern: combines more than one pattern.

Important limitations
---------------------
- This is synthetic data; results do not represent real-world fraud prevalence.
- Account flags are leads for testing, not proof of wrongdoing.
- Transfers are case-linked observations, not proof that the exact same funds
  were traced between accounts.
- Currency is INR and timestamps are synthetic.

Next step
---------
Build a Python intelligence engine to detect cross-case account reuse, repeated
activity, multi-hop paths, fraud-category trends, and reported-loss summaries.
Then build a Streamlit dashboard around those outputs.
