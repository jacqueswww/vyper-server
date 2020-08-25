#!/usr/bin/env python3
import logging
from aiohttp import web

import vyper
from vyper.compiler import compile_code
from vyper.exceptions import VyperException

from concurrent.futures import ThreadPoolExecutor


routes = web.RouteTableDef()
headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "X-Requested-With, Content-type"
}
executor_pool = ThreadPoolExecutor(max_workers=4)


@routes.get('/')
async def handle(request):
    return web.Response(text='Vyper Compiler. Version: {} \n'.format(vyper.__version__))


def _compile(data):
        code = data.get('code')
        if not code:
            return {'status': 'failed', 'message': 'No "code" key supplied'}, 400
        if not isinstance(code, str):
            return {'status': 'failed', 'message': '"code" must be a non-empty string'}, 400

        try:
            out_dict = compile_code(code, ['abi', 'bytecode', 'bytecode_runtime', 'ir', 'method_identifiers'])
            out_dict['ir'] = str(out_dict['ir'])
        except VyperException as e:
            if e.col_offset and e.lineno:
                col_offset, lineno = e.col_offset, e.lineno
            elif e.annotations and len(e.annotations) > 0:
                ann = e.annotations[0]
                col_offset, lineno = ann.col_offset, ann.lineno
            else:
                col_offset, lineno = None, None
            return {
                'status': 'failed',
                'message': str(e),
                'column': col_offset,
                'line': lineno
            }, 400

        out_dict.update({'status': "success"})

        return out_dict, 200

@routes.route('OPTIONS', '/compile')
async def compile_it_options(request):
    return web.json_response(status=200, headers=headers)


@routes.post('/compile')
async def compile_it(request):
    json = await request.json()
    out, status = await request.loop.run_in_executor(executor_pool, _compile, json)
    return web.json_response(out, status=status, headers=headers)


app = web.Application()
app.add_routes(routes)
logging.basicConfig(level=logging.DEBUG)
web.run_app(app)
