import click
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scraper.spiders.fundaspider import FundaSpider


# the type of zone defaults to string due to the fact that the default
# is a string
@click.command()
@click.option('--zone', default='heel-nederland',
              help='the zone to search for postings(defaults to all of the'
                   'Netherlands)')
@click.option('--type', default='koop', type=click.Choice(['koop', 'huur']),
              show_default=True, help='the type of postings')
@click.option('--format', default='json', show_default=True,
              type=click.Choice(['json', 'csv', 'jsonlines']),
              help='the format which to export the items in')
@click.option('--logfile', type=click.Path(), metavar='FILE',
              help='the file to log to')
@click.option('--loglevel', type=click.STRING, metavar='LEVEL',
              help='the log level')
@click.argument('output', type=click.Path(), metavar='[OUTPUT_URI]',
                default='%(time)s-items.json',
                )
def scrape(zone, type, format, output, logfile, loglevel):
    """Scrapes funda.nl api for postings of a given type and in a given
    zone. Outputs the results to OUTPUT_URI(defaults to %(time)s-items.json)"""

    #  update the settings
    settings = get_project_settings()

    # feed export settings
    settings.set('FEED_URI', output, priority='cmdline')
    settings.set('FEED_FORMAT', format, priority='cmdline')

    # logging settings
    # click passes the arguments as null if unspecified
    if logfile:
        settings.set('LOG_ENABLED', True, priority='cmdline')
        settings.set('LOG_FILE', logfile, priority='cmdline')

    if loglevel:
        settings.set('LOG_ENABLED', True, priority='cmdline')
        settings.set('LOG_LEVEL', loglevel, prioriy='cmdline')

    crawler = CrawlerProcess(settings=settings)
    crawler.crawl(FundaSpider, zone=zone, type=type)
    crawler.start()


if __name__ == '__main__':
    scrape()  # run the command
