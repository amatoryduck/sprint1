#!/usr/bin/env python3

import argparse
import datetime
import requests
import os
import unicodedata
import numpy as np
import pandas as pd
import pandas_datareader as pdr
from bs4 import BeautifulSoup
from functools import reduce

def get_Dow():
    Dow_Website = requests.get("https://money.cnn.com/data/dow30/")
    soup = BeautifulSoup(Dow_Website.content, "html.parser")

    Dow_Table = soup.find("div", {"id": "wsod_indexConstituents"})
    rows = Dow_Table.find_all("tr")
    Dow_data = list()

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
    SP_Website = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(SP_Website.content, "html.parser")

    SP_Table = soup.find("table", {"id": "constituents"})
    SP_table_body = SP_Table.find('tbody')
    rows = SP_table_body.find_all('tr')
    SP_data = list()

    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        SP_data.append([ele for ele in cols if ele])

    SP_tags = list()
    for company in SP_data:
        if company != []:
            SP_tags.append(company[0])

    return SP_tags

if __name__=="__main__":
    parser = argparse.ArgumentParser("stocks")
    parser.add_argument("-d", "--dow", help="Select the Dow Jones as your selected stocks", default=False, action="store_true")
    parser.add_argument("-p", "--sp", help="Select the S&P500 as your selected stocks", default=False, action="store_true")
    parser.add_argument("-e", "--end", help="End date in YYYY-MM-DD format", required=True)
    parser.add_argument("-s", "--start", help="Start date in YYYY-MM-DD format", required=True)
    parser.add_argument("-n", "--name", help="Name of .csv file to be written to. Please add the extension", required=True)
    parser.add_argument("-m", "--manual", help="Set the stocks you want to watch manually, tickers separated by commas, no whitespace.", default="")
    parser.add_argument("-q", "--quick", help="Only get one datapoint instead of all of them.", default="")

    args = parser.parse_args()

    try:
        start = datetime.datetime.strptime(args.start, "%Y-%m-%d")
    except:
        raise Exception("Start date must be in YYYY-MM-DD format")

    try:
        end = datetime.datetime.strptime(args.end, "%Y-%m-%d")
    except:
        raise Exception("End date must be in YYYY-MM-DD format")

    if not args.dow and not args.sp and args.manual == "":
        raise Exception("You need to select a market")

    tickers = set()

    if args.dow:
        tickers = tickers.union(set(get_Dow()))
    if args.sp:
        tickers = tickers.union(set(get_SP()))
    if args.manual != "":
        tickers = tickers.union(set(args.manual.split(",")))

    data_list = list()
    for tag in tickers:
        try:
            print("Working on : {}".format(tag))
            if args.quick == "":
                data = pdr.get_data_yahoo(tag, start=start, end=end)
                data['Ticker'] = tag
                data_list.append(data)
            else:
                data = pdr.get_data_yahoo(tag, start=start, end=end)
                data["Ticker"] = tag
                data = data[[ args.quick, "Ticker"]]
                data_list.append(data)
        except:
            continue

    if args.quick == "":
        table = reduce(lambda x, acc: pd.concat([x, acc]), data_list, pd.DataFrame())
        table = table.sort_index()
        dates = list(set(table.index.values))

        highs = dict()
        lows = dict()
        opens = dict()
        closes = dict()
        volume = dict()
        adj_close = dict()
        for tag in tickers:
            highs[tag] = table[table["Ticker"].str.contains(tag)]["High"].values
            lows[tag] = table[table["Ticker"].str.contains(tag)]["Low"].values
            opens[tag] = table[table["Ticker"].str.contains(tag)]["Open"].values
            closes[tag] = table[table["Ticker"].str.contains(tag)]["Close"].values
            adj_close[tag] = table[table["Ticker"].str.contains(tag)]["Adj Close"].values
            volume[tag] = table[table["Ticker"].str.contains(tag)]["Volume"].values

        dicts = [highs, lows, opens, closes, volume, adj_close]
        for datapoint in dicts:
            datapoint["Dates"] = dates
            for tag in datapoint:
                l = list()
                for x in datapoint[tag]:
                    l.append(x)
                datapoint[tag] = l

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
        for name in ["high", "low", "open", "close", "volume", "adj_close"]:
            csv = frames[i].to_csv()
            f = open("{}.csv".format(name), 'w')
            f.write(csv)
            f.close()
            i = i + 1
        
    else:
        table = reduce(lambda x, acc: pd.concat([x, acc]), data_list, pd.DataFrame())
        table = table.sort_index()
        dates = list(set(table.index.values))

        d = dict()
        for tag in tickers:
            d[tag] = table[table["Ticker"].str.contains(tag)].values

        for x in d:
            l = list()
            for y in d[x]:
                l.append(y[0])
            d[x] = l
        d["Dates"] = dates
        
        df = pd.DataFrame(d)
        df.set_index("Dates", inplace=True)
        df.sort_index()

        csv = df.to_csv()
        f = open(args.name, 'w')
        f.write(csv)
        f.close()