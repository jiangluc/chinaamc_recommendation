from datetime import date
from pony.orm import *


db = Database()


def quantile(a, n):
    a.sort()
    nid = int(len(a) / 100 * n)
    return a[nid]


class Fund(db.Entity):
    id = PrimaryKey(int, auto=True)
    code = Required(str, unique=True)
    name = Required(str, nullable=True)
    fund_prices = Set('FundPrice')
    matched_index = Required('Index')


class BusinessDate(db.Entity):
    id = PrimaryKey(int, auto=True)
    date_rank = Required(int, unique=True)
    biz_date = Required(date)
    fund_prices = Set('FundPrice')
    index_values = Set('IndexValue')


class Index(db.Entity):
    id = PrimaryKey(int, auto=True)
    code = Required(str, unique=True)
    name = Required(str, nullable=True)
    related_funds = Set(Fund)
    index_values = Set('IndexValue')


class IndexValue(db.Entity):
    id = PrimaryKey(int, auto=True)
    biz_date = Required(BusinessDate)
    index = Required(Index)
    value = Required(int)  # Real index value * 10000

    def x_days_percentile_low(self, ndays, percentage):
        """The percentile index value between x days ago and today."""
        if self.biz_date.id <= ndays:
            return
        start_date = BusinessDate[self.biz_date.id-ndays]
        index_values = IndexValue.select(lambda iv: iv.index == self.index and start_date.id-1 < iv.biz_date.id and iv.biz_date.id < self.biz_date.id)
        value_list = [index_value.value for index_value in index_values]
        return quantile(value_list, percentage)

    def index_buy_signal(self, ndays, percentage):
        comp_value = self.x_days_percentile_low(ndays, percentage)
        if comp_value:
            return self.value < comp_value
        else:
            return False

    def index_sell_signal(self, ndays, percentage):
        comp_value = self.x_days_percentile_low(ndays, percentage)
        if comp_value:
            return self.value > comp_value
        else:
            return False


class FundPrice(db.Entity):
    id = PrimaryKey(int, auto=True)
    biz_date = Required(BusinessDate)
    fund = Required(Fund)
    nav = Required(int)  # Real NAV * 100
    actions = Set('Action')
    action_assumptions = Set('ActionAssumption')

    @property
    def index_value_object(self):
        return IndexValue.get(biz_date=self.biz_date, index=self.fund.matched_index)

    @property
    def has_action(self):
        return not self.actions.is_empty()

    @property
    def last_sell_date(self):
        if len(Action.select(lambda a: a.action_type.id == 2)) == 0:
            return
        action = list(Action.select(lambda a: a.action_type.id == 2).order_by(lambda a: desc(a.fund_price.biz_date.id)))[0]
        return action.fund_price.biz_date

    @property
    def last_buy_date(self):
        if len(Action.select(lambda a: a.action_type.id == 1)) == 0:
            return
        action = list(Action.select(lambda a: a.action_type.id == 1).order_by(lambda a: desc(a.fund_price.biz_date.id)))[0]
        return action.fund_price.biz_date

    @property
    def higher_than_110_last_sell(self):
        index_comp = IndexValue.get(index=self.fund.matched_index, biz_date=self.last_sell_date)
        return self.index_value_object.value > 1.1 * index_comp.value

    def buy_signal(self, days_gap, ndays, percentage):
        if not self.index_value_object.index_buy_signal(ndays, percentage):
            return False
        start_date_id = self.biz_date.id - days_gap
        end_date_id = self.biz_date.id - 1
        actions = Action.select(lambda a: start_date_id <= a.fund_price.biz_date.id and a.fund_price.biz_date.id <= end_date_id and a.action_type.id == 1)
        return len(actions) == 0

    def sell_signal(self, ndays, percentage):
        if not self.index_value_object.index_sell_signal(ndays, 100 - percentage):
            return False
        if self.last_sell_date is None:
            return True
        elif self.last_sell_date > self.last_buy_date:
            return self.higher_than_110_last_sell
        else:
            return True

    @property
    def assumed_last_sell_date(self):
        if len(ActionAssumption.select(lambda a: a.action_type.id == 2)) == 0:
            return
        action = list(ActionAssumption.select(lambda a: a.action_type.id == 2).order_by(lambda a: desc(a.fund_price.biz_date.id)))[0]
        return action.fund_price.biz_date

    @property
    def assumed_last_buy_date(self):
        if len(ActionAssumption.select(lambda a: a.action_type.id == 1)) == 0:
            return
        action = list(ActionAssumption.select(lambda a: a.action_type.id == 1).order_by(lambda a: desc(a.fund_price.biz_date.id)))[0]
        return action.fund_price.biz_date

    @property
    def assumed_higher_than_110_last_sell(self):
        index_comp = IndexValue.get(index=self.fund.matched_index, biz_date=self.assumed_last_sell_date)
        return self.index_value_object.value > 1.1 * index_comp.value

    def assumed_buy_signal(self, days_gap, ndays, percentage):
        if not self.index_value_object.index_buy_signal(ndays, percentage):
            return False
        start_date_id = self.biz_date.id - days_gap
        end_date_id = self.biz_date.id - 1
        actions = ActionAssumption.select(lambda a: start_date_id <= a.fund_price.biz_date.id and a.fund_price.biz_date.id <= end_date_id and a.action_type.id == 1)
        return len(actions) == 0

    def assumed_sell_signal(self, ndays, percentage):
        if not self.index_value_object.index_sell_signal(ndays, 100 - percentage):
            return False
        if self.assumed_last_sell_date is None:
            return True
        elif self.assumed_last_sell_date > self.assumed_last_buy_date:
            return self.assumed_higher_than_110_last_sell
        else:
            return True


class Action(db.Entity):
    id = PrimaryKey(int, auto=True)
    action_type = Required('ActionType')
    fund_price = Required(FundPrice)
    amount = Required(int)  # Real Amount * 100
    total_value = Required(int)  # Real value * 100

    @property
    def unit_price(self):
        return self.fund_price.nav


class ActionType(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    actions = Set(Action)
    action_assumptions = Set('ActionAssumption')


class ActionAssumption(db.Entity):
    id = PrimaryKey(int, auto=True)
    action_type = Required(ActionType)
    fund_price = Required(FundPrice)
    amount = Required(int)  # Real Amount * 100
    total_value = Required(int)  # Real value * 100


class UserSettings(db.Entity):
    name = PrimaryKey(str)
    value = Required(int)


db.bind(provider='sqlite', filename='fundtracking.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
