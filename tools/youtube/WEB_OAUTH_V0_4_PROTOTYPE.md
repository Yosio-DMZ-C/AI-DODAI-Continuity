# AD&C YouTube ブラウザ初回OAuth認証 v0.4（実装試作）

- 更新: 2026-10-20
- 状態: **LOCAL_TEST_PASS / GOOGLE_OAUTH_NOT_RUN / WORKER_DEPLOY_NOT_RUN**
- 対象Worker: `adnc-youtube-private` （本番環境へまだ反映しない）
- 目的: WindowsにPython・Node.js・npmを導入せず、ブラウザ操作だけで、既存Drive動画→YouTube非公開投稿のバックエンド初回OAuth認証を完了する。

## 現在の実機PASS

Cloudflare公式MCPをWindows Codexへ直接登録し、OAuth Read onlyでCloudflareのGET APIへ接続成功。Worker `adnc-youtube-private`、KV `adnc-youtube-uploads` / `UPLOADS_KV`、`EXPECTED_CHANNEL_ID = UCrLzqKRdeNsCpSrHPQy8Ifg` は **Codexの報告上GET 200**（2026-10-20）。MCP `search`、`execute` はPASS、Workerへの書込みは未実施。Claude/Gemini等、別AIから使えることまで検証したわけではない。

## v0.4の実装

試作用の依存ゼロJS `oauth_web_module.mjs` を作成済み。ローカルNode.js 22の模擬テスト **6/6 PASS**。主な機能:

- 既存Workerに `/auth/start` (GET: 本人向け画面、POST: `MCP_API_KEY` が必要) と `/auth/callback` (GET: Google OAuthコード交換) を追加する。
- Web application型のGoogle OAuth Clientを使用し、`offline`、`prompt=consent` でRefresh Tokenを受ける。
- `state` にHMAC署名と10分期限を付し、Secure/HttpOnly/SameSite=Lax Cookieで開始ブラウザを確認。
- 認証後のGoogle YouTube API `channels?mine=true` のIDと `EXPECTED_CHANNEL_ID` を照合。違えばトークン提示禁止。
- 必要スコープが欠けていれば停止。旧Driveアップロード検証のため `youtube.force-ssl` と `drive.readonly` を要求。将来Drive非依存で再設計。
- Refresh TokenはOAuth完了ページの**コピー専用ボタン**から**本人がCloudflare WorkerのSecret `GOOGLE_REFRESH_TOKEN` へ貼り付け**。チャット・URL・KVに保存しない。ただし認証完了ページのHTML/JSには一時的に値を含むため、第三者へ画面やHTMLを共有せず、ブラウザ拡張にも注意。
- GoogleクライアントSecret、MCP_API_KEY、Refresh Tokenをリポジトリへ格納しない。OAuth実行前にHTTPS／CSP／認証制御のコードレビューが必要。

**配布形態**：この会話で検証済みの試作ZIPを成果物として提供。正式採用前にGitHubの原本Workerへ組み込み、モック6件の再検査と本番向けセキュリティレビューを行う。ZIPのリンクはGitHubリポジトリ内には記録しない（会話添付参照）。

## 次のユーザー操作：Google Web OAuth Clientの作成

1. [Google Auth Platform > Clients](https://console.cloud.google.com/auth/clients) で対象Google Cloudプロジェクトを選択する。以前使ったデスクトップ用Clientは**そのまま維持**。
2. 新しいOAuth Clientの種類 **Web application / ウェブアプリケーション** を選び、任意名 `AD&C YouTube Web OAuth`。**「Use this client for an AI-powered agent」はON**。このクライアントは将来ChatGPT→Cloudflare Worker→YouTube REST APIの自動投稿（AIによるツール実行）専用に使用する。GoogleはAIエージェントの代理操作に専用OAuthクライアントを使用するよう案内している。
3. **Authorized redirect URI** を次の値で登録（完全一致）：`https://adnc-youtube-private.yosio-hasenaka.workers.dev/auth/callback`
4. 作成完了だけをAIへ報告。Client SecretやJSONは**安全上チャットへ送信・添付禁止**。
5. 次工程でCloudflare WorkerにWeb Client ID、Web Client Secret、`AUTH_REDIRECT_URI`、`MCP_API_KEY` を設定。現在のCloudflare公式MCPはRead onlyで接続済み。書込みが必要なら影響箇所と対象Workerを示し、最小限の権限をユーザーに再承認してもらう。**これらのSecretをCloudflare公式MCPのチャット実行引数に直接貼らせない**。秘密値はCloudflare管理画面へ本人が入力する。

## 前提・残作業

- Cloudflare本番WorkerにはOAuth bootstrapコードがまだない。モジュール試作だけで `/auth/start` が利用可能と案内しない。
- Cloudflare Workerの `/mcp` は別途ユーザー個人向けプラグインへ接続する必要がある。Cloudflare管理用MCP `cloudflare-api` と YouTube投稿用MCPは**別**。
- 初回Web OAuthのユーザー許可／対象YouTubeチャンネル確認／Refresh Token Secret保存はNOT_RUN。
- 既存動画1件の非公開アップロード後に、APIで `privacyStatus=private` およびYouTubeで動画内容を検証する。第三者との共有を目的とする限定公開への変更は**ユーザー本人のみ**。
- Drive原本の削除は**未実装・未承認**。成功確認後に独立の承認を求める。
- CloudflareのWorkerコードをユーザーがWebエディタで管理しているため、過去のMCP認証・Bindings・変数を壊さない**既存コードへの最小差分**を必須とする。
- OAuth Refresh Tokenが失効する要因はGoogle側のポリシー・アプリ公開状態に依存し、再認証手順を用意する。

## 出典

- [Google OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Cloudflare Workers Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)
- [Cloudflare Workers limits](https://developers.cloudflare.com/workers/platform/limits/)
- [YouTube videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)

## 追補（2026-10-20）：AI-powered agentチェック

- Google公式 [Manage OAuth Clients](https://support.google.com/cloud/answer/15549257) は、AIがユーザーに代わって操作するOAuth ClientをAgenticとして区別し、通常の対話型クライアントとは別IDを維持するよう推奨している。
- 本Web OAuthクライアントは、ブラウザで本人が初回承認するが**継続的な用途はAIから起動するCloudflare WorkerのYouTube/Drive REST API呼び出し**。そのため `Use this client for an AI-powered agent` を**ON**にする。別のブラウザ人手操作用 `videos.html` のOAuth Web Clientは分離する。
- GoogleのWeb OAuthクライアント作成後はこの種別チェックを変更できない旨が公式クイックスタートに明記されている。すでにOFFで作成した場合、基本は**別のWeb Clientを新規作成**してこちらに採用する。
- Agenticタグは自動で追加権限を与えない。公式: https://developers.google.com/people/quickstart/js
