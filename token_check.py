import os
import requests
import time
from twitch_token import token, update_token_field

def is_token_expired(token_data, buffer_seconds=300):
    expires_at = token_data.get('expires_at')
    if not expires_at:
        return True
    return time.time() > expires_at - buffer_seconds

def refresh_app_token():
    data = token
    client_id = token['client_id'] or os.getenv('TWITCH_CLIENT_ID')
    client_secret = token['client_secret'] or os.getenv('TWITCH_CLIENT_SECRET')
    if not client_id or not client_secret:
        raise RuntimeError("缺少 client_id 或 client_secret")
    resp = requests.post(
        'https://id.twitch.tv/oauth2/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
    )
    resp.raise_for_status()
    d = resp.json()
    access_token = d.get('access_token')
    expires_in = d.get('expires_in')
    if not access_token or not expires_in:
        raise RuntimeError("取得 access_token 或 expires_in 失敗")

    update_token_field('access_token', access_token)
    update_token_field('expires_at', time.time() + expires_in)
    print(f"取得新 token，有效期 {expires_in} 秒 (至 {time.ctime(data['expires_at'])})")

    return access_token

def get_valid_token():
    data = token
    if is_token_expired(data):
        print("Token 已過期或快到期，刷新中...")
        return refresh_app_token()
    print("Token 尚未到期，直接使用舊的 access_token")
    return data['access_token']

def validate_token_with_twitch(token):
    resp = requests.get(
        'https://id.twitch.tv/oauth2/validate',
        headers={'Authorization': f'Bearer {token}'}
    )
    return resp.status_code == 200

def main():
    try:
        token = get_valid_token()
        if not validate_token_with_twitch(token):
            print("雖然 local 判斷未過期，但 Twitch 驗證回 401，強制刷新")
            token = refresh_app_token()
        print("目前 token 可用：", token)
    except Exception as e:
        print("Token 取得或驗證失敗：", e)

if __name__ == '__main__':
    main()
