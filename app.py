# app.py
# Ola Ride Insights - Streamlit app
# Pages: Home, Dashboard, SQL Insights, Ride Explorer, Anomaly Watch, Power BI Report, Insights

import os
import glob
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from helpers import (
    load_data, load_vehicles, run_sql, inr, kpis, load_css, page_header, kpi_row, card,
    style_fig, hbar, VEHICLE_ORDER, DAY_ORDER, BLUE, ORANGE, AQUA, YELLOW, STATUS_COLORS,
    INK, INK_2, INK_3,
)
from sql_queries import QUERIES

st.set_page_config(page_title="Ola Ride Insights", page_icon="🚕", layout="wide")
load_css()

df = load_data()
vehicles = load_vehicles()

# paste your Power BI "Publish to web" link here, or add POWERBI_EMBED_URL to the app secrets
POWERBI_EMBED_URL = ""


# ------------------------------------------------------------- sidebar ----

st.sidebar.markdown(
    '<div class="brand"><div class="dot"><span></span></div>'
    '<div><div class="name">OLA</div><div class="sub">Ride Insights</div></div></div>',
    unsafe_allow_html=True,
)

PAGES = ["🏠 Home", "📊 Dashboard", "🧮 SQL Insights", "🔎 Ride Explorer",
         "🚨 Anomaly Watch", "📈 Power BI Report", "💡 Insights"]
page = st.sidebar.radio("Go to", PAGES, label_visibility="collapsed")


def sidebar_filters():
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filters**")
    min_d, max_d = df["Ride_Date"].min().date(), df["Ride_Date"].max().date()
    dates = st.sidebar.date_input("Date range", (min_d, max_d), min_value=min_d, max_value=max_d)
    picked = st.sidebar.multiselect("Vehicle type", VEHICLE_ORDER, default=VEHICLE_ORDER)
    bands = ["Late Night (0-5)", "Morning (6-11)", "Afternoon (12-16)", "Evening (17-20)", "Night (21-23)"]
    band = st.sidebar.multiselect("Time of day", bands, default=bands)

    out = df
    if isinstance(dates, (list, tuple)) and len(dates) == 2:
        out = out[(out["Ride_Date"].dt.date >= dates[0]) & (out["Ride_Date"].dt.date <= dates[1])]
    out = out[out["Vehicle_Type"].isin(picked) & out["Time_Band"].isin(band)]
    st.sidebar.caption(f"{len(out):,} of {len(df):,} bookings selected")
    return out


st.sidebar.markdown("---")
st.sidebar.caption("Data: 103,024 Ola bookings, Bengaluru, July 2024")


# ================================================================ HOME ====

def home():
    st.markdown(
        """
<div class="hero">
  <div class="tag">Ride-sharing analytics</div>
  <h1>Ola Ride Insights</h1>
  <p>A month of Ola bookings in Bengaluru, cleaned, queried with SQL and turned into a dashboard
  that shows where rides are won, where they are lost and what that means for the business.</p>
  <div class="road"></div><div class="car">🚕</div><div class="pin">📍</div>
</div>
""",
        unsafe_allow_html=True,
    )

    k = kpis(df)
    kpi_row([
        ("Total bookings", f"{k['bookings']:,}", "1 – 31 July 2024"),
        ("Completed rides", f"{k['success']:,}", f"{k['success_rate']:.1f}% success rate"),
        ("Revenue", inr(k["revenue"]), f"avg {inr(k['avg_fare'], False)} per ride"),
        ("Lost to drivers", f"{k['driver_cancel'] + k['no_driver']:.1f}%", "driver cancels + no driver"),
        ("Avg rating", f"{k['driver_rating']:.2f} ★", "drivers and customers alike"),
    ])

    st.write("")
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown("#### About the project")
        st.markdown(
            "Ola generates a huge amount of booking data every day, but raw rows do not tell you "
            "where the business is losing rides or money. This project takes **103,024 bookings** "
            "and works through them end to end:\n\n"
            "1. **Clean** the raw Excel export and add useful columns (hour, time band, cancel reason, revenue).\n"
            "2. **Query** it with SQL to answer 10 business questions.\n"
            "3. **Visualise** it in a 5 page Power BI report and in this app.\n"
            "4. **Flag** unusual rides that an operations team should check.\n\n"
            "Use the menu on the left to move between pages. The Dashboard and Ride Explorer pages "
            "have filters for date, vehicle type and time of day."
        )
        st.markdown("#### Business questions")
        for q in [
            "When is demand highest and how should drivers be allocated?",
            "How do customers choose vehicles and pay?",
            "What do fares and pricing look like?",
            "Which rides look unusual or possibly fraudulent?",
        ]:
            st.markdown(f"- {q}")
    with right:
        st.markdown("#### What's inside")
        for t, d in [
            ("📊 Dashboard", "Overall, Vehicle Type, Revenue, Cancellation and Ratings views"),
            ("🧮 SQL Insights", "The 10 SQL questions with live results"),
            ("🔎 Ride Explorer", "Search any booking or customer"),
            ("🚨 Anomaly Watch", "Rides that do not add up"),
            ("📈 Power BI Report", "The Power BI dashboard"),
            ("💡 Insights", "Findings and recommendations"),
        ]:
            card(t, d)
        st.markdown("#### Tools")
        st.markdown(
            "".join(f'<span class="pill">{t}</span>' for t in
                    ["Python", "Pandas", "NumPy", "SQL", "SQLite / MySQL", "Plotly", "Matplotlib",
                     "Seaborn", "Power BI", "Streamlit"]),
            unsafe_allow_html=True,
        )


# =========================================================== DASHBOARD ====

def dashboard():
    page_header("Dashboard", "Five views, same split as the Power BI report. Filters are in the sidebar.")
    data = sidebar_filters()
    if data.empty:
        st.warning("No bookings match these filters.")
        return
    ok = data[data["Booking_Status"] == "Success"]
    k = kpis(data)

    t1, t2, t3, t4, t5 = st.tabs(["Overall", "Vehicle Type", "Revenue", "Cancellation", "Ratings"])

    # ---------------- overall
    with t1:
        kpi_row([
            ("Bookings", f"{k['bookings']:,}", ""),
            ("Success rate", f"{k['success_rate']:.1f}%", f"{k['success']:,} rides"),
            ("Revenue", inr(k["revenue"]), ""),
            ("Driver cancel", f"{k['driver_cancel']:.1f}%", ""),
            ("Customer cancel", f"{k['cust_cancel']:.1f}%", ""),
            ("No driver found", f"{k['no_driver']:.1f}%", ""),
        ])
        st.write("")

        daily = data.groupby([data["Ride_Date"], "Booking_Status"]).size().unstack(fill_value=0)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily.index, y=daily.sum(axis=1), name="All bookings", mode="lines+markers",
            line=dict(color=BLUE, width=2), marker=dict(size=8),
            hovertemplate="%{x|%a %d %b}<br>All bookings: %{y:,}<extra></extra>"))
        if "Success" in daily:
            fig.add_trace(go.Scatter(
                x=daily.index, y=daily["Success"], name="Completed", mode="lines+markers",
                line=dict(color=AQUA, width=2), marker=dict(size=8),
                hovertemplate="%{x|%a %d %b}<br>Completed: %{y:,}<extra></extra>"))
        fig.update_yaxes(rangemode="tozero")
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(style_fig(fig, 340, "Ride volume over time", legend=True), width="stretch")

        c1, c2 = st.columns([2, 3], gap="large")
        with c1:
            s = data["Booking_Status"].value_counts()
            fig = go.Figure(go.Pie(
                labels=s.index, values=s.values, hole=0.62, sort=False,
                marker=dict(colors=[STATUS_COLORS[x] for x in s.index], line=dict(color="#0E0F11", width=2)),
                textinfo="percent", textfont=dict(color=INK),
                hovertemplate="%{label}<br>%{value:,} bookings (%{percent})<extra></extra>"))
            fig.add_annotation(text=f"<b>{k['success_rate']:.0f}%</b><br><span style='font-size:11px'>success</span>",
                               showarrow=False, font=dict(size=20, color=INK))
            fig = style_fig(fig, 360, "Booking status breakdown", legend=True)
            fig.update_layout(legend=dict(orientation="v", y=-0.05, x=0, yanchor="top"), margin=dict(b=90))
            st.plotly_chart(fig, width="stretch")
        with c2:
            # average bookings per day for each weekday x hour, so months with 5 Mondays do not skew it
            grid = data.pivot_table(index="Day_Name", columns="Ride_Hour", values="Booking_ID", aggfunc="count")
            days = data.groupby("Day_Name")["Ride_Date"].nunique()
            grid = grid.div(days, axis=0).reindex([d for d in DAY_ORDER if d in grid.index])
            fig = go.Figure(go.Heatmap(
                z=grid.values, x=grid.columns, y=grid.index,
                colorscale=[[0, "#1A2433"], [0.5, "#256ABF"], [1, "#9EC5F4"]], zmin=0,
                hovertemplate="%{y}, %{x}:00<br>Avg bookings: %{z:.0f}<extra></extra>",
                colorbar=dict(thickness=10, tickfont=dict(color=INK_3))))
            fig.update_xaxes(dtick=2, title="Hour of day")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(style_fig(fig, 360, "Demand heatmap: avg bookings per weekday & hour"),
                            width="stretch")
        st.caption("Demand is flat across hours and weekdays once each weekday is averaged over the number of "
                   "times it occurs in the month. There is no rush-hour peak in this data.")

    # ---------------- vehicle type
    with t2:
        g = data.groupby("Vehicle_Type", observed=True)
        table = pd.DataFrame({
            "Total Booking Value": g["Booking_Value"].sum(),
            "Success Booking Value": ok.groupby("Vehicle_Type", observed=True)["Booking_Value"].sum(),
            "Avg Distance (km)": ok.groupby("Vehicle_Type", observed=True)["Ride_Distance"].mean().round(1),
            "Total Distance (km)": ok.groupby("Vehicle_Type", observed=True)["Ride_Distance"].sum(),
            "Success Rate %": (g["Revenue"].apply(lambda s: (s > 0).mean() * 100)).round(1),
        }).reset_index()
        table = vehicles[["Vehicle_Type", "Vehicle_Image_URL"]].merge(table, on="Vehicle_Type")
        table = table.rename(columns={"Vehicle_Image_URL": "Icon", "Vehicle_Type": "Vehicle Type"})
        st.dataframe(
            table[["Icon", "Vehicle Type", "Total Booking Value", "Success Booking Value",
                   "Avg Distance (km)", "Total Distance (km)", "Success Rate %"]],
            hide_index=True, width="stretch",
            column_config={
                "Icon": st.column_config.ImageColumn("", width="small"),
                "Total Booking Value": st.column_config.NumberColumn("Total Booking Value (₹)", format="localized"),
                "Success Booking Value": st.column_config.NumberColumn("Success Booking Value (₹)", format="localized"),
                "Total Distance (km)": st.column_config.NumberColumn(format="localized"),
                "Success Rate %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
            },
        )
        c1, c2 = st.columns(2, gap="large")
        with c1:
            top = ok.groupby("Vehicle_Type", observed=True)["Ride_Distance"].sum().nlargest(5)
            st.plotly_chart(hbar(top.index, top.values, "Top 5 vehicle types by total ride distance",
                                 fmt="{:,.0f} km", hover_name="Distance"), width="stretch")
        with c2:
            avg = ok.groupby("Vehicle_Type", observed=True)["Ride_Distance"].mean().sort_values(ascending=False)
            colors = [ORANGE if v == "Auto" else BLUE for v in avg.index]
            st.plotly_chart(hbar(avg.index, avg.values, "Average distance per completed ride",
                                 fmt="{:.1f} km", color=colors, hover_name="Avg distance"),
                            width="stretch")
        st.caption("Demand is spread almost evenly over the seven types. Auto is the outlier: its rides average "
                   "about 10 km, against about 25 km for everything else.")

    # ---------------- revenue
    with t3:
        kpi_row([
            ("Revenue", inr(k["revenue"]), "completed rides only"),
            ("Avg fare", inr(k["avg_fare"], False), "per completed ride"),
            ("Avg distance", f"{k['avg_distance']:.1f} km", "per completed ride"),
            ("Value lost", inr(data["Booking_Value"].sum() - k["revenue"]), "booking value of cancelled rides"),
        ])
        st.write("")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            pay = ok.groupby("Payment_Method")["Booking_Value"].sum().sort_values(ascending=False)
            share = pay / pay.sum() * 100
            fig = hbar(pay.index, pay.values, "Revenue by payment method", hover_name="Revenue")
            fig.data[0].text = [f"{inr(v)}  ({s:.1f}%)" for v, s in zip(pay.values, share.values)]
            st.plotly_chart(fig, width="stretch")
        with c2:
            top = ok.groupby("Customer_ID")["Booking_Value"].sum().nlargest(5)
            st.plotly_chart(hbar(top.index, top.values, "Top 5 customers by total booking value",
                                 fmt="₹{:,.0f}", hover_name="Booking value"), width="stretch")

        per_day = ok.groupby("Ride_Date")["Ride_Distance"].agg(["sum", "mean"]).reset_index()
        fig = go.Figure(go.Bar(
            x=per_day["Ride_Date"], y=per_day["sum"], marker=dict(color=BLUE, cornerradius=4),
            customdata=per_day["mean"],
            hovertemplate="%{x|%a %d %b}<br>Total distance: %{y:,} km<br>Avg per ride: %{customdata:.1f} km<extra></extra>"))
        fig.update_yaxes(title="km")
        st.plotly_chart(style_fig(fig, 320, "Ride distance per day (completed rides)"), width="stretch")

        box = ok[["Day_Name", "Ride_Distance"]].copy()
        fig = go.Figure()
        for d in [d for d in DAY_ORDER if d in box["Day_Name"].unique()]:
            fig.add_trace(go.Box(y=box.loc[box["Day_Name"] == d, "Ride_Distance"], name=d[:3],
                                 marker=dict(color=BLUE), line=dict(color=BLUE, width=1.5),
                                 fillcolor="rgba(57,135,229,0.25)", boxpoints=False))
        fig.update_yaxes(title="km")
        st.plotly_chart(style_fig(fig, 300, "Ride distance distribution by weekday"), width="stretch")

    # ---------------- cancellation
    with t4:
        kpi_row([
            ("Cancelled by customer", f"{(data['Booking_Status'] == 'Canceled by Customer').sum():,}", f"{k['cust_cancel']:.1f}% of bookings"),
            ("Cancelled by driver", f"{(data['Booking_Status'] == 'Canceled by Driver').sum():,}", f"{k['driver_cancel']:.1f}% of bookings"),
            ("Driver not found", f"{(data['Booking_Status'] == 'Driver Not Found').sum():,}", f"{k['no_driver']:.1f}% of bookings"),
            ("Incomplete rides", f"{(data['Incomplete_Rides'] == 'Yes').sum():,}", "started but not finished"),
        ])
        st.write("")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            c = data["Canceled_Rides_by_Customer"].value_counts()
            st.plotly_chart(hbar(c.index, c.values, "Why customers cancel", hover_name="Rides"),
                            width="stretch")
        with c2:
            d = data["Canceled_Rides_by_Driver"].value_counts()
            st.plotly_chart(hbar(d.index, d.values, "Why drivers cancel", hover_name="Rides"),
                            width="stretch")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            # booking funnel: where rides drop out
            assigned = len(data) - (data["Booking_Status"] == "Driver Not Found").sum()
            not_cancelled = len(ok)
            finished = (ok["Incomplete_Rides"] == "No").sum()
            fig = go.Figure(go.Funnel(
                y=["Booked", "Driver assigned", "Ride started", "Ride finished"],
                x=[len(data), assigned, not_cancelled, finished],
                texttemplate="%{value:,}<br>%{percentInitial:.0%}", textfont=dict(color=INK),
                marker=dict(color=[BLUE, BLUE, BLUE, AQUA]),
                connector=dict(line=dict(color="#2A2B2F")),
                hovertemplate="%{y}: %{x:,}<extra></extra>"))
            st.plotly_chart(style_fig(fig, 340, "Booking funnel"), width="stretch")
        with c2:
            inc = data["Incomplete_Rides_Reason"].value_counts()
            st.plotly_chart(hbar(inc.index, inc.values, "Why rides were left incomplete", hover_name="Rides"),
                            width="stretch")
        st.caption("Over half of customer cancellations point back at the driver (not moving, asked to cancel). "
                   "Together with driver cancels and 'no driver found', about a third of all bookings are lost on the supply side.")

    # ---------------- ratings
    with t5:
        kpi_row([
            ("Avg driver rating", f"{k['driver_rating']:.2f} ★", "given to drivers"),
            ("Avg customer rating", f"{k['cust_rating']:.2f} ★", "given to customers"),
            ("Rated 4.5+ (drivers)", f"{(ok['Driver_Ratings'] >= 4.5).mean() * 100:.1f}%", "of completed rides"),
            ("Rated below 3.5 (drivers)", f"{(ok['Driver_Ratings'] < 3.5).mean() * 100:.1f}%", "of completed rides"),
        ])
        st.write("")
        c1, c2 = st.columns(2, gap="large")
        for col, field, title in [(c1, "Driver_Ratings", "Driver ratings distribution"),
                                  (c2, "Customer_Rating", "Customer ratings distribution")]:
            with col:
                dist = ok[field].value_counts().sort_index()
                fig = go.Figure(go.Bar(x=dist.index, y=dist.values, marker=dict(color=BLUE, cornerradius=3),
                                       hovertemplate="Rating %{x}<br>%{y:,} rides<extra></extra>"))
                fig.update_xaxes(dtick=0.5, title="Rating")
                st.plotly_chart(style_fig(fig, 300, title), width="stretch")

        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            # dot plot, so a zoomed-in axis is honest (bars would need to start at 0)
            avg = ok.groupby("Vehicle_Type", observed=True)[["Driver_Ratings", "Customer_Rating"]].mean()
            fig = go.Figure()
            for x0, x1, v in zip(avg["Driver_Ratings"], avg["Customer_Rating"], avg.index):
                fig.add_shape(type="line", x0=x0, x1=x1, y0=v, y1=v, line=dict(color="#3A3C42", width=2))
            fig.add_trace(go.Scatter(x=avg["Driver_Ratings"], y=avg.index, mode="markers", name="Driver rating",
                                     marker=dict(size=13, color=BLUE, line=dict(color="#0E0F11", width=2)),
                                     hovertemplate="%{y}<br>Driver rating: %{x:.3f}<extra></extra>"))
            fig.add_trace(go.Scatter(x=avg["Customer_Rating"], y=avg.index, mode="markers", name="Customer rating",
                                     marker=dict(size=13, color=ORANGE, line=dict(color="#0E0F11", width=2)),
                                     hovertemplate="%{y}<br>Customer rating: %{x:.3f}<extra></extra>"))
            fig.update_xaxes(range=[3.9, 4.1], title="Average rating (zoomed in)")
            fig.update_yaxes(autorange="reversed", showgrid=False)
            st.plotly_chart(style_fig(fig, 340, "Customer vs driver rating by vehicle type", legend=True),
                            width="stretch")
        with c2:
            pair = ok.groupby(["Driver_Ratings", "Customer_Rating"]).size().unstack(fill_value=0)
            fig = go.Figure(go.Heatmap(
                z=pair.values, x=pair.columns, y=pair.index,
                colorscale=[[0, "#1A2433"], [1, "#5598E7"]],
                hovertemplate="Driver %{y} / Customer %{x}<br>%{z:,} rides<extra></extra>",
                colorbar=dict(thickness=10, tickfont=dict(color=INK_3))))
            fig.update_xaxes(title="Customer rating", dtick=0.5)
            fig.update_yaxes(title="Driver rating", dtick=0.5)
            st.plotly_chart(style_fig(fig, 340, "Driver vs customer rating pairs"), width="stretch")
        st.caption("The dot plot is zoomed to 3.9 – 4.1: every vehicle type averages 4.0 on both sides, and the "
                   "rating pairs are spread evenly, so one side's rating does not predict the other's.")


# ======================================================== SQL INSIGHTS ====

def sql_insights():
    page_header("SQL Insights", "The 10 business questions from the brief, answered with SQL on a live SQLite copy of the data.")

    labels = [f"Q{q['id']}. {q['title']}" for q in QUERIES]
    choice = st.selectbox("Pick a question", labels)
    q = QUERIES[labels.index(choice)]

    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown("**Query**")
        st.code(q["sql"], language="sql")
        st.markdown(f"<span style='color:{INK_3}'>{q['why']}</span>", unsafe_allow_html=True)
    with right:
        result = run_sql(q["sql"])
        st.markdown(f"**Result** · {len(result):,} row{'s' if len(result) != 1 else ''}")

        if len(result) == 1 and len(result.columns) <= 3:
            cols = st.columns(len(result.columns))
            for c, name in zip(cols, result.columns):
                val = result.iloc[0][name]
                shown = inr(val, False) if "Value" in name else f"{val:,}" if isinstance(val, (int, np.integer)) else f"{val}"
                c.markdown(f'<div class="kpi"><div class="label">{name.replace("_", " ")}</div>'
                           f'<div class="value">{shown}</div></div>', unsafe_allow_html=True)
        elif len(result) > 50:
            search = st.text_input("Search inside the result", placeholder="Booking ID, customer, location...")
            view = result
            if search:
                mask = view.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
                view = view[mask]
            st.dataframe(view.head(1000), hide_index=True, width="stretch", height=380)
            if len(view) > 1000:
                st.caption(f"Showing the first 1,000 of {len(view):,} rows. Download for the full set.")
        else:
            st.dataframe(result, hide_index=True, width="stretch")

        if q["id"] in (2, 4, 8):
            x, y = result.columns[0], result.columns[1]
            fmt = "{:.2f}" if q["id"] == 8 else "{:,.2f}" if q["id"] == 2 else "{:,.0f}"
            st.plotly_chart(hbar(result[x], result[y], "", fmt=fmt), width="stretch")

        st.download_button("⬇ Download result as CSV", result.to_csv(index=False).encode(),
                           file_name=f"ola_sql_q{q['id']}.csv", mime="text/csv")

    with st.expander("✍️ Write your own query"):
        st.caption("Table name: `ola_rides`. Only SELECT queries are allowed.")
        cols = ", ".join(run_sql("SELECT * FROM ola_rides LIMIT 1").columns)
        st.markdown(f"<span style='color:{INK_3}; font-size:0.85rem'>Columns: {cols}</span>", unsafe_allow_html=True)
        own = st.text_area("SQL", "SELECT Pickup_Location, COUNT(*) AS rides\nFROM ola_rides\n"
                                  "WHERE Booking_Status = 'Success'\nGROUP BY Pickup_Location\n"
                                  "ORDER BY rides DESC\nLIMIT 10;", height=160)
        if st.button("Run query"):
            text = own.strip().rstrip(";")
            if not re.match(r"(?is)^\s*(select|with)\b", text) or ";" in text:
                st.error("Please run a single SELECT query.")
            else:
                try:
                    out = run_sql(text)
                    st.dataframe(out.head(1000), hide_index=True, width="stretch")
                    st.caption(f"{len(out):,} rows")
                except Exception as e:
                    st.error(f"Query failed: {e}")


# ======================================================= RIDE EXPLORER ====

def ride_explorer():
    page_header("Ride Explorer", "Search and filter individual bookings.")
    data = sidebar_filters()

    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("Search", placeholder="Booking ID, Customer ID or location (e.g. CID954071, Hebbal)")
    status = c2.multiselect("Status", sorted(df["Booking_Status"].unique()))
    pay = c3.multiselect("Payment", sorted(df["Payment_Method"].dropna().unique()))
    dmin, dmax = st.slider("Ride distance (km)", 0, int(df["Ride_Distance"].max()), (0, int(df["Ride_Distance"].max())))

    if search:
        s = search.strip()
        data = data[
            data["Booking_ID"].str.contains(s, case=False)
            | data["Customer_ID"].str.contains(s, case=False)
            | data["Pickup_Location"].str.contains(s, case=False)
            | data["Drop_Location"].str.contains(s, case=False)
        ]
    if status:
        data = data[data["Booking_Status"].isin(status)]
    if pay:
        data = data[data["Payment_Method"].isin(pay)]
    data = data[data["Ride_Distance"].between(dmin, dmax)]

    k = kpis(data) if len(data) else None
    if k:
        kpi_row([
            ("Bookings", f"{k['bookings']:,}", ""),
            ("Completed", f"{k['success']:,}", f"{k['success_rate']:.1f}%"),
            ("Revenue", inr(k["revenue"]), ""),
            ("Avg distance", f"{k['avg_distance']:.1f} km", "completed rides"),
        ])
        st.write("")

    cols = ["Booking_ID", "Ride_Date", "Ride_Time", "Booking_Status", "Customer_ID", "Vehicle_Type",
            "Pickup_Location", "Drop_Location", "Ride_Distance", "Booking_Value", "Payment_Method",
            "Driver_Ratings", "Customer_Rating", "Cancel_Reason", "Incomplete_Rides_Reason"]
    st.dataframe(
        data[cols].head(2000), hide_index=True, width="stretch", height=460,
        column_config={
            "Ride_Date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "Booking_Value": st.column_config.NumberColumn("Booking Value", format="₹%d"),
            "Ride_Distance": st.column_config.NumberColumn("Distance", format="%d km"),
        },
    )
    st.caption(f"{len(data):,} matching bookings" + (" · showing first 2,000" if len(data) > 2000 else ""))
    st.download_button("⬇ Download filtered rides", data[cols].to_csv(index=False).encode(),
                       file_name="ola_filtered_rides.csv", mime="text/csv")


# ======================================================= ANOMALY WATCH ====

def anomaly_watch():
    page_header("Anomaly Watch", "Rule-based checks that surface rides worth a second look.")
    ok = df[df["Booking_Status"] == "Success"].copy()

    rules = {
        "Same pickup and drop location": df["Pickup_Location"] == df["Drop_Location"],
        "Over ₹200 per km (completed)": (df["Booking_Status"] == "Success") & (df["Fare_Per_Km"] > 200),
        "Short ride (≤2 km), fare over ₹1,500": (df["Booking_Status"] == "Success") & (df["Ride_Distance"] <= 2) & (df["Booking_Value"] > 1500),
        "Marked Success but incomplete": df["Incomplete_Rides"] == "Yes",
    }
    kpi_row([(name, f"{mask.sum():,}", f"{mask.mean() * 100:.1f}% of bookings") for name, mask in rules.items()])
    st.write("")

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        sample = ok.sample(min(8000, len(ok)), random_state=7)
        flagged = ok[ok["Fare_Per_Km"] > 200]
        fig = go.Figure()
        fig.add_trace(go.Scattergl(x=sample["Ride_Distance"], y=sample["Booking_Value"], mode="markers",
                                   name="Normal (sample)", marker=dict(size=5, color=BLUE, opacity=0.35),
                                   hovertemplate="%{x} km · ₹%{y:,}<extra></extra>"))
        fig.add_trace(go.Scattergl(x=flagged["Ride_Distance"], y=flagged["Booking_Value"], mode="markers",
                                   name="Over ₹200 / km", marker=dict(size=7, color=ORANGE,
                                   line=dict(color="#0E0F11", width=1)),
                                   customdata=flagged["Booking_ID"],
                                   hovertemplate="%{customdata}<br>%{x} km · ₹%{y:,}<extra></extra>"))
        fig.update_xaxes(title="Ride distance (km)")
        fig.update_yaxes(title="Booking value (₹)")
        st.plotly_chart(style_fig(fig, 400, "Fare vs distance", legend=True), width="stretch")
    with c2:
        st.markdown("#### What the checks mean")
        card("Fare does not follow distance",
             f"Correlation between fare and distance is only {ok['Booking_Value'].corr(ok['Ride_Distance']):.3f}. "
             "Very short trips with high fares are the first place to look for overcharging or fake trips.")
        card("Status field overstates completion",
             "3,926 rides say Success but are flagged incomplete. True finished rides are 60,041.")
        card("Same pickup and drop",
             "Could be round trips, but also a common pattern in test or fake bookings.")

    rule = st.selectbox("Show rides for rule", list(rules.keys()))
    hits = df[rules[rule]]
    show = ["Booking_ID", "Ride_Date", "Ride_Time", "Booking_Status", "Customer_ID", "Vehicle_Type",
            "Pickup_Location", "Drop_Location", "Ride_Distance", "Booking_Value", "Fare_Per_Km",
            "Incomplete_Rides_Reason"]
    st.dataframe(hits[show].sort_values("Booking_Value", ascending=False).head(1000), hide_index=True,
                 width="stretch", height=360,
                 column_config={"Fare_Per_Km": st.column_config.NumberColumn("₹ per km", format="%.0f"),
                                "Ride_Date": st.column_config.DateColumn("Date", format="DD MMM")})
    st.download_button("⬇ Download flagged rides", hits[show].to_csv(index=False).encode(),
                       file_name="ola_flagged_rides.csv", mime="text/csv")


# ===================================================== POWER BI REPORT ====

def powerbi_report():
    page_header("Power BI Report", "The same analysis built as a 5 page Power BI dashboard.")

    url = POWERBI_EMBED_URL
    try:
        url = st.secrets.get("POWERBI_EMBED_URL", url)
    except Exception:
        pass

    if url:
        components.iframe(url, height=640, scrolling=False)
        st.caption("Interactive report. Use the left menu inside the report to switch pages.")

    shots = sorted(glob.glob("powerbi/screenshots/*.png") + glob.glob("powerbi/screenshots/*.jpg"))
    if shots:
        names = [re.sub(r"^\d+[_\- ]*", "", os.path.splitext(os.path.basename(s))[0]).replace("_", " ").title()
                 for s in shots]
        tabs = st.tabs(names)
        for tab, path in zip(tabs, shots):
            with tab:
                st.image(path, width="stretch")
    elif not url:
        st.info("The Power BI report pages will show here. Meanwhile, the Dashboard page has the same five views.")

    st.markdown("#### Report pages")
    c = st.columns(5)
    for col, (t, d) in zip(c, [
        ("Overall", "Ride volume over time, booking status breakdown"),
        ("Vehicle Type", "Booking value, success value and distance per vehicle"),
        ("Revenue", "Payment methods, top customers, distance per day"),
        ("Cancellation", "Customer and driver cancel reasons"),
        ("Ratings", "Driver and customer ratings per vehicle"),
    ]):
        with col:
            card(t, d)


# ============================================================ INSIGHTS ====

def insights():
    page_header("Insights & Recommendations", "What the data says and what Ola could do about it.")
    k = kpis(df)

    items = [
        ("1 · Supply is the real bottleneck",
         f"Only {k['success_rate']:.1f}% of bookings become rides. Drivers cancel {k['driver_cancel']:.1f}% and no driver "
         f"is found for another {k['no_driver']:.1f}%, against {k['cust_cancel']:.1f}% cancelled by customers.",
         "Reward acceptance and completion streaks, penalise late cancels, widen the matching radius when no driver is found."),
        ("2 · Customers cancel because of drivers",
         "The top two customer reasons are 'driver not moving towards pickup' (30%) and 'driver asked to cancel' (25%).",
         "Auto-alert riders and re-match when a driver's ETA stops improving. Track 'asked to cancel' reports per driver."),
        ("3 · No rush hour in this data",
         "Once each weekday is averaged over the number of times it appears in July, demand is flat at about "
         "3,300 bookings a day and about 140 an hour, every hour.",
         "Keep driver supply steady through the day. Fixing cancellations is worth more than shifting drivers between hours."),
        ("4 · Driver side cancel reasons are fixable",
         "Personal & car related issues lead driver cancellations (35%), then customer related issues (29%).",
         "Vehicle check-ups and quick maintenance partnerships. Clear rules for refusing sick or over-capacity riders."),
        ("5 · Cash still dominates",
         "Cash brings in 54.9% of revenue and UPI 40.4%. Cards are under 5%.",
         "UPI cashback or wallet offers to move riders to digital payments, which also lowers cash handling risk."),
        ("6 · Auto is the short-trip product",
         "Every vehicle type gets about 14% of bookings, but Auto rides average ~10 km against ~25 km for the rest.",
         "Promote Auto for short hops and bundle it with first-mile / last-mile offers near metro stations."),
        ("7 · Pricing needs a review",
         "Fare has almost no link to distance (correlation 0.002), and 3,591 completed rides cost over ₹200 per km.",
         "Audit the fare and surge rules, and review the flagged short, expensive rides for overcharging."),
        ("8 · Ratings are steady",
         f"Drivers average {k['driver_rating']:.2f} and customers {k['cust_rating']:.2f}, with no vehicle type standing out.",
         "Satisfaction is not the problem. Focus effort on getting more bookings completed."),
    ]
    c1, c2 = st.columns(2, gap="large")
    for i, (t, txt, act) in enumerate(items):
        with (c1 if i % 2 == 0 else c2):
            card(t, txt, act)


# ---------------------------------------------------------------- route ----

if page == PAGES[0]:
    home()
elif page == PAGES[1]:
    dashboard()
elif page == PAGES[2]:
    sql_insights()
elif page == PAGES[3]:
    ride_explorer()
elif page == PAGES[4]:
    anomaly_watch()
elif page == PAGES[5]:
    powerbi_report()
else:
    insights()
