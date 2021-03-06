#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  1 22:18:31 2018

@author: gykovacs
"""

__all__= ['get_price_data',
          'get_sp500_price_data',
          'get_sp500_descriptors',
          'get_djia_descriptors',
          'get_key_financial_descriptors',
          'get_balance_sheet_data',
          'get_cashflow_data',
          'get_income_statement_data',
          'get_sp500_tickers']

import sys
import requests
import json
import datetime

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

def get_price_data(tickers, start= '2017-10-10', end= None):
    end= end or datetime.datetime.now().strftime('%Y-%m-%d')
    
    results= {}
    
    sys.stdout.write('Downloading price data for ')
    for ticker in tickers:
        sys.stdout.write('%s, ' % ticker)
        url= "http://globalquote.morningstar.com/globalcomponent/RealtimeHistoricalStockData.ashx?ticker=%s&showVol=true&dtype=his&f=d&curry=USD&range=%s|%s&isD=true&isS=true&hasF=true&ProdCode=DIRECT" % (ticker, start, end)
        d= json.loads(requests.get(url).content.decode('utf-8'))
        if not d is None and len(d) > 0:
            results[ticker]= pd.DataFrame(data= d['PriceDataList'][0]['Datapoints'], index= pd.to_datetime('1900-1-1') + pd.to_timedelta(d['PriceDataList'][0]['DateIndexs'], unit= 'd'), columns= ['Open', 'High', 'Low', 'Close'])
    print('')
    
    return results

def get_sp500_price_data(start= '2017-10-10', end= '2018-3-9'):
    return get_price_data(get_sp500_tickers(), start, end)

def get_djia_price_data(start= '2017-10-10', end= '2018-3-9'):
    return get_price_data(get_djia_tickers(), start, end)

def get_sp500_tickers():
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
    
    return data.reset_index()[['Ticker symbol', 'GICS Sector']]

def get_sp500_descriptors():
    """
    Get financial descriptors for S&P500 stocks
    Returns:
        dict(dict(pd.DataFrame)): the descriptors by stocks and categories
    """

    return get_key_financial_descriptors(get_sp500_tickers()['Ticker symbol'].values)

def get_djia_tickers():
    tables= import_tables("Dow Jones Industrial Average")
    data= pd.DataFrame(tables[0].rows)
    data= data.astype(str)
    str_cols= data.select_dtypes(['object'])
    data[str_cols.columns]= str_cols.apply(lambda x: x.str.strip())
    
    return data.reset_index()[['Symbol', 'Industry']]

def get_djia_descriptors():
    """
    Get financial descriptors for S&P500 stocks
    Returns:
        dict(dict(pd.DataFrame)): the descriptors by stocks and categories
    """
    
    return get_key_financial_descriptors(get_djia_tickers()['Symbol'].values)

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

def get_data_from_url(url, max_trials= 10):
    try:
        s= requests.get(url).content
        d= s.decode('utf-8')
        num_trials= 0
        while len(d) == 0 and num_trials < max_trials:
            s= requests.get(url).content
            d= s.decode('utf-8')
            num_trials= num_trials + 1
            sys.stdout.write('.')
    except Exception as e:
        print('ERROR: downloading data failed: %s' % str(e))
        
    return d

def get_key_financial_descriptors(tickers, max_trials= 10):
    """
    Downloads and tokenizes morningstar financial data.
    Args:
        tickers (list(str)): list of tickers to donwload
    Returns:
        dict(dict(pd.DataFrame)): financial descriptors by ticker, by category
    """
    
    raw_data= {}
    
    sys.stdout.write('Downloading key ratios data for ')
    for t in tickers:
        sys.stdout.write('%s, ' % t)
        sys.stdout.flush()
        num_trials= 0
        
        while num_trials < max_trials:
            num_trials= num_trials + 1
            url= 'http://financials.morningstar.com/ajax/exportKR2CSV.html?t=%s' % t
            data= get_data_from_url(url)
            if len(data) > 0:
                raw_data[t]= data
                break
            else:
                print('WARNING: downloading %s data failed at trial %d' % (t, num_trials))

    print('')

    sys.stdout.write('Processing ticker: ')
    result= {}
    for t in raw_data:
        sys.stdout.write('%s ' % t)
        result[t]= process_key_raw_data(raw_data[t])

    print('')
    
    return result

def process_balance_sheet_raw_data(string):
    lines= string.splitlines()
    for i in range(len(lines)):
        lines[i]= tokenize_line(lines[i])
    
    results= {}
    index= None
    
    for i in range(len(lines)):
        if len(lines[i]) == 0:
            continue
        
        # extract identifier
        identifier= lines[i][0]
        
        if identifier.startswith('Fiscal year ends in'):
            index= lines[i][1:]
        elif identifier in ['Cash and cash equivalents', 'Short-term investments',
                            'Total cash', 'Receivables', 'Deferred income taxes',
                            'Prepaid expenses', 'Total current assets', 
                            'Gross property, plant and equipment', 'Accumulated Depreciation',
                            'Net property, plant and equipment', 'Goodwill', 'Intangible assets',
                            'Other long-term assets', 'Total non-current assets', 'Total assets',
                            'Capital leases', 'Accounts payable', 'Taxes payable',
                            'Accrued liabilities', 'Deferred revenues', 'Total current liabilities',
                            'Long-term debt', 'Non-current capital leases', 'Deferred taxes liabilities',
                            'Other long-term liabilities', 'Total non-current liabilities', 
                            'Total liabilities', 'Common stock', 'Additional paid-in capital',
                            'Retained earnings', 'Accumulated other comprehensive income',
                            "Total stockholders' equity", "Total liabilities and stockholders' equity"] and len(lines[i]) > 1:
            results[identifier]= lines[i][1:]
    
    return pd.DataFrame(data= results, index= index)

def get_balance_sheet_data(tickers, max_trials= 10):
    raw_data= {}
    sys.stdout.write('Downloading balance sheet data for ')
    for t in tickers:
        num_trials= 0
        sys.stdout.write('%s, ' % t)
        url= 'http://financials.morningstar.com/ajax/ReportProcess4CSV.html?t=%s&reportType=bs&period=12&dataType=A&order=asc&columnYear=10&number=3' % t
        while num_trials < max_trials:
            num_trials= num_trials + 1
            try:
                s= requests.get(url).content
                raw_data[t]= s.decode('utf-8')
                break
            except:
                print('WARNING: downloading %s data failed at trial %d' % (t, num_trials))
    
    print('')
    
    results= {}
    for t in raw_data:
        results[t]= process_balance_sheet_raw_data(raw_data[t])
        
    return results

def process_cashflow_raw_data(string):
    lines= string.splitlines()
    for i in range(len(lines)):
        lines[i]= tokenize_line(lines[i])
    
    results= {}
    index= None
    
    for i in range(len(lines)):
        if len(lines[i]) == 0:
            continue
        
        # extract identifier
        identifier= lines[i][0]
        
        if identifier.startswith('Fiscal year ends in'):
            index= lines[i][1:]
        elif identifier in ['Net income', 'Depreciation & amortization',
                            'Amortization of debt discount/premium and issuance costs',
                            'Deferred income taxes',
                            'Stock based compensation', 'Change in working capital',
                            'Accounts receivable', 'Prepaid expenses', 'Accounts payable',
                            'Accrued liabilities', 'Other non-cash items',
                            'Net cash provided by operating activities', 
                            'Investments in property, plant, and equipment',
                            'Acquisitions, net', 'Purchases of investments',
                            'Sales/Maturities of investments', 'Other investing activities',
                            'Net cash used for investing activities',
                            'Debt issued', 'Debt repayment', 'Warrant issued',
                            'Common stock issued', 'Other financing activities',
                            'Net cash provided by (used for) financing activities',
                            'Effect of exchange rate changes', 'Net change in cash',
                            'Cash at beginning of period', 'Cash at end of period',
                            'OPerating cash flow', 'Capital expenditure', 'Free cash flow' ] and len(lines[i]) > 1:
            results[identifier]= lines[i][1:]
    
    return pd.DataFrame(data= results, index= index)

def get_cashflow_data(tickers, max_trials= 10):
    raw_data= {}
    sys.stdout.write('Downloading cashflow data for ')
    for t in tickers:
        num_trials= 0
        sys.stdout.write('%s, ' % t)
        url= 'http://financials.morningstar.com/ajax/ReportProcess4CSV.html?t=%s&reportType=cf&period=12&dataType=A&order=asc&columnYear=10&number=3' % t
        while num_trials < max_trials:
            num_trials= num_trials + 1
            try:
                s= requests.get(url).content
                raw_data[t]= s.decode('utf-8')
                break
            except:
                print('Warning: downloading %s data failed at trial %d' % (t, num_trials))
    
    print('')
    
    results= {}
    for t in raw_data:
        results[t]= process_cashflow_raw_data(raw_data[t])
        
    return results

def process_income_statement_raw_data(string):
    lines= string.splitlines()
    for i in range(len(lines)):
        lines[i]= tokenize_line(lines[i])
    
    results= {}
    index= None
    
    for i in range(len(lines)):
        if len(lines[i]) == 0:
            continue
        
        # extract identifier
        identifier= lines[i][0]
        
        if identifier.startswith('Fiscal year ends in'):
            index= lines[i][1:]
        elif identifier in ['Revenue', 'Cost of revenue', 'Gross profit',
                            'Research and development', 'Sales, General and administrative',
                            'Total operating expenses', 'Operating income',
                            'Interest Expense', 'Other income (expense)',
                            'Income before taxes', 'Provision for income taxes',
                            'Net income from continuing operations', 'Net income',
                            'Preferred dividend', 'Net income available to common shareholders',
                            'EBITDA'] and len(lines[i]) > 1:
            results[identifier]= lines[i][1:]
    
    return pd.DataFrame(data= results, index= index)

def get_income_statement_data(tickers, max_trials= 10):
    raw_data= {}
    sys.stdout.write('Downloading income statement data for ')
    for t in tickers:
        num_trials= 0
        sys.stdout.write('%s, ' % t)
        url= 'http://financials.morningstar.com/ajax/ReportProcess4CSV.html?t=%s&reportType=is&period=12&dataType=A&order=asc&columnYear=10&number=3' % t
        while num_trials < max_trials:
            num_trials= num_trials + 1
            try:
                s= requests.get(url).content
                raw_data[t]= s.decode('utf-8')
                break
            except:
                print('Warning: downloading %s data failed at trial %d' % (t, num_trials))
    
    print('')
    
    results= {}
    for t in raw_data:
        results[t]= process_income_statement_raw_data(raw_data[t])
        
    return results

def process_key_raw_data(string):
    """
    Processes the raw data downloaded from morningstar.
    Args:
        string (str): the raw data string
    Returns:
        dict(pd.DataFrame): the financial descriptors by categories
    """
    
    #print(string)
    
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
        #print("id: " + str(identifier))
        
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
    