from datetime import date
import time

def date_months_ago(n):
	now = time.localtime()
	y, m = time.localtime(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0)))[:2]
	return date(y, m, 1)

def avg(lst):
	return sum(lst) / len(lst)

def positive(lst):
	return [x for x in lst if x > 0]

def negative(lst):
	return [x for x in lst if x < 0]

def aggregate_tuples(lst):
	agg = {}
	for key, val in lst:
		if key not in agg: agg[key] = 0
		agg[key] += val
	return agg

class Display:
	def __init__(self, config, table):
		self.config = config
		self.table = table

	def project_year(self, year, months_ago=None):
		months = {}

		start_date = date_months_ago(months_ago) if months_ago else date(year, 1, 1)
		
		def predict(month):
			history = {}
			for t in self.table.filtered_no_ignored(from_date=start_date,
													till_date=date(year, month, 1),
													ignore_savings=True):
				history.setdefault(t.date().month, []).append(t.val())
			return avg([sum(vals) for vals in history.values()] or [float('inf')])
		
		for t in self.table.filtered(from_date=date(year, 1, 1)):
			months.setdefault(t.date().month, []).append(t.val())

		predictions = {}
		for m in range(1, 13):
			if not months.get(m):
				predictions[m] = predict(m)
		
		return months, predictions

class Plain(Display):
	def _row(self, row, cell_widths):
		print('|', end='')
		for i, cell in enumerate(row):
			print((' {:' + str(cell_widths[i]) + '} ').format(cell), end='')
			print('|', end='')
		print('')

	def _hline(self, w):
		print('*' + '-' * (w - 2) + '*')

	def _money(self, val):
		return '{:.2f}'.format(val) if val else '?'
		
	def _table(self, header, rows):
		cells = len(header)
		cell_widths = [
			max(len(str(row[i])) for row in rows + [header]) for i in range(cells)
		]
		width = sum(cell_widths) + (3*cells +1)
		self._hline(width)
		self._row(header, cell_widths)
		self._hline(width)
		for row in rows:
			self._row(row, cell_widths)
		self._hline(width)

	def project_year(self, year, months_ago=None):
		months, predictions = super().project_year(year, months_ago=months_ago)
		
		rows = []
		prev = 0
		planned_expenses = aggregate_tuples(
			(int(val['date'].split('-')[1]), float(val['value']))
			for val in self.config.plans['expenses']
		)
		planned_income = aggregate_tuples(
			(int(val['date'].split('-')[1]), float(val['value']))
			for val in self.config.plans['income']
		)
		for m in range(1, 13):
			values = months.get(m)
			planned = planned_income.get(m, 0) - planned_expenses.get(m, 0)
			if values:
				overall = prev + sum(values) + planned
				row = (m, overall, sum(positive(values)), sum(negative(values)), planned)
			else:
				overall = prev + predictions[m] + planned
				row = (m, overall, None, None, planned)
			
			rows.append(row)
			prev = overall

		
		print('Year projection')
		
		self._table(['Date', 'Balance', 'Income', 'Expenses', 'Planned'], [
			('{}-{:02}'.format(year, r[0]),
			 self._money(r[1]), self._money(r[2]), self._money(r[3]), self._money(r[4]), )
			for r in rows
		])

class Plot(Display):
	pass
