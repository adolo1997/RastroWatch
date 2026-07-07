from ...config import settings
from .apify_base import ApifySource


class ApifyWallapopSource(ApifySource):
    name = "Wallapop Apify"
    actor_setting = "apify_wallapop_actor_id"
