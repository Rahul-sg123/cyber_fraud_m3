from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Module 3 | Fraud Network Intelligence", layout="wide")
ROOT = Path(__file__).resolve().parent

# Premium cyber-intelligence visual theme with subtle motion.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --line: rgba(137,168,215,.18); --cyan:#63e6e2; --blue:#6d8cff; }
html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
.stApp { background:radial-gradient(ellipse at 8% 0%,rgba(47,104,180,.20),transparent 34%),radial-gradient(ellipse at 92% 8%,rgba(102,65,180,.16),transparent 30%),linear-gradient(145deg,#080d18 0%,#0a1221 52%,#080d18 100%); }
[data-testid="stHeader"] { background:rgba(8,13,24,.72); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0b1323,#0a1020); border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:#dce8fa; }
.block-container { max-width:1500px; padding-top:1.5rem; padding-bottom:3rem; }
h1,h2,h3 { color:#f1f6ff; letter-spacing:-.035em; }
p, label, .stCaption { color:#a7b8d2; }
hr { border-color:var(--line); }
div[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(20,34,57,.9),rgba(13,22,39,.9)); border:1px solid var(--line); border-radius:17px; padding:17px 19px; box-shadow:0 12px 30px rgba(0,0,0,.12); transition:transform .22s ease,border-color .22s ease; }
div[data-testid="stMetric"]:hover { transform:translateY(-3px); border-color:rgba(99,230,226,.45); }
div[data-testid="stMetricLabel"] { color:#91a8c8 !important; }
div[data-testid="stMetricValue"] { color:#f4f8ff !important; font-weight:800; }
.stTabs [data-baseweb="tab-list"] { gap:7px; background:rgba(12,21,37,.76); padding:7px; border:1px solid var(--line); border-radius:15px; }
.stTabs [data-baseweb="tab"] { border-radius:10px; color:#9db0cd; padding:9px 15px; }
.stTabs [aria-selected="true"] { background:linear-gradient(110deg,rgba(99,230,226,.16),rgba(109,140,255,.18)); color:#f2fbff !important; }
.stButton button,.stDownloadButton button { border:1px solid rgba(99,230,226,.34); background:linear-gradient(105deg,rgba(31,89,110,.92),rgba(49,57,115,.92)); color:#f3ffff; border-radius:11px; font-weight:700; transition:transform .2s ease,filter .2s ease; }
.stButton button:hover,.stDownloadButton button:hover { transform:translateY(-2px); filter:brightness(1.15); color:white; border-color:rgba(99,230,226,.65); }
[data-testid="stDataFrame"],div[data-testid="stExpander"] { border:1px solid var(--line); border-radius:13px; overflow:hidden; }
.hero { position:relative; overflow:hidden; padding:28px 30px 25px; border:1px solid rgba(122,165,220,.23); border-radius:22px; background:linear-gradient(115deg,rgba(19,39,64,.95),rgba(18,25,49,.9) 56%,rgba(41,27,70,.8)); box-shadow:0 18px 60px rgba(0,0,0,.18); margin-bottom:23px; animation:riseIn .65s ease both; }
.hero:before { content:""; position:absolute; width:340px; height:340px; right:-80px; top:-190px; border-radius:50%; background:rgba(99,230,226,.13); filter:blur(5px); animation:orbitGlow 7s ease-in-out infinite alternate; }
.hero-kicker { color:#7ee8e2; text-transform:uppercase; letter-spacing:.2em; font:500 11px 'DM Mono',monospace; margin-bottom:10px; }
.hero-title { font-size:clamp(28px,3.2vw,43px); font-weight:800; letter-spacing:-.055em; color:#f3f7ff; line-height:1.08; }
.hero-sub { margin-top:11px; color:#a6bad7; font-size:14px; max-width:760px; line-height:1.7; }
.hero-status { display:inline-flex; align-items:center; gap:8px; margin-top:18px; border:1px solid rgba(99,230,226,.25); border-radius:99px; padding:6px 11px; background:rgba(99,230,226,.07); color:#a9f4ee; font:11px 'DM Mono',monospace; }
.status-dot { width:7px; height:7px; border-radius:50%; background:#63e6b5; box-shadow:0 0 0 4px rgba(99,230,181,.11); animation:pulse 1.8s infinite; }
.section-head { display:flex; align-items:center; gap:10px; margin:8px 0 14px; font-size:17px; font-weight:800; color:#eaf2ff; letter-spacing:-.03em; }
.section-mark { width:4px; height:19px; border-radius:9px; background:linear-gradient(#63e6e2,#7b8cff); box-shadow:0 0 15px rgba(99,230,226,.25); }
.pill { display:inline-block; padding:5px 9px; border-radius:99px; border:1px solid rgba(99,230,226,.24); background:rgba(99,230,226,.07); color:#9af1e8; font:10px 'DM Mono',monospace; letter-spacing:.05em; }
@keyframes pulse { 0%,100%{box-shadow:0 0 0 4px rgba(99,230,181,.10)} 50%{box-shadow:0 0 0 7px rgba(99,230,181,.02)} }
@keyframes orbitGlow { from{transform:translate(0,0) scale(1)} to{transform:translate(-25px,20px) scale(1.15)} }
@keyframes riseIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_csv(name):
    path = ROOT / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


cases = load_csv("synthetic_cases.csv")
transactions = load_csv("synthetic_transactions.csv")
accounts = load_csv("synthetic_accounts.csv")
truth = load_csv("scenario_truth.csv")

st.markdown("""
<div class="hero">
  <div class="hero-kicker">◈ SENTINEL / FINANCIAL CRIME INTELLIGENCE</div>
  <div class="hero-title">Fraud Network Intelligence</div>
  <div class="hero-sub">Connect cases, trace transaction paths, and surface account activity patterns in one investigator workspace. Designed for explainable triage on synthetic data.</div>
  <div class="hero-status"><span class="status-dot"></span> SYSTEM ONLINE &nbsp;·&nbsp; SYNTHETIC ENVIRONMENT</div>
</div>
""", unsafe_allow_html=True)

required = {
    "synthetic_cases.csv": (cases, ["case_id", "reported_date", "fraud_category", "reported_loss_inr",
                                    "victim_account_id", "initial_recipient_account_id", "case_status"]),
    "synthetic_transactions.csv": (transactions, ["transaction_id", "case_id", "source_account_id",
                                                  "destination_account_id", "amount_inr", "timestamp"]),
    "synthetic_accounts.csv": (accounts, ["account_id"]),
}
missing = []
for filename, (frame, cols) in required.items():
    absent = [c for c in cols if c not in frame.columns]
    if frame.empty or absent:
        missing.append(f"{filename}: " + ("file missing/empty" if frame.empty else "missing columns " + ", ".join(absent)))
if missing:
    st.error("The dashboard cannot read the expected dataset structure:\n\n- " + "\n- ".join(missing))
    st.stop()

cases["reported_date"] = pd.to_datetime(cases["reported_date"], errors="coerce")
transactions["timestamp"] = pd.to_datetime(transactions["timestamp"], errors="coerce")
cases["reported_loss_inr"] = pd.to_numeric(cases["reported_loss_inr"], errors="coerce").fillna(0)
transactions["amount_inr"] = pd.to_numeric(transactions["amount_inr"], errors="coerce").fillna(0)

with st.sidebar:
    st.markdown("### ◈ CONTROL CENTER")
    st.caption("Filter the intelligence workspace")
    categories = sorted(cases["fraud_category"].dropna().astype(str).unique())
    chosen_categories = st.multiselect("Fraud category", categories, default=categories)
    statuses = sorted(cases["case_status"].dropna().astype(str).unique())
    chosen_statuses = st.multiselect("Case status", statuses, default=statuses)
    search_account = st.text_input("Account ID contains", placeholder="e.g. ACC00010")

filtered_cases = cases[
    cases["fraud_category"].astype(str).isin(chosen_categories)
    & cases["case_status"].astype(str).isin(chosen_statuses)
].copy()
if search_account.strip():
    q = search_account.strip().upper()
    filtered_cases = filtered_cases[
        filtered_cases["victim_account_id"].astype(str).str.upper().str.contains(q, na=False)
        | filtered_cases["initial_recipient_account_id"].astype(str).str.upper().str.contains(q, na=False)
    ]

case_ids = set(filtered_cases["case_id"].astype(str))
filtered_tx = transactions[transactions["case_id"].astype(str).isin(case_ids)].copy()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Cases in view", f"{len(filtered_cases):,}")
m2.metric("Reported losses", f"₹{filtered_cases['reported_loss_inr'].sum():,.0f}")
m3.metric("Linked transactions", f"{len(filtered_tx):,}")
m4.metric("Unique accounts in transactions", f"{pd.unique(pd.concat([filtered_tx['source_account_id'], filtered_tx['destination_account_id']])).size:,}" if not filtered_tx.empty else "0")

tab_overview, tab_accounts, tab_network, tab_truth, tab_data = st.tabs(
    ["◉ Overview", "⌁ Account intelligence", "⌘ Network explorer", "◎ Scenario evaluation", "▤ Data vault"]
)

with tab_overview:
    st.markdown('<div class="section-head"><span class="section-mark"></span> Case telemetry</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        category_summary = filtered_cases.groupby("fraud_category", dropna=False).agg(
            cases=("case_id", "nunique"), reported_loss_inr=("reported_loss_inr", "sum")
        ).reset_index().sort_values("reported_loss_inr", ascending=False)
        st.plotly_chart(go.Figure(go.Bar(
            x=category_summary["fraud_category"], y=category_summary["cases"], name="Cases",
            hovertemplate="%{x}<br>Cases: %{y}<extra></extra>"
        )).update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Fraud category", yaxis_title="Cases", margin=dict(l=10,r=10,t=20,b=10)),
            use_container_width=True)
    with right:
        if filtered_cases["reported_date"].notna().any():
            daily = filtered_cases.dropna(subset=["reported_date"]).assign(
                day=lambda d: d["reported_date"].dt.date
            ).groupby("day").size().reset_index(name="cases")
            st.plotly_chart(go.Figure(go.Scatter(
                x=daily["day"], y=daily["cases"], mode="lines+markers",
                hovertemplate="%{x}<br>Cases: %{y}<extra></extra>"
            )).update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Reported date", yaxis_title="Cases", margin=dict(l=10,r=10,t=20,b=10)),
                use_container_width=True)
        else:
            st.info("No parseable reported dates available.")
    st.subheader("Cases")
    st.dataframe(filtered_cases.sort_values("reported_date", ascending=False), use_container_width=True, hide_index=True)

with st.spinner("Calculating transparent account review indicators..."):
    tx_all = transactions.copy()
    incoming = tx_all.groupby("destination_account_id").agg(
        incoming_tx_count=("transaction_id", "count"),
        incoming_amount_inr=("amount_inr", "sum"),
        distinct_senders=("source_account_id", "nunique")
    ).rename_axis("account_id")
    outgoing = tx_all.groupby("source_account_id").agg(
        outgoing_tx_count=("transaction_id", "count"),
        outgoing_amount_inr=("amount_inr", "sum"),
        distinct_recipients=("destination_account_id", "nunique")
    ).rename_axis("account_id")
    acct_ind = accounts.set_index("account_id").join(incoming).join(outgoing).fillna(0).reset_index()
    acct_ind["outgoing_incoming_ratio"] = acct_ind.apply(
        lambda r: round(r["outgoing_amount_inr"] / r["incoming_amount_inr"], 2)
        if r["incoming_amount_inr"] > 0 else 0, axis=1
    )
    # Cross-case links are computed from case-level victim/recipient references.
    recipient_cases = cases.groupby("initial_recipient_account_id")["case_id"].nunique()
    acct_ind["linked_cases_as_initial_recipient"] = acct_ind["account_id"].map(recipient_cases).fillna(0).astype(int)
    def reasons(row):
        flags = []
        if row["linked_cases_as_initial_recipient"] >= 2:
            flags.append("recipient linked to multiple cases")
        if row["incoming_tx_count"] >= 5:
            flags.append("high incoming transaction count")
        if row["outgoing_tx_count"] >= 5:
            flags.append("high outgoing transaction count")
        if row["incoming_amount_inr"] > 0 and row["outgoing_incoming_ratio"] >= 0.8:
            flags.append("outgoing amount is at least 80% of incoming amount")
        return "; ".join(flags) if flags else "no configured rule triggered"
    acct_ind["review_indicators"] = acct_ind.apply(reasons, axis=1)
    acct_ind["review_flag"] = acct_ind["review_indicators"] != "no configured rule triggered"

with tab_accounts:
    st.markdown('<div class="section-head"><span class="section-mark"></span> Account signals</div>', unsafe_allow_html=True)
    st.write("These are transparent heuristics computed from the supplied synthetic transaction and case data.")
    flagged = acct_ind[acct_ind["review_flag"]].sort_values(
        ["linked_cases_as_initial_recipient", "incoming_tx_count", "outgoing_tx_count"], ascending=False
    )
    a1, a2, a3 = st.columns(3)
    a1.metric("Accounts triggering a rule", f"{len(flagged):,}")
    a2.metric("Multi-case recipient accounts", f"{(acct_ind['linked_cases_as_initial_recipient'] >= 2).sum():,}")
    a3.metric("Accounts in metadata", f"{len(accounts):,}")
    show_all = st.checkbox("Show accounts without a triggered rule", value=False)
    table = acct_ind if show_all else flagged
    st.dataframe(table.sort_values(["review_flag", "linked_cases_as_initial_recipient"], ascending=False),
                 use_container_width=True, hide_index=True)
    st.download_button("Download account indicators CSV", acct_ind.to_csv(index=False).encode("utf-8"),
                       "account_review_indicators.csv", "text/csv")

with tab_network:
    st.markdown('<div class="section-head"><span class="section-mark"></span> Transaction path viewer</div>', unsafe_allow_html=True)
    all_case_options = sorted(filtered_cases["case_id"].astype(str).unique())
    if not all_case_options:
        st.info("No cases match the selected filters.")
    else:
        selected_case = st.selectbox("Choose a case", all_case_options)
        case_tx = transactions[transactions["case_id"].astype(str) == selected_case].copy()
        if case_tx.empty:
            st.info("No transaction rows are linked to this case.")
        else:
            G = nx.DiGraph()
            for row in case_tx.itertuples(index=False):
                src, dst = str(row.source_account_id), str(row.destination_account_id)
                G.add_edge(src, dst, amount=float(row.amount_inr), transaction_id=str(row.transaction_id))
            pos = nx.spring_layout(G, seed=17)
            edge_x, edge_y = [], []
            for u, v in G.edges():
                x0, y0 = pos[u]; x1, y1 = pos[v]
                edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
            edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1.5),
                                    hoverinfo="none", name="Transfers")
            node_x, node_y, labels, hover = [], [], [], []
            for node in G.nodes():
                node_x.append(pos[node][0]); node_y.append(pos[node][1]); labels.append(node)
                hover.append(f"Account: {node}<br>In-degree: {G.in_degree(node)}<br>Out-degree: {G.out_degree(node)}")
            node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text", text=labels,
                                    textposition="top center", hovertext=hover, hoverinfo="text",
                                    marker=dict(size=20, line=dict(width=1)), name="Accounts")
            fig = go.Figure([edge_trace, node_trace])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False, margin=dict(l=10,r=10,t=25,b=10),
                              xaxis=dict(visible=False), yaxis=dict(visible=False),
                              title=f"Case {selected_case} — account transfer links")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(case_tx.sort_values("timestamp"), use_container_width=True, hide_index=True)
            st.download_button("Download selected case transactions",
                               case_tx.to_csv(index=False).encode("utf-8"),
                               f"{selected_case}_transactions.csv", "text/csv")

with tab_truth:
    st.markdown('<div class="section-head"><span class="section-mark"></span> Synthetic scenario truth</div>', unsafe_allow_html=True)
    if truth.empty:
        st.info("scenario_truth.csv was not found; scenario evaluation is unavailable.")
    else:
        joined = filtered_cases.merge(truth, on="case_id", how="left", suffixes=("", "_truth"))
        st.write("This tab displays the supplied scenario labels. It does not claim model accuracy unless a detector is explicitly compared with a well-defined truth label.")
        st.dataframe(joined, use_container_width=True, hide_index=True)
        if "scenario_type" in truth.columns:
            summary = truth.groupby("scenario_type").size().reset_index(name="cases")
            st.plotly_chart(go.Figure(go.Bar(x=summary["scenario_type"], y=summary["cases"])).update_layout(
                xaxis_title="Scenario type", yaxis_title="Cases", margin=dict(l=10,r=10,t=20,b=10)),
                use_container_width=True)
        if "expected_pattern_flags" in truth.columns:
            st.caption("Expected pattern flags are provided by the synthetic scenario file; flags may be stored as text and need explicit parsing before calculating precision/recall.")

with tab_data:
    st.markdown('<div class="section-head"><span class="section-mark"></span> Data vault</div>', unsafe_allow_html=True)
    with st.expander("Cases"):
        st.dataframe(filtered_cases, use_container_width=True, hide_index=True)
    with st.expander("Transactions"):
        st.dataframe(filtered_tx, use_container_width=True, hide_index=True)
    with st.expander("Accounts"):
        st.dataframe(accounts, use_container_width=True, hide_index=True)
    with st.expander("Scenario truth"):
        st.dataframe(truth, use_container_width=True, hide_index=True)
    st.download_button("Download filtered cases CSV", filtered_cases.to_csv(index=False).encode("utf-8"),
                       "filtered_cases.csv", "text/csv")

st.divider()
st.markdown('<div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:#7187a8;font:10px DM Mono,monospace;letter-spacing:.08em;"><span>◈ SENTINEL INTELLIGENCE WORKSPACE</span><span>PROTOTYPE BUILD · SYNTHETIC DATA ONLY</span></div>', unsafe_allow_html=True)
st.caption("Safety note: all conclusions are review indicators only. Synthetic links and heuristic flags are not proof of wrongdoing.")
