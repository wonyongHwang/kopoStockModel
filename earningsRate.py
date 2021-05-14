import FinanceDataReader as web
from datetime import date, timedelta
import matplotlib.pyplot as plt
import datetime
import numpy as np


class earningCalc:

    # calculate profit
    def earning(self, code, buyDate, sellDate):

        if sellDate - buyDate > timedelta(720):
            return 0,0

        stockData = web.DataReader(code, buyDate - timedelta(10),sellDate)
        stockData = stockData[stockData['Volume'] != 0]
        stockData = stockData.reset_index(drop=False)

        print(stockData)
        sellPrice = (stockData.loc[stockData['Date'] == str(sellDate)]['Close']).iloc[0]
        print(sellPrice)
        buyPrice = (stockData.loc[stockData['Date'] == str(buyDate)]['Close']).iloc[0]
        print(buyPrice)
        gap = sellPrice - buyPrice
        rate = np.log(sellPrice/buyPrice)

        return gap, rate


#ec = earningCalc()
#test = ec.earning("207940",date(2018,4,2),date(2018,4,27))
#print(test)
