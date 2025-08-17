class ScraperError(Exception):
    """Generic scraping/repository error."""


class DataNotFoundError(Exception):
    """Raised when expected data is missing/empty."""
