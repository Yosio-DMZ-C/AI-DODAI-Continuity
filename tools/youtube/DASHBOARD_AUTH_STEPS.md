# AD&C YouTube 初回認証（Cloudflare Dashboard構築済み）

**2026-10-20 実機状況**: Google CloudのOAuth Desktop JSON取得済み（ユーザー端末のみ）。Cloudflare Worker `adnc-youtube-private` を配置、KV `adnc-youtube-uploads` を `UPLOADS_KV` としてBinding済み、平文変数 `EXPECTED_CHANNEL_ID=UCrLzqKRdeNsCpSrHPQy8Ifg` を保存済み（いずれもユーザー画面による確認）。**Google OAuthとYouTube動画実投稿はまだ未実行**。

## ステップ16: PC実行環境の確認

Windows PowerShellで次を実行。認証情報は含まない。

```powershell
py --version
node --version
npm --version
```

Python・Node.js/npmが必要。未インストールなら公式サイトから導入する。初回だけPC側のOAuth承認を行う試験版であり、一般利用者向けの最終形ではない。

## ステップ17: 初回認証準備

1. 最新の `ADNC_YouTube_Tools_v0.3.1_DASHBOARD.zip` をユーザーPCに展開。
2. OAuth DesktopクライアントJSONは自分のPC内にのみ置く。**セキュリティ上、JSON・client_secret・Google認証トークンをチャット/公開GitHubへ送信してはいけない。**
3. 展開フォルダで `npx wrangler login` を実行し、本人がCloudflareにログイン。
4. `py -m pip install google-auth-oauthlib` を実行。

## ステップ18: YouTube認証（ユーザー端末内）

```powershell
py setup_once.py --configure --dashboard-configured --credentials "C:\\YOUR\\PRIVATE\\PATH\\client_secret.json" --expected-channel-id "UCrLzqKRdeNsCpSrHPQy8Ifg" --worker-url "https://adnc-youtube-private.yosio-hasenaka.workers.dev"
```

- `--dashboard-configured` はCloudflareダッシュボードで設定済みのWorkerを保持。**コードをWranglerから再デプロイしない**。`/health`でWorkerを事前検査する。
- OAuthの初期スコープは `https://www.googleapis.com/auth/youtube.force-ssl` のみ。**Drive経由の旧MCPアップロード試験をする時だけ** `--include-drive-access` で `https://www.googleapis.com/auth/drive.readonly` を追加。ただしDrive全体への広い読取権限になるため本人が承認を判断する。現行MCPの実装はまだDrive経由であり、YouTubeのみの権限ではDriveファイルのアップロードはできない。
- `channels?mine=true` のチャンネルIDが期待値と一致しなければSecretを一切登録しない。
- 本人の確認 `YES` の後、`npx wrangler secret put --name adnc-youtube-private` を4回呼び、CloudflareにSecretを書き込む。秘密の値はターミナルへ表示しない。**Secret更新はWorkerの新バージョンを作成・デプロイする**ので、既存Bindingと`/health`は実行後に再確認する。
- ローカルの `.adnc_private/ADNC_YouTube_PRIVATE_PLUGIN.zip` にMCP認証キーが入る。公開・共有禁止。ChatGPTへのプラグイン接続は本人の承認が必要。

## 次の検証と保留事項

Cloudflare Worker Secret登録後、ChatGPTにプライベートプラグインを接続し `check_connection` を実行。結果の `ready`・`channel_id` の一致を確認してから投稿。APIからの非公開登録 `private_verified` を検査した後、公開範囲変更は人間が行う。Driveファイルの自動削除とDriveなしのチャット添付直送は別工程で未実装。

公式参考: https://developers.cloudflare.com/workers/configuration/secrets/ 、https://developers.google.com/youtube/data/guides/auth/installed-apps
