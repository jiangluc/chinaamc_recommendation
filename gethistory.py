import urllib.request
import json
import xlsxwriter



def get_hs300(workbook, worksheets):
    
    url = 'http://www.chinaamc.com/fund/%s/zoust_all.js'
    
    for i, worksheet in enumerate(worksheets):
        data_raw = urllib.request.urlopen((url % worksheet)).read()
        data_arranged = json.loads(data_raw)
        days = eval(data_arranged['ShowData'])
        jingzhi = eval(data_arranged['JingzhiName'])
        if i == 0:
            book = xlsxwriter.Workbook(workbook + '.xlsx')
        sheet = book.add_worksheet(worksheet)

        sheet.write(0, 0, 'date')
        sheet.write(0, 1, 'NAV')

        for j, row in enumerate(days):
            sheet.write(j+1, 0, days[j])
            sheet.write(j+1, 1, jingzhi[j])

    book.close()
