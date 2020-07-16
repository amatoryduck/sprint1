#!/usr/bin/env python3

import argparse
import datetime
import requests
import os
import unicodedata
import numpy as np
import pandas as pd
import pandas_datareader as pdr
import statsmodels.formula.api as sm
from bs4 import BeautifulSoup
from functools import reduce

def get_Dow():
    """
    Get dow uses Beautiful Soup to scrape the money.cnn website
    in order to get a list of all the symbols used in the
    Dow Jones Industrial Average. This function is only called
    if the user passes the '-d' or '--dow' option in the command line.
    """

    # Request website
    Dow_Website = requests.get("https://money.cnn.com/data/dow30/")
    soup = BeautifulSoup(Dow_Website.content, "html.parser")

    # Find the table with the symbols
    Dow_Table = soup.find("div", {"id": "wsod_indexConstituents"})
    rows = Dow_Table.find_all("tr")
    Dow_data = list()

    # Get all the symbols in a list, and return that list
    for row in rows:
        cols = row.find_all("td")
        cols = [ele.text.strip() for ele in cols]
        Dow_data.append([ele for ele in cols if ele])
    Dow_tags = list()
    for company in Dow_data:
        if company != []:
            name = unicodedata.normalize("NFKD", company[0])
            tag = name.split(" ")[0]
            Dow_tags.append(tag)

    return Dow_tags

def get_SP(): 
    """
    This function scrapes wikipedia in order to get all of the symbols
    included in the S&P 500. This function is only called if the user
    uses the '-p' or '--sp' flags in the command line.
    """

    # Request Website
    SP_Website = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(SP_Website.content, "html.parser")

    # Find table with symbols
    SP_Table = soup.find("table", {"id": "constituents"})
    SP_table_body = SP_Table.find('tbody')
    rows = SP_table_body.find_all('tr')
    rows = rows[1:]
    SP_data = list()

    # Turn that table into a list of symbols
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        SP_data.append([ele for ele in cols if ele])
    SP_tags = list()
    for company in SP_data:
        if company != []:
            SP_tags.append(company[0])

    return SP_tags

def get_commodities():
    """
    Get commodities scrapes yahoo finance in order to return a list 
    of all the commodities symbols. This function is only called if the
    user uses the '-o' or '--commodities' flags in the command line 
    """
    comm_website = requests.get("https://finance.yahoo.com/commodities")
    soup = BeautifulSoup(comm_website.content, "html.parser")
    commodities = soup.findAll("a", {"class":"Fw(b)", "data-symbol":True})

    titles = {}
    tickers = []
    for commodity in commodities:
        ticker = commodity.get("data-symbol")
        tickers.append(ticker)
        # Ticker - Title dictionary can be useful later
        titles[ticker] = commodity.get("title")

    # Hard coded commodities list backup
        # Gold, Corn, Crude
    commodities = ["GC=F", "C=F", "CL=F"]
   	# use following code if you want all tickers
    # return tickers 
    return commodities

def get_currency():
    """
    Get currency scrapes the xe website in order to get a list of all
    the currency symbols. This function is only called if the user uses
    the '-c' or '--currency' flags.
    """
    site = requests.get("https://xe.com/symbols.php")
    soup = BeautifulSoup(site.content, "html.parser")
    table = soup.find("table", {"class": "currencySymblTable"})
    rows = table.find_all("tr")

    currency_data = list()
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        currency_data.append([ele for ele in cols if ele])

    currencies = list()
    for company in currency_data:
        if company != []:
            if company[1] != "Currency Code":
                currencies.append(company[1])

    return currencies

if __name__=="__main__":

    # Setting the command line options
    parser = argparse.ArgumentParser("stocks")
    parser.add_argument("-d", "--dow", help="Select the Dow Jones as your selected stocks", default=False, action="store_true")
    parser.add_argument("-p", "--sp", help="Select the S&P500 as your selected stocks", default=False, action="store_true")
    parser.add_argument("-e", "--end", help="End date in YYYY-MM-DD format", required=True)
    parser.add_argument("-s", "--start", help="Start date in YYYY-MM-DD format", required=True)
    parser.add_argument("-m", "--manual", help="Set the stocks you want to watch manually, tickers separated by commas, no whitespace.", default="")
    parser.add_argument("-q", "--quick", help="Only get one datapoint instead of all of them.", default="")
    parser.add_argument("-c", "--currency", help="Get currency tickers", default=False, action="store_true")
    parser.add_argument("-o", "--commodities", help="Get commodities tickers", default=False, action="store_true")
    parser.add_argument("-v", "--verbose", help="Each stock has its own directory", default=False, action="store_true")
    parser.add_argument("-r", "--regress", help="Return regression csv", default=False, action="store_true")

    args = parser.parse_args()

    # Sanitizing user inputted start date
    try:
        start = datetime.datetime.strptime(args.start, "%Y-%m-%d")
    except:
        raise Exception("Start date must be in YYYY-MM-DD format")

    # Sanitizing user inputted end date
    try:
        end = datetime.datetime.strptime(args.end, "%Y-%m-%d")
    except:
        raise Exception("End date must be in YYYY-MM-DD format")

    # Making sure the tickers will not be empty
    if not args.dow and not args.sp and args.manual and args.commodities == "" and not args.currency:
        raise Exception("You need to select a market")

    tickers = set()

    # Adding all requested symbols to the tickers list
    if args.dow:
        tickers = tickers.union(set(get_Dow()))
    if args.sp:
        tickers = tickers.union(set(get_SP()))
    if args.currency:
        tickers = tickers.union(set(get_currency()))
    if args.commodities:
        tickers = tickers.union(set(get_commodities()))
    if args.manual != "":
        tickers = tickers.union(set(args.manual.split(",")))

    # For each tag requested, get that data from yfinance as a DataFrame
    data_list = list()
    index = 0
    for tag in tickers:
        index = index + 1
        try:
            print("Working on : {}, {} OUT OF {}".format(tag, index, len(tickers)))
            if args.quick == "": # If asking for all datapoints
                data = pdr.get_data_yahoo(tag, start=start, end=end)
                print(data)
                data['Ticker'] = tag
                data_list.append(data)
            else: # If only want user selected datapoint
                data = pdr.get_data_yahoo(tag, start=start, end=end)
                data["Ticker"] = tag
                data = data[[ args.quick, "Ticker"]]
                data_list.append(data)
        except: # Data returned by yfinance was None
            print("DATA NOT FOUND, LIKELY A WEEKEND")
            continue

    if args.verbose: # If verbose mode was selected with '-v' or '--verbose'
        # Make a table with all the combined data
        table = reduce(lambda x, acc: pd.concat([x, acc]), data_list, pd.DataFrame())
        table = table.sort_index()
        dates = list(set(table.index.values))

        mode = dict()
        highs = dict()
        lows = dict()
        opens = dict()
        closes = dict()
        volume = dict()
        adj_close = dict()
        for tag in tickers: # Filling each datapoint with values for each symbol
            highs[tag] = table[table["Ticker"].str.contains(tag)]["High"].values
            lows[tag] = table[table["Ticker"].str.contains(tag)]["Low"].values
            opens[tag] = table[table["Ticker"].str.contains(tag)]["Open"].values
            closes[tag] = table[table["Ticker"].str.contains(tag)]["Close"].values
            adj_close[tag] = table[table["Ticker"].str.contains(tag)]["Adj Close"].values
            volume[tag] = table[table["Ticker"].str.contains(tag)]["Volume"].values

            if len(highs[tag]) in mode: # Making sure each symbol has the same number of rows
                mode[len(highs[tag])] = mode[len(highs[tag])] + 1
            else:
                mode[len(highs[tag])] = 1

        # Finding the mode number of rows
        tmp = 0
        m = 0
        for i in mode:
            if mode[i] > tmp and i != 0:
                tmp = mode[i]
                m = i

        # Turning DataFrames into dicts 
        dicts = [highs, lows, opens, closes, volume, adj_close]
        for datapoint in dicts:
            datapoint["Dates"] = dates
            for tag in datapoint:
                l = list()
                for x in datapoint[tag]:
                    l.append(x)
                if len(l) == m:
                    datapoint[tag] = l

        # Deleting symbols with odd number of rows
        tmp = dicts
        deletes = list()
        for i in dicts:
            for j in list(i.keys()):
                if len(i[j]) != m:
                    del i[j]

        # Adding date index
        for i in dicts:
            i["Dates"] = dates

        # Writing to a csv
        l = ["high", "low", "open", "close", "volume", "adj_close"]
        i = 0
        for datapoint in dicts:
            for ticker in datapoint:
                try:
                    df = pd.DataFrame({ticker: datapoint[ticker]})
                    df["Dates"] = dates
                    df.set_index("Dates", inplace=True)
                    df.sort_index()
                    csv = df.to_csv()
                    os.system("mkdir {}".format(ticker))
                    f = open("{}/{}.csv".format(ticker, l[i]), 'w')
                    f.write(csv)
                    f.close()
                except:
                    continue
            i = i + 1

    elif args.quick == "": # If user only wanted all datapoints
        # Getting one table with all the data
        table = reduce(lambda x, acc: pd.concat([x, acc]), data_list, pd.DataFrame())
        table = table.sort_index()
        dates = list(set(table.index.values))

        mode = dict()
        highs = dict()
        lows = dict()
        opens = dict()
        closes = dict()
        volume = dict()
        adj_close = dict()
        for tag in tickers: # Filling each datapoint with values for each symbol
            highs[tag] = table[table["Ticker"].str.contains(tag)]["High"].values
            lows[tag] = table[table["Ticker"].str.contains(tag)]["Low"].values
            opens[tag] = table[table["Ticker"].str.contains(tag)]["Open"].values
            closes[tag] = table[table["Ticker"].str.contains(tag)]["Close"].values
            adj_close[tag] = table[table["Ticker"].str.contains(tag)]["Adj Close"].values
            volume[tag] = table[table["Ticker"].str.contains(tag)]["Volume"].values

            if len(highs[tag]) in mode: # Making sure each symbol has the same number of rows
                mode[len(highs[tag])] = mode[len(highs[tag])] + 1
            else:
                mode[len(highs[tag])] = 1

        tmp = 0 
        m = 0
        for i in mode: # Finding mode number of rows
            if mode[i] > tmp and i != 0:
                tmp = mode[i]
                m = i

        dicts = [highs, lows, opens, closes, volume, adj_close]
        for datapoint in dicts: # Turning DataFrames into dicts
            datapoint["Dates"] = dates
            for tag in datapoint:
                l = list()
                for x in datapoint[tag]:
                    l.append(x)
                if len(l) == m:
                    datapoint[tag] = l

        tmp = dicts
        deletes = list()
        for i in dicts: # Deleting symbols with odd number of rows
            for j in list(i.keys()):
                if len(i[j]) != m:
                    del i[j]

        for i in dicts: # Adding date as index
            i["Dates"] = dates

        # Creating the dataframes needed
        highs_frame = pd.DataFrame(highs)
        highs_frame.set_index("Dates", inplace=True)
        highs_frame.sort_index()
        lows_frame = pd.DataFrame(lows)
        lows_frame.set_index("Dates", inplace=True)
        lows_frame.sort_index()
        opens_frame = pd.DataFrame(opens)
        opens_frame.set_index("Dates", inplace=True)
        opens_frame.sort_index()
        closes_frame = pd.DataFrame(closes)
        closes_frame.set_index("Dates", inplace=True)
        closes_frame.sort_index()
        volume_frame = pd.DataFrame(volume)
        volume_frame.set_index("Dates", inplace=True)
        volume_frame.sort_index()
        adj_close_frame = pd.DataFrame(adj_close)
        adj_close_frame.set_index("Dates", inplace=True)
        adj_close_frame.sort_index()

        frames = [highs_frame, lows_frame, opens_frame, closes_frame, volume_frame, adj_close_frame]
        i = 0
        for name in ["high", "low", "open", "close", "volume", "adj_close"]: # Write to csv
            csv = frames[i].to_csv()
            f = open("{}.csv".format(name), 'w')
            f.write(csv)
            f.close()
            i = i + 1

        i = 0
        names = ["high", "low", "open", "close", "volume", "adj_close"]
        if args.regress: # Creates regression csv's if user requested it with the '-r' option
            for frame in frames:
                returns = frame.pct_change()
                csv = returns.to_csv()
                f = open("{}_pct_change.csv".format(names[i]), 'w')
                f.write(csv)
                f.close()

                line = " + ".join(frame.columns[1:])
                model = sm.ols("{} ~ {}".format(frame.columns[0], line), data=frame)
                model = returns.to_csv()
                f = open("{}_sm.csv".format(names[i]), 'w')
                f.write(csv)
                f.close()

                i = i + 1
        
    else: # User wants only one datapoint
        # Getting one table with all the data
        table = reduce(lambda x, acc: pd.concat([x, acc]), data_list, pd.DataFrame())
        table = table.sort_index()
        dates = list(set(table.index.values))

        d = dict()
        for tag in tickers: # Turning data into dict
            d[tag] = table[table["Ticker"].str.contains(tag)].values

        for x in d: # Adding dates
            l = list()
            for y in d[x]:
                l.append(y[0])
            d[x] = l
        d["Dates"] = dates
        
        # Creating dataframe
        df = pd.DataFrame(d)
        df.set_index("Dates", inplace=True)
        df.sort_index()

        # Writing to csv
        csv = df.to_csv()
        f = open("{}.csv".format(args.quick), 'w')
        f.write(csv)
        f.close()