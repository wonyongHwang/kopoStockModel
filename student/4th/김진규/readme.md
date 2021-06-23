###    Author: 김진규                           
###    Created: 2021.06.18
###    Description: selenium을 통해 유저가 입력하는 주식 종목의 종목 코드 및 주가 정보를 크롤링



| 주요 함수 목록 | 설명 |
| --- | --- |
| isGoodStock | 5개의 지표를 활용, 해당 종목이 투자하기 좋은 종목인지 판단 |
| sellBuyDay | 골든크로스, 데드크로스 상황에서의 장기적 추세로 사고 파는 날을 결정, 마진율을 표시. |
| drawGraph | 추세선을 그려주는 함수 |
|사용 예시 |  http://localhost:8201/stock/isGoodStock?code=102280 으로 get 요청 |


