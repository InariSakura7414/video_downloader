import requests
from config import config, update_config_field
from twitch_token import token

def get_user_id(username, headers):
    url = 'https://api.twitch.tv/helix/users'
    r = requests.get(url, headers=headers, params={'login': username})
    r.raise_for_status()
    data = r.json().get('data', [])
    return data[0]['id'] if data else None

def get_latest_vod_url(user_id, headers):
    url = 'https://api.twitch.tv/helix/videos'
    r = requests.get(url, headers=headers, params={'user_id': user_id, 'type': 'archive', 'first': 1})
    r.raise_for_status()
    data = r.json().get('data', [])
    return data[0]['url'] if data else None

def parse_vod_id(vod_url):
    import re
    match = re.search(r"/videos/(\d+)", vod_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("無法解析 VOD ID")

def main():
    headers = {
    'Client-ID': token['client_id'],
    'Authorization': f'Bearer {token["access_token"]}',
    }

    try:
        user_id = get_user_id(config['twitch_username'], headers)
    except requests.HTTPError as e:
        print(f'Failed to get user ID: {e}')
        return

    if not user_id:
        print(f'找不到用戶名 {config["twitch_username"]}')
        return

    vod_url = get_latest_vod_url(user_id, headers)
    if vod_url:
        vod_id = parse_vod_id(vod_url)
        update_config_field("vod_url", vod_url)
        update_config_field("vod_id", vod_id)
        print('最新實況 VOD 連結：', vod_id)
    else:
        print('沒有找到任何過去的實況影片')

if __name__ == '__main__':
    main()
