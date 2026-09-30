"""模型适配器：默认不执行外部命令或网络请求。"""
import json
import os
import re
import subprocess
import urllib.request
from urllib.parse import urlparse

ADAPTERS = {'manual', 'mock', 'command', 'openai_compatible', 'anthropic', 'codex'}

def key_names(config):
    names=[config.get('api_key_env')]+config.get('api_key_aliases',[])
    # 老 DeepSeek 本地配置无需改写；不为其他提供商猜测凭据。
    if config.get('provider')=='deepseek' or urlparse(config.get('base_url') or '').hostname=='api.deepseek.com':
        names.append('ds_apikey')
    return list(dict.fromkeys(name for name in names if name))

def local_environment(path):
    values={}
    if path and os.path.isfile(path):
        with open(path,encoding='utf-8-sig') as source:
            for line in source.read().splitlines():
                if not line.strip() or line.lstrip().startswith('#'):continue
                key,sep,value=line.partition('=')
                if not sep or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key.strip()):raise ValueError('.env 格式错误；请使用 变量名=值，不显示原始内容')
                values[key.strip()]=value.strip().strip('\"\'')
    return values

def key_value(config):
    names=key_names(config)
    # 任一系统候选名均优先于本地文件，值只在调用瞬间读取，不进入配置或日志。
    for name in names:
        if os.environ.get(name):return os.environ[name]
    values=local_environment(config.get('_env_file'))
    return next((values[name] for name in names if values.get(name)),None)

def check(config, require_credentials=True):
    kind = config.get('adapter')
    if kind not in ADAPTERS:
        raise ValueError('未知 adapter')
    if not config.get('enabled', True):
        raise ValueError('角色已禁用')
    if not isinstance(config.get('timeout_seconds'), (int, float)) or config['timeout_seconds'] <= 0:
        raise ValueError('timeout_seconds 必须为正数')
    if kind == 'command':
        command = config.get('command')
        if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
            raise ValueError('command 必须是非空参数数组，不支持 shell 字符串')
    if kind in {'openai_compatible','anthropic'}:
        if not isinstance(config.get('base_url'),str):raise ValueError('base_url 必须为字符串')
        url = urlparse(config['base_url'])
        if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('base_url 必须是无凭据、无查询参数的 HTTP 地址')
        if url.scheme != 'https' and url.hostname not in ('localhost', '127.0.0.1', '::1'):
            raise ValueError('远程服务必须使用 HTTPS')
        if not isinstance(config.get('model'),str) or not config['model'].strip() or not isinstance(config.get('api_key_env'),str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',config['api_key_env']):
            raise ValueError('需要 model 与 api_key_env')
        aliases=config.get('api_key_aliases',[])
        if not isinstance(aliases,list) or any(not isinstance(name,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name) for name in aliases):
            raise ValueError('api_key_aliases 必须是合法环境变量名列表')
        if require_credentials and not key_value(config):
            raise ValueError('缺少所配置的密钥环境变量')
        options=config.get('request_options',{})
        if not isinstance(options,dict) or set(options)&{'model','messages','stream','api_key','token','password','headers','authorization','system','tools','tool_choice'}:
            raise ValueError('request_options 不得覆盖模型、消息、流式模式或认证字段')
        try:json.dumps(options,allow_nan=False)
        except (ValueError,TypeError):raise ValueError('request_options 必须是有效 JSON 参数') from None
        if 'max_tokens' in options and (not isinstance(options['max_tokens'],int) or isinstance(options['max_tokens'],bool) or options['max_tokens']<1):
            raise ValueError('max_tokens 必须为正整数')
        if kind=='openai_compatible' and (config.get('provider')=='deepseek' or url.hostname=='api.deepseek.com') and 'thinking' in options and options['thinking'] not in ({'type':'enabled'},{'type':'disabled'}):
            raise ValueError('thinking 必须包含 enabled/disabled 的 type')
        if 'reasoning_effort' in options and options['reasoning_effort'] not in ('none','minimal','low','medium','high','xhigh','max'):
            raise ValueError('reasoning_effort 不合法')
        if kind=='anthropic' and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',config.get('api_version','2023-06-01')):
            raise ValueError('api_version 必须为 YYYY-MM-DD')

def execute(config, prompt, cwd, execute_external=False):
    check(config,require_credentials=execute_external)
    kind = config['adapter']
    if kind in {'manual','codex'}:
        return 'waiting-manual', None
    if kind == 'mock':
        return 'mock', '# 占位草稿\n\n这是 mock 数据，未阅读论文，未执行复现，不能作为研究证据。\n\n路线：未知；结论：未知；来源：无。\n'
    if not execute_external:
        return 'dry-run', None
    if kind == 'command':
        command_env=dict(local_environment(config.get('_env_file')),**os.environ)
        result = subprocess.run(config['command'], input=prompt, text=True, encoding='utf-8',
                                capture_output=True, cwd=cwd, timeout=config['timeout_seconds'], shell=False,env=command_env)
        if result.returncode:
            raise RuntimeError(f'外部命令失败，退出码 {result.returncode}；未记录可能含密钥的 stderr')
        return 'draft', result.stdout
    body={'model': config['model'], 'messages': [{'role': 'user', 'content': prompt}], **config.get('request_options',{})}
    base=config['base_url'].rstrip('/')
    headers={'Content-Type':'application/json'}
    if kind=='anthropic':
        body.setdefault('max_tokens',4096)
        url=base+('/messages' if base.endswith('/v1') else '/v1/messages')
        headers.update({'x-api-key':key_value(config),'anthropic-version':config.get('api_version','2023-06-01')})
    else:
        url=base+'/chat/completions'
        headers['Authorization']='Bearer '+key_value(config)
    payload = json.dumps(body).encode()
    request = urllib.request.Request(url,data=payload,headers=headers)
    # 禁用重定向，避免携带密钥访问另一个域名。
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    with urllib.request.build_opener(NoRedirect).open(request, timeout=config['timeout_seconds']) as response:
        data = json.load(response)
    if kind=='anthropic':
        content='\n'.join(block['text'] for block in data.get('content',[]) if block.get('type')=='text' and isinstance(block.get('text'),str))
        finish=data.get('stop_reason')
        complete=finish in {'end_turn','stop_sequence'}
    else:
        choice=data['choices'][0]
        content=choice['message']['content']
        complete=choice.get('finish_reason','stop')=='stop'
    if not isinstance(content,str) or not content.strip():
        raise ValueError('模型没有返回有效正文，不能作为完成结果')
    # 保留截断正文，但明确标为 partial，不把输出限制当作已完成。
    return ('draft' if complete else 'partial'), content
