# Car Hire For You

## Description
Wheel Deal is a comprehensive car rental management system built with Streamlit. It provides a web-based interface for managing rental orders, tracking fleet status, and creating new orders with customizable preferences. The system automatically allocates cars to orders based on availability, preferences, and optimization algorithms to maximize utilization and revenue.

## Features
- Order Management: View and manage existing rental orders
- Fleet Status: Monitor car availability and maintenance
- Create New Orders: Add new rental requests with preferences
- Automatic Allocation: Optimize car assignments to orders

## Order Creation Flow
When a new order is created, the following sequence of functions is executed:

1. **User Input Collection**: The `show_createOrderForm()` function in `UI/createOrder.py` displays the order form and collects user input including customer details, pickup/dropoff locations, dates, revenue, and car preferences.

2. **Order Data Validation**: Input validation ensures required fields are filled and dates are in the correct format.

3. **Order Number Generation**: `_next_order_number()` generates a unique order ID (e.g., ORD-1001) by checking existing orders in `openOrders.csv`.

4. **Order Persistence**: `create_order_from_data()` saves the order details to `CarAvailability/openOrders.csv` using the `DataManager` class.

5. **Preferences Storage**: Order preferences (hard/soft constraints on manufacturer, condition, seats, etc.) are saved to `CarAvailability/orderPreferences.csv`.

6. **Allocation Trigger**: After saving, `produceOptimalAllocation()` in `orders/orderManager.py` is called to update the car-to-order assignments.

7. **Car Matching**: For each pending order, `matchCarToOrder()` uses similarity scoring (`CarSimilarity` class) to find up to 5 suitable cars based on preferences and availability.

8. **Optimal Assignment**: `SolveRentalAllocation()` from `orders/assignOrders.py` solves the assignment problem to allocate cars to orders, considering date overlaps and constraints.

9. **UI Update**: The session state is refreshed with the new allocation plan, updating the displayed fleet status and order management pages.</content>
<parameter name="filePath">c:\Users\Shadow\Documents\CarPool\README.txt
