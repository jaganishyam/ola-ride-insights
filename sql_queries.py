# sql_queries.py
# The 10 business questions from the project brief, written as plain SQL.
# Same queries live in sql/ola_ride_queries.sql (MySQL version with views).
# Everything here runs on SQLite inside the app and on MySQL without changes.

QUERIES = [
    {
        "id": 1,
        "title": "Retrieve all successful bookings",
        "sql": """SELECT *
FROM ola_rides
WHERE Booking_Status = 'Success';""",
        "why": "Base list of rides that actually happened. Every revenue and rating number is built on this set.",
    },
    {
        "id": 2,
        "title": "Average ride distance for each vehicle type",
        "sql": """SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Distance_Km
FROM ola_rides
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY Avg_Distance_Km DESC;""",
        "why": "Only completed rides are used. Cancelled rides carry a distance of 0 and would pull the average down.",
    },
    {
        "id": 3,
        "title": "Total number of rides cancelled by customers",
        "sql": """SELECT COUNT(*) AS Cancelled_By_Customer
FROM ola_rides
WHERE Booking_Status = 'Canceled by Customer';""",
        "why": "Customer side cancellations, the part of lost demand the app experience can influence.",
    },
    {
        "id": 4,
        "title": "Top 5 customers by number of rides booked",
        "sql": """SELECT Customer_ID,
       COUNT(Booking_ID) AS Total_Rides
FROM ola_rides
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5;""",
        "why": "Many customers tie at 4 rides, so Customer_ID is used as a tie breaker to keep the result stable.",
    },
    {
        "id": 5,
        "title": "Rides cancelled by drivers due to personal and car related issues",
        "sql": """SELECT COUNT(*) AS Driver_Cancels_Personal_Car
FROM ola_rides
WHERE Canceled_Rides_by_Driver = 'Personal & Car related issue';""",
        "why": "The biggest single reason drivers give for cancelling.",
    },
    {
        "id": 6,
        "title": "Max and min driver ratings for Prime Sedan bookings",
        "sql": """SELECT MAX(Driver_Ratings) AS Max_Driver_Rating,
       MIN(Driver_Ratings) AS Min_Driver_Rating
FROM ola_rides
WHERE Vehicle_Type = 'Prime Sedan'
  AND Booking_Status = 'Success';""",
        "why": "Ratings only exist for completed rides, so the filter on Success makes that explicit.",
    },
    {
        "id": 7,
        "title": "All rides paid using UPI",
        "sql": """SELECT *
FROM ola_rides
WHERE Payment_Method = 'UPI';""",
        "why": "UPI is the second biggest payment channel after cash.",
    },
    {
        "id": 8,
        "title": "Average customer rating per vehicle type",
        "sql": """SELECT Vehicle_Type,
       ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM ola_rides
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY Avg_Customer_Rating DESC;""",
        "why": "Shows if any vehicle category has noticeably happier or unhappier riders.",
    },
    {
        "id": 9,
        "title": "Total booking value of rides completed successfully",
        "sql": """SELECT SUM(Booking_Value) AS Total_Successful_Booking_Value
FROM ola_rides
WHERE Booking_Status = 'Success';""",
        "why": "This is the realised revenue for July 2024. It includes the 3,926 Success rides marked as incomplete.",
    },
    {
        "id": 10,
        "title": "All incomplete rides with the reason",
        "sql": """SELECT Booking_ID,
       Customer_ID,
       Vehicle_Type,
       Incomplete_Rides_Reason
FROM ola_rides
WHERE Incomplete_Rides = 'Yes';""",
        "why": "Rides that started but did not finish, with what went wrong.",
    },
]
