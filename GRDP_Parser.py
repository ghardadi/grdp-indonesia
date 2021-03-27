# -*- coding: utf-8 -*-
"""
Created on Sat Mar 27 01:17:02 2021

@author: ghardadi
"""

import xlrd
import pandas as pd

class GRDP_Parser:
    
    """This class is built to parse GRDP information from National Report
    'Produk Domestik Regional Bruto Kabupaten/Kota di Indonesia 2014-2018',
    which later could be applied to other reports with similar format."""
    
    def __init__(self, file, sheets, years):
        
        """Class initialization requires three parameters: file in string
        format, sheets as a list of strings, and years as a list of numbers"""
        
        self.file = file #String format
        self.sheets = sheets #List of strings
        self.years = years #List of numbers
        
        self.Excel_file = xlrd.open_workbook(self.file)
    
    def row_parser(self, row, sheet):
        
        """This helper function parses data from the selected row and sheet
        from the report"""
        
        text = str(sheet.cell_value(row, 0))
        
        """In accordance to the GADM data, 'Kab. ' is removed from the
        municipality name. Link to GADM: https://gadm.org/data.html"""
        
        try:
            end  = text.index('.')
            kota = str(sheet.cell_value(row, 0))[end+2:]
        except ValueError:
            kota = str(sheet.cell_value(row, 0))
        
        if kota[:5] == 'Kab. ':
            kota = kota[5:]
        
        kota = [kota]
        
        duration = len(self.years)
        
        for y in range(1,duration+1):
            kota.append(sheet.cell_value(row, y))
            
        """This funtion returns variable text (from the first column)
        as string and kota as a list of annual GRDP"""
        
        return text, kota
        
    def data(self):
        
        """Returns the parsed data in Pandas Dataframe format"""
        
        df = pd.DataFrame(columns=(['Kabupaten'] + self.years))

        Excel_file = xlrd.open_workbook(self.file)
        
        for i in self.sheets:
            Working_sheet = Excel_file.sheet_by_name(i)
            
            m, text = 0, ''
            
            """This loop is used to find the first municipal listed in the
            sheet, since row number might vary depending on the conversion
            process from PDF to xlsx"""
            
            while text[:3] != '01.':
                m += 1
                text, kota = self.row_parser(m, Working_sheet)
            
            """This loop is used to find the first municipal listed in the
            sheet, since row number might vary depending on the number of
            municipalities"""
            
            while text[:3] != 'Jml':
                df = df.append(pd.DataFrame([kota,], columns=['Kabupaten'] + self.years))
                m += 1
                text, kota = self.row_parser(m, Working_sheet)
            
        return df
