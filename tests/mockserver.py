import argparse
import json
import socket
import sys
import time
from importlib import import_module
from subprocess import PIPE, Popen
from typing import Any, Dict

from scrapy_zyte_api.responses import _API_RESPONSE
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site


def get_ephemeral_port():
    s = socket.socket()
    s.bind(("", 0))
    return s.getsockname()[1]


class DefaultResource(Resource):
    """Mock server to fake Zyte API responses.

    To use, include the mockserver fixture in the signature of your test, and
    point the ZYTE_API_URL setting to the mock server. See
    ``tests/test_ecommerce.py::test_crawl_strategies`` for an example.

    This mock server is designed to fake the following:

    -   An e-commerce website with the following pages:

        ```
        https://example.com/
        https://example.com/page/2
        https://example.com/category/1
        https://example.com/category/1/page/2
        https://example.com/non-navigation
        ```

        When browserHtml is requested (for any URL, listed above or not), it is
        a minimal HTML with an anchor tag pointing to
        https://example.com/non-navigation.

        When productNavigation is requested, nextPage and subCategories are filled
        accordingly. productNavigation.items always has 2 product URLs, which are
        the result of appending ``/product/<n>`` to the request URL.
        https://example.com/non-navigation is not reachable through
        productNavigation.

        When product or productList is requested, an item with the current URL is
        always returned.

        All output also includes unsupported links (mailto:…).

    -   Job-posting websites with the following endpoints:

        -   https://jobs.example (jobPostingNavigation pointing to the 2 items
            below).

        -   https://jobs.offsite.example/jobs/1 (jobPosting)

        -   https://jobs.offsite.example/jobs/2 (jobPosting)
    """

    def getChild(self, path, request):
        return self

    def render_POST(self, request):
        request_data = json.loads(request.content.read())
        request.responseHeaders.setRawHeaders(
            b"Content-Type",
            [b"application/json"],
        )
        request.responseHeaders.setRawHeaders(
            b"request-id",
            [b"abcd1234"],
        )

        response_data: _API_RESPONSE = {}

        response_data["url"] = request_data["url"]

        if request_data["url"] == "https://jobs.example":
            assert request_data["jobPostingNavigation"] is True
            response_data["jobPostingNavigation"] = {
                "url": request_data["url"],
                "items": [
                    {"url": "https://jobs.offsite.example/jobs/1"},
                    {"url": "https://jobs.offsite.example/jobs/2"},
                ],
            }
            return json.dumps(response_data).encode()

        if request_data["url"].startswith("https://jobs.offsite.example/"):
            assert request_data["jobPosting"] is True
            response_data["jobPosting"] = {
                "url": request_data["url"],
            }
            return json.dumps(response_data).encode()

        non_navigation_url = "https://example.com/non-navigation"
        html = f"""<html><body><a href="{non_navigation_url}"></a><a href="mailto:jane@example.com"></a></body></html>"""
        if request_data.get("browserHtml", False) is True:
            response_data["browserHtml"] = html

        if request_data.get("product", False) is True:
            response_data["product"] = {
                "url": request_data["url"],
            }

        if request_data.get("productList", False) is True:
            response_data["productList"] = {
                "url": request_data["url"],
            }

        if request_data.get("productNavigation", False) is True:
            kwargs: Dict[str, Any] = {}
            if (
                "/page/" not in request_data["url"]
                and "/non-navigation" not in request_data["url"]
            ):
                kwargs["nextPage"] = {
                    "url": f"{request_data['url'].rstrip('/')}/page/2"
                }
                if "/category/" not in request_data["url"]:
                    kwargs["subCategories"] = [
                        {"url": "mailto:jane@example.com"},
                        {"url": f"{request_data['url'].rstrip('/')}/category/1"},
                    ]
            else:
                kwargs["nextPage"] = {"url": "mailto:jane@example.com"}
            response_data["productNavigation"] = {
                "url": request_data["url"],
                "items": [
                    {"url": "mailto:jane@example.com"},
                    {"url": f"{request_data['url'].rstrip('/')}/product/1"},
                    {"url": f"{request_data['url'].rstrip('/')}/product/2"},
                ],
                **kwargs,
            }

        return json.dumps(response_data).encode()


class MockServer:
    def __init__(self, resource=None, port=None):
        resource = resource or DefaultResource
        self.resource = "{}.{}".format(resource.__module__, resource.__name__)
        self.proc = None
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = port or get_ephemeral_port()
        self.root_url = "http://%s:%d" % (self.host, self.port)

    def __enter__(self):
        self.proc = Popen(
            [
                sys.executable,
                "-u",
                "-m",
                "tests.mockserver",
                self.resource,
                "--port",
                str(self.port),
            ],
            stdout=PIPE,
        )
        assert self.proc.stdout is not None
        self.proc.stdout.readline()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert self.proc is not None
        self.proc.kill()
        self.proc.wait()
        time.sleep(0.2)

    def urljoin(self, path):
        return self.root_url + path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("resource")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    module_name, name = args.resource.rsplit(".", 1)
    sys.path.append(".")
    resource = getattr(import_module(module_name), name)()
    # Typing issue: https://github.com/twisted/twisted/issues/9909
    http_port = reactor.listenTCP(args.port, Site(resource))  # type: ignore[attr-defined]

    def print_listening():
        host = http_port.getHost()
        print(
            "Mock server {} running at http://{}:{}".format(
                resource, host.host, host.port
            )
        )

    # Typing issue: https://github.com/twisted/twisted/issues/9909
    reactor.callWhenRunning(print_listening)  # type: ignore[attr-defined]
    reactor.run()  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
