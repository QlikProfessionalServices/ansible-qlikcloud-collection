#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
from qlik_sdk import AuthType, Config, Qlik

def asdict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = asdict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return asdict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [asdict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, asdict(value, classkey)) 
            for key, value in obj.__dict__.items() 
            if not callable(value) and not key.startswith('_') and key != 'auth'])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def construct_state_from_params(module_params: dict, ignore_params=[]):
    '''Returns true if existing space is different to module params, otherwise false'''
    state = {}
    ignore_params += ['state', 'tenant_uri', 'api_key']
    for k, v in module_params.items():
        if k in ignore_params:
            continue
        state[to_camel_case(k)] = v

    return state

def get_client(module: AnsibleModule, Client=Qlik) -> Qlik:
    client = Client(Config(
        host=module.params['tenant_uri'],
        auth_type=AuthType.APIKey,
        api_key=module.params['api_key']))

    def log_req(req):
        module.log("request: %s %s" % (req.method, req.url))
        return req

    def log_res(res):
        module.log("response: %s %s -> %s" % (
            res.request.method,
            res.request.url,
            res.status_code))
        return res

    client.auth.rest.interceptors["response"].use(log_res)
    client.auth.rest.interceptors["request"].use(log_req)

    return client
