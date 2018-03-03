# morningstar_descriptors

The package provides functions enabling the downloading of financial descriptors data from the Morningstar repository.

## Dependencies

* pandas
* wikitables
* requests

## Installation

`git clone https://github.com/morningstar_descriptors`
`cd morningstar_descriptors`
`pip install .`

## Usage

Call the function `get_financial_descriptors` with a list of tickers to download their descriptors:
`get_financial_descriptors(['MMM', 'GOOG'])`

Call `get_djia_descriptors` to download the data for all DJIA tickers:
`get_djia_descriptors()`

Call `get_sp500_descriptors` to download the data for all S&P500 tickers:
`get_sp500_descriptors()`

## Contact

If you have any comments, suggestions or updates, feel free to fork, pull, or contact me!
