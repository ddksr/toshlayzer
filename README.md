# toshlayzer
Analyze toshl csv dumps

Examples:

	$ ./toshlayzer predict 2015 5 --plain --income=1800 --expenses=1000 toshl_example.csv

	####################### Yearly projection ########################
	*----------------------------------------------------------------*
	|  Date   | Balance | Income  | Expenses | Planned  |   Desc.    |
	*----------------------------------------------------------------*
	| 2015-01 |  568.78 | 2371.99 | -1803.21 |        ? |            |
	| 2015-02 |  685.68 |  300.00 |  -183.10 |        ? |            |
	| 2015-03 | 1485.68 |       ? |        ? |        ? |            |
	| 2015-04 | 1985.68 |       ? |        ? |  -300.00 |    -travel |
	| 2015-05 | 1785.68 |       ? |        ? | -1000.00 | -car, -tax |
	| 2015-06 | 2085.68 |       ? |        ? |  -500.00 |    -travel |
	| 2015-07 | 2885.68 |       ? |        ? |        ? |            |
	| 2015-08 | 1685.68 |       ? |        ? | -2000.00 |    -travel |
	| 2015-09 | 2485.68 |       ? |        ? |        ? |            |
	| 2015-10 | 3285.68 |       ? |        ? |        ? |            |
	| 2015-11 | 3585.68 |       ? |        ? |  -500.00 |    -travel |
	| 2015-12 | 4385.68 |       ? |        ? |        ? |            |
	*----------------------------------------------------------------*

# Configuration
Can also be overwritten with command line arguments.

Example:

	{
		"plans": {
			"income": [
	
			],
			"expenses": [
				{ "tags": ["tax"], "date": "2015-05-01", "value": 500 },
				{ "tags": ["car"], "date": "2015-05-01", "value": 500 },
				{ "tags": ["travel"], "date": "2015-04-01", "value": 300 },
				{ "tags": ["travel"], "date": "2015-06-01", "value": 500 },
				{ "tags": ["travel"], "date": "2015-08-01", "value": 2000 },
				{ "tags": ["travel"], "date": "2015-11-01", "value": 500 }
			]
		},
		"exceptions": {
			"income": [
				"returns"
			],
			"expenses": [
				"lending",
				{ "tag": "travel", "mode": "ignore" }
			]
		},
		"savings": {
			"income": [
				"cash"
			],
			"expenses": [
				"savings"
			]
		},
		"exception_mode": "ignore"
	}

## Descriptions
- **exception_mode** / *[exception].mode* default mode for exceptions
  Values:
  - *ignore* ignore when predicting balance
  - *hide* hide from predictions and 

- **savings**
  Specify tags that describe savings transactons

- **plans**
  List income and expenses plans
