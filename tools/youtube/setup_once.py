#!/usr/bin/env python3
"""AD&C private YouTube MCP one-time local authorization helper.

Only runs on the owner's PC. Never prints, uploads to chat, or stores token values in a document.
Requires existing Cloudflare Worker and OAuth Desktop client credentials.
"""
import argparse
import json
import secrets
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/drive.readonly",
]
ROOT = Path(__file__).resolve().parent


def require_https(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query or parsed.path not in ("", "/"):
        raise ValueError("--worker-url must be the Worker HTTPS origin only (no path, token or query)")
    return f"https://{parsed.netloc}"


def check_client(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    c = doc.get("installed")
    if not isinstance(c, dict) or not c.get("client_id") or not c.get("client_secret"):
        raise ValueError("Google Cloudで『デスクトップアプリ』のOAuth JSONをダウンロードしてください（Web用JSONは不可）")
    return c


def google_channel(access_token):
    request = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/channels?mine=true&part=id,snippet",
        headers={"Authorization": "Bearer " + access_token},
    )
    with urllib.request.urlopen(request, timeout=20) as resp:
        data = json.load(resp)
    item = next(iter(data.get("items") or []), None)
    if not item or not item.get("id"):
        raise RuntimeError("YouTubeチャンネルを確認できません。Googleのログインアカウントを確認してください")
    return item


def put_secret(key, value, worker):
    # Avoid placing values in process command-line arguments and terminal output.
    result = subprocess.run(
        ["npx", "wrangler", "secret", "put", key, "--name", worker],
        input=value + "\n", text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, cwd=ROOT,
    )
    if result.returncode:
        raise RuntimeError("Cloudflare Secretの登録に失敗: " + key + "。WranglerのログインとWorker名を確認してください")
    print("PASS: Cloudflare Secret登録 " + key)


def plugin_zip(url, mcp_key):
    # Private local file. The plugin contains an access secret; never commit/share the ZIP.
    out_dir = ROOT / ".adnc_private"
    out_dir.mkdir(mode=0o700, exist_ok=True)
    out = out_dir / "ADNC_YouTube_PRIVATE_PLUGIN.zip"
    source = ROOT / "plugin-template"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in source.rglob("*"):
            if f.is_file():
                name = f.relative_to(source).as_posix()
                if name == ".mcp.json":
                    d = json.loads(f.read_text(encoding="utf-8"))
                    cfg = d["mcpServers"]["adnc-youtube"]
                    cfg["url"] = url + "/mcp"
                    cfg["headers"]["Authorization"] = "Bearer " + mcp_key
                    body = json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8")
                    z.writestr(name, body)
                else:
                    z.write(f, name)
    try:
        out.chmod(0o600)
    except OSError:
        pass
    return out


def run(args):
    if not args.configure:
        print("AD&C YouTube  初回認証チェック / 実API呼び出しなし")
        print("1. Google CloudでYouTube Data API v3 / Google Drive APIを有効にする")
        print("2. Google Auth PlatformでAudienceを設定し、自分をTest userに追加する")
        print("3. Google Auth Platform > ClientsでDesktop appのOAuth JSONをダウンロードする")
        print("4. Cloudflare WranglerでログインしKVを作り、wrangler.tomlを設定・Workerをdeployする")
        print("5. python -m pip install google-auth-oauthlib")
        print("6. python setup_once.py --configure --credentials PATH --expected-channel-id UC... --worker-url https://YOUR.workers.dev")
        print("認証情報をチャットや共有KBに貼り付けないでください。")
        return 0
    if not args.credentials or not args.expected_channel_id or not args.worker_url:
        raise ValueError("--configure requires --credentials, --expected-channel-id, --worker-url")
    worker_origin = require_https(args.worker_url)
    url_host = urllib.parse.urlsplit(worker_origin).hostname
    if not (url_host.endswith('.workers.dev') and url_host.split('.')[0] == args.worker_name):
        raise ValueError('Worker URLは登録予定のCloudflare *.workers.dev ドメインとWorker名が一致する必要があります')
    cfg = ROOT / 'wrangler.toml'
    if not cfg.exists():
        raise ValueError('wrangler.toml がありません。wrangler.toml.exampleをコピーし、KVと対象チャンネルを設定してください')
    config_text = cfg.read_text(encoding='utf-8')
    if 'REPLACE_' in config_text or f'EXPECTED_CHANNEL_ID = "{args.expected_channel_id}"' not in config_text:
        raise ValueError('wrangler.toml に未設定の項目があるか、期待チャンネルIDが一致しません')
    if not args.expected_channel_id.startswith("UC") or len(args.expected_channel_id) != 24:
        raise ValueError("--expected-channel-id は UC で始まる24文字のYouTubeチャンネルIDを指定してください")
    client = check_client(args.credentials)
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError("必要モジュールがありません: python -m pip install google-auth-oauthlib") from exc
    flow = InstalledAppFlow.from_client_secrets_file(str(args.credentials), SCOPES)
    print("Googleの承認画面を開きます。パスワードや認証情報はチャットに貼らないでください。")
    creds = flow.run_local_server(port=0, open_browser=True, prompt="consent", access_type="offline")
    if not creds.refresh_token or not creds.token:
        raise RuntimeError("更新トークンが取得できません。テストユーザー登録・同意設定を確認してください")
    channel = google_channel(creds.token)
    title = channel.get("snippet", {}).get("title") or "(no name)"
    print("Google認証されたYouTubeチャンネル:", title, channel["id"])
    if channel["id"] != args.expected_channel_id:
        raise RuntimeError("予定チャンネルと一致しません。安全のためSecret登録を中止しました")
    print("対象が正しい場合のみ、CloudflareへSecretを4件登録します。")
    if input("進める場合は YES と入力してください: ").strip() != "YES":
        print("キャンセルしました。")
        return 1
    worker = args.worker_name
    mcp_key = secrets.token_urlsafe(48)
    for key, value in (
        ("GOOGLE_CLIENT_ID", client["client_id"]),
        ("GOOGLE_CLIENT_SECRET", client["client_secret"]),
        ("GOOGLE_REFRESH_TOKEN", creds.refresh_token),
        ("MCP_API_KEY", mcp_key),
    ):
        put_secret(key, value, worker)
    private_zip = plugin_zip(worker_origin, mcp_key)
    print("PASS: チャネルID一致、認証登録完了")
    print("次: ChatGPTのプライベートプラグインへ、下記ローカルZIPを登録してください。")
    print(private_zip)
    print("※ZIPは認証鍵を含みます。第三者や共有リポジトリへ送らないでください。")
    print("次: 接続後に『check_connection』を実行し、非公開テスト動画で検証します。")
    return 0


def main():
    p = argparse.ArgumentParser(description="AD&C YouTube 初回認証ガイド + 安全なCloudflare Secret登録")
    p.add_argument("--configure", action="store_true", help="実際にGoogle OAuth認証とCloudflare Secret登録を行う")
    p.add_argument("--credentials", help="Google Cloud Desktop app OAuth JSONのローカルパス")
    p.add_argument("--expected-channel-id", help="アップロード対象のYouTubeチャンネルID (UC...)")
    p.add_argument("--worker-url", help="デプロイ済WorkerのHTTPS origin")
    p.add_argument("--worker-name", default="adnc-youtube-private", help="wrangler Worker名")
    a = p.parse_args()
    try:
        return run(a)
    except Exception as exc:
        print("SETUP BLOCKED:", exc, file=sys.stderr)
        print("わからないところは教えてください。現在の画面に合わせて案内します。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())