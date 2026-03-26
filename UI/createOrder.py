import streamlit as st
import pandas as pd
import re
import random
from datetime import datetime as dt, timedelta
from orders.dataManager import DataManager

AVAILABLE_OPTIONS = {
    'Manufacturer': ['Toyota', 'Fiat', 'Ford', 'Volkswagen', 'Tesla', 'Jeep', 'Mercedes', 'Hyundai', 'Kia', 'BMW', 'Nissan', 'Volvo', 'Chevrolet', 'Land Rover', 'Audi'],
    'Condition': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
    'Seats': ['2', '4', '5', '6', '7'],
    'BootSpace': [300, 400, 450, 500, 550, 600, 650, 700, 800],
    'GearType': ['Manual', 'Auto'],
    'FuelType': ['Petrol', 'Diesel', 'Hybrid', 'Electric'],
    'Category': ['Economy', 'Sedan', 'SUV', 'Hatchback', 'Luxury', 'Premium', 'Crossover', 'Coupe', '4x4', 'Compact', 'Luxury SUV'],
    # Add more attributes as needed
}


def generate_random_order_data():
    """Generate random customer and preference data for an order."""
    # Random customer details
    first_names = ['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    
    driving_license_no = f"{random.choice(['ABC', 'DEF', 'GHI'])}{random.randint(100000, 999999)}"
    driving_license_country = random.choice(['United Kingdom', 'USA', 'Spain', 'France', 'Germany', 'Japan', 'Nigeria', 'Italy', 'Australia'])
    
    locations = ['Heathrow Airport', 'Gatwick Airport', 'Manchester Airport', 'Birmingham City Centre', 'Heathrow Airport (Relocated)', 'Gatwick Airport (Relocated)']
    pickup_location = random.choice(locations)
    dropoff_location = random.choice(locations)
    
    # Random dates: pickup in next 1-30 days, dropoff 1-7 days after
    pickup_days = random.randint(1, 30)
    dropoff_extra = random.randint(1, 7)
    pickup_date = dt.now() + timedelta(days=pickup_days)
    dropoff_date = pickup_date + timedelta(days=dropoff_extra)
    expected_pickup = pickup_date.strftime('%d/%m/%Y %H:%M')
    expected_dropoff = dropoff_date.strftime('%d/%m/%Y %H:%M')
    
    order_revenue = round(random.uniform(50.0, 1500.0), 2)
    
    # Random preferences: choose 1-5 random preferences
    num_prefs = random.randint(1, 5)
    selected_prefs = random.sample(list(AVAILABLE_OPTIONS.keys()), num_prefs)
    
    preferences = {}
    for pref in selected_prefs:
        preferences[pref] = random.choice(AVAILABLE_OPTIONS[pref])
    
    # Random hard/soft for each
    hard_prefs = {pref: random.choice([True, False]) for pref in selected_prefs}
    
    return {
        'customer_name': customer_name,
        'driving_license_no': driving_license_no,
        'driving_license_country': driving_license_country,
        'pickup_location': pickup_location,
        'dropoff_location': dropoff_location,
        'expected_pickup': expected_pickup,
        'expected_dropoff': expected_dropoff,
        'order_revenue': order_revenue,
        'preferences': preferences,
        'hard_prefs': hard_prefs
    }


def create_order_from_data(order_data):
    """Create an order from the provided data dict."""
    # Generate order number atomically
    order_dm = DataManager('openOrders')
    open_orders_df = order_dm.read()
    next_order = _next_order_number() if open_orders_df is not None else 'ORD-1000'

    # re-read and adjust for race condition
    open_orders_df = order_dm.read()
    if not open_orders_df.empty:
        existing_ids = set(open_orders_df['OrderNumber'].astype(str))
        while next_order in existing_ids:
            next_order = _next_order_number()
            open_orders_df = order_dm.read()
            existing_ids = set(open_orders_df['OrderNumber'].astype(str))

    # Append open order row
    order_row = {
        'OrderNumber': next_order,
        'CustomerFullName': order_data['customer_name'],
        'DrivingLicenseNo': order_data['driving_license_no'],
        'DrivingLicenseCountry': order_data['driving_license_country'],
        'PickUpLocation': order_data['pickup_location'],
        'DropOffLocation': order_data['dropoff_location'],
        'ExpectedPickUpTime': order_data['expected_pickup'],
        'ExpectedDropOffTime': order_data['expected_dropoff'],
        'OrderRevenue': order_data['order_revenue'],
        'Status': 'Pending'
    }
    order_dm.writeSingleLine(order_row)

    # Append preferences rows
    prefs_dm = DataManager('orderPreferences')
    pref_id_base = _next_preference_id()
    pref_next_num = int(re.search(r'(\d+)', pref_id_base).group(1))

    for pref_key, pref_value in order_data['preferences'].items():
        pref_category = 'Hard' if order_data['hard_prefs'][pref_key] else 'Soft'
        pref_row = {
            'PreferenceId': f'P{pref_next_num}',
            'OrderNumber': next_order,
            'PreferenceType': pref_key,
            'PreferenceCategory': pref_category,
            'PreferenceValue': str(pref_value)
        }
        prefs_dm.writeSingleLine(pref_row)
        pref_next_num += 1

    # Refresh session state plan
    if 'order_manager' in st.session_state:
        st.session_state['order_plan'] = st.session_state['order_manager'].produceOptimalAllocation()


def _next_order_number():
    dm = DataManager('openOrders')
    orders_df = dm.read()
    if orders_df.empty:
        return 'ORD-1000'

    highest = 0
    for value in orders_df['OrderNumber'].astype(str):
        m = re.search(r'(\d+)', value)
        if m:
            highest = max(highest, int(m.group(1)))
    return f'ORD-{highest + 1}'


def _next_preference_id():
    dm = DataManager('orderPreferences')
    prefs_df = dm.read()
    if prefs_df.empty:
        return 'P100'

    highest = 0
    for value in prefs_df['PreferenceId'].astype(str):
        m = re.search(r'(\d+)', value)
        if m:
            highest = max(highest, int(m.group(1)))
    return f'P{highest + 1}'


def show_createOrderForm(container=st):
    """Display a create-order form and append to openOrders + orderPreferences."""
    container.header('Create New Order')

    # Button to generate random order
    if container.button('Generate Random Order'):
        random_data = generate_random_order_data()
        st.session_state['random_order_data'] = random_data
        st.rerun()

    # If random data exists, display it and provide submit button
    if 'random_order_data' in st.session_state:
        random_data = st.session_state['random_order_data']
        container.subheader('Generated Random Order Details')
        container.write(f"**Customer Name:** {random_data['customer_name']}")
        container.write(f"**Driving License No:** {random_data['driving_license_no']}")
        container.write(f"**Driving License Country:** {random_data['driving_license_country']}")
        container.write(f"**PickUp Location:** {random_data['pickup_location']}")
        container.write(f"**DropOff Location:** {random_data['dropoff_location']}")
        container.write(f"**Expected PickUp Time:** {random_data['expected_pickup']}")
        container.write(f"**Expected DropOff Time:** {random_data['expected_dropoff']}")
        container.write(f"**Order Revenue:** {random_data['order_revenue']}")
        container.write(f"**Preferences:** {len(random_data['preferences'])}")
        for pref, value in random_data['preferences'].items():
            hard = "Hard" if random_data['hard_prefs'][pref] else "Soft"
            container.write(f"- {pref}: {value} ({hard})")

        if container.button('Submit This Random Order'):
            # Use the random data to create the order
            create_order_from_data(random_data)
            del st.session_state['random_order_data']
            container.success('Random order created successfully!')
            st.rerun()

        container.markdown('---')

    col_a, col_b = container.columns(2)
    with col_a:
        customer_first_name = st.text_input('Customer First Name')
        driving_license_no = st.text_input('Driving License Number')
        dropoff_location = st.selectbox('DropOff Location', ['Heathrow Airport', 'Gatwick Airport', 'Manchester Airport', 'Birmingham City Centre', 'Heathrow Airport (Relocated)', 'Gatwick Airport (Relocated)'])
        expected_pickup = st.text_input('Expected PickUp Time (dd/mm/yyyy HH:MM)', value=dt.now().strftime('%d/%m/%Y %H:%M'))
        order_revenue = st.number_input('Maximum Daily Price', min_value=0.0, step=5.0, format='%.2f')
        
    with col_b:
        customer_last_name = st.text_input('Customer Last Name')
        driving_license_country = st.text_input('Driving License Country')
        pickup_location = st.selectbox('PickUp Location', ['Heathrow Airport', 'Gatwick Airport', 'Manchester Airport', 'Birmingham City Centre', 'Heathrow Airport (Relocated)', 'Gatwick Airport (Relocated)'])
        expected_dropoff = st.text_input('Expected DropOff Time (dd/mm/yyyy HH:MM)', value=(dt.now() + pd.Timedelta(days=1)).strftime('%d/%m/%Y %H:%M'))

    customer_name = f"{customer_first_name} {customer_last_name}".strip()

    status = 'Pending'

    container.markdown('---')
    container.subheader('Car Attribute Preferences (hard/soft)')

    # Define preference list to capture from carPool.csv-like columns
    preference_fields = [
        ('Manufacturer', AVAILABLE_OPTIONS['Manufacturer']),
        ('Condition', AVAILABLE_OPTIONS['Condition']),
        ('Seats', AVAILABLE_OPTIONS['Seats']),
        ('BootSpace', AVAILABLE_OPTIONS['BootSpace']),
        ('GearType', AVAILABLE_OPTIONS['GearType']),
        ('FuelType', AVAILABLE_OPTIONS['FuelType']),
        ('Category', AVAILABLE_OPTIONS['Category'])
    ]

    preference_values = {}
    preference_hard = {}

    # Show preferences in two columns
    left_col, right_col = container.columns(2)

    for idx, (pref_key, options) in enumerate(preference_fields):
        parent_col = left_col if idx % 2 == 0 else right_col
        with parent_col:
            if options is None:
                selected_value = container.text_input(f'{pref_key}', value='', key=f'pref_{pref_key}')
            else:
                selected_value = container.selectbox(f'{pref_key}', [''] + options, key=f'pref_{pref_key}')

            preference_values[pref_key] = selected_value
            preference_hard[pref_key] = container.checkbox('Hard', value=False, key=f'prefreq_{pref_key}')

    if container.button('Create Order'):
        if not customer_name or not driving_license_no or not pickup_location or not dropoff_location or not expected_pickup or not expected_dropoff:
            container.error('Please fill required order fields before submitting.')
            return

        # Validate dates
        try:
            dt.strptime(expected_pickup, '%d/%m/%Y %H:%M')
            dt.strptime(expected_dropoff, '%d/%m/%Y %H:%M')
        except ValueError:
            container.error('Dates must follow dd/mm/yyyy HH:MM format.')
            return

        # Generate order number atomically from latest snapshot
        order_dm = DataManager('openOrders')
        open_orders_df = order_dm.read()
        next_order = _next_order_number() if open_orders_df is not None else 'ORD-1000'

        # re-read and adjust for race condition to avoid duplicates
        open_orders_df = order_dm.read()
        if not open_orders_df.empty:
            existing_ids = set(open_orders_df['OrderNumber'].astype(str))
            while next_order in existing_ids:
                next_order = _next_order_number()
                open_orders_df = order_dm.read()
                existing_ids = set(open_orders_df['OrderNumber'].astype(str))

        # Append open order row
        order_row = {
            'OrderNumber': next_order,
            'CustomerFullName': customer_name,
            'DrivingLicenseNo': driving_license_no,
            'DrivingLicenseCountry': driving_license_country,
            'PickUpLocation': pickup_location,
            'DropOffLocation': dropoff_location,
            'ExpectedPickUpTime': expected_pickup,
            'ExpectedDropOffTime': expected_dropoff,
            'OrderRevenue': order_revenue,
            'Status': status
        }
        order_dm.writeSingleLine(order_row)

        # Append preferences rows
        prefs_dm = DataManager('orderPreferences')
        pref_id_base = _next_preference_id()
        pref_next_num = int(re.search(r'(\d+)', pref_id_base).group(1))

        for pref_key, pref_value in preference_values.items():
            if pref_value is None or pref_value == '':
                continue

            pref_category = 'Hard' if preference_hard.get(pref_key, False) else 'Soft'
            pref_row = {
                'PreferenceId': f'P{pref_next_num}',
                'OrderNumber': next_order,
                'PreferenceType': pref_key,
                'PreferenceCategory': pref_category,
                'PreferenceValue': pref_value
            }
            prefs_dm.writeSingleLine(pref_row)
            pref_next_num += 1

        container.success(f'Order {next_order} created successfully')

        # Refresh session state plan and rerun so UI updates
        if 'order_manager' in st.session_state:
            st.session_state['order_plan'] = st.session_state['order_manager'].produceOptimalAllocation()
        st.rerun()