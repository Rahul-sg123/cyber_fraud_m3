from pathlib import Path
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Sentinel | Case Intelligence", page_icon="S", layout="wide")
ROOT = Path(__file__).resolve().parent

# A restrained analyst-console style: slate, warm white, teal, and amber.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --bg:#10161d; --panel:#171f28; --line:#2a3744; --ink:#e8edf1; --muted:#9baab7; --teal:#68c7bb; --amber:#e6b566; }
html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
.stApp { background:linear-gradient(135deg,#10161d 0%,#111a22 60%,#121920 100%); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(16,22,29,.94); }
[data-testid="stSidebar"] { background:#131b23; border-right:1px solid #2a3744; }
.block-container { max-width:1480px; padding-top:1.4rem; padding-bottom:3rem; }
h1,h2,h3 { letter-spacing:-.035em; color:#edf2f5; }
p, label, .stCaption { color:#aab7c2; }
hr { border-color:#2a3744; }
[data-testid="stMetric"] { background:#18222c; border:1px solid #2b3946; border-radius:12px; padding:15px 18px; transition:transform .18s ease,border-color .18s ease; }
[data-testid="stMetric"]:hover { transform:translateY(-2px); border-color:#68c7bb; }
[data-testid="stMetricLabel"] { color:#9baab7 !important; font-size:.82rem; }
[data-testid="stMetricValue"] { color:#f0f4f6 !important; font-weight:750; }
.stTabs [data-baseweb="tab-list"] { gap:5px; border-bottom:1px solid #2a3744; }
.stTabs [data-baseweb="tab"] { color:#aab7c2; padding:10px 14px; }
.stTabs [aria-selected="true"] { color:#80d8cc !important; border-bottom-color:#68c7bb !important; }
.stButton button, .stDownloadButton button { border-radius:8px; border:1px solid #477b79; background:#203a3b; color:#e8f4f2; transition:all .18s ease; }
.stButton button:hover, .stDownloadButton button:hover { border-color:#68c7bb; background:#294849; transform:translateY(-1px); color:white; }
[data-testid="stDataFrame"] { border:1px solid #2a3744; border-radius:10px; overflow:hidden; }
div[data-testid="stExpander"] { border:1px solid #2a3744; border-radius:10px; background:#141d26; }
.kicker { font:500 11px 'DM Mono',monospace; text-transform:uppercase; letter-spacing:.13em; color:#81cfc4; }
.hero { border:1px solid #2c4149; border-radius:14px; padding:22px 25px; margin-bottom:22px; background:linear-gradient(105deg,#192630,#18212b 62%,#202c30); position:relative; overflow:hidden; animation:fadeUp .45s ease-out both; }
.hero:after { content:""; position:absolute; right:-80px; top:-130px; width:330px; height:330px; border:1px solid rgba(104,199,187,.18); border-radius:50%; box-shadow:0 0 0 32px rgba(104,199,187,.025),0 0 0 68px rgba(104,199,187,.02); pointer-events:none; }
.hero h1 { margin:8px 0 7px; font-size:clamp(27px,3vw,38px); font-weight:800; }
.hero p { max-width:760px; line-height:1.65; margin:0; color:#adbbc6; font-size:14px; }
.section { margin:8px 0 12px; font-weight:750; font-size:17px; color:#e8edf1; }
.section:before { content:""; display:inline-block; height:17px; width:3px; border-radius:3px; background:#68c7bb; margin-right:10px; vertical-align:-3px; }
.note { background:#19252d; border:1px solid #30434b; border-radius:9px; padding:11px 13px; color:#b9c8d0; font-size:12px; }
.legend { display:flex; flex-wrap:wrap; gap:14px; color:#aab7c2; font-size:12px; margin:4px 0 12px; }
.dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; }
@keyframes fadeUp { from {opacity:0; transform:translateY(5px)} to {opacity:1; transform:translateY(0)} }
@media (prefers-reduced-motion:reduce) { *,*:before,*:after { animation:none!important; transition:none!important; } }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def read_csv(filename):
    path = ROOT / filename
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


cases = read_csv("synthetic_cases.csv")
transactions = read_csv("synthetic_transactions.csv")
accounts = read_csv("synthetic_accounts.csv")
truth = read_csv("scenario_truth.csv")

st.markdown("""
<div class="hero">
  <div class="kicker">SENTINEL / CASE INTELLIGENCE</div>
  <h1>Fraud Network Investigation</h1>
  <p>Review connected accounts, follow transaction paths, and build a time-ordered view of activity. The interface is designed for case review—not automated verdicts.</p>
</div>
""", unsafe_allow_html=True)

needed = {
    "synthetic_cases.csv": (cases, ["case_id","reported_date","fraud_category","reported_loss_inr","victim_account_id","initial_recipient_account_id","case_status"]),
    "synthetic_transactions.csv": (transactions, ["transaction_id","case_id","source_account_id","destination_account_id","amount_inr","timestamp"]),
    "synthetic_accounts.csv": (accounts, ["account_id"]),
}
errors = []
for filename, (df, columns) in needed.items():
    absent = [col for col in columns if col not in df.columns]
    if df.empty or absent:
        errors.append(f"{filename}: " + ("file missing or empty" if df.empty else "missing " + ", ".join(absent)))
if errors:
    st.error("Dataset check failed:\n\n- " + "\n- ".join(errors))
    st.stop()

cases["reported_date"] = pd.to_datetime(cases["reported_date"], errors="coerce")
transactions["timestamp"] = pd.to_datetime(transactions["timestamp"], errors="coerce")
cases["reported_loss_inr"] = pd.to_numeric(cases["reported_loss_inr"], errors="coerce").fillna(0)
transactions["amount_inr"] = pd.to_numeric(transactions["amount_inr"], errors="coerce").fillna(0)
transactions["source_account_id"] = transactions["source_account_id"].astype(str)
transactions["destination_account_id"] = transactions["destination_account_id"].astype(str)

with st.sidebar:
    st.markdown("### Case filters")
    category_options = sorted(cases["fraud_category"].dropna().astype(str).unique())
    chosen_categories = st.multiselect("Fraud category", category_options, default=category_options)
    status_options = sorted(cases["case_status"].dropna().astype(str).unique())
    chosen_statuses = st.multiselect("Case status", status_options, default=status_options)
    st.markdown("---")
    st.caption("Dataset: synthetic records")
    st.caption("Account flags are review leads only.")

filtered_cases = cases[
    cases["fraud_category"].astype(str).isin(chosen_categories)
    & cases["case_status"].astype(str).isin(chosen_statuses)
].copy()
filtered_case_ids = set(filtered_cases["case_id"].astype(str))
filtered_tx = transactions[transactions["case_id"].astype(str).isin(filtered_case_ids)].copy()

st.markdown('<div class="section">Current review queue</div>', unsafe_allow_html=True)
k1,k2,k3,k4 = st.columns(4)
k1.metric("Cases in view", f"{len(filtered_cases):,}")
k2.metric("Reported losses", f"₹{filtered_cases['reported_loss_inr'].sum():,.0f}")
k3.metric("Transactions in view", f"{len(filtered_tx):,}")
all_nodes = set(filtered_tx["source_account_id"]) | set(filtered_tx["destination_account_id"])
k4.metric("Accounts connected", f"{len(all_nodes):,}")

overview, tracing, account_tab, timeline_tab, scenarios_tab, data_tab = st.tabs(
    ["Overview", "Network tracing", "Account file", "Investigation timeline", "Scenario labels", "Data tables"]
)

with overview:
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="section">Cases by category</div>', unsafe_allow_html=True)
        cat = filtered_cases.groupby("fraud_category", dropna=False).size().reset_index(name="cases")
        fig = go.Figure(go.Bar(x=cat["fraud_category"], y=cat["cases"],
                               marker_color="#68c7bb", hovertemplate="%{x}<br>%{y} cases<extra></extra>"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=5,r=5,t=15,b=5), xaxis_title=None, yaxis_title="Cases")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown('<div class="section">Reported case activity</div>', unsafe_allow_html=True)
        dated = filtered_cases.dropna(subset=["reported_date"]).assign(day=lambda d: d["reported_date"].dt.date)
        daily = dated.groupby("day").size().reset_index(name="cases")
        fig = go.Figure(go.Scatter(x=daily["day"], y=daily["cases"], mode="lines+markers",
                                   line=dict(color="#68c7bb",width=2.5), marker=dict(color="#e6b566",size=6),
                                   fill="tozeroy", fillcolor="rgba(104,199,187,.08)"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=5,r=5,t=15,b=5), xaxis_title=None, yaxis_title="Cases")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="section">Recent cases</div>', unsafe_allow_html=True)
    st.dataframe(filtered_cases.sort_values("reported_date", ascending=False), use_container_width=True, hide_index=True)

with tracing:
    st.markdown('<div class="section">Trace a case through its transaction graph</div>', unsafe_allow_html=True)
    case_options = sorted(filtered_cases["case_id"].astype(str).unique())
    if not case_options:
        st.info("No cases match the filters.")
    else:
        chosen_case = st.selectbox("Case reference", case_options, key="trace_case")
        tx_case = transactions[transactions["case_id"].astype(str) == chosen_case].copy()
        tx_case = tx_case.sort_values("timestamp", na_position="last").reset_index(drop=True)
        if tx_case.empty:
            st.info("No transaction records are linked to this case.")
        else:
            # The step control gives an investigator a deterministic, transaction-by-transaction trace.
            max_step = len(tx_case)
            step = st.slider("Reveal transfers up to step", min_value=1, max_value=max_step, value=max_step, key="trace_step")
            visible_tx = tx_case.iloc[:step].copy()
            G = nx.DiGraph()
            for row in visible_tx.itertuples(index=False):
                G.add_edge(row.source_account_id, row.destination_account_id,
                           amount=float(row.amount_inr), timestamp=row.timestamp,
                           transaction_id=row.transaction_id)
            victim_ids = set(cases.loc[cases["case_id"].astype(str) == chosen_case, "victim_account_id"].astype(str))
            recipient_ids = set(cases.loc[cases["case_id"].astype(str) == chosen_case, "initial_recipient_account_id"].astype(str))
            in_deg, out_deg = dict(G.in_degree()), dict(G.out_degree())
            pos = nx.spring_layout(G, seed=19, k=1.0)
            edge_x, edge_y, edge_mid_x, edge_mid_y, edge_text = [], [], [], [], []
            for u,v,data in G.edges(data=True):
                x0,y0=pos[u]; x1,y1=pos[v]
                edge_x += [x0,x1,None]; edge_y += [y0,y1,None]
                edge_mid_x.append((x0+x1)/2); edge_mid_y.append((y0+y1)/2)
                edge_text.append(f"{u} → {v}<br>₹{data['amount']:,.2f}<br>{data['timestamp']}")
            edges = go.Scatter(x=edge_x,y=edge_y,mode="lines",line=dict(width=2,color="rgba(130,159,176,.55)"),
                               hoverinfo="skip",name="Transfer path")
            edge_hover = go.Scatter(x=edge_mid_x,y=edge_mid_y,mode="markers",
                                    marker=dict(size=9,color="rgba(230,181,102,.01)"),
                                    hovertext=edge_text,hoverinfo="text",name="Transfer details")
            nxs,nys,nlabels,ncolors,nsizes,nhover=[],[],[],[],[],[]
            for node in G.nodes():
                nx0,ny0=pos[node]; nx0=float(nx0); ny0=float(ny0)
                if node in victim_ids: role,color="Victim / source","#6f9de8"
                elif node in recipient_ids: role,color="Initial recipient","#e6b566"
                elif out_deg.get(node,0)>0 and in_deg.get(node,0)>0: role,color="Intermediary","#b89ae8"
                else: role,color="Other connected account","#68c7bb"
                nx_list=[nx0]
                nxs.append(nx0); nys.append(ny0); nlabels.append(node); ncolors.append(color)
                nsizes.append(24 + min((in_deg.get(node,0)+out_deg.get(node,0))*4,20))
                nhover.append(f"Account: {node}<br>Role in this view: {role}<br>Incoming links: {in_deg.get(node,0)}<br>Outgoing links: {out_deg.get(node,0)}")
            nodes = go.Scatter(x=nxs,y=nys,mode="markers+text",text=nlabels,textposition="top center",
                               textfont=dict(color="#e5edf2",size=10),hovertext=nhover,hoverinfo="text",
                               marker=dict(size=nsizes,color=ncolors,line=dict(width=1.5,color="#17212a")),
                               name="Accounts")
            fig=go.Figure([edges,edge_hover,nodes])
            fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(l=10,r=10,t=20,b=10),height=480,showlegend=False,
                              xaxis=dict(visible=False),yaxis=dict(visible=False),
                              title=f"{chosen_case} · {step} of {max_step} transfers shown")
            st.plotly_chart(fig,use_container_width=True)
            st.markdown('<div class="legend"><span><i class="dot" style="background:#6f9de8"></i>Victim/source</span><span><i class="dot" style="background:#e6b566"></i>Initial recipient</span><span><i class="dot" style="background:#b89ae8"></i>Intermediary</span><span><i class="dot" style="background:#68c7bb"></i>Other connected account</span></div>',unsafe_allow_html=True)
            st.caption("Move the transfer slider to reveal the path in timestamp order. Hover over an edge or node for details.")
            st.dataframe(visible_tx[["transaction_id","timestamp","source_account_id","destination_account_id","amount_inr","status","transaction_type"]],
                         use_container_width=True,hide_index=True)
            nodes_in_view = sorted(G.nodes())
            selected_account = st.selectbox("Open account details", nodes_in_view, key="trace_account")
            detail_row = accounts[accounts["account_id"].astype(str) == selected_account]
            node_tx = visible_tx[(visible_tx["source_account_id"]==selected_account)|(visible_tx["destination_account_id"]==selected_account)]
            d1,d2,d3 = st.columns(3)
            d1.metric("Transfers touching account", len(node_tx))
            d2.metric("Money received", f"₹{node_tx.loc[node_tx['destination_account_id']==selected_account,'amount_inr'].sum():,.2f}")
            d3.metric("Money sent", f"₹{node_tx.loc[node_tx['source_account_id']==selected_account,'amount_inr'].sum():,.2f}")
            if not detail_row.empty:
                st.dataframe(detail_row, use_container_width=True, hide_index=True)
            st.markdown("**Related transactions**")
            st.dataframe(node_tx.sort_values("timestamp"),use_container_width=True,hide_index=True)

with account_tab:
    st.markdown('<div class="section">Account activity and cross-case links</div>', unsafe_allow_html=True)
    incoming = transactions.groupby("destination_account_id").agg(
        incoming_tx_count=("transaction_id","count"), incoming_amount_inr=("amount_inr","sum"),
        distinct_senders=("source_account_id","nunique")).rename_axis("account_id")
    outgoing = transactions.groupby("source_account_id").agg(
        outgoing_tx_count=("transaction_id","count"), outgoing_amount_inr=("amount_inr","sum"),
        distinct_recipients=("destination_account_id","nunique")).rename_axis("account_id")
    indicators = accounts.set_index("account_id").join(incoming).join(outgoing).fillna(0).reset_index()
    indicators["outgoing_incoming_ratio"] = indicators.apply(
        lambda r: round(r["outgoing_amount_inr"]/r["incoming_amount_inr"],2) if r["incoming_amount_inr"] else 0,axis=1)
    shared = cases.groupby("initial_recipient_account_id")["case_id"].nunique()
    indicators["linked_cases_as_recipient"] = indicators["account_id"].map(shared).fillna(0).astype(int)
    def reason(row):
        items=[]
        if row["linked_cases_as_recipient"] >= 2: items.append("Recipient appears in multiple cases")
        if row["incoming_tx_count"] >= 5: items.append("High incoming transfer count")
        if row["outgoing_tx_count"] >= 5: items.append("High outgoing transfer count")
        if row["incoming_amount_inr"]>0 and row["outgoing_incoming_ratio"]>=.8: items.append("Outgoing/incoming amount ratio ≥ 0.8")
        return "; ".join(items) if items else "No configured indicator"
    indicators["review_reasons"] = indicators.apply(reason,axis=1)
    indicators["review_flag"] = indicators["review_reasons"]!="No configured indicator"
    f1,f2,f3=st.columns(3)
    f1.metric("Accounts with indicators",int(indicators["review_flag"].sum()))
    f2.metric("Recipients in multiple cases",int((indicators["linked_cases_as_recipient"]>=2).sum()))
    f3.metric("Account records",len(accounts))
    include_all=st.checkbox("Include accounts without indicators",value=False)
    view=indicators if include_all else indicators[indicators["review_flag"]]
    st.dataframe(view.sort_values(["linked_cases_as_recipient","incoming_tx_count"],ascending=False),use_container_width=True,hide_index=True)
    st.download_button("Export account review table",indicators.to_csv(index=False).encode("utf-8"),"account_review_indicators.csv","text/csv")
    account_ids=sorted(indicators["account_id"].astype(str).unique())
    account_pick=st.selectbox("Inspect any account",account_ids,key="account_detail_pick")
    picked=indicators[indicators["account_id"].astype(str)==account_pick]
    if not picked.empty:
        st.markdown("**Account detail**")
        st.dataframe(picked,use_container_width=True,hide_index=True)
        tx_rel=transactions[(transactions["source_account_id"]==account_pick)|(transactions["destination_account_id"]==account_pick)].sort_values("timestamp")
        st.markdown(f"**Related transaction history · {len(tx_rel)} records**")
        st.dataframe(tx_rel,use_container_width=True,hide_index=True)

with timeline_tab:
    st.markdown('<div class="section">Chronology of a case</div>', unsafe_allow_html=True)
    case_options=sorted(filtered_cases["case_id"].astype(str).unique())
    if not case_options:
        st.info("No cases match the selected filters.")
    else:
        timeline_case=st.selectbox("Case to investigate",case_options,key="timeline_case")
        case_record=filtered_cases[filtered_cases["case_id"].astype(str)==timeline_case]
        case_events=transactions[transactions["case_id"].astype(str)==timeline_case].copy()
        if not case_record.empty:
            r=case_record.iloc[0]
            st.markdown(f'<div class="note"><b>Case opened in dataset:</b> {r["reported_date"]} &nbsp; · &nbsp; <b>Category:</b> {r["fraud_category"]} &nbsp; · &nbsp; <b>Reported loss:</b> ₹{r["reported_loss_inr"]:,.2f}</div>',unsafe_allow_html=True)
        if case_events.empty:
            st.info("No transaction events found for this case.")
        else:
            case_events=case_events.sort_values("timestamp",na_position="last").reset_index(drop=True)
            valid_times=case_events["timestamp"].dropna()
            if not valid_times.empty:
                lo,hi=valid_times.min().to_pydatetime(),valid_times.max().to_pydatetime()
                if lo < hi:
                    time_window=st.slider("Timeline window",min_value=lo,max_value=hi,value=(lo,hi),format="YYYY-MM-DD HH:mm")
                    events=case_events[case_events["timestamp"].between(pd.Timestamp(time_window[0]),pd.Timestamp(time_window[1]))]
                else:
                    events=case_events
            else:
                events=case_events
            st.markdown(f"**{len(events)} transaction event(s) in selected window**")
            # Compact, readable event cards with a chronological connector.
            for idx,row in enumerate(events.itertuples(index=False)):
                when = str(row.timestamp) if pd.notna(row.timestamp) else "Time not recorded"
                amount = f"₹{float(row.amount_inr):,.2f}"
                st.markdown(f"""
                <div style="display:grid;grid-template-columns:145px 18px 1fr;gap:12px;padding:11px 0;border-bottom:1px solid #293641;">
                  <div style="font:11px 'DM Mono',monospace;color:#9baab7;padding-top:3px;">{when}</div>
                  <div style="display:flex;justify-content:center;"><div style="width:8px;height:8px;border-radius:50%;background:#68c7bb;margin-top:5px;box-shadow:0 0 0 4px rgba(104,199,187,.10);"></div></div>
                  <div><div style="color:#e8edf1;font-weight:700;">{row.source_account_id} <span style="color:#68c7bb;">→</span> {row.destination_account_id}</div>
                  <div style="color:#9baab7;font-size:12px;margin-top:4px;">{row.transaction_id} · {row.transaction_type} · {row.status}</div>
                  <div style="color:#e6b566;font:500 13px 'DM Mono',monospace;margin-top:5px;">{amount}</div></div>
                </div>
                """,unsafe_allow_html=True)
            st.download_button("Export timeline events",events.to_csv(index=False).encode("utf-8"),f"{timeline_case}_timeline.csv","text/csv")

with scenarios_tab:
    st.markdown('<div class="section">Scenario reference</div>', unsafe_allow_html=True)
    if truth.empty:
        st.info("scenario_truth.csv is not available.")
    else:
        st.caption("Ground-truth descriptions from the supplied synthetic dataset. These labels alone do not represent measured detector performance.")
        joined=filtered_cases.merge(truth,on="case_id",how="left",suffixes=("","_truth"))
        st.dataframe(joined,use_container_width=True,hide_index=True)
        if "scenario_type" in truth.columns:
            counts=truth.groupby("scenario_type").size().reset_index(name="cases")
            fig=go.Figure(go.Bar(x=counts["scenario_type"],y=counts["cases"],marker_color="#e6b566"))
            fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(l=5,r=5,t=15,b=5),xaxis_title=None,yaxis_title="Cases")
            st.plotly_chart(fig,use_container_width=True)
        st.download_button("Export scenario labels",truth.to_csv(index=False).encode("utf-8"),"scenario_truth.csv","text/csv")

with data_tab:
    st.markdown('<div class="section">Source tables</div>', unsafe_allow_html=True)
    with st.expander("Cases"): st.dataframe(filtered_cases,use_container_width=True,hide_index=True)
    with st.expander("Transactions"): st.dataframe(filtered_tx,use_container_width=True,hide_index=True)
    with st.expander("Accounts"): st.dataframe(accounts,use_container_width=True,hide_index=True)
    with st.expander("Scenario truth"): st.dataframe(truth,use_container_width=True,hide_index=True)

st.divider()
st.caption("SENTINEL · Internal prototype · Synthetic data only. Shared accounts and rule-based indicators are not proof of wrongdoing.")
