"""
Data Management Utilities

Provides a unified interface for reading and writing CSV data files
used throughout the car rental management system.
"""

import pandas as pd
import os

class DataManager():
    """
    Manages CSV data files for the car rental system.

    Handles reading and writing operations for various data sources
    including orders, cars, and preferences.

    Attributes:
        data_source (str): Name of the data source (e.g., 'openOrders', 'carPool')
        file_path (str): Full path to the CSV file
    """

    def __init__(self, dataSource):
        """
        Initialize DataManager for a specific data source.

        Args:
            dataSource (str): Name of the data source file (without .csv extension)
        """
        self.data_source = dataSource
        self.__file_location = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.file_path = os.path.join(self.__file_location, f'CarAvailability/{self.data_source}.csv')

    def read(self):
        """
        Read the CSV file and return as a pandas DataFrame.

        Returns:
            pd.DataFrame: Data from the CSV file
        """
        df = pd.read_csv(  self.file_path, header=0)
        return df
    
    def writeSingleLine(self, data: dict):
        """
        Append a single row of data to the CSV file.

        Args:
            data (dict): Dictionary with column names as keys and values to write
        """
        df = self.read()
        new_row = {col: data.get(col, None) for col in df.columns}
        new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        new_df.to_csv(self.file_path, index=False)

    def writeMultipleLines(self, data:pd.DataFrame, mode: str = 'append'):
        """
        Write multiple rows to the CSV file.

        Args:
            data (pd.DataFrame): DataFrame containing rows to write
            mode (str): 'append' to add to existing data, 'overwrite' to replace
        """
        df = self.read()
        
        if mode == 'append':
            result_df = pd.concat([df, data], ignore_index=True)
        else:  # mode == 'overwrite'
            result_df = data
        
        # Write the result to the CSV file
        result_df.to_csv(self.file_path, index=False)