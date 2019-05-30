# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 11:50:02 2019

@author: klin059
"""
import pyDEA.main
import pandas as pd
import openpyxl
import pickle

class DEAModel(object):
    def __init__(self, df, parameter_dict, description = None, efficiency_only = True):
        self.efficiency_only = efficiency_only  # control if other solutions (weight, target etc) are recorded
        self.description = description
        self.parameter_dict = parameter_dict
        self.df = df
        self.parameter_filename = None
        self.exist_solution = False
        self.target_dict = {}
    
    def __repr__(self):
        return "DEAModel class for storing data, parameters and solutions of a dea problem instance"
    
    def __str__(self):
        print('********************************************************')
        for key, item in self.parameter_dict.items():
            print('<{}>: {}\n'.format(key, item))
        print('********************************************************')
        return 'Description: {}'.format(self.description)
    
    def run_dea(self):
        # generate the data file
        self.df.to_csv(self.parameter_dict["DATA_FILE"])
        # create parameter file
        self.create_parameter_file('param_RT_DEA.txt')
        
        pyDEA.main.main(self.parameter_filename)
        self.exist_solution = True
        self.get_list_of_solution_df()
    
    def create_parameter_file(self, filename):
        with open(filename, 'w') as f:
            for key, item in self.parameter_dict.items():
                f.write('<{}> {{{}}}\n'.format(key, item))
        self.parameter_filename = filename
        
    def get_list_of_solution_df(self):
        if not self.exist_solution:
            return "Solutions don't exist yet, use run_dea to generate solution"
        soluition_file = self.parameter_dict['OUTPUT_FILE']
        
        
        efficiency_df = pd.read_excel(soluition_file, sheet_name = 'EfficiencyScores', header = 1)
        if self.efficiency_only:
            efficiency_df.index = efficiency_df['DMU']
            efficiency_df.drop(columns = 'DMU', inplace = True)
            self.efficiency_df = efficiency_df
            return
        peers_df = pd.read_excel(soluition_file, sheet_name = 'PeerCount', header = 1)
        InputOutputWeights_df = pd.read_excel(soluition_file, sheet_name = 'InputOutputWeights', header = 1)
        WeightedData_df = pd.read_excel(soluition_file, sheet_name = 'WeightedData', header = 1)
        
        # post processing
        peers_df.drop(index = [0,peers_df.shape[0]-1], inplace = True)
        peers_df.index = peers_df['Efficient Peers']
        peers_df.drop(columns = 'Efficient Peers', inplace = True)
        
        for col in peers_df.columns:
            for ind in peers_df.index:
                if pd.isnull(peers_df.loc[ind, col]) or peers_df.loc[ind, col] == '-':
                    peers_df.loc[ind, col] = 0
                    
        for sol_df in [efficiency_df, InputOutputWeights_df, WeightedData_df]:
            sol_df.index = sol_df['DMU']
            sol_df.drop(columns = 'DMU', inplace = True)
        self.efficiency_df = efficiency_df
        self.peers_df = peers_df
        self.InputOutputWeights_df = InputOutputWeights_df
        self.WeightedData_df = WeightedData_df
        
    def get_individual_target_dictionary(self, dmu):
        book = openpyxl.load_workbook(self.parameter_dict['OUTPUT_FILE'])
        sheet_target = book['Targets']
        dmu_found = False
        for cell in sheet_target['A']:
            if (cell.value is not None):
                if dmu == cell.value:
#                    dmu_cell = cell
#                    current_col = cell.column 
                    current_row = cell.row
                    dmu_found = True
                    break
        if not dmu_found:
            raise Exception('{} not found in the solution file'.format(dmu))
        cont = True
        dea_parameter_dict = {}           
        while cont:
            criterion_name = sheet_target['B' + str(current_row)].value
        #                original_value = sheet_target[cell.column + str(cell.row+2)]
        #                target_value = sheet_target[cell.column + str(cell.row+3)]
        #                Non-radial = sheet_target[cell.column + str(cell.row+4)]
            dea_parameter_dict[criterion_name] = {}
            dea_parameter_dict[criterion_name]['original_value'] = sheet_target['C' + str(current_row)].value
            dea_parameter_dict[criterion_name]['target_value'] = sheet_target['D' + str(current_row)].value
            dea_parameter_dict[criterion_name]['Radial'] = sheet_target['E'+ str(current_row)].value
            dea_parameter_dict[criterion_name]['Non-radial'] = sheet_target['F'+ str(current_row)].value
            current_row += 1
            # if the entry in current_pos is empty, end while loop
            if (sheet_target['B'+str(current_row)].value is None):
                cont = False
        return dea_parameter_dict
    
    def get_target_dictionary(self, dmu_name = None):
        """ get the target info, store the info in dea_model.target_dict
            The function replaces existing target dict 
        """
        target_dict = {}
        if dmu_name:
            target_dict = self.get_individual_target_dictionary(dmu_name)
            self.target_dict[dmu_name] = target_dict
        else:
            for dmu in self.df.index:
                target_dict[dmu] = self.get_individual_target_dictionary(dmu)
                self.target_dict = target_dict
        return target_dict
        
    
    def save(self, file_name):
        with open(file_name,'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod        
    def load_dea(file_name):
        with open(file_name, 'rb') as f:
            model = pickle.load(f)
        return model
    
    def get_efficiency_stats(self):
        min_efficiency = self.efficiency_df.min().values[0]
        max_efficiency = self.efficiency_df.max().values[0]
        avg_efficiency = self.efficiency_df.mean().values[0]
        # number of efficnet dmus
        n_efficient = self.efficiency_df[self.efficiency_df == 1.0].count().values[0]
        return {'min efficiency':min_efficiency,
                'max_efficiency': max_efficiency,
                'avg_efficiency': avg_efficiency,
                'n_efficient': n_efficient} 
    
    def get_mean_efficiency_by_category(self, category_series):
        # category series and efficiency series must have the same set of index
        categories_index = set(category_series.index)
        efficeincy_index = set(self.efficiency_df.index)
        diff_index = categories_index^efficeincy_index
        if diff_index != set():
            raise Exception('Cannot find {} in the indices'.format(diff_index))
        category_series_fillna = category_series.fillna('na')
        eff_df = pd.concat([category_series_fillna, self.efficiency_df], axis = 1, sort = False)
        return eff_df.groupby(category_series.name).mean()
        