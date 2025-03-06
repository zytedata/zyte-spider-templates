from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import pytest
import pytest_twisted
from aiohttp.test_utils import TestServer

if TYPE_CHECKING:
    from aiohttp.web import Application


@pytest.fixture(scope="session")
def mockserver():
    from .mockserver import MockServer

    with MockServer() as server:
        yield server


# copied verbatim from pytest-aiohttp
@pytest_twisted.async_yield_fixture(scope="module")
async def aiohttp_server():
    """Factory to create a TestServer instance, given an app.

    aiohttp_server(app, **kwargs)
    """
    servers = []

    async def go(
        app: Application,
        *,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        **kwargs: Any,
    ) -> TestServer:
        server = TestServer(app, host=host, port=port)
        await server.start_server(**kwargs)
        servers.append(server)
        return server

    yield go

    while servers:
        await servers.pop().close()


@pytest_twisted.async_fixture(scope="module")
async def zyte_api_server(aiohttp_server):
    from fake_zyte_api.main import make_app

    app = make_app()
    return await aiohttp_server(app)
