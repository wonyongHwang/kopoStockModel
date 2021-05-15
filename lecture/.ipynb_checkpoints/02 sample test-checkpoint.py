import FinanceDataReader as web
from datetime import date, timedelta
import matplotlib.pyplot as plt
import datetime

# %matplotlib inline
# test

plt.figure(figsize=(15,9))
from matplotlib import font_manager, rc
# font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
rc('font', family='AppleGothic')

today = date.today()
startday = date.today() - timedelta(720)
yesterday = date.today() - timedelta(1)
#startday = '3/14/2014'
#yesterday = '4/14/2016'
print(yesterday)

SEC = web.DataReader("207940", startday, yesterday)
# print(type(SEC))
print(SEC.tail(10))
# SEC['Close'].plot(figsize=(16,4))
plt.subplot(211)
SEC["2020-01-01":"2020-03-31"]['Close'].plot(figsize=(16,4), style='b')
plt.subplot(212)
SEC["2020-01-01":"2020-03-31"]["Volume"].plot(figsize=(16,4), style='g')

plt.show()