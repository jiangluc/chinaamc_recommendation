import xlrd


class FundHistory:

    def read_excel(self, path, sheet_name):
        workbook = xlrd.open_workbook(path)
        sheet = workbook.sheet_by_name(sheet_name)
        record_list = []
        for i in range(1, sheet.nrows):
            row = []
            for j in range(4):
                row.append(sheet.cell(i,j).value)
            record_list.append(row)
        return record_list

    def __getitem__(self, item):
        if type(item) == str:
            col_id = self.col_names.index(item)
            return [row[col_id] for row in self.records_by_row]
        elif type(item) == int:
            return self.records_by_row[item]
        elif type(item) == slice:
            return self.records_by_row[slice]

    def __len__(self):
        return len(self.records_by_row)

    def __init__(self, path, sheet_name):
        self.records_by_row = self.read_excel(path, sheet_name)
        self.col_names = ['date_no', 'biz_date', 'nav', 'index', 'buy_signal', 'sell_signal']
        for i, row in enumerate(self.records_by_row):
            if i<240:
                self.records_by_row[i].append(None)
                self.records_by_row[i].append(None)
            else:
                self.records_by_row[i].append(row[3] < self['index'][i-240:i].sort()[48])
                self.records_by_row[i].append(row[3] > self['index'][i-240:i].sort()[191])
        for i in range(1, 4):
            self.records_by_col.append([row[i] for row in self.records_by_row])
        return


class DailyAction:
    buy_signal = 0
    signal_l20d = 0
    share_flow = 0
    sell_signal = 0
    sell_index_previous = 0
    cash_flow = 0

    def __init__(self, date_no, biz_date, nav, index):
        self.biz_date = biz_date
        self.date_no = date_no
        self.nav = nav
        self.index = index
        return


class FundAccount:
    share = 0
    investment = 0
    net_value = 0
    profit = 0


def main():
    fund_hist = FundHistory('test.xlsx', 'Sheet1')
    n =len(fund_hist)
    actionList = []
    for i in range(240, n):
        action = DailyAction(i+1, fund_hist[i][0], fund_hist[i][1], fund_hist[i][2])



if __name__ == '__main__':
    fund_hist = FundHistory('test.xlsx', 'Sheet1')
    print(fund_hist[240])
