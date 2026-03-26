"""
Utility functions for the CarPool rental system.

This module provides utility functions for managing car availability, order status,
and allocation recalculation based on fleet changes.
"""

import streamlit as st
import shutil

from orders.dataManager import DataManager

def _update_car_status(car_id, status):
    """
    Update the availability status of a specific car.
    
    Args:
        car_id (str): ID of the car to update
        status (str): New availability status ('Available', 'Maintenance', etc.)
    
    Returns:
        bool: True if update successful, False if car not found
    """
    #====================================================================================================================
    #----   Load and Update Car Status   ---------------------------------------------------------------------------------

    cars_dm = DataManager('carPool')
    cars_df = cars_dm.read()
    if car_id not in cars_df['CarId'].values:
        st.error(f"Car {car_id} not found in car pool")
        return False
    cars_df.loc[cars_df['CarId'] == car_id, 'Availability'] = status
    cars_df.to_csv(cars_dm.file_path, index=False)
    return True


def _update_order_status(order_id, status):
    """
    Update the status of a specific order.
    
    Args:
        order_id (str): Order number to update
        status (str): New order status ('Pending', 'No Cars Available', etc.)
    
    Returns:
        bool: True if update successful, False if order not found
    """
    #====================================================================================================================
    #----   Load and Update Order Status   ------------------------------------------------------------------------------

    orders_dm = DataManager('openOrders')
    orders_df = orders_dm.read()
    if order_id not in orders_df['OrderNumber'].values:
        st.error(f"Order {order_id} not found in open orders")
        return False
    orders_df.loc[orders_df['OrderNumber'] == order_id, 'Status'] = status
    orders_df.to_csv(orders_dm.file_path, index=False)
    return True


def mark_car_unavailable(car_id):
    """
    Mark a car as unavailable (maintenance) and recalculate the allocation plan.
    
    Identifies orders that depend on this car and attempts to find alternative cars
    or marks orders as 'No Cars Available' if no alternatives exist.
    
    Args:
        car_id (str): ID of the car to mark as unavailable
    """
    #====================================================================================================================
    #----   Mark Car as Unavailable   -----------------------------------------------------------------------------------

    _update_car_status(car_id, 'Maintenance')

    #====================================================================================================================
    #----   Identify Affected Orders   ---------------------------------------------------------------------------------

    old_plan = st.session_state['order_plan']
    new_plan = st.session_state['order_manager'].produceOptimalAllocation()

    unfilfilled_orders = []
    if new_plan is None:
        orders_with_no_cars = [order_id for order_id in old_plan.keys() if old_plan[order_id]['car_id'] == car_id]
    
        #====================================================================================================================
        #----   Try to Find Alternative Assignments   ----------------------------------------------------------------------

        for oid in orders_with_no_cars:
            _update_order_status(oid, 'No Cars Available')
        
        st.session_state['order_plan'] = st.session_state['order_manager'].produceOptimalAllocation()

        for oid in orders_with_no_cars:
            _update_order_status(oid, 'Pending')
            updated_plan = st.session_state['order_manager'].produceOptimalAllocation()
            if updated_plan is None:
                _update_order_status(oid, 'No Cars Available')
                unfilfilled_orders.append(oid)
        
        st.session_state['order_plan'] = updated_plan
        st.success(f"Car {car_id} marked as unavailable. Orders unfillable: {unfilfilled_orders}.")
            
    else:
        st.session_state['order_plan'] = new_plan
        st.success(f"Car {car_id} marked as unavailable. Allocation recalculated with no unfillable orders.")

    st.rerun()


def mark_car_available(car_id):
    """
    Mark a car available and recalculate the allocation plan.
    
    Attempts to reassign previously blocked orders to the newly available car if possible.
    
    Args:
        car_id (str): ID of the car to mark as available
    """
    #====================================================================================================================
    #----   Mark Car as Available   -------------------------------------------------------------------------------------

    _update_car_status(car_id, 'Available')

    st.info(f"Marking car {car_id} as Available")

    #====================================================================================================================
    #----   Attempt to Reassign Blocked Orders   -----------------------------------------------------------------------

    orders_dm = DataManager('openOrders')
    orders_df = orders_dm.read()
    blocked_orders = orders_df[orders_df['Status'] == 'No Cars Available']['OrderNumber'].tolist()

    for oid in blocked_orders:
        _update_order_status(oid, 'Pending')
        updated_plan = st.session_state['order_manager'].produceOptimalAllocation()
        if updated_plan is None:
            _update_order_status(oid, 'No Cars Available')
        
    st.session_state['order_plan'] = st.session_state['order_manager'].produceOptimalAllocation()

    st.success(f"Car {car_id} marked available and allocation recalculated")
    st.rerun()


def reset_allocation():
    """
    Reset the entire allocation plan to its initial state by restoring from backup files.
    
    Resets car availability, open orders, and preferences to their backed-up versions,
    then recalculates the allocation plan.
    """
    #====================================================================================================================
    #----   Restore Backup Files   --------------------------------------------------------------------------------------

    shutil.copy('CarAvailability/backup_carPool.csv', 'CarAvailability/carPool.csv')
    shutil.copy('CarAvailability/backup_openOrders.csv', 'CarAvailability/openOrders.csv')
    shutil.copy('CarAvailability/backup_orderPreferences.csv', 'CarAvailability/orderPreferences.csv')
    
    st.success("Allocations reset and backups restored successfully!")
    if 'init' in st.session_state.keys():
        del st.session_state['init']

    st.rerun()


def set_order_upgrade(order_id, upgrade=True):
    """
    Set the Upgrade flag for an order in openOrders.

    Args:
        order_id (str): Order number to update (e.g., 'ORD-7701').
        upgrade (bool): True for upgrade, False for downgrade.

    Returns:
        bool: True if update succeeded, False if order not found.
    """
    orders_dm = DataManager('openOrders')
    orders_df = orders_dm.read()

    if order_id not in orders_df['OrderNumber'].astype(str).values:
        st.error(f"Order {order_id} not found in open orders")
        return False

    orders_df.loc[orders_df['OrderNumber'] == order_id, 'Upgrade'] = 'TRUE' if upgrade else 'FALSE'
    orders_df.to_csv(orders_dm.file_path, index=False)

    st.success(f"Order {order_id} {'upgraded' if upgrade else 'downgraded'} successfully.")
    return True