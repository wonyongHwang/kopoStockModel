# -*- coding: utf-8 -*-
import FinanceDataReader as web
from datetime import date, timedelta
import matplotlib.pyplot as plt
import datetime
import earningsRate
import numpy as np
from codeList import queryCodeList
from matplotlib import font_manager, rc
from scipy import stats # line regression
from chart_studio.plotly import plot, iplot #  conda install -c plotly chart-studio
# import plotly.graph_objects as go
import plotly.express as px #  conda install -c plotly plotly-orca
import os

ma1 = 5
ma2 = 20
duration = 720
last_period = 50

'''
# line chart test
t = np.linspace(0, 2*np.pi, 100)
fig = px.line(x=t, y=np.cos(t), labels={'x':'t', 'y':'cos(t)'})
fig.show()
fig.write_image("aa.png")
print(fig)
'''

qc = queryCodeList()


def getClosePrice(code, startDay, EndDay):
    today = date.today()
    if startDay >= today or EndDay >= today or startDay > EndDay:
        print("date Error #1")
        return None
    if code is None:
        print("code Error #1")
        return None
    df = web.DataReader(code, startDay, EndDay)
    #print(df.head())
    return df

def getDiffMAs(code, df,n1,n2):
    if n1 >= n2:
        print("MA set error #1")
        return None
    if len(df) == 0:
        print("dataFrame has no data - ",qc.get_codename_by_codenum(code))
        return None
    if len(df) <= n1:
        print("length of dataFrame is less than or equal to ma #1")
        return None
    df["MA#1"] = np.round(df["Close"].rolling(window=n1, center=False).mean(),2)
    df["MA#2"] = np.round(df["Close"].rolling(window=n2, center=False).mean(),2)
    df["MA#Diff"] = df["MA#1"] - df["MA#2"]
    #print(df.head())
    #print(df["MA#Diff"].tolist())
    return df["MA#Diff"].tolist()


tc = earningsRate.earningCalc()

myCodeList = qc.get_code_list()
print(myCodeList) # ['005560', '101380', '114140', '064900', ...
print(len(myCodeList))

for i in myCodeList:
    data = getClosePrice(i,date.today() - timedelta(duration),date.today() - timedelta(1))
    madf = getDiffMAs(i,data,ma1,ma2)
    #print(i," ",qc.get_codename_by_codenum(i),madf)
    code_name = qc.get_codename_by_codenum(i)
    if madf is not None: # 마지막 ** 기간의 추세 확인
        tempX = list(range(0,last_period))
        tempY = madf[-(last_period)-1:-1]
        try:
            grad, intercept, r_square, p_value, std_err = stats.linregress(tempX, tempY)
            #print(grad, intercept, r_square*r_square, p_value, std_err) # p_value <= 05, r^2 >=0..64
            if grad >= 0 :

                print(">>>>> ",i," ",code_name," ", grad, " ", r_square*r_square, " ",p_value)
                print("     ---->",tempY)
                tempText = code_name
                tempText += ' grad: %4.2f, R^2: %4.2f, p_value: %4.2f' % (grad, r_square*r_square, p_value)

                fig = px.line(x=tempX, y=tempY, labels={'x': 'days', 'y': 'MA diff'}, title=tempText)
                fig.show()
                tempToday = str(date.today())
                if not os.path.exists(tempToday):
                    os.mkdir(tempToday)
                tempStr = tempToday+"/"+code_name + ".png"
                fig.write_image(tempStr)
                #print(fig)
        except Exception as e:
            print("Error Occurs while trying to get lineregress X:", tempX)
            print("Error Occurs while trying to get lineregress Y:",tempY)
            print("Exception e :",e)
    else:
        print(code_name," ", "ma diff gradient less than zero")

# pycharm에서 자신의 모듈 임포트하기 위해서 필요한 설정(mark as a source root)
# https://stackoverflow.com/questions/28705029/pycharm-error-no-module-when-trying-to-import-own-module-python-script
