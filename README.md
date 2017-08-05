# housepredictor
House prediction app for Funda

## Running the scraper
To run the scraper, simply install the dependencies from `requirements.txt` and run `funda-scraper.sh`. For more info on the script, call it with `--help`. The scraper defaults to CSV, and the area of search defaults to *heel-nederland* as in
[http://www.funda.nl/koop/**heel-nederland**](http://www.funda.nl/koop/heel-nederland). You can check the search urls and restrict crawling to specific areas of the Netherlands as well.

### Important note
The `funda.nl` API is throttled to 100 requests/min. If you wish to scrape all the listings on the site, it might take more than 24 hours!
