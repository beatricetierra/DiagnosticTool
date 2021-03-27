# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 15:42:38 2021

@author: btierra
"""
import json 

# Read json file
with open("setup.json", "r") as file:
    variables = json.load(file)

# unload json dictionary to variables
for key, value in variables.items():
    exec(key + '=value')
    
# Add fixed variables
endpoints = {'logstart_findkey': 'Configuring log file:',
             'nodestart_findkey': 'set to load_config',
             'nodeend_findkey': 'Signal 15'}

fixed_columns = ['Date', 
                 'Active Time', 
                 'Inactive Time', 
                 'SW Version', 
                 'Mode', 
                 'Interlock Number', 
                 'Time from Node Start (min)', 
                 'Interlock Duration (min)']

interlock_keys = ['is active',
                  'is inactive',
                  'is clear',
                  'KV.Error',
                  'Set tube voltage']

variables['fixed_columns'] = fixed_columns
variables['interlock_keys'] = interlock_keys
variables['endpoints'] = endpoints
    