import scrapy


class FundaItem(scrapy.Item):
    id = scrapy.Field()
    type = scrapy.Field()
    data = scrapy.Field()  # the detail page
