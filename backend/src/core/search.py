from opensearchpy import OpenSearch

from src.configurations.settings import settings

opensearch_client = OpenSearch(
    hosts=[{"host": settings.OPENSEARCH_HOST, "port": settings.OPENSEARCH_PORT}],
    http_compress=True,  # enables gzip compression for request bodies
    # http_auth=(settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD),
    # use_ssl=True,
    # verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)
