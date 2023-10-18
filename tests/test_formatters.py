from zyte_common_items import ProductNavigation

from zyte_spider_templates.formatters import product_navigation_report


def test_product_navigation_report():
    data = {
        "url": "https://example.com/category/tech",
        "nextPage": {
            "url": "https://example.com/category/tech?p=2",
            "name": "Category Page 2",
        },
        "subCategories": [
            {
                "url": "https://example.com/category/tech/C1",
                "name": "C1",
                "metadata": {"probability": 0.998765},
            },
            {
                "url": "https://example.com/category/tech/C2",
                "name": "C2",
                "metadata": {"probability": 0.998765},
            },
        ],
        "items": [
            {
                "url": "https://example.com/products?id=1",
                "name": "P1",
                "metadata": {"probability": 0.998765},
            },
            {
                "url": "https://example.com/products?id=2",
                "name": "P2",
                "metadata": {"probability": 0.998765},
            },
            {
                "url": "https://example.com/products?id=3",
                "name": "P3",
                "metadata": {"probability": 0.998765},
            },
        ],
    }
    nav = ProductNavigation.from_dict(data)
    assert product_navigation_report(nav) == (
        "[page: category] https://example.com/category/tech\n"
        "1 next page link:\n"
        "- Category Page 2, https://example.com/category/tech?p=2\n"
        "2 subcategory links:\n"
        "- (probability=99.88%) C1, https://example.com/category/tech/C1\n"
        "- (probability=99.88%) C2, https://example.com/category/tech/C2\n"
        "3 item links:\n"
        "- (probability=99.88%) P1, https://example.com/products?id=1\n"
        "- (probability=99.88%) P2, https://example.com/products?id=2\n"
        "- (probability=99.88%) P3, https://example.com/products?id=3"
    )

    del data["nextPage"]
    nav = ProductNavigation.from_dict(data)
    assert product_navigation_report(nav) == (
        "[page: category] https://example.com/category/tech\n"
        "NO next page link.\n"
        "2 subcategory links:\n"
        "- (probability=99.88%) C1, https://example.com/category/tech/C1\n"
        "- (probability=99.88%) C2, https://example.com/category/tech/C2\n"
        "3 item links:\n"
        "- (probability=99.88%) P1, https://example.com/products?id=1\n"
        "- (probability=99.88%) P2, https://example.com/products?id=2\n"
        "- (probability=99.88%) P3, https://example.com/products?id=3"
    )

    del data["subCategories"]
    nav = ProductNavigation.from_dict(data)
    assert product_navigation_report(nav) == (
        "[page: category] https://example.com/category/tech\n"
        "NO next page link.\n"
        "0 subcategory links:\n"
        "3 item links:\n"
        "- (probability=99.88%) P1, https://example.com/products?id=1\n"
        "- (probability=99.88%) P2, https://example.com/products?id=2\n"
        "- (probability=99.88%) P3, https://example.com/products?id=3"
    )

    del data["items"]
    nav = ProductNavigation.from_dict(data)
    assert product_navigation_report(nav) == (
        "[page: category] https://example.com/category/tech\n"
        "NO next page link.\n"
        "0 subcategory links:\n"
        "0 item links:"
    )
