-- =====================================================================
-- Ola Ride Insights : SQL analysis (MySQL 8)
-- Data   : data/ola_rides_clean.csv  (103,024 bookings, Bengaluru, July 2024)
-- Author : Shyam Jagani
-- =====================================================================

CREATE DATABASE IF NOT EXISTS ola_db;
USE ola_db;

DROP TABLE IF EXISTS ola_rides;
CREATE TABLE ola_rides (
    Booking_ID                 VARCHAR(20) PRIMARY KEY,
    Ride_Date                  DATE,
    Ride_Time                  VARCHAR(5),
    Ride_Hour                  TINYINT,
    Day_Name                   VARCHAR(10),
    Time_Band                  VARCHAR(20),
    Booking_Status             VARCHAR(25),
    Cancelled_By               VARCHAR(15),
    Customer_ID                VARCHAR(15),
    Vehicle_Type               VARCHAR(15),
    Pickup_Location            VARCHAR(40),
    Drop_Location              VARCHAR(40),
    V_TAT                      DECIMAL(6,1),
    C_TAT                      DECIMAL(6,1),
    Canceled_Rides_by_Customer VARCHAR(60),
    Canceled_Rides_by_Driver   VARCHAR(60),
    Cancel_Reason              VARCHAR(60),
    Incomplete_Rides           VARCHAR(5),
    Incomplete_Rides_Reason    VARCHAR(30),
    Booking_Value              INT,
    Revenue                    INT,
    Payment_Method             VARCHAR(15),
    Ride_Distance              INT,
    Driver_Ratings             DECIMAL(2,1),
    Customer_Rating            DECIMAL(2,1)
);

-- Load the CSV (blank cells become NULL, they mean "not applicable").
-- Change the path to where the file sits on your machine.
LOAD DATA LOCAL INFILE 'C:/ola-ride-insights/data/ola_rides_clean.csv'
INTO TABLE ola_rides
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(Booking_ID, Ride_Date, Ride_Time, Ride_Hour, Day_Name, Time_Band, Booking_Status, Cancelled_By,
 Customer_ID, Vehicle_Type, Pickup_Location, Drop_Location, @v_tat, @c_tat, @cust_reason,
 @drv_reason, @cancel_reason, @incomplete, @incomplete_reason, Booking_Value, Revenue,
 @payment, Ride_Distance, @drv_rating, @cust_rating)
SET V_TAT                      = NULLIF(@v_tat, ''),
    C_TAT                      = NULLIF(@c_tat, ''),
    Canceled_Rides_by_Customer = NULLIF(@cust_reason, ''),
    Canceled_Rides_by_Driver   = NULLIF(@drv_reason, ''),
    Cancel_Reason              = NULLIF(@cancel_reason, ''),
    Incomplete_Rides           = NULLIF(@incomplete, ''),
    Incomplete_Rides_Reason    = NULLIF(@incomplete_reason, ''),
    Payment_Method             = NULLIF(@payment, ''),
    Driver_Ratings             = NULLIF(@drv_rating, ''),
    Customer_Rating            = NULLIF(TRIM(TRAILING '\r' FROM @cust_rating), '');

-- quick check: should return 103024
SELECT COUNT(*) AS total_rows FROM ola_rides;

-- indexes on the columns the questions filter on
CREATE INDEX idx_status  ON ola_rides (Booking_Status);
CREATE INDEX idx_vehicle ON ola_rides (Vehicle_Type);
CREATE INDEX idx_payment ON ola_rides (Payment_Method);

-- =====================================================================
-- Business questions. Each one is saved as a view so it can be reused
-- (e.g. pulled straight into Power BI) and then queried.
-- =====================================================================

-- Q1. Retrieve all successful bookings
-- Result: 63,967 rows
CREATE OR REPLACE VIEW Successful_Bookings AS
SELECT *
FROM ola_rides
WHERE Booking_Status = 'Success';

SELECT * FROM Successful_Bookings;

-- Q2. Average ride distance for each vehicle type
-- Result: Auto ~10 km, every other type ~25 km
CREATE OR REPLACE VIEW Avg_Distance_By_Vehicle AS
SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Distance_Km
FROM ola_rides
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY Avg_Distance_Km DESC;

SELECT * FROM Avg_Distance_By_Vehicle;

-- Q3. Total number of rides cancelled by customers
-- Result: 10,499
CREATE OR REPLACE VIEW Customer_Cancellations AS
SELECT COUNT(*) AS Cancelled_By_Customer
FROM ola_rides
WHERE Booking_Status = 'Canceled by Customer';

SELECT * FROM Customer_Cancellations;

-- Q4. Top 5 customers by number of rides booked
-- Result: CID954071 (5 rides), then a tie at 4 rides
CREATE OR REPLACE VIEW Top_5_Customers AS
SELECT Customer_ID,
       COUNT(Booking_ID) AS Total_Rides
FROM ola_rides
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5;

SELECT * FROM Top_5_Customers;

-- Q5. Rides cancelled by drivers due to personal and car related issues
-- Result: 6,542
CREATE OR REPLACE VIEW Driver_Cancels_Personal_Car AS
SELECT COUNT(*) AS Driver_Cancels_Personal_Car
FROM ola_rides
WHERE Canceled_Rides_by_Driver = 'Personal & Car related issue';

SELECT * FROM Driver_Cancels_Personal_Car;

-- Q6. Max and min driver ratings for Prime Sedan bookings
-- Result: max 5.0 / min 3.0
CREATE OR REPLACE VIEW Prime_Sedan_Driver_Rating_Range AS
SELECT MAX(Driver_Ratings) AS Max_Driver_Rating,
       MIN(Driver_Ratings) AS Min_Driver_Rating
FROM ola_rides
WHERE Vehicle_Type = 'Prime Sedan'
  AND Booking_Status = 'Success';

SELECT * FROM Prime_Sedan_Driver_Rating_Range;

-- Q7. All rides paid using UPI
-- Result: 25,881 rows
CREATE OR REPLACE VIEW UPI_Payments AS
SELECT *
FROM ola_rides
WHERE Payment_Method = 'UPI';

SELECT * FROM UPI_Payments;

-- Q8. Average customer rating per vehicle type
-- Result: all types between 3.99 and 4.01
CREATE OR REPLACE VIEW Avg_Customer_Rating_By_Vehicle AS
SELECT Vehicle_Type,
       ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM ola_rides
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY Avg_Customer_Rating DESC;

SELECT * FROM Avg_Customer_Rating_By_Vehicle;

-- Q9. Total booking value of rides completed successfully
-- Result: Rs 35,080,467
CREATE OR REPLACE VIEW Total_Successful_Value AS
SELECT SUM(Booking_Value) AS Total_Successful_Booking_Value
FROM ola_rides
WHERE Booking_Status = 'Success';

SELECT * FROM Total_Successful_Value;

-- Q10. All incomplete rides with the reason
-- Result: 3,926 rows
CREATE OR REPLACE VIEW Incomplete_Rides_With_Reason AS
SELECT Booking_ID,
       Customer_ID,
       Vehicle_Type,
       Incomplete_Rides_Reason
FROM ola_rides
WHERE Incomplete_Rides = 'Yes';

SELECT * FROM Incomplete_Rides_With_Reason;
