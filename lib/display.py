from datetime import date
import time

import numpy as np
import matplotlib.pyplot as plt

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
	for key, val, names in lst:
		if key not in agg: agg[key] = [0, set()]
		agg[key][0] += val
		agg[key][1] |= names
	return agg

class Calculation:
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
			return avg([sum(vals) for vals in history.values()])
		
		for t in self.table.filtered(from_date=date(year, 1, 1)):
			months.setdefault(t.date().month, []).append(t.val())

		predictions = {}
		for m in range(1, 13):
			if not months.get(m):
				predictions[m] = predict(m)
		
		return months, predictions

class Plain(Calculation):
	ALIGN_RIGHT='>'
	ALIGN_LEFT='<'
	ALIGN_CENTER='^'
	
	def _row(self, row, cell_widths, align=ALIGN_RIGHT):
		print('|', end='')
		for i, cell in enumerate(row):
			print((' {:' + align + str(cell_widths[i]) + '} ').format(cell), end='')
			print('|', end='')
		print('')

	def _hline(self, w):
		print('*' + '-' * (w - 2) + '*')

	def _money(self, val):
		return '{:.2f}'.format(val) if val else '?'

	def _title(self, title, width):
		print('#' * (int((width-len(title))/2) - 1), end='')
		print(' {} '.format(title), end='')
		print('#' * (int((width-len(title))/2) - 1), end='')
		print('#' if width%2==0 else '', end='\n')
	
	def _table(self, title, header, rows):
		cells = len(header)
		cell_widths = [
			max(len(str(row[i])) for row in rows + [header]) for i in range(cells)
		]
		width = sum(cell_widths) + (3*cells +1)

		self._title(title, width)
		self._hline(width)
		self._row(header, cell_widths, align=Plain.ALIGN_CENTER)
		self._hline(width)
		for row in rows:
			self._row(row, cell_widths)
		self._hline(width)

	def project_year(self, year, months_ago=None):
		months, predictions = super().project_year(year, months_ago=months_ago)
		
		rows = []
		prev = 0
		planned_expenses = aggregate_tuples(
			(int(val['date'].split('-')[1]), float(val['value']), set(val['tags']))
			for val in self.config.plans['expenses']
		)
		planned_income = aggregate_tuples(
			(int(val['date'].split('-')[1]), float(val['value']), set(val['tags']))
			for val in self.config.plans['income']
		)
		for m in range(1, 13):
			values = months.get(m)
			planned_pos_m = planned_income.get(m, [0, []])
			planned_neg_m = planned_expenses.get(m, [0, []])
			planned = planned_pos_m[0] - planned_neg_m[0]
			planned_desc = list(
				map(lambda name: '+' + name, planned_pos_m[1])
			) + list(
				map(lambda name: '-' + name, planned_neg_m[1])
			)

			if values:
				overall = prev + sum(values) + planned
				row = (m, overall, sum(positive(values)), sum(negative(values)),
					   planned, planned_desc)
			else:
				overall = prev + predictions[m] + planned
				row = (m, overall, None, None,
					   planned, planned_desc)
			
			rows.append(row)
			prev = overall

		header = ['Date', 'Balance', 'Income', 'Expenses', 'Planned', 'Desc.']
		self._table('Yearly projection', header, [
			('{}-{:02}'.format(year, r[0]),
			 self._money(r[1]), self._money(r[2]), self._money(r[3]), self._money(r[4]),
			 ', '.join(r[5]))
			for r in rows
		])

class Plot(Calculation):
	def project_year(self, year, months_ago=None):
		months, predictions = super().project_year(year, months_ago=months_ago)

		x = np.arange(1, 13)
		y = []
		planned_expenses = aggregate_tuples(
			(int(val['date'].split('-')[1]), float(val['value']))
			for val in self.config.plans['expenses']
		)
		planned_income = aggregate_tuples(
			(int(val['date'].split('-')[1]), float(val['value']))
			for val in self.config.plans['income']
		)
		prev = 0
		for m in range(1, 13):
			values = months.get(m)
			planned = planned_income.get(m, 0) - planned_expenses.get(m, 0)
			if values:
				overall = prev + sum(values) + planned
			else:
				overall = prev + predictions[m] + planned
			
			y.append(overall)
			prev = overall

		y = np.array(y)
		
		plt.plot(x, y)
		plt.show()
		
