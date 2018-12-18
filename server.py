#!/usr/bin/env python3

from aiohttp import web

import vyper
from vyper.compiler import compile_code
from vyper.exceptions import ParserException


routes = web.RouteTableDef()
headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "X-Requested-With, Content-type"
}


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
            out_dict = compile_code(code, ['abi', 'bytecode', 'bytecode_runtime', 'ir'])
            out_dict['ir'] = str(out_dict['ir'])
        except ParserException as e:
            return {
                'status': 'failed',
                'message': str(e),
                'column': e.col_offset,
                'line': e.lineno
            }, 400
        except SyntaxError as e:
            return {
                'status': 'failed',
                'message': str(e),
                'column': e.offset,
                'line': e.lineno
            }, 400

        out_dict.update({'status': "success"})

        return out_dict, 200


@routes.route('OPTIONS', '/compile')
async def compile_it_options(request):
    return web.json_response(status=200, headers=headers)


@routes.post('/compile')
async def compile_it(request):
    json = await request.json()
    out, status = _compile(json)
    return web.json_response(out, status=status, headers=headers)


app = web.Application()
app.add_routes(routes)
web.run_app(app)
