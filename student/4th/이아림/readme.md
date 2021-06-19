###    Author: 이아림                           
###    Created: 2021.06.16
###    Description: 종목별/업종별 SMA(단순이동평균), WMA(가중이동평균), EMA(지수이동평균) 을 산출하여 매수/매도 결정
> 용어 : SMA(단순이동평균), WMA(가중이동평균), EMA(지수이동평균), Price Oscillator 지표 
> 
> SMA -> WMA -> EMA : EMA가 가장 최근의 값에 가중치를 두면서 이동평균을 계산하는 방법.
> 
> Price Oscillator(POSC) : 단기이동평균과 장기이동평균의 차이를 분석하여 %의 선을 보여줌.
> 
>> Price Oscillator(POSC)[%] > 0 : 매수 시점 
>> 
>> Price Oscillator(POSC)[%] < 0 : 매도 시점 
>> 
>> Price Oscillator(POSC) 공식 : ( (단기이동평균-장기이동평균)/단기이동평균 ) * 100 
#### 구현 순서
> 1. target stock의 SMA, WMA, EMA를 구함.(종가 이용)
> 2. SMA를 사용한 POSC, WMA를 사용한 POSC, EMA를 사용한 POSC 구해줌 
> 3. 각 POSC 가중치를 두어 가중평균 POSC 구함. (여기서 구한 가중평균 POSC를 POSCc로 사용)
> 4. 한 종목이 속한 산업의 POSC 구함(target stock POSC). 
> 5. target stock POSC(%) > 0 인 경우 > 매수 결정. 
>> 5-1. target stock POSC(%) > 0  : 해당 종목이 속한 산업의 POSC(%)보다 클 경우, 
>>                                  과매수로 의심할 수 있음 > 매수 위험
>> 
>> 5-2. target stock posc(%) < 0 : 매도 결정.
