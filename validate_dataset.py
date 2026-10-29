import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent
cases = pd.read_csv(ROOT / "synthetic_cases.csv")
accounts = pd.read_csv(ROOT / "synthetic_accounts.csv")
tx = pd.read_csv(ROOT / "synthetic_transactions.csv")
truth = pd.read_csv(ROOT / "scenario_truth.csv")

checks = {
    "cases_nonempty": len(cases) > 0,
    "accounts_nonempty": len(accounts) > 0,
    "transactions_nonempty": len(tx) > 0,
    "case_ids_unique": cases["case_id"].is_unique,
    "account_ids_unique": accounts["account_id"].is_unique,
    "transaction_ids_unique": tx["transaction_id"].is_unique,
    "truth_has_one_row_per_case": len(truth) == len(cases) and truth["case_id"].is_unique,
    "all_case_ids_in_transactions_exist": set(tx["case_id"]).issubset(set(cases["case_id"])),
    "all_source_accounts_exist": set(tx["source_account_id"]).issubset(set(accounts["account_id"])),
    "all_destination_accounts_exist": set(tx["destination_account_id"]).issubset(set(accounts["account_id"])),
    "positive_transaction_amounts": (tx["amount_inr"] > 0).all(),
    "positive_reported_losses": (cases["reported_loss_inr"] > 0).all(),
    "all_records_marked_synthetic": (
        cases["synthetic_record"].astype(str).str.lower().eq("true").all()
        and accounts["synthetic_record"].astype(str).str.lower().eq("true").all()
        and tx["synthetic_record"].astype(str).str.lower().eq("true").all()
    ),
}
print("MODULE 3 DATASET VALIDATION")
print("=" * 32)
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
print()
print(f"Cases: {len(cases)}")
print(f"Accounts: {len(accounts)}")
print(f"Transactions: {len(tx)}")
print(f"Scenario truth rows: {len(truth)}")
if not all(checks.values()):
    raise SystemExit("Validation failed. Please inspect the CSV files.")
print("All validation checks passed.")
