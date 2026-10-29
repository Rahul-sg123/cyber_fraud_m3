SENTINEL — MODULE 3 COMPLETE INVESTIGATION UPGRADE

Copy app.py into your existing Module 3 project folder alongside:
- synthetic_cases.csv
- synthetic_transactions.csv
- synthetic_accounts.csv
- scenario_truth.csv
- requirements.txt

Your current requirements should include:
pandas
streamlit
networkx
plotly

Install if needed:
python -m pip install -r requirements.txt

Run:
python -m streamlit run app.py

Features:
1. Cross-case network connecting cases to shared initial recipient accounts.
2. Money-flow tracing with a step slider, role-colored nodes, account detail selector, and transaction totals.
3. Explainable case review score (0–100) with visible rule contributions.
4. Investigator decisions stored in local SQLite file investigator_review.db, with audit history and CSV export.
5. Scenario evaluation table with TP/FP/FN/TN, precision, recall, and F1 for four mapped pattern rules.
6. Case overview, filters, data tables, CSV exports.

Important:
- The score is a heuristic review score, not a probability.
- Scenario metrics are only meaningful if scenario_truth.csv labels and the documented rule mapping are correct. Check raw labels in the Scenario evaluation tab.
- All data is synthetic. Flags and account links are not proof of fraud.
- Back up your existing app.py before replacing it. The source CSV files are not included in this ZIP and are not modified.
