"""
Car similarity calculation module for the CarPool rental system.

This module provides functions to calculate similarity scores between car requirements
and available car options, as well as recommendation scores for car assignments.
"""

import numpy as np

SIMILARITY_WEIGHTS = {'Manufacturer': 10, 'Condition': 5, 'Seats': 20, 'BootSpace': 15, 'GearType': 20, 'FuelType': 0, 'Category': 20, 'ComfortRating': 20, 'SpeedRating': 5, 'OffRoadRating': 5, 'FuelUseRating': 10}
QUALITY_WEIGHTS = {'Manufacturer': 0, 'Condition': 20, 'Seats': 5, 'BootSpace': 15, 'GearType': 0, 'FuelType': 0, 'Category': 20, 'ComfortRating': 20, 'SpeedRating': 10, 'OffRoadRating': 10, 'FuelUseRating': 10}
UPGRADE_WEIGHTS =  (0.7, 0.2, 0.1)
STANDARD_WEIGHTS = (0.45, 0.45, 0.1)


def CarSimilarity(requirments: dict, optionCar: dict, hardConditions: list, dailyRevenue: float, miniumumMargin=0.2):
    """
    Calculates similarity and quality scores between car requirements and an available car option.
    
    Args:
        requirments (dict): Dictionary of required car attributes (e.g., {'Seats': 5, 'Category': 'SUV'})
        optionCar (dict): Dictionary of available car attributes
        hardConditions (list): List of attribute names that must be met exactly or as minimum thresholds
        dailyRevenue (float): Daily revenue rate for the rental
        miniumumMargin (float, optional): Minimum profit margin required (default 0.2)
    
    Returns:
        dict: Result containing:
            - 'similarity_score': Float between 0-1 indicating how well the car matches requirements
            - 'quality_score': Float indicating quality upgrade/downgrade
            - 'breaks_hard_condition': Boolean indicating if hard conditions are violated
            - 'missing_conditions': List of violated hard conditions
    """
    #====================================================================================================================
    #----   Handle Special Case: Exact Car ID Match   -------------------------------------------------------------------

    if requirments.get('CarId') == optionCar['CarId']:
        return {'similarity_score': 1, 'quality_score': 0, 'breaks_hard_condition': False, 'missing_conditions': []}
    elif 'CarId' in requirments:
        del requirments['CarId']
    
    #====================================================================================================================
    #----   Calculate Attribute Differences and Weights   --------------------------------------------------------------

    similarity_weights = []
    quality_weights = []
    differences = []
    
    for attr in requirments.keys():
        if attr in optionCar.keys():
            similarity_weights.append(SIMILARITY_WEIGHTS[attr])
            quality_weights.append(QUALITY_WEIGHTS[attr])

            if (type(requirments[attr]) == float or attr in ('BootSpace')) and requirments[attr] != 0:
                differences.append( min(max( 
                    (float(optionCar[attr]) - float(requirments[attr])) / float(requirments[attr]), 
                1),-1) )
            elif attr == 'Seats':
                 differences.append((int(optionCar[attr]) - int(requirments[attr])) / 7)
            elif type(requirments[attr]) in [int]: # Assuming numerical attributes are on a 0-10 scale
                differences.append(int(optionCar[attr]) - int(requirments[attr]) /10 )
            elif type(requirments[attr]) == str:
                differences.append(0 if optionCar[attr] == requirments[attr] else 1)
            else :
                differences.append(0)

    similarity_weights = np.array(similarity_weights)
    quality_weights = np.array(quality_weights)
    differences = np.array(differences)

    similarity_score = np.sum((1-abs(differences)) * similarity_weights) / np.sum(similarity_weights)
    quality_score = np.sum(differences * quality_weights) / np.sum(quality_weights)

    #====================================================================================================================
    #----   Check Hard Conditions and Cost Constraints   ---------------------------------------------------------------

    missing_conditions = []
    for condition in hardConditions:
        if condition in ('seats', 'bootspace', 'comfortrating', 'speedrating', 'offroadrating', 'fueluserating', 'condition'):
            if requirments.get(condition) > optionCar.get(condition):
                missing_conditions.append(condition)
        elif requirments.get(condition) != optionCar.get(condition):
            missing_conditions.append(condition)
    
    if float(optionCar['DailyCost']) > dailyRevenue * (1 - miniumumMargin):
        missing_conditions.append('cost')

    if len(missing_conditions) > 0:
        return {'similarity_score': 0, 'quality_score': 0, 'breaks_hard_condition': True, 'missing_conditions': missing_conditions}
    else:
        return {'similarity_score': similarity_score, 'quality_score': quality_score, 'breaks_hard_condition': False, 'missing_conditions': []}


def RecomendationScore(similarity_score:float, quality_score:float, daily_revenue: float, car_daily_cost: float, miniumumMargin=0.2, giveUpgrade=False):
    """
    Calculates a recommendation score for assigning a car to an order.
    
    Args:
        similarity_score (float): Similarity score from CarSimilarity function
        quality_score (float): Quality score from CarSimilarity function
        daily_revenue (float): Daily revenue rate for the rental
        car_daily_cost (float): Daily cost of the car
        miniumumMargin (float, optional): Minimum profit margin required (default 0.2)
        giveUpgrade (bool, optional): Whether to use upgrade weights instead of standard weights
    
    Returns:
        float: Recommendation score between 0-1, where higher scores indicate better assignments
    """
    #====================================================================================================================
    #----   Check Profit Margin Constraint   ---------------------------------------------------------------------------

    if car_daily_cost > daily_revenue * (1 - miniumumMargin):
        return 0
    
    #====================================================================================================================
    #----   Calculate Weighted Recommendation Score   ------------------------------------------------------------------

    elif giveUpgrade:
        return similarity_score * UPGRADE_WEIGHTS[0] + quality_score * UPGRADE_WEIGHTS[1] + (daily_revenue - car_daily_cost) / daily_revenue * UPGRADE_WEIGHTS[2]
    else:
        return similarity_score * STANDARD_WEIGHTS[0] + quality_score * STANDARD_WEIGHTS[1] + (daily_revenue - car_daily_cost) / daily_revenue * STANDARD_WEIGHTS[2]