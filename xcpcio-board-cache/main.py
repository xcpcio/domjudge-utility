import asyncio
from aiohttp import web, ClientSession
import os
import logging
from typing import Dict

from common import utils

logger = logging.getLogger(__name__)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))
ORIGIN_DOMAIN = os.getenv('ORIGIN_DOMAIN')

cache_map: Dict[str, str] = {}


async def fetch_data(path: str, query: Dict[str, str]) -> str:
    async with ClientSession() as session:
        url = f'{ORIGIN_DOMAIN}/{path}'
        async with session.get(url, params=query) as response:
            if response.status == 200:
                return await response.text()
            else:
                raise web.HTTPException(status=response.status)


async def async_update_cache(path: str, query: Dict[str, str]):
    try:
        data = await fetch_data(path, query)
        cache_map[path] = data
        logger.info(f'Update cache for {path}')
    except Exception as e:
        logger.error(f'Failed to update cache for {path}: {e}')


async def hello(request: web.Request):
    return web.Response(text="Hello, World!")


async def cache(request: web.Request):
    path = request.path
    query = request.query
    logger.info(f'Cache request for {path}')

    if path in cache_map:
        asyncio.create_task(async_update_cache(path, query))
        return web.Response(text=cache_map[path])
    else:
        data = await fetch_data(path, query)
        cache_map[path] = data
        return web.Response(text=data)


async def init_app():
    app = web.Application()
    app.router.add_get('/hello', hello)
    app.router.add_get('/{path:.*}', cache)
    return app


def main():
    utils.init_logging()
    app = init_app()
    web.run_app(asyncio.run(app), host=HOST, port=PORT)


if __name__ == '__main__':
    main()
