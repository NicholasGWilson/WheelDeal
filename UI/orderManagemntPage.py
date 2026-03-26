"""
Order management UI module for the CarPool rental system.

This module provides functions for displaying order management controls,
order details, and upcoming orders in the rental system.
"""

import streamlit as st
import pandas as pd
from datetime import datetime as dt
from orders.dataManager import DataManager
from utils import functions as F

def show_orderManagementHeader(container=st):
    """
    Display order management header with order selection and reset button.
    
    Args:
        container: Streamlit container to render the UI in
    """
    #====================================================================================================================
    #----   Display Header and Load Order List   -----------------------------------------------------------------------

    st.header("Order Management")
    
    order_manager = st.session_state['order_manager']
    order_ids = order_manager.getOrderIDs()
    
    #====================================================================================================================
    #----   Display Order Selection and Reset Control   ----------------------------------------------------------------

    col1, col2, col3 = container.columns([4, 1, 1])
    with col1:
        #container.write("Select an order to view details and manage the assignment.")
        st.session_state['selected_order'] = container.selectbox(
            label="",
            options=order_ids,
            key="selected_order_input",
            label_visibility="collapsed"
        )

    with col2:
        orders_dm = DataManager('openOrders')
        orders_df = orders_dm.read()
        selected_order = st.session_state.get('selected_order')

        if selected_order is not None and selected_order in orders_df['OrderNumber'].astype(str).values:
            row = orders_df[orders_df['OrderNumber'] == selected_order].iloc[0]
            current_upgrade = str(row.get('Upgrade', 'FALSE')).upper() == 'TRUE'
            button_text = 'Downgrade' if current_upgrade else 'Upgrade'

            if container.button(button_text, use_container_width=True, type='secondary'):
                if current_upgrade:
                    F.set_order_upgrade(selected_order, False)
                else:
                    F.set_order_upgrade(selected_order, True)

                st.session_state['order_plan'] = st.session_state['order_manager'].produceOptimalAllocation()
                st.rerun()
        else:
            container.info('Select an order to enable upgrade/downgrade')
    
    with col3:
        if container.button("🔄 Reset", use_container_width=True):
            F.reset_allocation()

def show_orderDetails(container=st):
    """
    Display detailed information for the selected order and assigned car.
    
    Displays driver details, order details, and car assignment information in separate sections.
    
    Args:
        container: Streamlit container to render the UI in
    """
    #====================================================================================================================
    #----   Retrieve Order and Assignment Information   ----------------------------------------------------------------

    selected_order = st.session_state['selected_order']
    assigned_car_id = st.session_state['order_plan'][selected_order]['car_id']
    order_details = st.session_state['order_manager'].getOrderDetails(selected_order, assigned_car_id)

    st.session_state['assigned_car_id'] = assigned_car_id
    st.session_state['order_details'] = order_details

    #====================================================================================================================
    #----   Display Driver Details   ------------------------------------------------------------------------------------

    container.subheader("Driver Details")
    container.table(order_details.iloc[:, :4])

    #====================================================================================================================
    #----   Display Order Details   -------------------------------------------------------------------------------------

    container.subheader("Order Details")
    container.table(order_details.iloc[:, 4:9])

    #====================================================================================================================
    #----   Display Assigned Car Details   ------------------------------------------------------------------------------

    container.subheader("Assigned Car Details")
    container.table(order_details.iloc[:, 9:])

    #====================================================================================================================
    #----   Display Customer Preferences   -------------------------------------------------------------------------------

    prefs_dm = DataManager('orderPreferences')
    prefs_df = prefs_dm.read()
    
    order_prefs = prefs_df[prefs_df['OrderNumber'] == selected_order][['PreferenceType', 'PreferenceCategory', 'PreferenceValue']]
    
    if not order_prefs.empty:
        container.subheader("Customer Preferences")
        st.session_state['style-sheet'].LabelElement('light_table-no_header', container=container)
        container.table(order_prefs)
    else:
        container.info("No preferences specified for this order")


def show_upcomingOrders(container=st):
    """
    Display upcoming orders with status, sorted by start date.
    
    Args:
        container: Streamlit container to render the UI in
    """
    #====================================================================================================================
    #----   Load and Parse Order Data   ---------------------------------------------------------------------------------

    orders_dm = DataManager('openOrders')
    orders_df = orders_dm.read()

    orders_df['ExpectedPickUpTime_parsed'] = pd.to_datetime(
        orders_df['ExpectedPickUpTime'], format='%d/%m/%Y %H:%M', errors='coerce'
    )

    today = dt.now()
    upcoming = orders_df[orders_df['ExpectedPickUpTime_parsed'] >= today].copy()

    if upcoming.empty:
        container.info('No upcoming orders found.')
        return

    #====================================================================================================================
    #----   Build Car Assignment Mapping   ------------------------------------------------------------------------------

    assigned_cars = {}
    if st.session_state['order_plan'] is not None:
        for order_id, assignment in st.session_state['order_plan'].items():
            assigned_cars[order_id] = assignment['car_id']

    #====================================================================================================================
    #----   Format and Display Upcoming Orders Table   ------------------------------------------------------------------

    upcoming = upcoming.assign(
        **{
            'Order number': upcoming['OrderNumber'],
            'Status': upcoming['Status'],
            'Location': upcoming['PickUpLocation'],
            'Start date': upcoming['ExpectedPickUpTime'],
            'End date': upcoming['ExpectedDropOffTime'],
            'Assigned car': upcoming['OrderNumber'].map(lambda oid: assigned_cars.get(oid, ''))
        }
    )

    upcoming = upcoming.sort_values('ExpectedPickUpTime_parsed')

    container.subheader('Upcoming Orders')
    st.session_state['style-sheet'].LabelElement('light_table-no_header', container=container)
    container.table(upcoming[['Order number', 'Status', 'Location', 'Start date', 'End date', 'Assigned car']])

    # Build result columns
    upcoming = upcoming.assign(
        **{
            'Order number': upcoming['OrderNumber'],
            'Status': upcoming['Status'],
            'Location': upcoming['PickUpLocation'],
            'Start date': upcoming['ExpectedPickUpTime'],
            'End date': upcoming['ExpectedDropOffTime'],
            'Assigned car': upcoming['OrderNumber'].map(lambda oid: assigned_cars.get(oid, ''))
        }
    )

    upcoming = upcoming.sort_values('ExpectedPickUpTime_parsed')

    container.subheader('Upcoming Orders')
    st.session_state['style-sheet'].LabelElement( 'light_table-no_header', container=container )
    container.table(upcoming[['Order number', 'Status', 'Location', 'Start date', 'End date', 'Assigned car']])
