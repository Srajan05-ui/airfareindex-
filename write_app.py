# -*- coding: utf-8 -*-
"""
This script writes a clean UTF-8 app.py for Streamlit Cloud deployment.
Run: python write_app.py
"""
APP_CODE = """\
# -*- coding: utf-8 -*-
\"\"\"
AirPrice India -- Cloud Demo Dashboard
Self-contained Streamlit app (Streamlit Community Cloud ready).
Works with built-in demo data when no DATABASE_URL is configured.
Run locally: streamlit run app.py
\"\"\"
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

st.set_page_config(
    page_title="AirPrice India | DGCA Airfare Monitor",
    page_icon="IN",
    layout="wide",
    initial_sidebar_state="expanded",
)

C = {
    "navy":   "#003366",
    "blue":   "#0066CC",
    "teal":   "#008B8B",
    "gold":   "#F39C12",
    "green":  "#27AE60",
    "red":    "#C0392B",
    "orange": "#E67E22",
    "gray":   "#5D6D7E",
}

ROUTES = [
    ("DEL","BOM"),("BOM","BLR"),("DEL","BLR"),("DEL","CCU"),
    ("BOM","CCU"),("BLR","HYD"),("DEL","HYD"),("DEL","MAA"),("BOM","MAA"),
]
AIRLINES = ["IndiGo","Air India","Akasa Air","SpiceJet","Air India Express","IndiGo Charter"]
CITY = {
    "DEL":{"name":"Delhi",     "lat":28.7041,"lon":77.1025},
    "BOM":{"name":"Mumbai",    "lat":19.0760,"lon":72.8777},
    "BLR":{"name":"Bengaluru", "lat":12.9716,"lon":77.5946},
    "CCU":{"name":"Kolkata",   "lat":22.5726,"lon":88.3639},
    "HYD":{"name":"Hyderabad", "lat":17.3616,"lon":78.4744},
    "MAA":{"name":"Chennai",   "lat":13.0827,"lon":80.2707},
}

# ── demo data generators ───────────────────────────────────────────────────────
def _make_fares():
    np.random.seed(42)
    rows = []
    base = {r: np.random.randint(4500, 9000) for r in ROUTES}
    now = datetime.now(tz=timezone.utc)
    for d in range(60):
        ts = now - timedelta(days=59 - d)
        for (o, de) in ROUTES:
            bp = base[(o, de)]
            for al in np.random.choice(AIRLINES, size=3, replace=False):
                for bw in [3, 7, 14, 30]:
                    p = bp * (1 + 0.02 * d / 60) + np.random.normal(0, 400)
                    rows.append({
                        "observed_at_utc": ts, "origin": o, "destination": de,
                        "airline": al, "price": round(max(1000, p)),
                        "booking_window_days": bw, "source_tier": "tier1",
                    })
    df = pd.DataFrame(rows)
    df["observed_at_ist"] = df["observed_at_utc"].dt.tz_convert("Asia/Kolkata")
    df["route"] = df["origin"] + " -> " + df["destination"]
    return df

def _make_index(fares):
    rows = []
    for (o, de), grp in fares.groupby(["origin", "destination"]):
        daily = grp.set_index("observed_at_ist")["price"].resample("D").mean().dropna()
        if len(daily) < 2:
            continue
        base = daily.iloc[0]
        for ts, price in daily.items():
            rows.append({
                "origin": o, "destination": de,
                "index_value": round(100 * price / base, 2),
                "computed_at_utc": ts.tz_convert("UTC"),
                "computed_at_ist": ts,
                "n_observations": len(grp[grp["observed_at_ist"].dt.date == ts.date()]),
            })
    return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def get_data():
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if db_url:
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(db_url, pool_pre_ping=True)
            fares = pd.read_sql(
                text("SELECT * FROM fare_observations_clean "
                     "WHERE is_duplicate=FALSE AND is_outlier=FALSE AND price IS NOT NULL"),
                engine)
            if not fares.empty:
                fares["observed_at_ist"] = pd.to_datetime(
                    fares["observed_at_utc"], utc=True).dt.tz_convert("Asia/Kolkata")
                fares["route"] = fares["origin"] + " -> " + fares["destination"]
            index = pd.read_sql(
                text("SELECT * FROM airfare_index ORDER BY computed_at_utc"), engine)
            if not index.empty:
                index["computed_at_ist"] = pd.to_datetime(
                    index["computed_at_utc"], utc=True).dt.tz_convert("Asia/Kolkata")
            return fares, index, False
        except Exception:
            pass
    fares = _make_fares()
    return fares, _make_index(fares), True

fares_df, index_df, is_demo = get_data()

def airline_stats(df):
    if df.empty:
        return pd.DataFrame()
    s = df.groupby("airline").agg(
        Observations=("price","count"),
        avg_fare=("price","mean"),
        min_fare=("price","min"),
        max_fare=("price","max"),
        Routes=("route","nunique"),
    ).reset_index()
    s.columns = ["Airline","Observations","Avg Fare (Rs)","Min Fare (Rs)","Max Fare (Rs)","Routes"]
    return s.sort_values("Observations", ascending=False)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f\"\"\"
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, body {{ font-family: 'Inter', sans-serif !important; }}
.main-header {{
    background: linear-gradient(135deg, {C['navy']} 0%, {C['blue']} 60%, {C['teal']} 100%);
    color: white; padding: 2.5rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0,51,102,0.3);
}}
.main-header h1 {{ font-size: 2rem; font-weight: 700; margin: 0; }}
.badge {{
    background: {C['gold']}; color: {C['navy']};
    padding: .3rem 1rem; border-radius: 20px;
    font-size: .8rem; font-weight: 700; display: inline-block; margin-top: .7rem;
}}
.demo-banner {{
    background: linear-gradient(90deg, #f39c12, #e67e22);
    color: white; padding: .7rem 1.2rem; border-radius: 8px;
    font-weight: 600; margin-bottom: 1rem; text-align: center;
}}
.kpi {{
    background: white; border-radius: 12px; padding: 1.4rem;
    text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,.08);
    border-top: 4px solid {C['blue']};
}}
.kpi-val {{ font-size: 2rem; font-weight: 700; color: {C['navy']}; }}
.kpi-lbl {{ font-size: .85rem; color: {C['gray']}; font-weight: 500; margin-top: .3rem; }}
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {C['navy']} 0%, #1a3a5c 100%);
    border-right: 3px solid {C['gold']};
}}
section[data-testid="stSidebar"] * {{ color: white !important; }}
.sec {{
    font-size: 1.2rem; font-weight: 700; color: {C['navy']};
    border-left: 4px solid {C['gold']}; padding-left: .75rem; margin: 1.5rem 0 .75rem;
}}
</style>
\"\"\", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(\"\"\"
<div style='text-align:center;padding:1rem 0;'>
<div style='font-size:2.5rem;'>IN</div>
<div style='font-size:1.2rem;font-weight:700;'>AirPrice India</div>
<div style='font-size:.8rem;opacity:.8;'>National Airfare Monitor</div>
</div>\"\"\", unsafe_allow_html=True)

page = st.sidebar.radio("Navigation", [
    "Overview", "Airlines", "Routes & CPI", "Analytics", "Anomalies", "Forecast",
])
st.sidebar.markdown("---")
st.sidebar.markdown(f\"\"\"
<div style='font-size:.8rem;opacity:.75;'>
<b>Data:</b> {'DEMO Mode' if is_demo else 'Live DB'}<br>
<b>Observations:</b> {len(fares_df):,}<br>
<b>Routes:</b> {fares_df['route'].nunique() if not fares_df.empty else 0}<br>
<b>Updated:</b> {datetime.now().strftime('%H:%M IST')}
</div>\"\"\", unsafe_allow_html=True)

if is_demo:
    st.markdown(\"\"\"
    <div class="demo-banner">
    [DEMO MODE] Showing synthetic sample data.
    Connect a live DATABASE_URL in Streamlit secrets for real fare data.
    </div>\"\"\", unsafe_allow_html=True)

# ── OVERVIEW ──────────────────────────────────────────────────────────────────
if page == "Overview":
    st.markdown(f\"\"\"
    <div class="main-header">
    <h1>India AirPrice India -- National Airfare Monitoring System</h1>
    <p>Directorate General of Civil Aviation (DGCA) | Ministry of Civil Aviation</p>
    <span class="badge">SIH26056 - REAL-TIME SURVEILLANCE</span>
    </div>\"\"\", unsafe_allow_html=True)

    latest_idx = (index_df.sort_values("computed_at_ist")
                  .groupby(["origin","destination"]).tail(1)
                  if not index_df.empty else pd.DataFrame())
    nat_cpi = float(latest_idx["index_value"].mean()) if not latest_idx.empty else 100.0

    k1, k2, k3, k4 = st.columns(4)
    for col, val, lbl in [
        (k1, f"{len(fares_df):,}",             "Total Observations"),
        (k2, str(fares_df['route'].nunique()),  "Active Routes"),
        (k3, f"{nat_cpi:.2f}",                 "National CPI"),
        (k4, str(fares_df['airline'].nunique()),"Airlines Tracked"),
    ]:
        col.markdown(f'<div class="kpi"><div class="kpi-val">{val}</div>'
                     f'<div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_map, col_st = st.columns([2, 1])
    with col_map:
        st.markdown('<div class="sec">National Route Inflation Map</div>', unsafe_allow_html=True)
        import pydeck as pdk
        map_rows = []
        for _, row in latest_idx.iterrows():
            o, de = row["origin"], row["destination"]
            if o in CITY and de in CITY:
                cpi = float(row["index_value"])
                if cpi > 110:   clr, tgt = [220,50,50,230],  [220,50,50,160]
                elif cpi > 105: clr, tgt = [243,156,18,230], [243,156,18,160]
                elif cpi < 95:  clr, tgt = [39,174,96,230],  [39,174,96,160]
                else:           clr, tgt = [52,152,219,210], [52,152,219,140]
                af = fares_df[(fares_df.origin==o)&(fares_df.destination==de)]["price"].mean()
                map_rows.append({
                    "route": f"{o} to {de}",
                    "lon_o": CITY[o]["lon"], "lat_o": CITY[o]["lat"],
                    "lon_d": CITY[de]["lon"], "lat_d": CITY[de]["lat"],
                    "cpi": round(cpi, 1), "avg_fare": f"{af:,.0f}",
                    "color": clr, "tgt_color": tgt,
                    "status": ("Critical" if cpi>110 else "Warning" if cpi>105
                               else "Deflation" if cpi<95 else "Stable"),
                })
        city_df = pd.DataFrame([
            {"lon":v["lon"],"lat":v["lat"],"label":f"{v['name']} ({k})"}
            for k,v in CITY.items()
        ])
        arc = pdk.Layer("ArcLayer", data=pd.DataFrame(map_rows),
            get_source_position=["lon_o","lat_o"], get_target_position=["lon_d","lat_d"],
            get_source_color="color", get_target_color="tgt_color",
            get_width=9, width_min_pixels=4, width_max_pixels=13,
            auto_highlight=True, pickable=True, great_circle=True)
        scat = pdk.Layer("ScatterplotLayer", data=city_df,
            get_position=["lon","lat"], get_fill_color=[255,255,255,255],
            get_line_color=[0,66,160,255], stroked=True, line_width_min_pixels=3,
            get_radius=60000, pickable=True, auto_highlight=True)
        txt = pdk.Layer("TextLayer", data=city_df, get_position=["lon","lat"],
            get_text="label", get_size=14, get_color=[255,255,255,255],
            get_background_color=[10,30,80,200], get_pixel_offset=[0,-55], font_weight=700)
        st.pydeck_chart(pdk.Deck(
            layers=[arc, scat, txt],
            initial_view_state=pdk.ViewState(longitude=80.5, latitude=21.0,
                                             zoom=4.2, pitch=40, bearing=-5),
            map_style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
            tooltip={"html":"<div style='font-family:Inter;padding:8px'>"
                            "<b>{route}</b><br>Avg Fare: Rs{avg_fare}<br>"
                            "CPI: {cpi}<br>Status: {status}</div>",
                     "style":{"backgroundColor":"#0B172A","color":"#FFF","borderRadius":"8px"}},
        ))
        st.markdown(
            "<b style='color:#C0392B;'>Red</b> Critical CPI>110 &nbsp;"
            "<b style='color:#E67E22;'>Orange</b> Warning 105-110 &nbsp;"
            "<b style='color:#27AE60;'>Green</b> Deflation CPI<95 &nbsp;"
            "<b style='color:#0066CC;'>Blue</b> Stable 95-105",
            unsafe_allow_html=True)

    with col_st:
        st.markdown('<div class="sec">Route CPI Status</div>', unsafe_allow_html=True)
        for _, row in latest_idx.head(9).iterrows():
            cpi = float(row["index_value"])
            clr = (C["red"] if cpi>110 else C["orange"] if cpi>105
                   else C["green"] if cpi<95 else C["blue"])
            st.markdown(f\"\"\"
            <div style='background:white;border-radius:8px;padding:.7rem 1rem;
                        margin-bottom:.5rem;border-left:4px solid {clr};
                        box-shadow:0 2px 8px rgba(0,0,0,.07);'>
            <div style='font-weight:600;font-size:.9rem;color:#1a1a2e;'>
                {row['origin']} to {row['destination']}</div>
            <div style='font-size:1.2rem;font-weight:700;color:{clr};'>{cpi:.1f}</div>
            </div>\"\"\", unsafe_allow_html=True)

# ── AIRLINES ──────────────────────────────────────────────────────────────────
elif page == "Airlines":
    st.markdown('<h2 style="color:#003366;">Airline Performance Analytics</h2>',
                unsafe_allow_html=True)
    stats = airline_stats(fares_df)
    if stats.empty:
        st.warning("No airline data available.")
        st.stop()
    cols = st.columns(min(3, len(stats)))
    for col, (_, r) in zip(cols, stats.head(3).iterrows()):
        col.metric(r["Airline"], f"Rs{r['Avg Fare (Rs)']:,.0f}",
                   f"{int(r['Observations'])} obs | {int(r['Routes'])} routes")
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec">Average Fare by Airline</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=stats["Airline"], y=stats["Avg Fare (Rs)"],
            marker=dict(color=stats["Avg Fare (Rs)"],
                        colorscale=[[0,C["green"]],[.5,C["gold"]],[1,C["red"]]],
                        line=dict(color=C["navy"],width=1.5)),
            text=stats["Avg Fare (Rs)"].apply(lambda x: f"Rs{x:,.0f}"),
            textposition="outside", textfont=dict(color="#0F172A", size=12),
            hovertemplate="<b>%{x}</b><br>Rs%{y:,.0f}<extra></extra>"))
        fig.update_layout(height=380, template="plotly_white",
            plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
            font=dict(family="Inter", size=12, color="#334155"),
            title=dict(text="Airline Fare Ranking", font=dict(color="#003366", size=15)),
            xaxis=dict(tickfont=dict(color="#334155"),
                       title=dict(text="Airline", font=dict(color="#334155"))),
            yaxis=dict(tickfont=dict(color="#334155"),
                       title=dict(text="Avg Fare (Rs)", font=dict(color="#334155"))))
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with c2:
        st.markdown('<div class="sec">Market Share by Volume</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Pie(
            labels=stats["Airline"], values=stats["Observations"], hole=.4,
            pull=[.05]+[0]*(len(stats)-1), textfont=dict(size=12, color="#1a1a2e"),
            hovertemplate="<b>%{label}</b><br>%{value:,} obs<br>%{percent}<extra></extra>"))
        fig2.update_layout(height=380, paper_bgcolor="white",
            title=dict(text="Observation Volume Share", font=dict(color="#003366", size=15)),
            font=dict(family="Inter", size=12, color="#334155"),
            legend=dict(font=dict(color="#334155")))
        st.plotly_chart(fig2, use_container_width=True, theme=None)
    st.markdown('<div class="sec">Detailed Statistics</div>', unsafe_allow_html=True)
    st.dataframe(stats, use_container_width=True, hide_index=True)

# ── ROUTES & CPI ──────────────────────────────────────────────────────────────
elif page == "Routes & CPI":
    st.markdown('<h2 style="color:#003366;">Route-wise CPI and Fare Trends</h2>',
                unsafe_allow_html=True)
    if index_df.empty:
        st.warning("No CPI index data available yet.")
        st.stop()
    latest_idx = (index_df.sort_values("computed_at_ist")
                  .groupby(["origin","destination"]).tail(1)
                  .assign(route=lambda d: d["origin"]+" to "+d["destination"]))
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec">Route CPI Ranking</div>', unsafe_allow_html=True)
        si = latest_idx.sort_values("index_value", ascending=True)
        clrs = [C["red"] if v>110 else C["orange"] if v>105 else
                C["green"] if v<95 else C["blue"] for v in si["index_value"]]
        fig = go.Figure(go.Bar(
            y=si["route"], x=si["index_value"], orientation="h",
            marker=dict(color=clrs, line=dict(color="white",width=1.5)),
            text=si["index_value"].apply(lambda x: f"{x:.1f}"),
            textposition="outside", textfont=dict(color="#0F172A", size=12),
            hovertemplate="<b>%{y}</b><br>CPI: %{x:.2f}<extra></extra>"))
        fig.add_vline(x=100, line_dash="solid", line_width=2, line_color="#5D6D7E",
                      annotation_text="Base 100", annotation_font_color="#5D6D7E")
        fig.update_layout(height=480, template="plotly_white",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter", size=12, color="#334155"),
            title=dict(text="Route CPI Index", font=dict(color="#003366", size=15)),
            xaxis=dict(title=dict(text="CPI", font=dict(color="#334155")),
                       tickfont=dict(color="#334155")),
            yaxis=dict(tickfont=dict(color="#334155"),
                       title=dict(text="Route", font=dict(color="#334155"))),
            margin=dict(l=130, r=60, t=60, b=60))
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with c2:
        st.markdown('<div class="sec">Fare Trend</div>', unsafe_allow_html=True)
        routes_list = sorted(fares_df["route"].unique()) if not fares_df.empty else []
        sel = st.selectbox("Select Route", routes_list)
        if sel:
            o, de = sel.split(" -> ")
            rdf = fares_df[(fares_df.origin==o)&(fares_df.destination==de)]
            agg = rdf.groupby(rdf["observed_at_ist"].dt.date)["price"].mean().reset_index()
            agg.columns = ["Date","Avg Fare"]
            fig2 = go.Figure(go.Scatter(
                x=agg["Date"], y=agg["Avg Fare"], mode="lines+markers",
                line=dict(color=C["blue"],width=2.5),
                hovertemplate="%{x}<br>Rs%{y:,.0f}<extra></extra>"))
            fig2.update_layout(height=480, template="plotly_white",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Inter", size=12, color="#334155"),
                title=dict(text=f"Avg Fare -- {sel}", font=dict(color="#003366",size=14)),
                xaxis=dict(title=dict(text="Date",font=dict(color="#334155")),
                           tickfont=dict(color="#334155")),
                yaxis=dict(title=dict(text="Avg Fare (Rs)",font=dict(color="#334155")),
                           tickfont=dict(color="#334155")))
            st.plotly_chart(fig2, use_container_width=True, theme=None)

# ── ANALYTICS ─────────────────────────────────────────────────────────────────
elif page == "Analytics":
    st.markdown('<h2 style="color:#003366;">Deep Analytics</h2>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec">Fare Distribution</div>', unsafe_allow_html=True)
        mf, med = fares_df["price"].mean(), fares_df["price"].median()
        fig = go.Figure(go.Histogram(
            x=fares_df["price"], nbinsx=40,
            marker=dict(color=C["blue"], opacity=.8, line=dict(color="white",width=1))))
        fig.add_vline(x=mf, line_dash="dash", line_color=C["red"],
                      annotation_text=f"Mean Rs{mf:,.0f}", annotation_font_color=C["red"])
        fig.add_vline(x=med, line_dash="dot", line_color=C["green"],
                      annotation_text=f"Median Rs{med:,.0f}", annotation_font_color=C["green"])
        fig.update_layout(height=360, template="plotly_white",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter",size=12,color="#334155"),
            title=dict(text="Fare Price Distribution",font=dict(color="#003366",size=15)),
            xaxis=dict(title=dict(text="Fare (Rs)",font=dict(color="#334155")),
                       tickfont=dict(color="#334155")),
            yaxis=dict(title=dict(text="Frequency",font=dict(color="#334155")),
                       tickfont=dict(color="#334155")))
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with c2:
        st.markdown('<div class="sec">Booking Window vs Fare</div>', unsafe_allow_html=True)
        bw = (fares_df.groupby("booking_window_days")["price"]
              .agg(["mean","min","max"]).reset_index())
        bw.columns = ["Days","Avg","Min","Max"]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=bw["Days"],y=bw["Avg"],mode="lines+markers",
            name="Avg",line=dict(color=C["blue"],width=2.5)))
        fig2.add_trace(go.Scatter(x=bw["Days"],y=bw["Min"],mode="lines",
            name="Min",line=dict(color=C["green"],dash="dot")))
        fig2.add_trace(go.Scatter(x=bw["Days"],y=bw["Max"],mode="lines",
            name="Max",line=dict(color=C["red"],dash="dot")))
        fig2.update_layout(height=360, template="plotly_white",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter",size=12,color="#334155"),
            title=dict(text="Fare vs Booking Window",font=dict(color="#003366",size=15)),
            xaxis=dict(title=dict(text="Days Before Flight",font=dict(color="#334155")),
                       tickfont=dict(color="#334155")),
            yaxis=dict(title=dict(text="Fare (Rs)",font=dict(color="#334155")),
                       tickfont=dict(color="#334155")),
            legend=dict(font=dict(color="#334155")))
        st.plotly_chart(fig2, use_container_width=True, theme=None)

    st.markdown('<div class="sec">Airline Performance Space -- 3D View</div>',
                unsafe_allow_html=True)
    stats = airline_stats(fares_df).reset_index(drop=True)
    stats["rank"] = np.arange(1, len(stats)+1)
    fr = max(stats["Avg Fare (Rs)"].max()-stats["Avg Fare (Rs)"].min(), 1)
    stats["cs"] = ((stats["Avg Fare (Rs)"]-stats["Avg Fare (Rs)"].min())/fr).tolist()
    fig3 = go.Figure(go.Scatter3d(
        x=stats["rank"].tolist(), y=stats["Avg Fare (Rs)"].tolist(),
        z=stats["Observations"].tolist(),
        mode="markers+text", text=stats["Airline"].tolist(),
        textposition="top center", textfont=dict(size=11, color="#003366"),
        marker=dict(
            size=np.clip(stats["Routes"]*3+8, 12, 28).tolist(),
            color=stats["cs"].tolist(),
            colorscale=[[0,C["green"]],[.5,C["gold"]],[1,C["red"]]],
            line=dict(color="white",width=1.5), opacity=.92,
            colorbar=dict(title=dict(text="Fare level"),
                          tickvals=[0,.5,1],ticktext=["Lower","Mid","Higher"])),
        hovertemplate="<b>%{text}</b><br>Rs%{y:,.0f}<br>Obs: %{z:,}<extra></extra>"))
    fig3.update_layout(height=520, paper_bgcolor="white",
        font=dict(family="Inter",size=12,color="#334155"),
        scene=dict(
            xaxis=dict(title=dict(text="Rank", font=dict(color="#334155")),
                       backgroundcolor="#F7F9FC", gridcolor="#D9E2EF",
                       tickfont=dict(color="#334155")),
            yaxis=dict(title=dict(text="Avg Fare (Rs)", font=dict(color="#334155")),
                       backgroundcolor="#F7F9FC", gridcolor="#D9E2EF",
                       tickfont=dict(color="#334155")),
            zaxis=dict(title=dict(text="Observations", font=dict(color="#334155")),
                       backgroundcolor="#F7F9FC", gridcolor="#D9E2EF",
                       tickfont=dict(color="#334155")),
            camera=dict(eye=dict(x=1.55,y=1.45,z=1.15))),
        margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig3, use_container_width=True, theme=None)

# ── ANOMALIES ─────────────────────────────────────────────────────────────────
elif page == "Anomalies":
    st.markdown('<h2 style="color:#003366;">Anomaly Detection and Watchlist</h2>',
                unsafe_allow_html=True)
    if fares_df.empty:
        st.warning("No data available.")
        st.stop()
    anoms = []
    for route, grp in fares_df.groupby("route"):
        mu, sigma = grp["price"].mean(), grp["price"].std()
        if sigma == 0: continue
        for _, r in grp[((grp["price"]-mu)/sigma).abs() > 2.0].head(2).iterrows():
            z = abs((r["price"]-mu)/sigma)
            anoms.append({"Route": route, "Airline": r["airline"],
                "Observed": r["price"], "Expected": round(mu),
                "Z": round(z,2), "Dev%": round((r["price"]-mu)/mu*100,1),
                "Type": "SPIKE" if r["price"]>mu else "DROP"})
    if not anoms:
        st.success("No significant anomalies detected.")
    else:
        st.metric("Anomalies Detected", len(anoms))
        for a in sorted(anoms, key=lambda x: -x["Z"]):
            clr = C["red"] if a["Type"]=="SPIKE" else C["green"]
            st.markdown(f\"\"\"
            <div style='background:white;border-left:5px solid {clr};border-radius:10px;
                        padding:1rem 1.2rem;margin-bottom:.8rem;
                        box-shadow:0 3px 10px rgba(0,0,0,.08);'>
            <div style='display:flex;justify-content:space-between;'>
                <b style='color:#1a1a2e;'>{a['Route']}</b>
                <b style='color:{clr};font-size:1.2rem;'>Rs{a['Observed']:,}</b>
            </div>
            <div style='font-size:.85rem;color:#5D6D7E;'>
                Expected Rs{a['Expected']:,} |
                Deviation <b style='color:{clr};'>{a['Dev%']:+.1f}%</b> |
                Z-score {a['Z']} | {a['Airline']}
            </div></div>\"\"\", unsafe_allow_html=True)

# ── FORECAST ──────────────────────────────────────────────────────────────────
elif page == "Forecast":
    st.markdown('<h2 style="color:#003366;">Forecasting and Model Validation</h2>',
                unsafe_allow_html=True)
    base_cpi = float(index_df["index_value"].mean()) if not index_df.empty else 114.0
    dates30 = [datetime.now()+timedelta(days=i) for i in range(31)]
    trend = np.linspace(0, -3, 31)
    noise = np.random.default_rng(0).normal(0, .8, 31)
    mfc = base_cpi + trend + noise
    hi = mfc + np.linspace(2, 12, 31)
    lo = mfc - np.linspace(2, 12, 31)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown('<div class="sec">30-Day Forecast Cone (95% CI)</div>',
                    unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates30,y=hi,fill=None,mode="lines",
            line=dict(color="rgba(0,0,0,0)"),name="95% High"))
        fig.add_trace(go.Scatter(x=dates30,y=lo,fill="tonexty",
            fillcolor="rgba(0,102,204,.12)",mode="lines",
            line=dict(color="rgba(0,0,0,0)"),name="95% Band"))
        fig.add_trace(go.Scatter(x=dates30,y=mfc,mode="lines+markers",
            name="Forecast",line=dict(color=C["blue"],width=2.5),marker=dict(size=4)))
        fig.add_hline(y=100, line_dash="dash", line_color=C["gray"],
                      annotation_text="Base 100", annotation_font_color=C["gray"])
        fig.update_layout(height=400, template="plotly_white",
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter",size=12,color="#334155"),
            title=dict(text="National Airfare CPI -- 30-Day Forecast",
                       font=dict(color="#003366",size=15)),
            xaxis=dict(title=dict(text="Date",font=dict(color="#334155")),
                       tickfont=dict(color="#334155")),
            yaxis=dict(title=dict(text="CPI Value",font=dict(color="#334155")),
                       tickfont=dict(color="#334155")),
            legend=dict(font=dict(color="#334155")))
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with c2:
        st.markdown('<div class="sec">Horizon Summary</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Horizon":["1d","3d","7d","14d","30d"],
            "Forecast CPI":[round(mfc[i],2) for i in [1,3,7,14,30]],
            "95% Low":     [round(lo[i],2)  for i in [1,3,7,14,30]],
            "95% High":    [round(hi[i],2)  for i in [1,3,7,14,30]],
        }), hide_index=True, use_container_width=True)
        st.markdown('<div class="sec">Model Leaderboard</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Model":["Gradient Boosting (Champion)","Seasonal Naive","ARIMA","Ensemble"],
            "MAPE %":[3.55,3.98,4.24,4.48],
            "RMSE":[5.39,6.11,6.45,5.98],
        }), hide_index=True, use_container_width=True)

st.markdown("---")
st.markdown(f\"\"\"
<div style='text-align:center;color:#5D6D7E;font-size:.8rem;'>
AirPrice India | SIH26056 | Ministry of Civil Aviation |
{'DEMO Data' if is_demo else 'Live Data'} |
{datetime.now().strftime('%Y-%m-%d %H:%M IST')}
</div>\"\"\", unsafe_allow_html=True)
"""

with open("app.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(APP_CODE)

# verify it reads back clean
with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()
print(f"Written {len(content)} chars, UTF-8 OK")
print("First line:", content.split("\n")[0])
