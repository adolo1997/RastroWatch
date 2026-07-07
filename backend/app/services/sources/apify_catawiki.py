from .apify_base import ApifySource


class ApifyCatawikiSource(ApifySource):
    name = "Catawiki Apify"
    actor_setting = "apify_catawiki_actor_id"
