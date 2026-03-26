"""
Rental Allocation Algorithms

Contains functions for solving the car rental allocation problem,
including optimal assignment of cars to orders and checking new order feasibility.
"""

from collections import Counter

def SolveRentalAllocation(orders):
    """
    Solve the optimal car rental allocation problem using backtracking.

    Uses a demand-based heuristic to prioritize cars with lower demand first,
    then backtracks to find a conflict-free assignment.

    Args:
        orders (list): List of order dicts with 'id', 'potential' cars, and 'dates'

    Returns:
        dict: Allocation mapping {order_id: {'car_id': car_id, 'start_date': date, 'end_date': date}}
              or None if no feasible allocation exists
    """
    #====================================================================================================================
    #----   Sort Orders by Duration (Longest First)   -------------------------------------------------------------------

    sorted_orders = sorted(orders, key=lambda x: len(x['dates']), reverse=True)
    
    attempts = 0
    max_attempts = 3

    def get_demand_scores(remaining_orders, dates):
        """
        Calculate demand scores for cars based on remaining orders.

        Args:
            remaining_orders (list): Orders still to be assigned
            dates (list): Date range for current order

        Returns:
            Counter: Demand count for each car
        """
        # Calculate how many times each car is requested across the specific dates
        demand = Counter()
        for order in remaining_orders:
            # Only count overlap with the current booking period
            if any(d in dates for d in order['dates']):
                for car in order['potential']:
                    demand[car] += 1
        return demand

    def backtrack(order_idx, current_assignments):
        """
        Recursive backtracking function to find valid car assignments.

        Args:
            order_idx (int): Current order index to assign
            current_assignments (dict): Current partial assignments

        Returns:
            dict: Complete assignments if successful, None otherwise
        """
        nonlocal attempts
        
        # Success: All orders assigned
        if order_idx == len(sorted_orders):
            return current_assignments

        order = sorted_orders[order_idx]
        
        # Calculate demand for cars available to THIS order
        demand_scores = get_demand_scores(sorted_orders[order_idx:], order['dates'])
        
        # Sort potential cars: Least in demand first (Algorithm Step A)
        # We only consider cars still in the 'potential' list for this order
        sorted_potential = sorted(
            order['potential'], 
            key=lambda c: demand_scores.get(c, 0)
        )

        for car in sorted_potential:
            # Check if car is already taken on these specific dates
            conflict = False
            for prev_car, prev_dates in current_assignments.values():
                if car == prev_car and any(d in order['dates'] for d in prev_dates):
                    conflict = True
                    break
            
            if not conflict:
                # Assign car (Algorithm Step B: Implicitly removed by 'conflict' check in next recursion)
                new_assignments = current_assignments.copy()
                new_assignments[order['id']] = (car, order['dates'])
                
                result = backtrack(order_idx + 1, new_assignments)
                if result:
                    return result

        # If we exit the loop, this branch failed (Algorithm Step C)
        attempts += 1
        if attempts >= max_attempts:
            return None
        
        return None

    #====================================================================================================================
    #----   Execute Backtracking Algorithm   ----------------------------------------------------------------------------

    final_result = backtrack(0, {})
    
    if final_result:
        # Format output to include order_id: car_assigned with start and end dates
        formatted_result = {}
        for order_id, (car, dates) in final_result.items():
            formatted_result[order_id] = {
                'car_id': car,
                'start_date': dates[0],
                'end_date': dates[-1]
            }
        return formatted_result
    return None


def checkNewOrderSolveable(plan, newOrder):
    """
    Checks if a new order can be added to an existing plan and adds it if possible.
    
    Args:
        plan: Dict where each order is mapped to assignment details:
              {order_id: {'car_id': car_id, 'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}, ...}
        new_order: Dict with 'id', 'potential' (list of car_ids), and 'dates' (list of date strings.
                   Start date is dates[0], end date is dates[-1])
    
    Returns:
        tuple: (success: bool, updated_plan: dict)
               - If successful: (True, updated_plan with new order assigned)
               - If failed: (False, original plan unchanged)
    """
    #====================================================================================================================
    #----   Extract Date Range from New Order   --------------------------------------------------------------------------

    if not newOrder['dates'] or len(newOrder['dates']) == 0:
        return (False, plan)
    
    new_start_date = newOrder['dates'][0]
    new_end_date = newOrder['dates'][-1]
    
    #====================================================================================================================
    #----   Build Car Booking Map from Existing Plan   ------------------------------------------------------------------

    car_date_bookings = {}  # Map car_id -> list of (start_date, end_date) tuples
    
    for order_id, assignment in plan.items():
        car_id = assignment['car_id']
        start_date = assignment['start_date']
        end_date = assignment['end_date']
        
        if car_id not in car_date_bookings:
            car_date_bookings[car_id] = []
        car_date_bookings[car_id].append((start_date, end_date))
    
    #====================================================================================================================
    #----   Try to Find Available Car Without Conflicts   ---------------------------------------------------------------

    for candidate_car in newOrder['potential']:
        # Check if this car has date conflicts
        has_conflict = False
        
        if candidate_car in car_date_bookings:
            # Check overlap with each booking for this car
            for booked_start, booked_end in car_date_bookings[candidate_car]:
                # Check if there's any overlap between [new_start, new_end] and [booked_start, booked_end]
                if new_start_date <= booked_end and new_end_date >= booked_start:
                    has_conflict = True
                    break
        
        if not has_conflict:
            # Successfully found an available car with no conflicts
            updated_plan = plan.copy()
            updated_plan[newOrder['id']] = {
                'car_id': candidate_car,
                'start_date': new_start_date,
                'end_date': new_end_date
            }
            return (True, updated_plan)
    
    # No available car found that doesn't conflict
    return (False, plan)