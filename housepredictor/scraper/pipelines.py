from extractor import sanitize_record


class ExtractionPipeline(object):
    """Pipeline that lets only the required data to go through,
    if the --all flag is"""

    collection_name = 'scrapy_items'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.sanitize = spider.sanitize  # check the flag's state

    def process_item(self, item, spider):
        # sanititze or no depending on the flag
        if not self.sanitize:
            return item
        return sanitize_record(item)
