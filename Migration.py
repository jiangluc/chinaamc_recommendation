from Models import *
from pony.orm import *
import xlrd
from datetime import date


@db_session
def wave1():
    index_code = '399300'
    index_name = '沪深300'
    fund_code = '000051'
    fund_name = '华夏沪深300ETF联接A'
    i1 = Index(code=index_code, name=index_name)
    Fund(code=fund_code, name=fund_name, matched_index=i1)
    ActionType(name='Buy')
    ActionType(name='Sell')
    return


@db_session
def wave2():
    workbook = xlrd.open_workbook('test.xlsx')
    sheet = workbook.sheet_by_name('Sheet1')
    index = Index[1]
    fund = Fund[1]
    raw_data = [[sheet.cell(i, j).value for j in range(4)] for i in range(1, 2408)]
    for data in raw_data:
        biz_date = BusinessDate(date_rank=int(data[0]), biz_date=date(*xlrd.xldate_as_tuple(data[1], 0)[:3]))
        IndexValue(biz_date=biz_date, index=index, value=int(data[3]*10000))
        FundPrice(biz_date=biz_date, fund=fund, nav=int(data[2]*10000))
    return


@db_session
def wave3():
    UserSettings(name='days_back', value=240)
    UserSettings(name='days_gap', value=10)
    UserSettings(name='investment_per_time', value=1000000)
    UserSettings(name='percentage', value=50)


if __name__ == '__main__':
    wave3()
