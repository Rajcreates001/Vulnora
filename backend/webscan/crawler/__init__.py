"""Web crawler for URL scan — discovers pages, forms, inputs, API endpoints."""

from webscan.crawler.crawler import crawl_url, CrawlResult

__all__ = ["crawl_url", "CrawlResult"]
