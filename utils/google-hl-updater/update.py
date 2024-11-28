from keyword import iskeyword
from pathlib import Path

import jinja2
import requests
from parsel import Selector

languages = []

response = requests.get(
    "https://developers.google.com/custom-search/docs/json_api_reference"
)
selector = Selector(text=response.text)
table = selector.xpath(
    '//*[@id="supported-interface-languages"]/following-sibling::table[1]'
)
for tr in table.css("tr"):
    name = tr.xpath("td/text()").get()
    if not name:  # header
        continue
    code = tr.xpath("td/span/text()").get()
    keyword = f"{code}_" if iskeyword(code) else code
    keyword = keyword.replace("-", "_")
    languages.append({"code": code, "keyword": keyword, "name": name})

template_path = Path(__file__).parent / "template.py"
template_environment = jinja2.Environment()
with template_path.open() as f:
    template = template_environment.from_string(f.read())
output = template.render(languages=languages)
output_path = (
    Path(__file__).parent.parent.parent
    / "zyte_spider_templates"
    / "spiders"
    / "_google_hl.py"
)
with output_path.open("w") as f:
    f.write(output)
