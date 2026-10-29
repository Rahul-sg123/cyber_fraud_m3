from pathlib import Path
import json
import sqlite3
from datetime import datetime

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "investigator_review.db"

st.set_page_config(page_title="Sentinel | Fraud Intelligence", page_icon="S", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --bg:#10161d; --panel:#18222c; --line:#2a3744; --ink:#e8edf1; --muted:#9baab7; --teal:#68c7bb; --amber:#e6b566; --red:#d97d76; --purple:#b89ae8; }
html,body,[class*="css"] { font-family:'Manrope',sans-serif; }
.stApp { background:linear-gradient(135deg,#10161d,#111a22 60%,#121920); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(16,22,29,.94); }
[data-testid="stSidebar"] { background:#131b23; border-right:1px solid var(--line); }
.block-container { max-width:1500px; padding-top:1.25rem; padding-bottom:3rem; }
h1,h2,h3 { letter-spacing:-.035em; color:#edf2f5; }
p,label,.stCaption { color:#aab7c2; }
hr { border-color:var(--line); }
[data-testid="stMetric"] { background:#18222c; border:1px solid #2b3946; border-radius:12px; padding:14px 17px; transition:transform .18s ease,border-color .18s ease; }
[data-testid="stMetric"]:hover { transform:translateY(-2px); border-color:var(--teal); }
[data-testid="stMetricLabel"] { color:var(--muted)!important; font-size:.82rem; }
[data-testid="stMetricValue"] { color:#f0f4f6!important; font-weight:750; }
.stTabs [data-baseweb="tab-list"] { gap:5px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { color:#aab7c2; padding:10px 13px; }
.stTabs [aria-selected="true"] { color:#80d8cc!important; border-bottom-color:var(--teal)!important; }
.stButton button,.stDownloadButton button { border-radius:8px; border:1px solid #477b79; background:#203a3b; color:#e8f4f2; transition:all .18s ease; }
.stButton button:hover,.stDownloadButton button:hover { border-color:var(--teal); background:#294849; transform:translateY(-1px); color:white; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; overflow:hidden; }
div[data-testid="stExpander"] { border:1px solid var(--line); border-radius:10px; background:#141d26; }
.hero { border:1px solid #2c4149; border-radius:14px; padding:21px 25px; margin-bottom:20px; background:linear-gradient(105deg,#192630,#18212b 62%,#202c30); position:relative; overflow:hidden; animation:fadeUp .4s ease-out both; }
.hero:after { content:""; position:absolute; right:-85px; top:-140px; width:330px; height:330px; border:1px solid rgba(104,199,187,.18); border-radius:50%; box-shadow:0 0 0 32px rgba(104,199,187,.025),0 0 0 68px rgba(104,199,187,.02); pointer-events:none; }
.kicker { font:500 11px 'DM Mono',monospace; text-transform:uppercase; letter-spacing:.13em; color:#81cfc4; }
.hero h1 { margin:8px 0 7px; font-size:clamp(27px,3vw,38px); font-weight:800; }
.hero p { max-width:800px; line-height:1.65; margin:0; color:#adbbc6; font-size:14px; }
.section { margin:8px 0 12px; font-weight:750; font-size:17px; color:#e8edf1; }
.section:before { content:""; display:inline-block; height:17px; width:3px; border-radius:3px; background:var(--teal); margin-right:10px; vertical-align:-3px; }
.note { background:#19252d; border:1px solid #30434b; border-radius:9px; padding:11px 13px; color:#b9c8d0; font-size:12px; }
.pill { display:inline-block; border:1px solid #35535a; background:#1b3035; color:#91d7cd; border-radius:99px; padding:4px 8px; font:10px 'DM Mono',monospace; }
@keyframes fadeUp { from {opacity:0;transform:translateY(5px)} to {opacity:1;transform:translateY(0)} }
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>
""", unsafe_allow_html=True)


def load_csv(filename):
    path = ROOT / filename
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS investigator_reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            reviewer TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT NOT NULL,
            related_case_id TEXT,
            notes TEXT
        )""")
        con.commit()


def get_reviews():
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query("SELECT * FROM investigator_reviews ORDER BY review_id DESC", con)


def save_review(reviewer, entity_type, entity_id, decision, reason, related_case_id, notes):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""INSERT INTO investigator_reviews
        (created_at, reviewer, entity_type, entity_id, decision, reason, related_case_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now().astimezone().isoformat(timespec="seconds"), reviewer, entity_type,
         entity_id, decision, reason, related_case_id, notes))
        con.commit()


def safe_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def style_fig(fig, height=470):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=28, b=8), height=height,
        font=dict(family="Manrope, sans-serif", color="#c6d1d9"),
        hoverlabel=dict(bgcolor="#18222c", bordercolor="#45606a", font_color="#eef4f6")
    )
    return fig


def build_case_features(cases, tx):
    """Transparent per-case feature engineering; not a trained model."""
    rows = []
    case_by_id = cases.set_index(cases["case_id"].astype(str), drop=False)
    tx = tx.copy()
    tx["timestamp"] = pd.to_datetime(tx["timestamp"], errors="coerce")
    tx["amount_inr"] = safe_num(tx["amount_inr"])
    for _, case in cases.iterrows():
        cid = str(case["case_id"])
        recipient = str(case["initial_recipient_account_id"])
        case_tx = tx[tx["case_id"].astype(str) == cid].sort_values("timestamp")
        first_time = case_tx["timestamp"].min() if not case_tx.empty else pd.NaT
        # Related movements from/to recipient, including transfers filed under other cases.
        recipient_tx = tx[(tx["source_account_id"].astype(str) == recipient) |
                          (tx["destination_account_id"].astype(str) == recipient)].copy()
        all_recipient_cases = cases[cases["initial_recipient_account_id"].astype(str) == recipient]["case_id"].astype(str).nunique()
        incoming = tx[tx["destination_account_id"].astype(str) == recipient]
        outgoing = tx[tx["source_account_id"].astype(str) == recipient]
        outgoing_after = pd.DataFrame()
        if pd.notna(first_time):
            outgoing_after = outgoing[outgoing["timestamp"] >= first_time]
        rapid = False
        if pd.notna(first_time) and not outgoing_after.empty:
            rapid = bool(((outgoing_after["timestamp"] - first_time) <= pd.Timedelta(minutes=60)).any())
        # Count distinct senders into recipient within 72 hours of this case's first transfer.
        multi_in = False
        if pd.notna(first_time):
            window_in = incoming[incoming["timestamp"].between(first_time - pd.Timedelta(hours=72),
                                                               first_time + pd.Timedelta(hours=72))]
            multi_in = window_in["source_account_id"].astype(str).nunique() >= 2
        # Graph reachable from the initial recipient within timestamp-ordered transaction rows for this case.
        G = nx.DiGraph()
        for row in case_tx.itertuples(index=False):
            if pd.notna(row.timestamp) and (pd.isna(first_time) or row.timestamp >= first_time):
                G.add_edge(str(row.source_account_id), str(row.destination_account_id))
        depth = 0
        if recipient in G:
            try:
                lengths = nx.single_source_shortest_path_length(G, recipient)
                depth = max(lengths.values()) if lengths else 0
            except Exception:
                depth = 0
        multi_hop = depth >= 2
        rows.append({
            "case_id": cid,
            "shared_account": all_recipient_cases >= 2,
            "rapid_onward_transfer": rapid,
            "multiple_incoming": multi_in,
            "multi_hop": multi_hop,
            "recipient_case_count": all_recipient_cases,
            "recipient_incoming_count": int(len(incoming)),
            "recipient_outgoing_count": int(len(outgoing)),
            "recipient_incoming_amount": float(incoming["amount_inr"].sum()),
            "recipient_outgoing_amount": float(outgoing["amount_inr"].sum()),
            "max_path_depth": int(depth),
            "first_transaction_time": first_time,
        })
    return pd.DataFrame(rows)


def parse_truth_flags(row):
    """Map scenario type/flag text into the four documented scenario flags."""
    raw = " ".join(str(row.get(c, "")) for c in ["scenario_type", "expected_pattern_flags"]).lower()
    mapping = {
        "shared_account": ["shared_account", "shared account", "shared", "cross_case", "cross case"],
        "rapid_onward_transfer": ["rapid_onward_transfer", "rapid onward", "rapid_transfer", "rapid transfer", "onward_transfer", "onward transfer"],
        "multiple_incoming": ["multiple_incoming", "multiple incoming", "many incoming", "multiple_payments"],
        "multi_hop": ["multi_hop", "multi hop", "multi-hop", "hop"],
    }
    flags = {}
    for key, terms in mapping.items():
        flags[key] = any(term in raw for term in terms)
    return flags


def metric_values(y_true, y_pred):
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "Precision": precision, "Recall": recall, "F1": f1}


init_db()
cases = load_csv("synthetic_cases.csv")
transactions = load_csv("synthetic_transactions.csv")
accounts = load_csv("synthetic_accounts.csv")
truth = load_csv("scenario_truth.csv")

st.markdown("""
<div class="hero">
  <div class="kicker">SENTINEL / CASE INTELLIGENCE</div>
  <h1>Fraud Network Investigation</h1>
  <p>Connect reports across cases, trace the movement of funds, and record investigator decisions. Designed as a transparent review workspace using synthetic data.</p>
</div>
""", unsafe_allow_html=True)

required = {
    "synthetic_cases.csv": (cases, ["case_id","reported_date","fraud_category","reported_loss_inr","victim_account_id","initial_recipient_account_id","case_status"]),
    "synthetic_transactions.csv": (transactions, ["transaction_id","case_id","source_account_id","destination_account_id","amount_inr","timestamp"]),
    "synthetic_accounts.csv": (accounts, ["account_id"]),
}
problems = []
for filename, (frame, cols) in required.items():
    absent = [c for c in cols if c not in frame.columns]
    if frame.empty or absent:
        problems.append(f"{filename}: " + ("missing or empty" if frame.empty else "missing columns: " + ", ".join(absent)))
if problems:
    st.error("Dataset validation failed:\n\n- " + "\n- ".join(problems))
    st.stop()

cases["case_id"] = cases["case_id"].astype(str)
cases["reported_date"] = pd.to_datetime(cases["reported_date"], errors="coerce")
cases["reported_loss_inr"] = safe_num(cases["reported_loss_inr"])
transactions["case_id"] = transactions["case_id"].astype(str)
transactions["timestamp"] = pd.to_datetime(transactions["timestamp"], errors="coerce")
transactions["amount_inr"] = safe_num(transactions["amount_inr"])
for c in ["source_account_id", "destination_account_id"]:
    transactions[c] = transactions[c].astype(str)
accounts["account_id"] = accounts["account_id"].astype(str)

with st.sidebar:
    st.markdown("### Investigation filters")
    categories = sorted(cases["fraud_category"].dropna().astype(str).unique())
    selected_categories = st.multiselect("Fraud category", categories, default=categories)
    statuses = sorted(cases["case_status"].dropna().astype(str).unique())
    selected_statuses = st.multiselect("Case status", statuses, default=statuses)
    st.divider()
    st.caption("Data source: synthetic records")
    st.caption("Risk scores are triage indicators, not findings of fraud.")

filtered_cases = cases[cases["fraud_category"].astype(str).isin(selected_categories) &
                        cases["case_status"].astype(str).isin(selected_statuses)].copy()
filtered_ids = set(filtered_cases["case_id"])
filtered_tx = transactions[transactions["case_id"].isin(filtered_ids)].copy()

features = build_case_features(cases, transactions)
# A deliberately transparent 0–100 review score, not a probability of fraud.
features["review_score"] = (
    features["shared_account"].astype(int) * 35
    + features["rapid_onward_transfer"].astype(int) * 25
    + features["multiple_incoming"].astype(int) * 20
    + features["multi_hop"].astype(int) * 20
).clip(upper=100)
features["score_band"] = pd.cut(features["review_score"], [-1, 0, 34, 64, 100],
                                labels=["No rule triggered", "Low", "Moderate", "Elevated"])
feature_cols = ["case_id","shared_account","rapid_onward_transfer","multiple_incoming","multi_hop",
                "recipient_case_count","recipient_incoming_count","recipient_outgoing_count",
                "recipient_incoming_amount","recipient_outgoing_amount","max_path_depth","review_score","score_band"]
case_analysis = filtered_cases.merge(features[feature_cols], on="case_id", how="left")

st.markdown('<div class="section">Review queue</div>', unsafe_allow_html=True)
k1,k2,k3,k4=st.columns(4)
k1.metric("Cases in view", f"{len(filtered_cases):,}")
k2.metric("Reported losses", f"₹{filtered_cases['reported_loss_inr'].sum():,.0f}")
k3.metric("Transactions", f"{len(filtered_tx):,}")
k4.metric("Cases with review indicators", int((case_analysis["review_score"].fillna(0)>0).sum()))

tab_overview, tab_cross, tab_flow, tab_risk, tab_reviews, tab_eval, tab_data = st.tabs([
    "Overview", "Cross-case network", "Money-flow tracing", "Explainable scoring",
    "Investigator review", "Scenario evaluation", "Data tables"
])

with tab_overview:
    left,right=st.columns(2)
    with left:
        st.markdown('<div class="section">Cases by category</div>',unsafe_allow_html=True)
        counts=filtered_cases.groupby("fraud_category").size().reset_index(name="cases")
        fig=go.Figure(go.Bar(x=counts["fraud_category"],y=counts["cases"],marker_color="#68c7bb"))
        fig.update_layout(xaxis_title=None,yaxis_title="Cases")
        st.plotly_chart(style_fig(fig,400),use_container_width=True)
    with right:
        st.markdown('<div class="section">Reported case activity</div>',unsafe_allow_html=True)
        dated=filtered_cases.dropna(subset=["reported_date"]).assign(day=lambda d:d["reported_date"].dt.date)
        daily=dated.groupby("day").size().reset_index(name="cases")
        fig=go.Figure(go.Scatter(x=daily["day"],y=daily["cases"],mode="lines+markers",
                                 line=dict(color="#68c7bb",width=2.5),marker=dict(color="#e6b566",size=6),
                                 fill="tozeroy",fillcolor="rgba(104,199,187,.08)"))
        fig.update_layout(xaxis_title=None,yaxis_title="Cases")
        st.plotly_chart(style_fig(fig,400),use_container_width=True)
    st.markdown('<div class="section">Cases needing a closer look</div>',unsafe_allow_html=True)
    st.dataframe(case_analysis.sort_values("review_score",ascending=False),use_container_width=True,hide_index=True)

with tab_cross:
    st.markdown('<div class="section">Shared accounts across complaints</div>',unsafe_allow_html=True)
    st.caption("An edge connects a case to an account named as its initial recipient. Shared recipients connect cases; this is a lead for review, not proof of coordination.")
    cross=nx.Graph()
    for row in filtered_cases.itertuples(index=False):
        case_node="CASE:"+str(row.case_id)
        acct_node="ACC:"+str(row.initial_recipient_account_id)
        cross.add_node(case_node,node_type="case",display=str(row.case_id))
        cross.add_node(acct_node,node_type="account",display=str(row.initial_recipient_account_id))
        cross.add_edge(case_node,acct_node,relationship="initial recipient")
    # only account nodes tied to two or more cases are emphasized
    account_case_counts=filtered_cases.groupby("initial_recipient_account_id")["case_id"].nunique().to_dict()
    positions=nx.spring_layout(cross,seed=11,k=0.8) if cross.number_of_nodes() else {}
    ex,ey=[],[]
    for u,v in cross.edges():
        x0,y0=positions[u]; x1,y1=positions[v]
        ex += [x0,x1,None]; ey += [y0,y1,None]
    edge_trace=go.Scatter(x=ex,y=ey,mode="lines",line=dict(width=1.2,color="rgba(134,157,171,.42)"),hoverinfo="skip")
    xx,yy,labels,colors,sizes,hover=[],[],[],[],[],[]
    for n,d in cross.nodes(data=True):
        x,y=positions[n]; xx.append(x); yy.append(y); labels.append(d["display"])
        if d["node_type"]=="case":
            colors.append("#6f9de8"); sizes.append(17); hover.append("Case "+d["display"])
        else:
            acct=d["display"]; count=int(account_case_counts.get(acct,0))
            colors.append("#e6b566" if count>=2 else "#68c7bb")
            sizes.append(20+min(count*3,18))
            hover.append(f"Account {acct}<br>Linked cases: {count}")
    node_trace=go.Scatter(x=xx,y=yy,mode="markers+text",text=labels,textposition="top center",
                          textfont=dict(size=9,color="#dce5eb"),hovertext=hover,hoverinfo="text",
                          marker=dict(size=sizes,color=colors,line=dict(width=1,color="#17212a")))
    fig=go.Figure([edge_trace,node_trace]); fig.update_layout(showlegend=False,xaxis=dict(visible=False),yaxis=dict(visible=False))
    st.plotly_chart(style_fig(fig,560),use_container_width=True)
    shared_table=filtered_cases.groupby("initial_recipient_account_id").agg(
        linked_cases=("case_id","nunique"),
        combined_reported_loss=("reported_loss_inr","sum"),
        case_list=("case_id",lambda s:", ".join(map(str,s)))
    ).reset_index().sort_values(["linked_cases","combined_reported_loss"],ascending=False)
    st.markdown('<div class="section">Most frequently shared recipients</div>',unsafe_allow_html=True)
    st.dataframe(shared_table[shared_table["linked_cases"]>=2] if (shared_table["linked_cases"]>=2).any() else shared_table.head(20),
                 use_container_width=True,hide_index=True)
    st.download_button("Export cross-case recipient links",shared_table.to_csv(index=False).encode("utf-8"),
                       "cross_case_recipient_links.csv","text/csv")

with tab_flow:
    st.markdown('<div class="section">Follow the movement of funds</div>',unsafe_allow_html=True)
    case_opts=sorted(filtered_cases["case_id"].unique())
    if not case_opts:
        st.info("No cases match the current filters.")
    else:
        selected_case=st.selectbox("Case reference",case_opts,key="flow_case")
        case_tx=transactions[transactions["case_id"]==selected_case].sort_values("timestamp",na_position="last").reset_index(drop=True)
        if case_tx.empty:
            st.info("No transaction rows are linked to this case.")
        else:
            max_step=len(case_tx)
            reveal=st.slider("Show transfers up to",1,max_step,max_step,key="flow_step")
            visible=case_tx.iloc[:reveal].copy()
            graph=nx.DiGraph()
            for row in visible.itertuples(index=False):
                graph.add_edge(row.source_account_id,row.destination_account_id,
                               amount=float(row.amount_inr),timestamp=row.timestamp,txid=row.transaction_id)
            # Layout is fixed for a selected case to avoid nodes jumping when slider changes.
            full_graph=nx.DiGraph()
            for row in case_tx.itertuples(index=False):
                full_graph.add_edge(row.source_account_id,row.destination_account_id)
            pos=nx.spring_layout(full_graph,seed=19,k=1.0)
            gx,gy=[],[]
            for u,v in graph.edges():
                gx += [pos[u][0],pos[v][0],None]; gy += [pos[u][1],pos[v][1],None]
            edge=go.Scatter(x=gx,y=gy,mode="lines",line=dict(width=2,color="rgba(130,159,176,.6)"),hoverinfo="skip")
            nodes_x,nodes_y,labels,colors,sizes,hover=[],[],[],[],[],[]
            case_row=cases[cases["case_id"]==selected_case].iloc[0]
            victim=str(case_row["victim_account_id"]); recipient=str(case_row["initial_recipient_account_id"])
            indeg=dict(graph.in_degree()); outdeg=dict(graph.out_degree())
            for n in graph.nodes():
                nodes_x.append(pos[n][0]); nodes_y.append(pos[n][1]); labels.append(n)
                if n==victim: role,color="Victim/source","#6f9de8"
                elif n==recipient: role,color="Initial recipient","#e6b566"
                elif indeg.get(n,0)>0 and outdeg.get(n,0)>0: role,color="Intermediary","#b89ae8"
                else: role,color="Other account","#68c7bb"
                colors.append(color); sizes.append(23+min(4*(indeg.get(n,0)+outdeg.get(n,0)),20))
                hover.append(f"{n}<br>{role}<br>Incoming links: {indeg.get(n,0)}<br>Outgoing links: {outdeg.get(n,0)}")
            node=go.Scatter(x=nodes_x,y=nodes_y,mode="markers+text",text=labels,textposition="top center",
                            textfont=dict(size=10,color="#e5edf2"),hovertext=hover,hoverinfo="text",
                            marker=dict(size=sizes,color=colors,line=dict(width=1.5,color="#17212a")))
            fig=go.Figure([edge,node]); fig.update_layout(showlegend=False,xaxis=dict(visible=False),yaxis=dict(visible=False),
                                                         title=f"{selected_case} · {reveal}/{max_step} transfers shown")
            st.plotly_chart(style_fig(fig,490),use_container_width=True)
            st.dataframe(visible,use_container_width=True,hide_index=True)
            ids=sorted(set(visible["source_account_id"])|set(visible["destination_account_id"]))
            chosen_account=st.selectbox("Inspect an account in this path",ids,key="flow_account")
            rel=visible[(visible["source_account_id"]==chosen_account)|(visible["destination_account_id"]==chosen_account)]
            in_amt=rel.loc[rel["destination_account_id"]==chosen_account,"amount_inr"].sum()
            out_amt=rel.loc[rel["source_account_id"]==chosen_account,"amount_inr"].sum()
            a,b,c=st.columns(3); a.metric("Transfers touching account",len(rel)); b.metric("Received in visible steps",f"₹{in_amt:,.2f}"); c.metric("Sent in visible steps",f"₹{out_amt:,.2f}")
            acct_row=accounts[accounts["account_id"]==chosen_account]
            if not acct_row.empty: st.dataframe(acct_row,use_container_width=True,hide_index=True)
            st.markdown("**Related transfers**"); st.dataframe(rel,use_container_width=True,hide_index=True)

with tab_risk:
    st.markdown('<div class="section">Explainable case review score</div>',unsafe_allow_html=True)
    st.markdown('<div class="note">This is a transparent heuristic score from 0 to 100, not a calibrated probability. Weights are visible below and should be validated against the scenario labels.</div>',unsafe_allow_html=True)
    st.write("Score components")
    st.markdown("- Shared initial recipient across cases: **35 points**\n- Onward transfer within 60 minutes of first case transfer: **25 points**\n- At least two distinct senders into the recipient within a 72-hour window: **20 points**\n- Transaction path depth of at least two hops: **20 points**")
    risk_view=case_analysis.sort_values(["review_score","reported_loss_inr"],ascending=False)
    st.dataframe(risk_view[["case_id","fraud_category","reported_loss_inr","initial_recipient_account_id","shared_account","rapid_onward_transfer","multiple_incoming","multi_hop","recipient_case_count","recipient_incoming_count","recipient_outgoing_count","max_path_depth","review_score","score_band"]],
                 use_container_width=True,hide_index=True)
    pick=st.selectbox("Explain score for case",sorted(filtered_cases["case_id"].unique()),key="explain_case") if not filtered_cases.empty else None
    if pick:
        row=case_analysis[case_analysis["case_id"]==pick].iloc[0]
        st.markdown(f"**{pick} — score {int(row['review_score'])}/100 ({row['score_band']})**")
        components=[
            ("Shared recipient",bool(row["shared_account"]),35,"Initial recipient is listed against more than one case."),
            ("Rapid onward transfer",bool(row["rapid_onward_transfer"]),25,"An outgoing transfer from the recipient appears within 60 minutes of the case's first transaction."),
            ("Multiple incoming senders",bool(row["multiple_incoming"]),20,"At least two distinct senders transferred to the recipient within the 72-hour window."),
            ("Multi-hop path",bool(row["multi_hop"]),20,"The case transaction graph has a path of at least two edges from the initial recipient.")
        ]
        for label,active,points,desc in components:
            st.markdown(f"{'🟠' if active else '⚪'} **{label}** — {'+'+str(points)+' points' if active else '0 points'}  \n{desc}")
    st.download_button("Export scored cases",case_analysis.to_csv(index=False).encode("utf-8"),"explainable_case_scores.csv","text/csv")

with tab_reviews:
    st.markdown('<div class="section">Investigator decisions and audit trail</div>',unsafe_allow_html=True)
    st.caption("Review decisions are saved locally to investigator_review.db and remain separate from source CSV files.")
    reviewer=st.text_input("Reviewer initials or team ID",placeholder="e.g. ANALYST-01")
    entity_type=st.selectbox("Record type",["Case","Account","Relationship"])
    if entity_type=="Case":
        entity_options=sorted(filtered_cases["case_id"].unique())
    elif entity_type=="Account":
        entity_options=sorted(accounts["account_id"].unique())
    else:
        entity_options=sorted(set(filtered_cases["initial_recipient_account_id"].astype(str)))
    entity_id=st.selectbox("Record to review",entity_options) if entity_options else ""
    decision=st.selectbox("Decision",["Pending","Confirmed relationship","Rejected relationship","Escalate for review","Closed — insufficient evidence"])
    reason=st.selectbox("Reason",["Shared across multiple cases","Transaction pattern requires review","Evidence supports relationship","Relationship not supported by available data","Insufficient data","Other"])
    related_case=st.selectbox("Related case (optional)",[""]+sorted(filtered_cases["case_id"].unique()))
    notes=st.text_area("Investigator notes",placeholder="Record the observable facts and next action. Avoid unsupported conclusions.")
    if st.button("Save review decision",type="primary"):
        if not reviewer.strip():
            st.error("Enter reviewer initials or a team ID before saving.")
        elif not entity_id:
            st.error("Select a record to review.")
        else:
            save_review(reviewer.strip(),entity_type, str(entity_id),decision,reason,related_case,notes.strip())
            st.success("Review decision saved to the local audit database.")
            st.rerun()
    reviews=get_reviews()
    st.markdown("**Review history**")
    if reviews.empty:
        st.info("No review decisions recorded yet.")
    else:
        st.dataframe(reviews,use_container_width=True,hide_index=True)
        st.download_button("Export audit trail CSV",reviews.to_csv(index=False).encode("utf-8"),"investigator_audit_trail.csv","text/csv")

with tab_eval:
    st.markdown('<div class="section">Scenario-based rule evaluation</div>',unsafe_allow_html=True)
    if truth.empty or "case_id" not in truth.columns:
        st.warning("scenario_truth.csv is missing or does not contain case_id. Evaluation cannot be computed.")
    else:
        st.caption("The evaluation maps scenario labels to the matching transparent rule. Results are only meaningful if scenario_truth.csv correctly describes each case and the mapping below matches your dataset's definitions.")
        joined=truth.merge(features,on="case_id",how="left",suffixes=("_truth","_detected"))
        mappings={
            "shared_account":"shared_account",
            "rapid_onward_transfer":"rapid_onward_transfer",
            "multiple_incoming":"multiple_incoming",
            "multi_hop":"multi_hop"
        }
        available_truth_cols=[c for c in ["scenario_type","expected_pattern_flags"] if c in joined.columns]
        if not available_truth_cols:
            st.warning("No scenario_type or expected_pattern_flags column was found.")
        else:
            rows=[]
            for _,r in joined.iterrows():
                flags=parse_truth_flags(r)
                for label,feature in mappings.items():
                    rows.append({"case_id":str(r["case_id"]),"pattern":label,"expected":int(flags[label]),
                                 "detected":int(bool(r.get(feature,False))) if pd.notna(r.get(feature,False)) else 0})
            eval_df=pd.DataFrame(rows)
            metrics=[]
            for pattern,g in eval_df.groupby("pattern"):
                vals=metric_values(g["expected"],g["detected"])
                metrics.append({"Pattern":pattern,"Cases":len(g),**vals})
            metrics_df=pd.DataFrame(metrics)
            st.dataframe(metrics_df.style.format({"Precision":"{:.2f}","Recall":"{:.2f}","F1":"{:.2f}"}),use_container_width=True,hide_index=True)
            st.caption("Expected flags are derived from scenario_type and expected_pattern_flags text. Review the raw labels below; unmatched or ambiguous label wording can distort metrics.")
            st.dataframe(truth,use_container_width=True,hide_index=True)
            st.download_button("Export scenario evaluation details",eval_df.to_csv(index=False).encode("utf-8"),"scenario_evaluation_details.csv","text/csv")

with tab_data:
    st.markdown('<div class="section">Dataset tables</div>',unsafe_allow_html=True)
    with st.expander("Cases"): st.dataframe(filtered_cases,use_container_width=True,hide_index=True)
    with st.expander("Transactions"): st.dataframe(filtered_tx,use_container_width=True,hide_index=True)
    with st.expander("Accounts"): st.dataframe(accounts,use_container_width=True,hide_index=True)
    with st.expander("Scenario truth"): st.dataframe(truth,use_container_width=True,hide_index=True)

st.divider()
st.caption("SENTINEL · Local prototype · Synthetic data only. Shared accounts and heuristic scores are leads for review, not proof of wrongdoing.")
