from .apify_catawiki import ApifyCatawikiSource
from .apify_milanuncios import ApifyMilanunciosSource
from .apify_wallapop import ApifyWallapopSource
from .ebay import EbaySource
from .thewatchapi import TheWatchApiSource
from .watchcharts import WatchChartsSource


def all_sources():
    return [EbaySource(), TheWatchApiSource(), WatchChartsSource(), ApifyWallapopSource(), ApifyMilanunciosSource(), ApifyCatawikiSource()]
