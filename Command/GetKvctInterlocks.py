# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 17:03:01 2020

@author: btierra
"""

import sys
import os
import pandas as pd
import InterlockDataframes as idf
import FilterInterlocks as filt

def ExportExcel(system, start_date, end_date):  
    # Dates to save file under new name each time
   filedate = ('-').join([start_date.replace('-',''), end_date.replace('-','')]).replace(' ','')
   
   # KVCT Interlocks
   kvct_writer = pd.ExcelWriter(folder + '/KvctInterlocks_' + system + '_' + filedate + '.xlsx', engine='xlsxwriter')
   sheetnames = ['KVCT Interlocks (All)' , 'KVCT Interlocks (Filtered)']
   dataframes = [kvct_unfiltered, kvct_filtered]
   for df,sheetname in zip(dataframes,sheetnames):
       df.to_excel(kvct_writer,sheetname, index=False)
       
   workbook  = kvct_writer.book
   align = workbook.add_format()
   for df, sheetname in zip(dataframes,sheetnames):
       worksheet = kvct_writer.sheets[sheetname]
       for idx, col in enumerate(df):  # loop through all columns
           series = df[col]
           max_len = max((series.astype(str).map(len).max(),len(str(series.name)))) + 1  # adding a little extra space
           worksheet.set_column(idx, idx, max_len)  # set column width
           align.set_align('center')
   kvct_writer.save()
   
   # Recon Interlocks
   recon_writer = pd.ExcelWriter(folder + '/ReconInterlocks_' + system + '_' + filedate + '.xlsx', engine='xlsxwriter')
   sheetnames = ['Recon Interlocks (All)' , 'Recon Interlocks (Filtered)']
   dataframes = [recon_unfiltered, recon_filtered]
   for df,sheetname in zip(dataframes,sheetnames):
       df.to_excel(recon_writer,sheetname, index=False)
       
   workbook  = recon_writer.book
   align = workbook.add_format()
   for df, sheetname in zip(dataframes,sheetnames):
       worksheet = recon_writer.sheets[sheetname]
       for idx, col in enumerate(df):  # loop through all columns
           series = df[col]
           max_len = max((series.astype(str).map(len).max(),len(str(series.name)))) + 1  # adding a little extra space
           worksheet.set_column(idx, idx, max_len)  # set column width
           align.set_align('center')
   recon_writer.save()

def AnalysisReport(kvct_filtered, recon_filtered, start_date, end_date):
    # Count unexpected interlocks from kvct and recon 
    dataframes = {'kvct': kvct_filtered, 'recon': recon_filtered}
    
    for key, dataframe in dataframes.items():
        analysis = dataframe.groupby('Interlock Number').count()
        analysis.reset_index(inplace=True)
        analysis = analysis[~analysis['Interlock Number'].str.contains('------')]
        analysis = analysis.iloc[:,:2]
        analysis.columns = ['Interlock Number', 'Count']
        analysis = analysis[analysis.columns[::-1]]
        dataframes[key] = analysis
    
    # Combine and export
    analysis = dataframes['kvct'].append(dataframes['recon'])
    filedate = ('-').join([start_date.replace('-',''), end_date.replace('-','')]).replace(' ','')
    analysis.to_csv(folder+ '/AnalysisReport_' + filedate + '.csv', encoding='utf-8', index=False, sep='\t')

# Get files from created directory
folder = sys.argv[1] # second argument of command line        
acceptable_files = ['-kvct-','-pet_recon-','-sysnode-']
filenames = []  

for root, dirs, files in os.walk(folder):
    for file in files:
        if '-000.log' in file:
            for word in acceptable_files:
                if word in file:  
                    filenames.append(os.path.join(root, file))
# Get Interlocks
system_model, kvct_df, recon_df = idf.GetEntries(filenames)

# Filter interlocks
try:
   if kvct_df.empty == False:
       kvct_filtered, kvct_unfiltered = filt.filter_kvct(kvct_df)
   else:
       kvct_filtered, kvct_unfiltered = kvct_df, kvct_df
   if recon_df.empty == False:
       recon_filtered, recon_unfiltered = filt.filter_recon(recon_df)
   else:
       recon_filtered, recon_unfiltered = recon_df, recon_df
except:
   kvct_filtered, kvct_unfiltered = pd.DataFrame(), pd.DataFrame()
   recon_filtered, recon_unfiltered = pd.DataFrame(), pd.DataFrame()
   
# Analyze filtered interlocks
AnalysisReport(kvct_filtered, recon_filtered, start_date=sys.argv[2], end_date=sys.argv[3])
# Export excel files
ExportExcel(system_model, start_date=sys.argv[2], end_date=sys.argv[3])
