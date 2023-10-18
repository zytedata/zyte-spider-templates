from zyte_common_items import ProbabilityRequest, ProductNavigation, Request


def format_request(request: Request) -> str:
    name = (request.name or "").strip()
    if isinstance(request, ProbabilityRequest) and request.metadata:
        probability = request.metadata.probability
        return f"- ({probability=:.2%}) {name}, {request.url}"

    return f"- {name}, {request.url}"


def product_navigation_report(navigation: ProductNavigation) -> str:
    report = [f"[page: category] {navigation.url}"]

    subcategories = navigation.subCategories or []
    items = navigation.items or []

    if navigation.nextPage:
        report.append("1 next page link:")
        report.append(format_request(navigation.nextPage))
    else:
        report.append("NO next page link.")

    report.append(f"{len(subcategories)} subcategory links:")
    for request in subcategories:
        report.append(format_request(request))

    report.append(f"{len(items)} item links:")
    for request in items:
        report.append(format_request(request))

    return "\n".join(report)
