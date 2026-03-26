"""
Order Management System

Handles all operations related to rental orders, including creation, allocation,
and matching cars to orders based on preferences and availability.
"""

import pandas as pd
from datetime import datetime as dt, timedelta

from orders.dataManager import DataManager
from orders.carSimilarity import CarSimilarity, RecomendationScore
from orders.assignOrders import SolveRentalAllocation, checkNewOrderSolveable

class OrderManager():
    """
    Manages rental orders and car allocations.

    Provides functionality to:
    - Retrieve order information
    - Match cars to orders based on preferences
    - Generate optimal allocation plans
    - Handle new order integration

    Attributes:
        order_data_manager (DataManager): Manages open orders data
        order_preferences_manager (DataManager): Manages order preferences data
        car_data_manager (DataManager): Manages car pool data
    """

    def __init__(self):
        """
        Initialize the OrderManager with data managers for orders, preferences, and cars.
        """
        self.order_data_manager = DataManager('openOrders')
        self.order_preferences_manager = DataManager('orderPreferences')
        self.car_data_manager = DataManager('carPool')

    def getOrderIDs(self):
        """
        Retrieve all order IDs from the open orders data.

        Returns:
            list: List of order number strings
        """
        orders_df = self.order_data_manager.read()
        return orders_df['OrderNumber'].tolist()
    
    def getOrderDetails(self, orderId, carId):
        """
        Get order and car details combined into a single dataframe.
        
        Args:
            orderId: The order number to retrieve
            carId: The car ID to retrieve
        
        Returns:
            pd.DataFrame: A dataframe with first 8 columns as order information
                         and remaining columns as car attributes
        """
        orders_df = self.order_data_manager.read()
        cars_df = self.car_data_manager.read()
        
        # Get order details
        order_details = orders_df[orders_df['OrderNumber'] == orderId]
        if order_details.empty:
            raise ValueError(f"No order found with OrderNumber: {orderId}")
        
        # Get car details
        car_details = cars_df[cars_df['CarId'] == carId]
        if car_details.empty:
            raise ValueError(f"No car found with CarId: {carId}")
        
        # Merge order and car details
        merged_df = pd.concat([order_details.reset_index(drop=True), 
                               car_details.reset_index(drop=True)], axis=1)
        
        # Get order columns (first 9) and car columns (rest)
        order_columns = list(order_details.columns)[:9]
        car_columns = list(car_details.columns)
        
        # Reorder columns: order columns first, then car columns
        reordered_columns = order_columns + car_columns
        merged_df = merged_df[reordered_columns]
        
        return merged_df
    
    def checkNewOrder(self, plan, newOrder):
        """
        Check if a new order can be accommodated in the existing allocation plan.

        Args:
            plan (dict): Current allocation plan {order_id: assignment_details}
            newOrder (dict): New order details with 'id', 'potential' cars, and 'dates'

        Returns:
            tuple: (bool, dict) - (success, updated_plan or original_plan)
        """
        solveable, updated_plan = checkNewOrderSolveable(plan, newOrder)
        if solveable:
            return solveable, updated_plan
        else:
            updated_plan = self.produceOptimalAllocation
            
            return solveable is not None, updated_plan

    def produceOptimalAllocation(self):
        """
        Produces optimal car allocation for all open orders.
        
        For each order, finds up to 5 suitable cars using matchCarToOrder,
        then uses SolveRentalAllocation to determine which car goes to which order.
        
        Returns:
            dict: Allocation mapping {order_id: car_id}, or None if no feasible allocation exists.
        """
        #====================================================================================================================
        #----   Load and Filter Orders   -----------------------------------------------------------------------------------

        orders_df = self.order_data_manager.read()
        orders_df = orders_df[orders_df['Status'] == 'Pending']
        orders_for_allocation = []

        unfillable_orders = []
        
        #====================================================================================================================
        #----   Prepare Order Data for Allocation Solver   ----------------------------------------------------------------

        for idx, row in orders_df.iterrows():
            order_details = row.to_dict()
            order_id = order_details['OrderNumber']
            
            # Get up to 5 suitable cars for this order
            matching_cars = self.matchCarToOrder(order_details, top_n=5)
            
            # Extract car IDs from matches (returns list of tuples: [(car_id, similarity_result), ...])
            if matching_cars is None or len(matching_cars) == 0:
                # If no suitable cars found for an order, allocation not possible
                unfillable_orders.append(order_id)
                continue

            potential_cars = [car_id for car_id, _ in matching_cars]
            
            #====================================================================================================================
            #----   Convert Date Range for Overlap Comparison   ------------------------------------------------------------

            pickup_date = dt.strptime(order_details['ExpectedPickUpTime'], '%d/%m/%Y %H:%M')
            dropoff_date = dt.strptime(order_details['ExpectedDropOffTime'], '%d/%m/%Y %H:%M').replace(hour=23, minute=59, second=59)
            
            # Generate list of date strings from pickup to dropoff (inclusive)
            date_range = []
            current_date = pickup_date
            while current_date <= dropoff_date:
                date_range.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            orders_for_allocation.append({
                'id': order_id,
                'potential': potential_cars,
                'dates': date_range
            })
        
        #====================================================================================================================
        #----   Solve Optimal Assignment   ---------------------------------------------------------------------------------

        allocation = SolveRentalAllocation(orders_for_allocation)
        
        return allocation
    

    
    def matchCarToOrder(self, orderDetails: dict, miniumumMargin=0.2, minimumSimilarityScore=50, top_n=1):
        """
        Match cars to an order based on preferences and similarity scoring.

        Args:
            orderDetails (dict): Order details including OrderNumber, dates, revenue, etc.
            miniumumMargin (float): Minimum profit margin required
            minimumSimilarityScore (int): Minimum similarity score threshold
            top_n (int): Number of top matches to return

        Returns:
            list: List of tuples [(car_id, similarity_result), ...] sorted by ranking score
        """
        #====================================================================================================================
        #----   Load Data and Extract Order Parameters   -------------------------------------------------------------------

        preference_df = self.order_preferences_manager.read()
        cars_df = self.car_data_manager.read()

        order_number =              orderDetails['OrderNumber']
        pickup_location =           orderDetails['PickUpLocation']
        pickup_date = dt.strptime(  orderDetails['ExpectedPickUpTime'], '%d/%m/%Y %H:%M')
        dropoff_date = dt.strptime( orderDetails['ExpectedDropOffTime'], '%d/%m/%Y %H:%M').replace(hour=23, minute=59)
        order_revenue =             orderDetails['OrderRevenue']
        daily_revenue =             order_revenue / (dropoff_date - pickup_date).days
        give_upgrade =              orderDetails['Upgrade']

        order_preference_df = preference_df[preference_df['OrderNumber'] == order_number]
        requirments = order_preference_df.set_index('PreferenceType')['PreferenceValue'].to_dict()
        hard_conditions = order_preference_df.loc[order_preference_df['PreferenceCategory'] == 'hard', 'PreferenceType'].unique().tolist()
        
        cars_df = cars_df[(cars_df['Location'] == pickup_location) & (cars_df['Availability'] == 'Available')]
        
        if cars_df.empty:
            return []
        
        #====================================================================================================================
        #----   Calculate Similarity Scores for Each Car   ----------------------------------------------------------------

        results = {}
        backup_results = {}
        for idx, row in cars_df.iterrows():
            option_car_details = row.to_dict()

            similarity_result = CarSimilarity(requirments, option_car_details, hard_conditions, float(daily_revenue), miniumumMargin)
            
            if similarity_result['similarity_score'] < minimumSimilarityScore or similarity_result['breaks_hard_condition']:
                ranking_score = RecomendationScore(
                    similarity_result['similarity_score'], 
                    similarity_result['quality_score'], 
                    float(daily_revenue), 
                    float(option_car_details['DailyCost']), 
                    miniumumMargin, 
                    giveUpgrade=give_upgrade)
                
                similarity_result['ranking_score'] = ranking_score
                backup_results[option_car_details['CarId']] = similarity_result
            
            else:
                ranking_score = RecomendationScore(
                    similarity_result['similarity_score'], 
                    similarity_result['quality_score'], 
                    float(daily_revenue), 
                    float(option_car_details['DailyCost']), 
                    miniumumMargin, 
                    giveUpgrade=give_upgrade)
                
                similarity_result['ranking_score'] = ranking_score
                results[option_car_details['CarId']] = similarity_result
        
        #====================================================================================================================
        #----   Return Top Matches   ---------------------------------------------------------------------------------------

        if len(results) > 0:
            sorted_options = sorted(results.items(), key=lambda x: x[1]['ranking_score'], reverse=True)
            return sorted_options[:top_n]
        
        elif len(backup_results) > 0:
            sorted_options = sorted(backup_results.items(), key=lambda x: x[1]['ranking_score'], reverse=True)
            return sorted_options[:top_n]
        else:
            return []