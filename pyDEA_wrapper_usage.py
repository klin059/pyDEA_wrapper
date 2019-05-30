# -*- coding: utf-8 -*-
"""
Created on Thu May 30 21:31:22 2019

@author: KML
"""
import os
import pandas as pd
import pyDEA_wrapper as dea

df = pd.read_csv(r"data\DEA_example_data.csv")
df.set_index('Unnamed: 0', inplace = True)
#df.drop(columns = 'Unnamed: 0', inplace = True)

# specify DEA parameters
DEA_inputs = ['I1','I2','I3']
DEA_outputs = ['O1', 'O2']
# pop category variable 
category_var = df.pop('category')

directory = os.getcwd()
parameter_dict = {
    # note that the dea object will create a copy of the data file from the dataframe    
    "DATA_FILE":directory + r"\output\DEA_created_data.csv",  
    'OUTPUT_FILE':directory + r"\output\DEA_example_data_solution.xlsx",
    "OUTPUT_CATEGORIES": ';'.join(DEA_outputs),
    "INPUT_CATEGORIES": ';'.join(DEA_inputs),
    "DEA_FORM": "env",
    "ORIENTATION": "input",
    "RETURN_TO_SCALE": "VRS",
    'ABS_WEIGHT_RESTRICTIONS':'I1 >= 0.014',
    'VIRTUAL_WEIGHT_RESTRICTIONS':'I2 >= 0.2;I2<= 0.4',
    'PRICE_RATIO_RESTRICTIONS':'I1/O1>= 1'
        }

dea1 = dea.DEAModel(df, parameter_dict, description = 'test problem', efficiency_only=False)
dea1.run_dea()

# get the solutions
dea1.efficiency_df
dea1.peers_df
dea1.InputOutputWeights_df 
dea1.WeightedData_df

# get target of a particular dmu
dea1.get_target_dictionary('A')
# get target for all dmu - time consuming because it loops throught the excel file cell by cell
dea1.get_target_dictionary()

# print the object shows the parameters used and the model description
print(dea1)

# get statistics of efficiency scores
dea1.get_efficiency_stats()

# view efficiency score by category
dea1.get_mean_efficiency_by_category(category_var)

# save the dea object into a pickle file
dea1.save('output\\dea1.pkl')
# load the dea object into another variable name (dea_test)
dea_test = dea.DEAModel.load_dea('output\\dea1.pkl')

print(dea_test)

# all the data and the parameters are saved in the object file for reproducibility
dea_test.df
dea_test.parameter_dict

# change the parameters 
dea_test.parameter_dict['VIRTUAL_WEIGHT_RESTRICTIONS'] = 'I2 >= 0.1;I2<= 0.3'

dea_test.run_dea()

