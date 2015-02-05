import json
import re
import datetime

class Config:
	EXCEPTION_MODE_IGNORE = 'ignore'
	EXCEPTION_MODE_HIDE = 'hide'
	EXCEPTION_MODES = (EXCEPTION_MODE_IGNORE, EXCEPTION_MODE_HIDE, )

	TEMPLATE_PLAN = lambda: { 'tags': [], 'value': 0, 'date': None}
	TEMPLATE_EXCEPTION = lambda: { 'tag': '', 'mode': None }

	ARG_OPTIONS = {
		'is_plain': '--plain',
		'exception_mode': 'EX_MODE'
	}
	
	def __init__(self, config, arguments={}):
		self.plans = {
			'income': [],
			'expenses': [],
		}
		self.exceptions = {
			'income': [],
			'expenses': [],
		}
		self.exception_mode = 'ignore'
		self.savings = {
			'income': [], # which tags come from savings
			'expenses': [], # which tags are transactions to savings
		}
		
		self.is_plain = arguments.get('display_mode')
		
		self.__dict__.update({
			dict: lambda c: c,
			str: lambda c: json.load(open(c)),
		}[type(config)](config))

		for ex_type, values in self.exceptions.items():
			new_vals = []
			for val in values[:]:
				if type(val) == str:
					new_val = Config.TEMPLATE_EXCEPTION()
					new_val['tag'] = val
					new_vals.append(new_val)
				else:
					new_vals.append(val)
			self.exceptions[ex_type] = new_vals

		for opt, key in Config.ARG_OPTIONS.items():
			val = arguments.get(key)
			if val:
				self.__dict__[opt] = val

	def __str__(self):
		return 'Config({})'.format(str(self.__dict__))

	def ignored_tags(self, group):
		return set(
			obj['tag'] for obj in self.exceptions[group]
			if Config.EXCEPTION_MODE_IGNORE in (obj['mode'], self.exception_mode, )
		)

	def hidden_tags(self, group):
		return set(
			obj['tag'] for obj in self.exceptions[group]
			if Config.EXCEPTION_MODE_HIDE in (obj['mode'], self.exception_mode, )
		)
		
	def dumps(self):
		return json.dumps(self.__dict__)

class Transaction(dict):
	FIELD_DATE = 'Date'
	FIELD_ENTRY = 'Entry (tags)'
	FIELD_EXPENSE = 'Expense amount'
	FIELD_INCOME = 'Income amount'
	FIELD_CURRENCY = 'Currency'
	FIELD_DESCRIPTION = 'Description'

	FIELDS = (
		FIELD_DATE,
		FIELD_ENTRY,
	)
	
	CONVERTER = {
		FIELD_DATE: lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(),
		FIELD_ENTRY: lambda x: set(re.split(r', *', x)),
		FIELD_EXPENSE: lambda x: float(x) if x else 0.,
		FIELD_INCOME: lambda x: float(x) if x else 0.,
		FIELD_CURRENCY: lambda x: x,
		FIELD_DESCRIPTION: lambda x: x
	}
	
	def val(self):
		raise NotImplementedError()

	def date(self):
		return self[Transaction.FIELD_DATE]

	def entry(self):
		return self[Transaction.FIELD_ENTRY]
	
	@staticmethod
	def convert(key, val):
		pass
	
	@staticmethod
	def prepare(mapper, row, fields):
		return {
			mapper[i]: Transaction.CONVERTER[mapper[i]](val)
			for i, val in enumerate(row) if mapper[i] in fields
		}

	@staticmethod
	def create(header, row):
		mapper = dict(enumerate(header))
		for i, val in enumerate(row):
			if not val and mapper[i] == Transaction.FIELD_INCOME:
				return Expense(Transaction.prepare(mapper, row, Expense.FIELDS))
			elif not val and mapper[i] == Transaction.FIELD_EXPENSE:
				return Income(Transaction.prepare(mapper, row, Income.FIELDS))
		return None
		

class Income(Transaction):
	FIELDS = Transaction.FIELDS + (
		Transaction.FIELD_INCOME,
	)

	def val(self):
		return self[Transaction.FIELD_INCOME]

	def __str__(self):
		return 'Income: {} ({})'.format(', '.join(Transaction.FIELD_ENTRY), self.val())


class Expense(Transaction):
	FIELDS = Transaction.FIELDS + (
		Transaction.FIELD_EXPENSE,
	)

	def val(self):
		return -self[Transaction.FIELD_EXPENSE]

	def __str__(self):
		return 'Expense: {} ({})'.format(', '.join(Transaction.FIELD_ENTRY), self.val())

class Table(list):
	def __init__(self, *args, config=None):
		super().__init__(*args)
		self.start, self.stop = None, None
		self.config = config

		self.hidden_expenses_tags = self.config.hidden_tags('expenses')
		self.hidden_income_tags = self.config.hidden_tags('income')

		self.ignored_expenses_tags = self.config.ignored_tags('expenses')
		self.ignored_income_tags = self.config.ignored_tags('income')

	def is_valid(self, obj):
		if type(obj) == Income and obj.entry() & self.hidden_income_tags:
			return False
		if type(obj) == Expense and obj.entry() & self.hidden_expenses_tags:
			return False
		return True
	
	def append(self, obj):
		if not self.is_valid(obj):
			return
		self.start = self.start and min(self.start, obj.date()) or obj.date()
		self.stop = self.stop and max(self.stop, obj.date()) or obj.date()
		super().append(obj)
	
	def add_row(self, header, row):
		self.append(Transaction.create(header, row))

	def filtered(self, vals_only=False, from_date=None, till_date=None):
		def in_range(t):
			valid = True
			if from_date:
				valid = valid and t.date() >= from_date
			if till_date:
				valid = valid and t.date() < till_date
			return valid
		return [
			t.val() if vals_only else t for t in self if in_range(t)
		]
		
	def filtered_no_ignored(self, vals_only=False, from_date=None, till_date=None,
							ignore_savings=False):
		def in_range(t):
			valid = True
			if from_date:
				valid = valid and t.date() >= from_date
			if till_date:
				valid = valid and t.date() < till_date
			return valid
		return [
			t.val() if vals_only else t for t in self
			if in_range(t) and ((type(t) == Income
								 and not (t.entry() & self.ignored_income_tags)
								 and not (t.entry() & set(self.config.savings['income'])))
								or (type(t) == Expense
									and	(not t.entry() & self.ignored_expenses_tags)
									and (not t.entry() & set(self.config.savings['expenses']))))
		]
		
	def income(self, vals_only=False, filtered=False):
		return [
			t.val() if vals_only else t for t in self
			if type(t) == Income and (not filtered or t.entry() & self.ignored_income_tags)
		]
	def expenses(self, vals_only=False, filtered=False):
		return [
			t.val() if vals_only else t for t in self
			if type(t) == Expense and (not filtered or t.entry() & self.ignored_expenses_tags)
		]


	def __str__(self):
		return 'Table(start={}, stop={}, rows={})'.format(
			self.start and self.start.isoformat() or '-Inf',
			self.stop and self.stop.isoformat() or '+Inf',
			len(self)
		)
