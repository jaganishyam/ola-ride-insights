# DAX measures – Ola Ride Insights

All measures live in a table called **_Measures**. Fact table: **Rides** (`ola_rides_clean.csv`). Dimensions: **Vehicles** (`vehicle_types.csv`) and **Calendar** (DAX).

Expected values for the full month are shown so the report can be checked against the SQL results.

---

## Calculated tables

```DAX
Calendar =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 7, 1 ), DATE ( 2024, 7, 31 ) ),
    "Day", DAY ( [Date] ),
    "Day Name", FORMAT ( [Date], "dddd" ),
    "Day Short", FORMAT ( [Date], "ddd" ),
    "Day Num", WEEKDAY ( [Date], 2 ),
    "Week", "Week " & WEEKNUM ( [Date], 2 )
)
```
Sort `Day Name` and `Day Short` by `Day Num`.

```DAX
Funnel Stages =
DATATABLE (
    "Stage", STRING,
    "Stage Order", INTEGER,
    {
        { "Booked", 1 },
        { "Driver Assigned", 2 },
        { "Ride Started", 3 },
        { "Ride Finished", 4 }
    }
)
```
Sort `Stage` by `Stage Order`. No relationship to other tables.

---

## Volume

```DAX
Total Bookings = COUNTROWS ( Rides )                                  -- 103,024
```
```DAX
Successful Rides =
CALCULATE ( [Total Bookings], Rides[Booking_Status] = "Success" )    -- 63,967
```
```DAX
Success Rate % = DIVIDE ( [Successful Rides], [Total Bookings] )      -- 62.1 %
```
```DAX
Finished Rides =
CALCULATE ( [Successful Rides], Rides[Incomplete_Rides] = "No" )     -- 60,041
```
```DAX
Avg Bookings per Day =
AVERAGEX ( VALUES ( 'Calendar'[Date] ), [Total Bookings] )           -- ~3,323
```
`AVERAGEX` runs `[Total Bookings]` once per date in the current filter and averages the results. In the weekday × hour matrix this removes the "July has five Mondays" effect.

## Revenue

```DAX
Total Booking Value = SUM ( Rides[Booking_Value] )                    -- ₹5,65,34,614
```
```DAX
Success Booking Value =
CALCULATE ( [Total Booking Value], Rides[Booking_Status] = "Success" ) -- ₹3,50,80,467
```
```DAX
Value Lost = [Total Booking Value] - [Success Booking Value]           -- ₹2,14,54,147
```
```DAX
Avg Fare = DIVIDE ( [Success Booking Value], [Successful Rides] )     -- ₹548
```
```DAX
Revenue Share % =
DIVIDE (
    [Success Booking Value],
    CALCULATE ( [Success Booking Value], REMOVEFILTERS ( Rides[Payment_Method] ) )
)
```

## Distance

```DAX
Total Distance = SUM ( Rides[Ride_Distance] )                         -- 14,61,903 km
```
```DAX
Avg Distance =
CALCULATE ( AVERAGE ( Rides[Ride_Distance] ), Rides[Booking_Status] = "Success" )  -- 22.9 km
```
Cancelled rides have a distance of 0, so they are excluded from the average.

## Cancellations

```DAX
Customer Cancels =
CALCULATE ( [Total Bookings], Rides[Booking_Status] = "Canceled by Customer" )  -- 10,499
```
```DAX
Driver Cancels =
CALCULATE ( [Total Bookings], Rides[Booking_Status] = "Canceled by Driver" )    -- 18,434
```
```DAX
Driver Not Found =
CALCULATE ( [Total Bookings], Rides[Booking_Status] = "Driver Not Found" )      -- 10,124
```
```DAX
Lost Bookings = [Total Bookings] - [Successful Rides]                            -- 39,057
```
```DAX
Incomplete Rides =
CALCULATE ( [Total Bookings], Rides[Incomplete_Rides] = "Yes" )                 -- 3,926
```
```DAX
Customer Cancel % = DIVIDE ( [Customer Cancels], [Total Bookings] )   -- 10.2 %
Driver Cancel %   = DIVIDE ( [Driver Cancels], [Total Bookings] )     -- 17.9 %
No Driver %       = DIVIDE ( [Driver Not Found], [Total Bookings] )   -- 9.8 %
```
(three separate measures)

```DAX
Funnel Value =
SWITCH (
    SELECTEDVALUE ( 'Funnel Stages'[Stage] ),
    "Booked", [Total Bookings],
    "Driver Assigned", [Total Bookings] - [Driver Not Found],
    "Ride Started", [Successful Rides],
    "Ride Finished", [Finished Rides]
)
```
Returns 103,024 → 92,900 → 63,967 → 60,041.

## Ratings

```DAX
Avg Driver Rating   = AVERAGE ( Rides[Driver_Ratings] )               -- 4.00
Avg Customer Rating = AVERAGE ( Rides[Customer_Rating] )              -- 4.00
```
Blank ratings (cancelled rides) are skipped by `AVERAGE`, so no extra filter is needed.

```DAX
Rated Rides = COUNT ( Rides[Driver_Ratings] )                         -- 63,967
```

## Dynamic titles

```DAX
Title Overall =
"Ola rides · " & FORMAT ( [Total Bookings], "#,0" ) & " bookings · "
    & FORMAT ( [Success Rate %], "0.0%" ) & " completed"
```
```DAX
Title Lost =
FORMAT ( [Lost Bookings], "#,0" ) & " bookings lost ("
    & FORMAT ( DIVIDE ( [Lost Bookings], [Total Bookings] ), "0.0%" ) & ")"
```
Use these in a visual's title with **fx → Field value**, so titles update with slicers.
