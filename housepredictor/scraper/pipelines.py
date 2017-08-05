from extractor import sanitize_record


class ExtractionPipeline(object):
    """Pipeline that sanitizes the items
    if the `sanitize` flag is set in the spider."""

    def open_spider(self, spider):
        self.sanitize = spider.sanitize  # check the flag's state

    def process_item(self, item, spider):
        # sanititze or no depending on the flag
        if not self.sanitize:
            return item
        return sanitize_record(item)
