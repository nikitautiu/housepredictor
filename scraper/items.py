import scrapy


class FundaItem(scrapy.Item):
    list = scrapy.Field()  # the listing on the page view
    detail = scrapy.Field()  # the detail page
