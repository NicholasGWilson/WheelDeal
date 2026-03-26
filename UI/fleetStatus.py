"""
Fleet status UI module for the CarPool rental system.

This module provides functions for displaying and managing car fleet status,
including marking cars as available/unavailable and showing current fleet overview.
"""

import streamlit as st
import pandas as pd

from orders.dataManager import DataManager
from utils import functions as F

def markCarUnavailable(container=st):
    """
    Display UI for marking a car as unavailable (maintenance).
    
    Args:
        container: Streamlit container to render the UI in
    """
    #====================================================================================================================
    #----   Load Available Cars and Display Selection   -----------------------------------------------------------------

    cars_df = DataManager('carPool').read()
    available_cars = cars_df[cars_df['Availability'] == 'Available']['CarId'].tolist()
    if available_cars:
        selected_car_to_block = container.selectbox(
            "Select a car to mark as under maintenance:",
            available_cars
        )
        if container.button("❌ Mark Car as Unavailable", use_container_width=True):
            F.mark_car_unavailable(selected_car_to_block)
        
def markCarAvailable(container=st):
    """
    Display UI for marking a car as available (out of maintenance).
    
    Args:
        container: Streamlit container to render the UI in
    """
    #====================================================================================================================
    #----   Load Unavailable Cars and Display Selection   ---------------------------------------------------------------

    cars_df = DataManager('carPool').read()
    available_cars = cars_df[cars_df['Availability'] != 'Available']['CarId'].tolist()
    if available_cars:
        selected_car_to_free = container.selectbox(
            "Select a car to mark as available:",
            available_cars
        )
        if container.button("✅ Mark as Available", use_container_width=True):
            F.mark_car_available(selected_car_to_free)

def show_fleetStatus(container=st):
    """
    Display the complete fleet status overview with maintenance and rental information.
    
    Args:
        container: Streamlit container to render the UI in
    """
    #====================================================================================================================
    #----   Display Fleet Management Controls   --------------------------------------------------------------------------

    container.subheader("Fleet Status")

    col1, col2 = container.columns(2)
    with col1:
        st.markdown("### Mark Car Unavailable")
        markCarUnavailable(container=col1)
    with col2:
        st.markdown("### Mark Car Available")
        markCarAvailable(container=col2)
            
    #====================================================================================================================
    #----   Build Fleet Status Data from Current Plan   -----------------------------------------------------------------

    cars_dm = DataManager('carPool')
    cars_df = cars_dm.read()
            
    car_to_order = {}
    if st.session_state['order_plan'] is not None:
        for order_id, assignment in st.session_state['order_plan'].items():
            car_id = assignment['car_id']
            car_to_order[car_id] = {
                'order_number': order_id,
                'start_date': assignment['start_date']
            }
            
    #====================================================================================================================
    #----   Create Fleet Status Records   -------------------------------------------------------------------------------

    fleet_data = []
    for _, car in cars_df.iterrows():
        car_id = car['CarId']
        if car['Availability'] != 'Available':
            availability = '❌ Maintenance'
            order_number = ''
            rental_start = ''
        elif car_id in car_to_order:
            availability = '🟡 Ordered'
            order_number = car_to_order[car_id]['order_number']
            rental_start = car_to_order[car_id]['start_date']
        else:
            availability = '🟢 Available'
            order_number = ''
            rental_start = ''
        
        fleet_data.append({
            'Car Id': car_id,
            'Car Make': car['Manufacturer'],
            'Car Model': car['Model'],
            'Availability': availability,
            'Location': car['Location'],
            'Order Number': order_number,
            'Rental Start Date': rental_start
        })
    
    #====================================================================================================================
    #----   Sort and Display Fleet Status Table   -----------------------------------------------------------------------

    fleet_df = pd.DataFrame(fleet_data)
    
    availability_map = {'❌ Maintenance': 0, '🟡 Ordered': 1, '🟢 Available': 2}
    fleet_df['availability_sort'] = fleet_df['Availability'].map(availability_map)
    
    fleet_df['rental_sort'] = fleet_df['Rental Start Date'].replace('', '9999-99-99')
    
    fleet_df = fleet_df.sort_values(['availability_sort', 'rental_sort', 'Order Number']).drop(['availability_sort', 'rental_sort'], axis=1)
    
    st.session_state['style-sheet'].LabelElement('light_table-no_header', container=container)
    container.table(
        fleet_df
    )