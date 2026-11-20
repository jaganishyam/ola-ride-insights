# clean_data.py
# Takes the raw OLA Excel export and turns it into one clean CSV that the
# Streamlit app, the SQL queries and the Power BI report all read from.
#
# Run:  python clean_data.py

import pandas as pd
import numpy as np

RAW_FILE = "data/raw/OLA_DataSet.xlsx"
CLEAN_FILE = "data/ola_rides_clean.csv"
VEHICLE_FILE = "data/vehicle_types.csv"

# the order used on the dashboard (same as the Power BI slide template)
VEHICLE_ORDER = ["Prime Sedan", "Prime SUV", "Prime Plus", "Mini", "Auto", "Bike", "E-Bike"]


def time_band(hour):
    if hour < 6:
        return "Late Night (0-5)"
    if hour < 12:
        return "Morning (6-11)"
    if hour < 17:
        return "Afternoon (12-16)"
    if hour < 21:
        return "Evening (17-20)"
    return "Night (21-23)"


def main():
    # only the "July" sheet holds ride data, Sheet1 / Sheet2 are scratch work
    df = pd.read_excel(RAW_FILE, sheet_name="July")
    print("raw shape:", df.shape)

    # --- basic tidy up -------------------------------------------------------
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df = df.drop_duplicates(subset="Booking_ID")

    # trim stray spaces in every text column
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()

    # "eBike" -> "E-Bike" so it matches the dashboard template
    df["Vehicle_Type"] = df["Vehicle_Type"].replace({"eBike": "E-Bike"})

    # --- dates and times -----------------------------------------------------
    # the Date column already carries the time, so the Time column is redundant
    df["Booking_DateTime"] = pd.to_datetime(df["Date"])
    df["Ride_Date"] = df["Booking_DateTime"].dt.date
    df["Ride_Time"] = df["Booking_DateTime"].dt.strftime("%H:%M")
    df["Ride_Hour"] = df["Booking_DateTime"].dt.hour
    df["Day_Name"] = df["Booking_DateTime"].dt.day_name()
    df["Time_Band"] = df["Ride_Hour"].apply(time_band)

    # --- derived business columns -------------------------------------------
    status_to_actor = {
        "Success": "Completed",
        "Canceled by Customer": "Customer",
        "Canceled by Driver": "Driver",
        "Driver Not Found": "No Driver",
    }
    df["Cancelled_By"] = df["Booking_Status"].map(status_to_actor)

    # one column that holds the cancel reason, whoever cancelled
    df["Cancel_Reason"] = df["Canceled_Rides_by_Customer"].fillna(df["Canceled_Rides_by_Driver"])
    df.loc[df["Booking_Status"] == "Driver Not Found", "Cancel_Reason"] = "Driver Not Found"

    # revenue only counts when the ride actually happened
    df["Revenue"] = np.where(df["Booking_Status"] == "Success", df["Booking_Value"], 0)

    df["Vehicle_Sort"] = df["Vehicle_Type"].map({v: i + 1 for i, v in enumerate(VEHICLE_ORDER)})

    # --- missing values ------------------------------------------------------
    # Blanks here are "not applicable", not lost data:
    #   ratings, V_TAT, C_TAT, payment method -> only exist for Success rides
    #   cancel reasons -> only exist for cancelled rides
    # so they stay as blanks (NULL in SQL) instead of being filled with 0,
    # which would drag every average down.
    check = df[df["Booking_Status"] == "Success"][["Payment_Method", "Driver_Ratings", "Customer_Rating"]]
    assert check.isna().sum().sum() == 0, "a success ride is missing payment / ratings"

    # --- vehicle lookup (used for icons in the app and Power BI) ------------
    vehicles = (
        df[["Vehicle_Type", "Vehicle_Sort", "Vehicle_Images"]]
        .drop_duplicates("Vehicle_Type")
        .sort_values("Vehicle_Sort")
        .rename(columns={"Vehicle_Images": "Vehicle_Image_URL"})
    )
    vehicles.to_csv(VEHICLE_FILE, index=False)

    # kept lean on purpose so the CSV stays well under GitHub's 25 MB upload limit
    # (anything else, like fare per km or distance bands, is rebuilt in the app / DAX)
    keep = [
        "Booking_ID", "Ride_Date", "Ride_Time", "Ride_Hour", "Day_Name", "Time_Band",
        "Booking_Status", "Cancelled_By", "Customer_ID", "Vehicle_Type", "Pickup_Location",
        "Drop_Location", "V_TAT", "C_TAT", "Canceled_Rides_by_Customer", "Canceled_Rides_by_Driver",
        "Cancel_Reason", "Incomplete_Rides", "Incomplete_Rides_Reason", "Booking_Value", "Revenue",
        "Payment_Method", "Ride_Distance", "Driver_Ratings", "Customer_Rating",
    ]
    df = df.sort_values("Booking_DateTime")[keep]
    df.to_csv(CLEAN_FILE, index=False)

    print("clean shape:", df.shape)
    print("saved ->", CLEAN_FILE, "and", VEHICLE_FILE)


if __name__ == "__main__":
    main()
