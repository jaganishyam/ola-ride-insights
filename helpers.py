# helpers.py
# Data loading, the SQLite connection, page styling and small chart helpers
# shared by every page of the app.

import sqlite3
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_FILE = "data/ola_rides_clean.csv"
VEHICLE_FILE = "data/vehicle_types.csv"

VEHICLE_ORDER = ["Prime Sedan", "Prime SUV", "Prime Plus", "Mini", "Auto", "Bike", "E-Bike"]
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# chart colours (stepped for a dark background)
BLUE = "#3987E5"
ORANGE = "#D95926"
AQUA = "#199E70"
YELLOW = "#C98500"
MAGENTA = "#D55181"
SERIES = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA]
STATUS_COLORS = {
    "Success": BLUE,
    "Canceled by Driver": ORANGE,
    "Canceled by Customer": AQUA,
    "Driver Not Found": YELLOW,
}
LIME = "#A6D84A"          # brand accent, used for UI only, not for data
INK = "#F0EFEC"
INK_2 = "#C3C2B7"
INK_3 = "#8C8B84"
GRID = "#2A2B2F"


# ---------------------------------------------------------------- data ----

@st.cache_data(show_spinner="Loading ride data...")
def load_data():
    df = pd.read_csv(DATA_FILE, parse_dates=["Ride_Date"])
    df["Ride_DateTime"] = pd.to_datetime(df["Ride_Date"].dt.strftime("%Y-%m-%d") + " " + df["Ride_Time"])
    df["Fare_Per_Km"] = np.where(df["Ride_Distance"] > 0, df["Booking_Value"] / df["Ride_Distance"], np.nan)
    df["Vehicle_Type"] = pd.Categorical(df["Vehicle_Type"], VEHICLE_ORDER, ordered=True)
    return df


@st.cache_data
def load_vehicles():
    return pd.read_csv(VEHICLE_FILE)


@st.cache_resource(show_spinner="Building the SQL database...")
def get_connection():
    # the clean CSV goes into an in-memory SQLite table called ola_rides
    con = sqlite3.connect(":memory:", check_same_thread=False)
    raw = pd.read_csv(DATA_FILE)
    raw.to_sql("ola_rides", con, index=False)
    con.execute("CREATE INDEX idx_status ON ola_rides (Booking_Status)")
    con.execute("CREATE INDEX idx_vehicle ON ola_rides (Vehicle_Type)")
    return con


def run_sql(sql):
    return pd.read_sql_query(sql, get_connection())


# ------------------------------------------------------------- numbers ----

def inr(x, short=True):
    # Rs 35.08 M style for big numbers, Rs 548 for small ones
    if short and abs(x) >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if short and abs(x) >= 1e5:
        return f"₹{x / 1e5:.2f} L"
    return f"₹{x:,.0f}"


def kpis(df):
    ok = df[df["Booking_Status"] == "Success"]
    total = len(df)
    return {
        "bookings": total,
        "success": len(ok),
        "success_rate": len(ok) / total * 100 if total else 0,
        "revenue": ok["Booking_Value"].sum(),
        "avg_fare": ok["Booking_Value"].mean() if len(ok) else 0,
        "avg_distance": ok["Ride_Distance"].mean() if len(ok) else 0,
        "driver_cancel": (df["Booking_Status"] == "Canceled by Driver").mean() * 100 if total else 0,
        "cust_cancel": (df["Booking_Status"] == "Canceled by Customer").mean() * 100 if total else 0,
        "no_driver": (df["Booking_Status"] == "Driver Not Found").mean() * 100 if total else 0,
        "driver_rating": ok["Driver_Ratings"].mean() if len(ok) else 0,
        "cust_rating": ok["Customer_Rating"].mean() if len(ok) else 0,
    }


# ----------------------------------------------------------------- css ----

def load_css():
    st.markdown(
        """
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1300px;}
[data-testid="stSidebar"] {background: #131417; border-right: 1px solid #222328;}
h1, h2, h3 {letter-spacing: -0.01em;}

/* sidebar brand */
.brand {display:flex; align-items:center; gap:10px; margin: 4px 0 18px 0;}
.brand .dot {width:30px; height:30px; border-radius:50%; background:#0E0F11;
             border:3px solid #F0EFEC; display:flex; align-items:center; justify-content:center;}
.brand .dot span {width:12px; height:12px; border-radius:50%; background:#A6D84A;}
.brand .name {font-weight:800; font-size:1.25rem; color:#F0EFEC; line-height:1;}
.brand .sub {font-size:0.72rem; color:#8C8B84; text-transform:uppercase; letter-spacing:0.12em;}

/* hero banner with the moving car */
.hero {position:relative; overflow:hidden; border-radius:14px; padding:26px 30px 52px 30px;
       background: linear-gradient(120deg, #17181C 0%, #1D2116 100%); border:1px solid #26282C;
       margin-bottom: 18px;}
.hero h1 {margin:0; font-size:2.1rem; color:#F0EFEC;}
.hero p {margin:6px 0 0 0; color:#C3C2B7; max-width: 760px;}
.hero .tag {display:inline-block; font-size:0.72rem; letter-spacing:0.12em; text-transform:uppercase;
            color:#0E0F11; background:#A6D84A; border-radius:20px; padding:3px 10px; margin-bottom:10px;
            font-weight:700;}
.road {position:absolute; left:0; right:0; bottom:16px; height:4px;
       background: repeating-linear-gradient(90deg, #4A4B50 0 28px, transparent 28px 52px);
       animation: roadmove 1.2s linear infinite;}
.car {position:absolute; bottom:18px; font-size:26px; left:-60px; animation: drive 9s linear infinite;
      transform: scaleX(-1);}
.pin {position:absolute; right:26px; bottom:18px; font-size:22px;}
@keyframes drive {0% {left:-60px;} 100% {left:calc(100% - 70px);} }
@keyframes roadmove {from {background-position:0 0;} to {background-position:-52px 0;} }

/* small page header */
.page-head {border-left:4px solid #A6D84A; padding:2px 0 2px 14px; margin: 0 0 14px 0;}
.page-head h2 {margin:0; font-size:1.6rem;}
.page-head p {margin:4px 0 0 0; color:#8C8B84; font-size:0.92rem;}

/* KPI cards */
.kpi {background:#1A1B1E; border:1px solid #26282C; border-radius:12px; padding:14px 16px; height:100%;}
.kpi .label {font-size:0.7rem; color:#8C8B84; text-transform:uppercase; letter-spacing:0.1em;}
.kpi .value {font-size:1.6rem; font-weight:750; color:#F0EFEC; margin-top:4px; line-height:1.15;}
.kpi .note {font-size:0.78rem; color:#C3C2B7; margin-top:4px;}

/* insight cards */
.card {background:#1A1B1E; border:1px solid #26282C; border-radius:12px; padding:16px 18px; margin-bottom:12px;}
.card h4 {margin:0 0 6px 0; font-size:1rem; color:#F0EFEC;}
.card p {margin:0; color:#C3C2B7; font-size:0.92rem; line-height:1.5;}
.card .act {margin-top:8px; color:#A6D84A; font-size:0.86rem;}
.pill {display:inline-block; background:#24262A; color:#C3C2B7; border-radius:20px; padding:3px 11px;
       margin:3px 4px 3px 0; font-size:0.8rem; border:1px solid #2E3035;}

.stTabs [data-baseweb="tab-list"] {gap: 6px;}
.stTabs [data-baseweb="tab"] {padding: 8px 14px;}
</style>
""",
        unsafe_allow_html=True,
    )


def page_header(title, subtitle):
    st.markdown(f'<div class="page-head"><h2>{title}</h2><p>{subtitle}</p></div>', unsafe_allow_html=True)


def kpi_row(items):
    # items: list of (label, value, note)
    cols = st.columns(len(items))
    for col, (label, value, note) in zip(cols, items):
        col.markdown(
            f'<div class="kpi"><div class="label">{label}</div>'
            f'<div class="value">{value}</div><div class="note">{note}</div></div>',
            unsafe_allow_html=True,
        )


def card(title, text, action=None):
    act = f'<div class="act">→ {action}</div>' if action else ""
    st.markdown(f'<div class="card"><h4>{title}</h4><p>{text}</p>{act}</div>', unsafe_allow_html=True)


# -------------------------------------------------------------- charts ----

def style_fig(fig, height=360, title=None, legend=False):
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=INK), x=0, xanchor="left") if title else None,
        height=height,
        margin=dict(l=10, r=20, t=48 if title else 16, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK_2, size=12),
        showlegend=legend,
        legend=dict(orientation="h", y=1.08, x=0, font=dict(color=INK_2)),
        hoverlabel=dict(bgcolor="#24262A", bordercolor="#3A3C42", font=dict(color=INK)),
        bargap=0.35,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=INK_3))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=INK_3))
    return fig


def hbar(labels, values, title, fmt="{:,.0f}", color=BLUE, height=None, hover_name="Value"):
    # horizontal bar, biggest on top, value written at the end of each bar
    labels = list(labels)
    values = list(values)
    text = [fmt.format(v) for v in values]
    fig = go.Figure(
        go.Bar(
            x=values, y=labels, orientation="h", marker=dict(color=color, cornerradius=4),
            text=text, textposition="outside", textfont=dict(color=INK_2),
            hovertemplate="%{y}<br>" + hover_name + ": %{text}<extra></extra>", cliponaxis=False,
        )
    )
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, max(values) * 1.22 if values else 1])
    return style_fig(fig, height or max(240, 46 * len(labels) + 60), title)
