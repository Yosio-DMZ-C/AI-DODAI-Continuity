> **v0.3.1 Dashboard認証対応:** GUIでWorker/KV/チャンネルIDを作成済みの場合、`setup_once.py --dashboard-configured` を使用。古い `wrangler.toml` で再デプロイする必要はありません。OAuthは初期状態でYouTube権限のみ。 [実機向け最短手順](DASHBOARD_AUTH_STEPS.md)（実認証・実投稿は未実施）。

> **v0.4 設計更新（2026-10-20）:** YouTubeを動画の保管・共有先とし、**Google Driveを必須としない**。ブラウザからの直接投稿を標準、チャット添付の直接転送は未実装（接続検証予定）、Drive→MCPは既存ファイル向け補助経路。Drive原本の整理はYouTube処理完了確認後に**明示的ポリシーに従いゴミ箱へ移動**する案で、**削除機能は未実装**。 [詳細設計](DIRECT_UPLOAD_DESIGN_v0.4_DRAFT.md)

# AD&C YouTube Tools v0.3 (draft / 初回認証導線追加)

## v0.3 変更点（2026-10-20）

- `INITIAL_AUTH_GUIDE.md`：Google / Cloudflare公式手順への直リンク、変更時の再検索、初回承認、トラブル時の分岐。
- `videos.html`：開設ナビとは別ページのまま、初回設定ガイドを開閉表示。**「わからないところは教えてください。現在の画面に合わせて案内します。」**を常設。
- `setup_once.py`：ローカルGoogle OAuthを取得し、期待チャンネルID一致後にCloudflare Secretsを標準出力へ露出せず設定。本人PC内に**共有禁止のプライベートプラグインZIP**を作成。Cloudflare/Google Cloudの初回準備を無断自動化はしない。
- MCP `check_connection`：接続状況・チャンネルID一致を**動画投稿せず**確認。未接続・不一致時は投稿しない。
- 旧 `setup_once.py`：更新トークンの画面表示を避けるため非推奨・実行停止。
- GitHub `wrangler.toml` やトークンJSONをコミットしない `.gitignore` を追加。

最新手順の要点は **[INITIAL_AUTH_GUIDE.md](INITIAL_AUTH_GUIDE.md)** を参照。Google/Cloudflareログイン・同意は必ず利用者のブラウザで実施します。自動投稿成功の証拠はGoogle/YouTube APIの実応答のみで、**ローカル試験PASSと混同しません**。

## 実装範囲

| ページ／部品 | 役割 | 現時点の状態 |
|---|---|---|
| `channel.html` | iPhone等でのチャンネル開設・プロフィール設定ナビ | 既存 `ADNC_YouTube_iPhone_Navi_v0.1.html` のUIを継承した別ページ。実際のチャンネル作成はYouTube公式ページで人間が実施 |
| `videos.html` + `videos.js` | ブラウザからGoogle OAuth接続、動画の**非公開**登録、動画一覧・限定公開/公開への変更、URLコピー・CSV出力 | 実装・静的検査。**Google OAuth設定と実際のYouTubeアカウントでの動作検証は未実施** |
| `worker.mjs` | ChatGPTから直接呼ぶMCPサーバー。**Google Drive上の動画を非公開アップロード**、YouTube一覧取得 | サーバー実装・模擬APIテスト。**未デプロイ／認証未設定／実アップロード未検証** |
| `plugin-template/` | MCPサーバーへ接続するChatGPTプラグイン雛形 | **未登録**。実際のWorker URLと安全な認証情報が設定された後に登録 |

**チャットからの自動アップロードは、Workerの配置・OAuth同意・秘密情報の登録・プラグインの接続が済むまで動かない。** UI画面のみでチャットの会話添付がYouTubeに自動送信されるわけではない。

## 画面構成・ユーザー導線

- チャンネルなし → `channel.html` を表示し公式チャンネル作成画面へ案内 → 作成後は `videos.html`。
- 動画登録依頼（チャット、接続済） → MCP `upload_private_from_drive`。Drive動画を取得し、非公開でアップロード・公開状態の再検証 → **動画URL＋`videos.html` を返す**。
- 未接続、ローカル動画、またはチャット接続なし → `videos.html`（人間がブラウザ認証してファイルを選ぶ）。
- 公開範囲の変更 → **人間が `videos.html` の一覧で非公開／限定公開／公開を選んで確認後更新**。チャット向けMCPには公開変更機能を設けない。
- どのケースでも登録時の既定値は `private`。`unlisted` や `public` をAPIの既定値に任せない。

## Web管理ページの初回セットアップ

1. Google Cloud Consoleでプロジェクトを作り、**YouTube Data API v3** を有効化。
2. OAuth同意画面を設定。テスト段階では対象Googleアカウントをテストユーザーに登録する。`youtube.force-ssl` スコープを要求する点に留意。
3. OAuthの**ウェブアプリケーション**クライアントIDを作る。`https://<ユーザーのサイト>` を承認済みJavaScript生成元として設定（パスは含まない）。サンプルサイトをGitHub Pagesで公開する場合も、実際に公開した生成元を指定する。GoogleのOAuthポップアップに`file://`は使えない。
4. `channel.html`, `videos.html`, `videos.js`, `shared.css` を同一パスへ配置し、HTTPSで開く。`videos.html`に**クライアントIDだけ**を入力して保存し「Googleで認証」。
5. 接続先チャンネル名とIDを確認。動画ファイル、タイトル、対象視聴者（子ども向けか否か）を指定して**非公開**アップロード。
6. APIで非公開の再取得を確認してから成功表示。公開変更は一覧で実行し、更新レスポンスの後に再取得して一致を検査。

*OAuthクライアントIDは秘密情報ではないが、OAuthクライアントシークレット、アクセストークン、リフレッシュトークンをHTML、localStorage、公開リポジトリに置かない。*

ブラウザOAuthは短命トークン方式。閉じると再認証が必要で、バックグラウンド自動アップロードには使えない。2026年10月時点の最新ブラウザ公式API動作検証は未実施。

## チャットから直接使うMCP（非公開のみ）

ChatGPTからの `upload_private_from_drive` はGoogle Driveに保存済みの**動画ファイルID**を入力とする。手元のMP4やチャット添付を自動的にDriveへ置く仕組みは含まない。Driveへ先に保存されている動画は、チャット側でGoogle DriveコネクタからIDを確認できる。

**認証情報を本リポジトリにコミットしない。** 以下は実運用者による一回限りのセットアップが必要。

1. Google Cloudで OAuth クライアントを作成し、承認スコープを `https://www.googleapis.com/auth/drive.readonly` と `https://www.googleapis.com/auth/youtube.force-ssl` に設定する。DriveのGoogleアカウントとアップロード対象YouTubeチャンネルの権限を持つユーザーで同意する。
2. Google Cloudの「デスクトップアプリ」型OAuthクライアントをダウンロードし、ローカルで `python -m pip install google-auth-oauthlib` → `python setup_once.py` の案内を確認し、`python setup_once.py --configure ...` から同意・Secret登録を行う。トークンをターミナルへ表示しない。OAuth Testing+Externalは更新トークンが通常7日で失効するため運用設定を確認。
3. Cloudflare Workerに `worker.mjs` をデプロイして、4つのSecret `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `MCP_API_KEY` と2つの環境変数 `EXPECTED_CHANNEL_ID`、`MANAGEMENT_URL`（動画管理ページの公開URL） を登録する。`MCP_API_KEY` は32文字以上の乱数を使う。
4. Cloudflare KVネームスペースを作り、`UPLOADS_KV` としてWorkerにバインドする。これは不明なアップロード結果の**誤再実行・二重投稿防止**に必須。
5. `/health` で稼働を確認。`/mcp` はBearer認証がない呼び出しを拒否する。Secretを含むURLやログを公開しない。
6. ローカルPCの `.adnc_private/ADNC_YouTube_PRIVATE_PLUGIN.zip` を個人用*非公開プラグイン*へ登録する（**秘匿ファイル。共有禁止**）。接続URLとBearerはZIP生成時に設定済み。接続後に `tools/list` と `check_connection` の `state=ready` が使えることを検証する。
7. Google Driveの小さいテスト動画を非公開で投稿 → プライバシーが `private` と確認できる場合のみチャットの自動アップロードを本利用。

Workerは対象のGoogle Driveファイルを8MiB単位で取得し、YouTubeへ再開可能アップロードする。対象は**最大128MiBの動画**。投稿先チャンネルは認証済みGoogleアカウントのデフォルト選択に従う。ブラウザ版同様に、誤チャンネルへのアップロードを避けるにはチャンネル名／IDを事前照合する。

MCPツール:

- `check_connection()` : 動画投稿せずにGoogle OAuth / Secret / 期待チャンネルの一致を検査。
- `list_uploaded_videos(limit=20)` : チャンネル名、チャンネルID、最近の動画・状態・URL一覧取得。
- `upload_private_from_drive(drive_file_id,title,description,made_for_kids,request_key)` : **非公開固定**アップロード。`request_key` は再実行時も同じ値を渡す（KV上で途中状態なら再アップロードしない）。子ども向け設定は本人確認が必要で自動推測しない。

**重要:** チャット起動のWorkerは対象チャンネルIDの強制一致検査を実装済み。`EXPECTED_CHANNEL_ID` の設定と実機での照合試験は未実施。これを満たさず本番運用しない。

## API仕様上の注意

- `videos.insert` は公開範囲を指定しなければ`public`になる場合があるため、送信時に`private`を明記。
- `videos.update(part=status)` は指定漏れで既存値を失う可能性があるため、ブラウザ管理UIでは既存の書き込み可能なstatus値をなるべく引き継いで更新する。公開予約済みはStudio案内とする。
- GoogleのAPIプロジェクトの状態、YouTubeのポリシー、クォータ制限により投稿結果や閲覧範囲が変わる可能性がある。現行公式資料と本番テストで確認する。
- アップロード後、URLを返しても`private`の間は第三者が視聴できない。第三者レビュー用は人間が一覧画面から`unlisted`へ変更する。
- **更新**は既存動画の「メタデータ（公開範囲）」を変える操作であり、**動画ファイル本体を同じURLで差し替える機能ではない**。本体の変更は新しい動画としてアップロードする。

## 開発・検証

```bash
node --check videos.js
node --check worker.mjs
node --test tests/*.test.mjs
python3 -m http.server 8765
```

`http://localhost:8765/videos.html`で画面を確認（認証動作はGoogle側で登録した生成元が必要）。

ドキュメント・外部仕様:
- https://developers.google.com/identity/oauth2/web/guides/use-token-model
- https://developers.google.com/youtube/v3/docs/videos/insert
- https://developers.google.com/youtube/v3/docs/videos/update
- https://developers.google.com/youtube/data/guides/using_resumable_upload_protocol
- https://developers.google.com/youtube/v3/docs/channels/list
- https://developers.google.com/youtube/data/reference/rest/v3/playlistItems/list

## 検証ゲート

- [x] ブラウザ側は公開URLにSecretを置かない設計
- [x] ブラウザ／Workerのアップロード指定は必ずprivate
- [x] UIにのみ公開範囲変更を配置（明示確認付き）
- [x] TypeScript/JavaScriptの構文とモックテスト
- [ ] 実際のGoogle OAuth同意
- [x] アップロード前に期待チャンネルIDと照合するコード
- [ ] GoogleチャンネルIDの本番一致検査
- [ ] 実際のGoogle Drive → YouTubeのアップロード
- [ ] 2端末でのブラウザUI試験
- [ ] MCPのChatGPTプラグイン登録・認証・動作確認

`NOT_RUN`項目が残る間は、本番自動化完成ではなく**動作前の実装候補**。
