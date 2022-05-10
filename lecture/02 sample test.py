import FinanceDataReader as web
from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import datetime

# plt.figure(figsize=(16,32))
from matplotlib import font_manager, rc
font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/Art.ttf").get_name()
# rc('font', family='AppleGothic')

today = date.today()
startday = date.today() - timedelta(720)
yesterday = date.today() - timedelta(1)
print(yesterday)

SEC = web.DataReader("207940", startday, yesterday)
print(type(SEC))
print(SEC.tail(10))
# SEC['Close'].plot(figsize=(16,4))

plt.subplot(211)
plt.title("Price Chart")
plt.ylim([600000, 1100000])     # Y축의 범위: [ymin, ymax]
plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

SEC["2020-05-06":"2022-05-06"]['Close'].plot(figsize=(16,10), style='b',xlabel='Date', ylabel='Close Price')
plt.subplots_adjust(hspace=0.5)

plt.subplot(212)
SEC["2020-05-06":"2022-05-06"]["Volume"].plot(figsize=(16,10), style='g')

plt.show()