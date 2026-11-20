# 🚕 Ola Ride Insights

**Ride-sharing & mobility analytics: SQL · Power BI · Streamlit**

An end-to-end analysis of **103,024 Ola bookings in Bengaluru (1 – 31 July 2024)**. The raw booking export is cleaned with Python, queried with SQL to answer ten business questions, visualised in a five page Power BI report, and presented in an interactive Streamlit web app.

---

## Problem statement

Ola generates a large volume of data on bookings, drivers, fares and customer feedback, but turning those rows into decisions is hard. This project analyses one month of ride data to improve operational efficiency, customer satisfaction and business strategy, using data cleaning, EDA, SQL, a Power BI dashboard and a Streamlit app.

### Business use cases

- Identify peak demand hours and optimise driver allocation
- Understand customer behaviour for targeted marketing
- Study pricing patterns and how fares behave
- Detect anomalies or possibly fraudulent rides

---

## Dataset

| | |
|---|---|
| Source | `OLA_DataSet.xlsx`, sheet **July** |
| Rows | 103,024 bookings (one row per booking, no duplicates) |
| Period | 1 – 31 July 2024 |
| City | Bengaluru, 50 pickup / drop locations |
| Customers | 94,544 unique customer IDs |
| Vehicle types | Prime Sedan, Prime SUV, Prime Plus, Mini, Auto, Bike, E-Bike |

Key columns: `Booking_ID`, `Date`, `Booking_Status`, `Customer_ID`, `Vehicle_Type`, `Pickup_Location`, `Drop_Location`, `V_TAT`, `C_TAT`, `Canceled_Rides_by_Customer`, `Canceled_Rides_by_Driver`, `Incomplete_Rides`, `Incomplete_Rides_Reason`, `Booking_Value`, `Payment_Method`, `Ride_Distance`, `Driver_Ratings`, `Customer_Rating`.

---

## Approach

**1. Data understanding.** Checked structure, types, unique values and missing values. Every blank lines up with the booking status: payment, ratings and TAT only exist for completed rides, and cancel reasons only exist for cancelled rides.

**2. Cleaning and feature engineering** (`clean_data.py`, `notebooks/Ola_Ride_EDA.ipynb`)
- Kept only the July sheet. `Sheet1` / `Sheet2` are scratch pivots.
- Trimmed text, standardised `eBike` → `E-Bike`, and dropped the redundant `Time` column because `Date` already holds the timestamp.
- **Did not fill** the "not applicable" blanks with 0 or the mean, because that would invent ratings for rides that never happened. They stay as NULL.
- Added `Ride_Date`, `Ride_Time`, `Ride_Hour`, `Day_Name`, `Time_Band`, `Cancelled_By`, a single `Cancel_Reason` column, and `Revenue` (booking value of completed rides only).

**3. SQL analysis** (`sql/ola_ride_queries.sql`). Ten business questions, each saved as a MySQL view. The same queries run on SQLite inside the app.

**4. Power BI dashboard** (`powerbi/`). Five pages (Overall, Vehicle Type, Revenue, Cancellation, Ratings) with a star schema, DAX measures, slicers and page navigation.

**5. Streamlit app** (`app.py`). An interactive front end for the SQL results, dashboards, search and anomaly checks.

---

## SQL questions and results

| # | Question | Result |
|---|---|---|
| 1 | Retrieve all successful bookings | 63,967 rides |
| 2 | Average ride distance per vehicle type | Auto 10.0 km, every other type ~25 km |
| 3 | Rides cancelled by customers | 10,499 |
| 4 | Top 5 customers by number of rides | CID954071 with 5 rides, then four customers on 4 |
| 5 | Driver cancellations for personal & car related issues | 6,542 |
| 6 | Max / min driver rating for Prime Sedan | 5.0 / 3.0 |
| 7 | Rides paid by UPI | 25,881 |
| 8 | Average customer rating per vehicle type | 3.99 – 4.01 for every type |
| 9 | Total booking value of successful rides | ₹3,50,80,467 (₹3.51 Cr) |
| 10 | Incomplete rides with reason | 3,926 (Customer Demand 1,601 · Vehicle Breakdown 1,591 · Other 734) |

---

## Power BI dashboard

| Page | Visuals |
|---|---|
| **Overall** | KPI cards, ride volume over time, booking status breakdown, weekday × hour demand matrix |
| **Vehicle Type** | Vehicle table with icons (total value, success value, avg & total distance), top 5 vehicle types by distance |
| **Revenue** | Revenue by payment method, top 5 customers by booking value, ride distance per day, revenue waterfall |
| **Cancellation** | Customer and driver cancel reasons, booking funnel, decomposition tree of lost bookings |
| **Ratings** | Driver and customer rating distributions, average ratings per vehicle type, driver vs customer rating scatter |

Built in Power BI Desktop with a custom theme (`powerbi/ola_theme.json`), page backgrounds from the project template (`powerbi/backgrounds/`) and DAX measures (`powerbi/dax_measures.md`).

---

## Streamlit app

| Page | What it does |
|---|---|
| 🏠 Home | Project overview and headline KPIs |
| 📊 Dashboard | Overall, Vehicle Type, Revenue, Cancellation and Ratings tabs with date, vehicle and time-of-day filters |
| 🧮 SQL Insights | Pick any of the 10 questions to see the SQL and its live result, search inside the result, download it as CSV, or write your own SELECT query |
| 🔎 Ride Explorer | Search by booking ID, customer ID or location and filter by status, payment and distance |
| 🚨 Anomaly Watch | Rule-based flags for suspicious rides, with a fare vs distance scatter and a downloadable list |
| 📈 Power BI Report | The Power BI report pages |
| 💡 Insights | Findings and recommendations |

---

## Key insights

| Area | Finding |
|---|---|
| **Overall** | 62.1% of bookings become rides, earning ₹3.51 Cr at an average of ₹548 a ride |
| **Supply** | Drivers cancel 17.9% of bookings and no driver is found for 9.8%, against 10.2% cancelled by customers |
| **Customer cancels** | The top two reasons blame the driver: *not moving towards pickup* (30%) and *asked to cancel* (25%) |
| **Driver cancels** | Led by *personal & car related issues* (35%) and *customer related issues* (29%) |
| **Demand timing** | Flat. After adjusting for July having five Mondays, Tuesdays and Wednesdays, every weekday averages ~3,300 bookings and every hour ~140 a day. There is no rush-hour peak |
| **Vehicles** | Bookings split almost evenly (~14% each). Auto rides average ~10 km against ~25 km for the rest |
| **Payments** | Cash 54.9% of revenue, UPI 40.4%, cards under 5% |
| **Pricing** | Fare has almost no link to distance (correlation 0.002) |
| **Ratings** | Drivers and customers both average 4.00, with no vehicle type standing out |
| **Anomalies** | 2,121 bookings with the same pickup and drop, 3,591 completed rides above ₹200/km, and 3,926 rides marked *Success* but flagged incomplete |

## Recommendations

1. **Fix supply-side losses first.** Reward acceptance and completion streaks, penalise late cancels, and widen the matching radius when no driver is found.
2. **Act on driver behaviour.** Alert riders and re-match automatically when a driver stops moving towards the pickup, and track "asked to cancel" reports per driver.
3. **Keep supply even through the day** instead of chasing peaks that the data does not show.
4. **Push digital payments** with UPI cashback to cut cash handling.
5. **Position Auto as the short-trip product** for first-mile / last-mile journeys.
6. **Audit pricing and the flagged rides.** Review fare and surge rules and check short, high-fare trips for overcharging.

---

## Repository structure

```
ola-ride-insights/
├── app.py                     # Streamlit app (all pages)
├── helpers.py                 # data loading, SQLite connection, styling, chart helpers
├── sql_queries.py             # the 10 SQL questions used by the app
├── clean_data.py              # raw Excel -> clean CSV
├── requirements.txt
├── .streamlit/config.toml     # app theme
├── data/
│   ├── raw/OLA_DataSet.xlsx
│   ├── ola_rides_clean.csv
│   └── vehicle_types.csv      # vehicle order + icon URLs
├── sql/
│   └── ola_ride_queries.sql   # MySQL: table, load, 10 views
├── notebooks/
│   └── Ola_Ride_EDA.ipynb     # cleaning + EDA
└── powerbi/
    ├── ola_theme.json         # Power BI theme
    ├── dax_measures.md        # all DAX measures
    ├── backgrounds/           # page backgrounds (1920×1080)
    └── screenshots/           # exported report pages
```

## Tech stack

Python · Pandas · NumPy · Matplotlib · Seaborn · SQL (MySQL / SQLite) · Power BI · Plotly · Streamlit

## Author

**Shyam Jagani**, Data Analyst · MSc Data Science, University of Essex
[LinkedIn](https://www.linkedin.com/in/shyam-jagani-356535141)
