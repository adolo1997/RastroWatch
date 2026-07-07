from .apify_base import ApifySource


class ApifyMilanunciosSource(ApifySource):
    name = "Milanuncios Apify"
    actor_setting = "apify_milanuncios_actor_id"
