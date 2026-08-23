"""测试 Volcengine V4 签名 — 从零实现

⚠️ 安全提示：AK / SK 改为从环境变量读取，避免硬编码泄露。
   请在 .env 文件中配置（.env 已 .gitignore 忽略）：

       VOLC_AK=<your access key id>
       VOLC_SK_RAW=<your secret key (base64-encoded)>

   历史版本中曾硬编码 AK + SK，现已移除。如密钥已泄露，
   请立即在火山引擎控制台禁用并轮换。
"""
import os
import json
import base64
import hashlib
import hmac
import datetime
from urllib.parse import quote
import requests


def load_credentials():
    """从环境变量加载火山引擎凭证，缺失则报错"""
    ak = os.environ.get('VOLC_AK')
    sk_raw = os.environ.get('VOLC_SK_RAW')
    if not ak or not sk_raw:
        raise RuntimeError(
            "未配置火山引擎凭证。请设置环境变量 VOLC_AK 与 VOLC_SK_RAW。\n"
            "或在 .env 文件中（参考 .env.example）：\n"
            "  VOLC_AK=your_access_key_id\n"
            "  VOLC_SK_RAW=base64_encoded_secret_key"
        )
    sk = base64.b64decode(sk_raw).decode('utf-8')
    return ak, sk


def hmac_sha256(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


# 加载凭证（从环境变量）
ak, sk = load_credentials()

# 构建请求
body = {
    'req_key': 'high_aes_general_v30l_zt2i',
    'prompt': 'Abstract zen background, dark ink wash, 8K. NO text.',
    'width': 900,
    'height': 383,
    'seed': -1,
    'scale': 2.5,
    'use_pre_llm': True,
}
body_str = json.dumps(body, ensure_ascii=False)
body_hash = hashlib.sha256(body_str.encode('utf-8')).hexdigest()

now = datetime.datetime.now(datetime.timezone.utc)
amz_date = now.strftime('%Y%m%dT%H%M%SZ')
date_stamp = now.strftime('%Y%m%d')

region = 'cn-north-1'
service = 'cv'
method = 'POST'

# 构建 canonical request
path = '/'
query_params = [('Action', 'CVSync2AsyncSubmitTask'), ('Version', '2022-08-31')]
canonical_query = '&'.join(f'{quote(k, safe="")}={quote(v, safe="")}' for k, v in sorted(query_params))

headers = {
    'content-type': 'application/json',
    'host': 'visual.volcengineapi.com',
    'x-date': amz_date,
    'x-content-sha256': body_hash,
}

signed_headers = sorted(headers.keys())
signed_headers_str = ';'.join(signed_headers)
canonical_headers = ''.join(f'{k}:{headers[k]}\n' for k in signed_headers)

canonical_request = f'{method}\n{path}\n{canonical_query}\n{canonical_headers}\n{signed_headers_str}\n{body_hash}'

print('=== Canonical Request ===')
print(canonical_request)

credential_scope = f'{date_stamp}/{region}/{service}/request'
string_to_sign = f'HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'

print('\n=== String to Sign ===')
print(string_to_sign)

# Signing key
k_date = hmac_sha256(f'AWS4{sk}'.encode('utf-8'), date_stamp)
k_region = hmac_sha256(k_date, region)
k_service = hmac_sha256(k_region, service)
k_signing = hmac_sha256(k_service, 'request')
signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

authorization = f'HMAC-SHA256 Credential={ak}/{credential_scope}, SignedHeaders={signed_headers_str}, Signature={signature}'

# 发送请求
http_headers = {
    'Content-Type': headers['content-type'],
    'Host': headers['host'],
    'X-Date': headers['x-date'],
    'X-Content-Sha256': headers['x-content-sha256'],
    'Authorization': authorization,
}

url = f'https://visual.volcengineapi.com/?{canonical_query}'
resp = requests.post(url, data=body_str.encode('utf-8'), headers=http_headers, timeout=60)
result = resp.json()

print(f'\n状态码: {resp.status_code}')
err = result.get('ResponseMetadata', {}).get('Error', {})
if err:
    print(f'错误: {err["Code"]}: {err["Message"]}')
elif result.get('code') == 10000:
    print(f'✅ 成功! task_id: {result["data"]["task_id"]}')
else:
    print(f'响应: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}')