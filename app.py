"""
Car Hire For You - Main Streamlit Application

This application provides a comprehensive car rental management system with order management,
fleet status tracking, and order creation capabilities.

Features:
- Order Management: View and manage existing rental orders
- Fleet Status: Monitor car availability and maintenance
- Create New Orders: Add new rental requests with preferences
- Automatic allocation: Optimize car assignments to orders

Dependencies:
- Streamlit for web interface
- Pandas for data manipulation
- Custom modules: orders, utils, UI, CSS
"""

import streamlit as st

from orders.orderManager import OrderManager

from utils import functions as F
from UI.orderManagemntPage import show_orderDetails, show_orderManagementHeader, show_upcomingOrders
from UI.fleetStatus import show_fleetStatus
from UI.createOrder import show_createOrderForm

from CSS.style import StyleConfig

#====================================================================================================================
#----   Application Initialization   ---------------------------------------------------------------------------------

if 'init' not in st.session_state.keys():
    st.session_state['init'] = True
    st.session_state['order_manager'] = OrderManager()
    st.session_state['order_plan'] = st.session_state['order_manager'].produceOptimalAllocation()
    st.session_state['style-sheet'] = StyleConfig( styleConfigPath = 'wheelDeal-style.toml' )
    st.session_state['selected_order'] = None

st.session_state['style-sheet'].AddStyleSheet()

#====================================================================================================================
#----   Page Configuration   ----------------------------------------------------------------------------------------

st.set_page_config(page_title="Car Hire For You", layout="wide")

#====================================================================================================================
#----   UI Setup   --------------------------------------------------------------------------------------------------

st.title("🚗 Wheel Deal!")
st.markdown("---")

# Create sidebar navigation
page = st.sidebar.radio("Navigation", ["Order Management", "Create New Order"])

#====================================================================================================================
#----   PAGE 1: ORDER MANAGEMENT   -----------------------------------------------------------------------------------

if page == "Order Management":

    show_orderManagementHeader()

    if st.session_state['selected_order'] is not None and st.session_state['order_plan'] is not None:
        if st.session_state['selected_order'] not in st.session_state['order_plan']:
            st.warning(f"No car allocated for Order {st.session_state['selected_order']}")
        else:
            show_orderDetails()
            
            # Fleet Status Section
            st.markdown("---")
            fleetStatus = st.expander("🚘 Fleet Status & Management", expanded=False)
            show_fleetStatus( container=fleetStatus )

            # Upcoming Orders Section
            st.markdown("---")
            upcomingOrders = st.expander("📅 Upcoming Orders", expanded=False)
            show_upcomingOrders(container=upcomingOrders)
            
    else:
        if st.session_state['order_plan'] is None:
            st.warning("No allocation plan available. Please generate one first.")
        else:
            st.info("Select an order to view details and manage allocations.")

#====================================================================================================================
#----   PAGE 2: CREATE NEW ORDER   -----------------------------------------------------------------------------------

elif page == "Create New Order":
    show_createOrderForm()
