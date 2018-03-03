#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  1 22:18:31 2018

@author: gykovacs
"""

__all__= ['get_sp500_descriptors',
          'get_djia_descriptors',
          'get_financial_descriptors']

import sys
import requests

import pandas as pd

from wikitables import import_tables

# names of descriptors in the category 'Financials'
financials_names= ['Revenue USD Mil', 'Gross Margin %', 'Operating Income USD Mil',
                   'Operating Margin %', 'Net Income USD Mil', 'Earnings Per Share USD',
                   'Dividends USD', 'Payout Ratio % *', 'Shares Mil', 'Book Value Per Share * USD',
                   'Operating Cash Flow USD Mil', 'Cap Spending USD Mil', 'Free Cash Flow USD Mil',
                   'Free Cash Flow Per Share  *USD', 'Working Capital USD Mil']

# names of descriptors in the category 'Margins % of Sales'
margins_perc_of_sales_names= ['Revenue', 'COGS', 'Gross Margin', 'SG&A', 'R&D',
                              'Other', 'Operating Margin', 'Net Int Inc & Other',
                              'EBT Margin']

# names of descriptors in the category 'Profitability'
profitability_names= ['Tax Rate %', 'Net Margin %', 'Asset Turnover (Average)',
                      'Return on Assets %', 'Financial Leverage (Average)',
                      'Return on Equity %', 'Return on Invested Capital %', 'Interest Coverage']

# names of descriptors in the category 'Growth'
growth_names= ['Year over Year', '3-Year Average', '5-Year Average', '10-Year Average']

# names of descriptors in the category 'Cash Flow Ratios'
cash_flow_ratios_names= ['Operating Cash Flow Growth % YOY', 'Free Cash Flow Growth % YOY',
                         'Cap Ex as a % of Sales', 'Free Cash Flow/Sales %', 'Free Cash Flow/Net Income']

# names of descriptors in the category 'Balance Sheet Items'
balance_sheet_items_names= ['Cash & Short Term Investments', 'Accounts Receivable',
                            'Inventory', 'Other Current Assets', 'Total Current Assets',
                            'Net PP&E', 'Intangibles', 'Other Long-Term Assets',
                            'Total Assets', 'Accounts Payable', 'Short-Term Debt',
                            'Taxes Payable', 'Accrued Liabilities', 'Other Short-Term Liabilities',
                            'Total Current Liabilities', 'Long-Term Debt', 'Other Long-Term Liabilities',
                            'Total Liabilities', "Total Stockholders' Equity",  'Total Liabilities & Equity']

# names of descriptors in the category 'Liquidity'
liquidity_names= ['Current Ratio', 'Quick Ratio', 'Financial Leverage', 'Debt/Equity']

# names of descriptors in the category 'Efficiency'
efficiency_names= ['Days Sales Outstanding', 'Days Inventory', 'Payables Period',
                   'Cash Conversion Cycle', 'Receivables Turnover', 'Inventory Turnover',
                   'Fixed Assets Turnover', 'Asset Turnover']

def get_sp500_descriptors():
    """
    Get financial descriptors for S&P500 stocks
    Returns:
        dict(dict(pd.DataFrame)): the descriptors by stocks and categories
    """
    
    tables= import_tables("List of S&P 500 companies")
    data= pd.DataFrame(tables[0].rows)
    data= data.astype(str)
    str_cols= data.select_dtypes(['object'])
    data[str_cols.columns]= str_cols.apply(lambda x: x.str.strip())
    
    return get_financial_descriptors(data['Ticker symbol'].values)

def get_djia_descriptors():
    """
    Get financial descriptors for S&P500 stocks
    Returns:
        dict(dict(pd.DataFrame)): the descriptors by stocks and categories
    """
    
    tables= import_tables("Dow Jones Industrial Average")
    data= pd.DataFrame(tables[0].rows)
    data= data.astype(str)
    str_cols= data.select_dtypes(['object'])
    data[str_cols.columns]= str_cols.apply(lambda x: x.str.strip())
    
    return get_financial_descriptors(data['Symbol'].values)
    

def convert_to_float(token):
    """
    Convert token to float.
    Args:
        token (str): a string token to convert to float
    Returns:
        float if the token can be converted, otherwise the token
    """
    
    if token == '':
        return None
    try:
        float(token.replace(',',''))
        return float(token.replace(',',''))
    except ValueError:
        return token

def tokenize_line(line):
    """
    Tokenize a line of the raw data.
    Args:
        line (str): a line of the raw data
    Returns:
        list(str/float): the tokenized line
    """
    
    tokens, state, pos, i= [], None, 0, 0

    # if the line starts with a comma, add an empty string to the tokens
    if len(line) > 0 and line[0] == ',':
        tokens.append('')

    while i < len(line):
        if line[i] == ',' and not state == '"':
            if pos != i or (line[pos] == ',' and line[pos-1] == ','):
                tokens.append(line[pos:i])
            pos= i + 1
        elif line[i] == '"' and not state == '"':
            state= '"'
            pos= i + 1
        elif line[i] == '"' and state == '"':
            if pos != i:
                tokens.append(line[pos:i])
            state= None
            pos= i + 1
        
        i= i + 1

    # handle the possible empty last token        
    if pos != i:
        tokens.append(line[pos:i])
    if len(line) > 0 and line[-1] == ',':
        tokens.append('')
    
    # convert the tokens to float, if they can be converted
    tokens= [convert_to_float(t) for t in tokens]

    return tokens

def get_financial_descriptors(tickers):
    """
    Downloads and tokenizes morningstar financial data.
    Args:
        tickers (list(str)): list of tickers to donwload
    Returns:
        dict(dict(pd.DataFrame)): financial descriptors by ticker, by category
    """
    
    raw_data= {}
    
    sys.stdout.write('Downloading data for ')
    for t in tickers:
        sys.stdout.write('%s, ' % t)
        url= 'http://financials.morningstar.com/ajax/exportKR2CSV.html?t=%s' % t
        try:
            s= requests.get(url).content
            raw_data[t]= s.decode('utf-8')
        except:
            print('ERROR: downloading %s data failed' % t)

    print('')

    result= {}
    for t in raw_data:
        result[t]= process_raw_data(raw_data[t])

    return result
    
def process_raw_data(string):
    """
    Processes the raw data downloaded from morningstar.
    Args:
        string (str): the raw data string
    Returns:
        dict(pd.DataFrame): the financial descriptors by categories
    """
    
    # split the string to lines
    lines= string.splitlines()
    for i in range(len(lines)):
        lines[i]= tokenize_line(lines[i])

    financials, margins_perc_of_sales, profitability, revenue_perc, \
    operating_income_perc, net_income_perc, eps_perc, cash_flow_ratios, \
    balance_sheet_items, liquidity, efficiency, \
    indices= {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

    growth_dict= None
    
    # iterating trough the lines and processing them
    for i in range(len(lines)):
        if len(lines[i]) == 0:
            continue
        
        # extract identifier
        identifier= lines[i][0]
        
        # handle category identifiers
        if identifier == 'Financials':
            indices['financials']= lines[i+1][1:]
        elif identifier == 'Key Ratios -> Profitability':
            indices['margins_perc_of_sales']= lines[i+1][1:]
        elif identifier == 'Profitability':
            indices['profitability']= lines[i][1:]
        elif identifier == 'Key Ratios -> Growth':
            indices['revenue_perc']= lines[i+1][1:]
            indices['operating_income_perc']= lines[i+1][1:]
            indices['net_income_perc']= lines[i+1][1:]
            indices['eps_perc']= lines[i+1][1:]
        elif identifier == 'Key Ratios -> Cash Flow':
            indices['cash_flow_ratios']= lines[i+1][1:]
        elif identifier == 'Key Ratios -> Financial Health':
            indices['balance_sheet_items']= lines[i+1][1:]
        elif identifier == 'Liquidity/Financial Health':
            indices['liquidity']= lines[i][1:]
        elif identifier == 'Key Ratios -> Efficiency Ratios':
            indices['efficiency']= lines[i+1][1:]
        elif identifier == 'Revenue %':
            growth_dict= revenue_perc
        elif identifier == 'Operating Income %':
            growth_dict= operating_income_perc
        elif identifier == 'Net Income %':
            growth_dict= net_income_perc
        elif identifier == 'EPS %':
            growth_dict= eps_perc
        
        # handle category entries
        elif identifier in financials_names:
            financials[identifier]= lines[i][1:]
        elif identifier in margins_perc_of_sales_names:
            margins_perc_of_sales[identifier]= lines[i][1:]
        elif identifier in profitability_names:
            profitability[identifier]= lines[i][1:]
        elif identifier in growth_names:
            growth_dict[identifier]= lines[i][1:]
        elif identifier in cash_flow_ratios_names:
            cash_flow_ratios[identifier]= lines[i][1:]
        elif identifier in balance_sheet_items_names:
            balance_sheet_items[identifier]= lines[i][1:]
        elif identifier in liquidity_names:
            liquidity[identifier]= lines[i][1:]
        elif identifier in efficiency_names:
            efficiency[identifier]= lines[i][1:]
    
    return {'financials': pd.DataFrame(data= financials, index= indices['financials']),
            'margins_perc_of_sales': pd.DataFrame(data= margins_perc_of_sales, index= indices['margins_perc_of_sales']),
            'profitability': pd.DataFrame(data= profitability, index= indices['profitability']),
            'revenue_perc': pd.DataFrame(data= revenue_perc, index= indices['revenue_perc']),
            'operating_income_perc': pd.DataFrame(data= operating_income_perc, index= indices['operating_income_perc']),
            'net_income_perc': pd.DataFrame(data= net_income_perc, index= indices['net_income_perc']),
            'eps_perc': pd.DataFrame(data= eps_perc, index= indices['eps_perc']),
            'cash_flow_ratios': pd.DataFrame(data= cash_flow_ratios, index= indices['cash_flow_ratios']),
            'balance_sheet_items': pd.DataFrame(data= balance_sheet_items, index= indices['balance_sheet_items']),
            'liquidity': pd.DataFrame(data= liquidity, index= indices['liquidity']),
            'efficiency': pd.DataFrame(data= efficiency, index= indices['efficiency'])}
    