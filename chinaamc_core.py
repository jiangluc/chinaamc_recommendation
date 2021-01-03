from pony.orm import *
from Models import *
import xlsxwriter


@db_session
def run_assumption(days_gap=10, ndays=240, percentage=25, fund_code='000051', value_per_time=1000000, sell_share_per=50):
    biz_dates = BusinessDate.select().order_by(BusinessDate.id)
    workbook = xlsxwriter.Workbook('doc\交易记录.xlsx')
    for i, biz_date in enumerate(biz_dates):
        if biz_date >= ndays:
            fund = Fund.get(code=fund_code)
            fund_price = FundPrice.get(biz_date=biz_date, fund=fund)
            if fund_price.assumed_buy_signal(days_gap, ndays, percentage):
                ActionAssumption(
                    action_type=ActionType.get(id=1),
                    fund_price=fund_price,
                    amount=int(round(value_per_time/fund_price.nav*10000, 0)),
                    total_value=value_per_time
                )
            elif fund_price.assumed_sell_signal(ndays, percentage):
                all_actions = ActionAssumption.select()
                current_investment = 0
                for action in all_actions:
                    current_investment += action.amount if action.action_type.id == 1 else -action.amount
                amount_to_sell = int(sell_share_per/100 * current_investment)
                ActionAssumption(
                    action_type=ActionType.get(id=2),
                    fund_price=fund_price,
                    amount=amount_to_sell,
                    total_value=int(round(amount_to_sell*fund_price.nav/10000,0))
                )
    commit()
    # Export result to excel
    all_actions = ActionAssumption.select().order_by(lambda a: a.fund_price.biz_date)
    sheet = workbook.add_worksheet('Records')
    headers = ['交易日期', '交易类型', '指数', '基金净值', '基金份额', '交易金额']
    for i, header in enumerate(headers):
        sheet.write(0, i, header)
    for i, action in enumerate(all_actions):
        sheet.write(i+1, 0, action.fund_price.biz_date.biz_date.strftime('%Y-%m-%d'))
        sheet.write(i+1, 1, action.action_type.name)
        sheet.write(i+1, 2, round(action.fund_price.index_value_object.value/10000, 2))
        sheet.write(i+1, 3, round(action.fund_price.nav/10000, 4))
        sheet.write(i+1, 4, round(action.amount/100, 2))
        sheet.write(i+1, 5, round(action.total_value/100, 2))
    workbook.close()
    delete(a for a in ActionAssumption)
    return


@db_session
def run_suggestion(days_gap=10, ndays=240, percentage=25, fund_code='000051', sell_share_per=50):
    biz_date = list(BusinessDate.select().order_by(desc(BusinessDate.id)))[0]
    fund = Fund.get(code=fund_code)
    current_fund_price = FundPrice.get(fund=fund, biz_date=biz_date)
    current_investment = 0
    all_actions = Action.select()
    for action in all_actions:
        current_investment += action.amount if action.action_type.id == 1 else -action.amount
    if current_fund_price.buy_signal(days_gap, ndays, percentage):
        return '当前数据库最新日期为：%s\n当前建议：推荐买入%s（代码：%s）' % (
            biz_date.biz_date.strftime('%Y-%m-%d'),
            fund.name,
            fund.code,
        )
    elif current_fund_price.sell_signal(ndays, percentage) and current_investment > 0:
        amount_to_sell = int(sell_share_per/100 * current_investment)
        return '当前数据库最新日期为：%s\n当前建议：推荐卖出%s（代码：%s）\n建议卖出份额：%.2f' % (
            biz_date.biz_date.strftime('%Y-%m-%d'),
            fund.name,
            fund.code,
            amount_to_sell/100,
        )
    else:
        return '当前数据库最新日期为：%s\n当前建议：不操作' % biz_date.biz_date.strftime('%Y-%m-%d')


if __name__ == '__main__':
    print(run_suggestion())