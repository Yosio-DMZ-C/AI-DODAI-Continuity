# AD&C YouTube 初回認証手順書 v0.3

更新確認: 2026-10-20。**接続時には、AIがGoogle/YouTube/Cloudflareの公式資料を再検索し、現在の画面名称に合わせて案内する。** 昨日の画面と違えば、画面に表示されている名称を優先して修正する。

## ユーザーへの標準表示（これを最初に出す）

> AD&CからYouTubeへ自動で**非公開アップロード**するための初回設定です。操作が必要なのは、Google CloudでAPIと認証を設定すること、Cloudflareで接続先を作ること、Googleの同意を承認することです。最新の公式手順を確認し、現在の画面に沿って短く案内します。**セキュリティ上、ダウンロードしたOAuthクライアントJSON（client_secretを含む）、パスワード、アクセストークン、更新トークン、秘密鍵、接続キーは、チャットへ送信・添付・貼り付けしてはいけません。第三者に認証情報を渡すリスクがあります。画面を送る場合も値を隠してください。****わからないところは教えてください。現在の画面に合わせて案内します。**

## 実機フィードバック（2026-10-20）：スコープ画面へのリンク不備

- **症状**: ユーザーに案内した `https://console.cloud.google.com/auth/data-access` で「URL が見つかりません」。画面上部は「プロジェクトの選択」。
- **確認した原因候補**: 前回のURLは**誤り**。Google公式ドキュメントの「データアクセス」リンクは `https://console.cloud.google.com/auth/scopes` へ転送される。また、その際プロジェクト選択も失われていた。両方を確認し、プロジェクト未選択だけが原因と断定しない。
- **標準回避策**: まずGoogle Cloud上部で正しいプロジェクト（今回の例は `WPGARankking`）を選択、**現在表示されている左メニュー「データアクセス」をクリック**。URLを提示する場合は公式リンク `https://console.cloud.google.com/auth/scopes` とし、プロジェクト選択を先に案内する。
- **検証**: ユーザーのスコープ画面表示はまだ未確認。修正URLのブラウザ動作を成功と扱わない。
- **説明方式**: 該当リンクで404/「URLが見つかりません」となったら、同じURLを繰り返さず、画面に見える操作で復旧。「わからないところは教えてください。現在の画面に合わせて案内します。」

## 事前条件・実施順

1. Google Cloud Consoleのプロジェクトを作成・選択する。Google API Libraryで **YouTube Data API v3** と **Google Drive API** を「有効にする」。
   - https://console.cloud.google.com/apis/library/youtube.googleapis.com
   - https://console.cloud.google.com/apis/library/drive.googleapis.com
2. [Google Auth Platform](https://console.cloud.google.com/auth/overview)でブランディングと対象ユーザーを構成。`Audience` が外部かつ `Testing` の場合は、自分のGoogleアカウントをテストユーザーに加える。
   - https://console.cloud.google.com/auth/audience
   - **Testing + External** で `youtube.force-ssl` 等のスコープを使用した更新トークンは、通常**7日**で失効する。継続使用には公開ステータス・審査要否を確認し、Googleの案内に従う。**無審査のまま恒久利用できるとは断定しない**。
3. [Clients](https://console.cloud.google.com/auth/clients)で **Desktop app / デスクトップアプリ** のOAuthクライアントを作成、JSONをPCにダウンロードする。**このJSONの中身は機密情報として扱い、チャットへの添付・コピー、公開GitHubへの保存を禁止する。画面を共有する場合は `client_secret` やIDの表示箇所を隠す。** **Web applicationクライアントのJSONでは `setup_once.py` は動かない**。同意画面のスコープには `youtube.force-ssl` と `drive.readonly` が使用される。
4. [Cloudflare](https://dash.cloudflare.com/) のユーザーアカウントを用意する。PCにNode.jsとPythonを用意し、配布ZIP内の `worker.mjs`、`wrangler.toml.example`、`setup_once.py` を同一フォルダに置く。 `wrangler.toml.example` を `wrangler.toml` にコピー。YouTube Studioで見たチャンネルIDを `EXPECTED_CHANNEL_ID` に、後述のKV IDを該当欄に設定する。
   - `npx wrangler login`
   - `npx wrangler kv namespace create UPLOADS_KV`
   - コマンドが返した **KV namespace ID** を `wrangler.toml` に記入する。
   - `MANAGEMENT_URL` に実際の `videos.html` HTTPSページを指定（未公開ならCloudflare Workerとは別にホストする必要がある）。
   - `npx wrangler deploy` によりWorkerを配置。デプロイで報告された `https://*.workers.dev` のURLを控える。
5. PCで下記を実行。OAuth JSONのファイル名・チャンネルID・Worker URLを自分の値に置き換える。
   ```powershell
   python -m pip install google-auth-oauthlib
   python setup_once.py
   python setup_once.py --configure --credentials "C:\Users\USER\Downloads\client_secret.json" --expected-channel-id "UCxxxxxxxxxxxxxxxxxxxxxx" --worker-url "https://adnc-youtube-private.ACCOUNT.workers.dev"
   ```
   - Googleログイン画面で対象YouTubeチャンネルのGoogleアカウントを選んで同意する。 `setup_once.py` は実チャンネルIDを確認し、一致しなければSecretを登録しない。
   - `YES` の入力後、認証情報は **ユーザーのPCからCloudflare Worker Secretに直接登録**。標準出力には認証トークンを表示しない。必要ならWranglerで再実行。
   - PC内の `.adnc_private/ADNC_YouTube_PRIVATE_PLUGIN.zip` を生成。**MCP認証鍵を含むため、共有KB・公開GitHub・第三者には送らない**。
6. ChatGPTの個人用プライベートプラグインへ生成されたZIPを登録・接続する。ツール `check_connection` で `state=ready`、`channel_id=期待値` を確認する。ここまでで**接続のみ**、YouTube動画投稿は未実施。
7. 元のレビュー用Drive動画 `ADNC_Opening_45s_Review.mp4` を利用し、ユーザーの依頼に基づいて `upload_private_from_drive` を実行。 `private_verified` のときだけ成功判定。最後に **「非公開アップロード済み。この画面から更新してください」** と管理URLを提示。公開・限定公開への変更は人間が選ぶ。

## 2026-10-20 実機フィードバック：スコープ追加時のUIと同一文字列ルール

- [Google Auth Platform「データアクセス」](https://console.cloud.google.com/auth/scopes) の「スコープを追加または削除」→「選択したスコープの更新」で、フィルタに**完全なスコープURL**をそのまま貼り付けると YouTube Data API v3 の対象行が表示され、チェック→「更新」で追加できた（スクリーンショット確認）。
- 入力用の短縮文字列は使わない。**コピー欄の文字列と入力指示欄の文字列を完全一致**させる。「上は `https://www.googleapis.com/auth/youtube.force-ssl`、下は `youtube.force-ssl`」のような別表記は禁止。長くても同じ `https://www.googleapis.com/auth/youtube.force-ssl` を繰り返す。
- 追加後、Google Cloudに「検証が必要」と表示される場合がある。Google公式の[個人利用の例外](https://support.google.com/cloud/answer/13464323?hl=ja)では、本人利用など少人数のアプリは直ちにOAuth審査申請しなくても試験可能。ただし未確認アプリ警告・ユーザー上限等あり、一般公開時は審査が必要となり得る。**モーダルの「続行」はGoogleによる審査完了ではない**。
- 「スコープの使用方法」の説明は実装している機能に合わせて正直に記入する。例：「YouTubeに動画を非公開でアップロードし、動画一覧と公開状態を取得し、利用者の明示操作によって限定公開・公開に変更するために使用します。権限の範囲は広いものの、AD&Cは動画削除を自動実行しません。」
- 手順の途中にすでにSSが届いていれば、同じ画面の撮り方のリンクや撮影依頼を繰り返さない。撮影方法は**必要で、画面未入手の場合のみ**案内する。
- 最後に「続行」→必要な理由の入力→保存を案内。実際の保存成功は次の画面の表示で判定し、推測でPASSにしない。

## 2026-10-20 実機フィードバック：アップロード先チャンネルを先に選ぶ

- **観測**: 「YouTubeの詳細設定を開く」を先に案内すると、普段使いのチャンネルが開いた。間違ったチャンネルIDを転記しかねない。
- **標準導線（Google公式 [チャンネル切り替え](https://support.google.com/youtube/answer/3046356?hl=ja) に準拠）**:
  1. まず [YouTubeトップ](https://www.youtube.com/) を開く。
  2. 右上のプロフィール画像 → **「アカウントを切り替える」** を選び、今回アップロードしたいチャンネルを選択。選択肢になければ [YouTube Studio](https://studio.youtube.com/) で切り替えを確認。
  3. 右上のチャンネル名とアイコンが**意図したチャンネル**に切り替わったことを確認。
  4. **その後**に [YouTube 詳細設定](https://www.youtube.com/account_advanced) を開き、対象チャンネル名と `UC` で始まるチャンネルIDを確認・記録。**ユーザーIDではなくチャンネルID**。
  5. OAuth同意が別チャンネルに結びつく可能性を前提として、`setup_once.py` や `check_connection` のAPI応答に含まれるチャンネルIDを期待値と突合し、一致しなければ投稿を禁止する。**画面上の切り替えだけでは認証済みAPIの接続先確定と見なさない**。
- YouTubeの「デフォルト チャンネルを設定」は他のアプリにも影響し得るため、**切替のために無断変更を指示しない**。必要なら本人へ理由・影響を説明して承認を得る。
- 秘密情報（OAuth JSON、トークン等）を送らない。一方、チャンネルIDは公開識別子なのでチャットへの提示は可能。

## 認証エラー時の分岐

| 表示例 | 確認すること | 安全な対応 |
|---|---|---|
| `access_denied` / testerでない | Audience/Test users | 対象アカウントを追加、別アカウントに切替 |
| `redirect_uri_mismatch` | OAuthクライアント種別 | デスクトップアプリのJSONを使う、古いclient JSONを混同しない |
| `invalid_grant` | トークン失効 | Testingの7日制限や同意取り消しを確認、同じセットアップを再実行 |
| `channel_mismatch` | YouTubeアカウント・UC ID | GoogleログインするアカウントとチャンネルIDを再確認。**投稿しない** |
| `not_ready` / `MCP unauthorized` | Workerシークレット、KV、Bearer認証 | `check_connection`、Cloudflare Secrets、プラグイン設定を確認 |
| `private`確認不可 | YouTube側の状態・API制限 | 登録状況をStudioで確認。自動で再投稿しない |

## 実行上の重要な制約

- **接続前にアップロードはできない。** AIは「アップロード成功」と言ってはならない。
- YouTube公式 `videos.insert` 現行リファレンスは、API未確認プロジェクトの非公開固定について旧改訂履歴と記述が異なるため、**実機の `private_verified` と、Studioでの公開範囲変更可否の両方を検査**する。
- `videos.update(part=status)` の公開変更をAIが自動実行しない。人間が管理ページで明示操作する。
- `setup_once.py` はテスト済みの既存 `worker.mjs` を前提とする。Workerの生成やGoogle Cloudプロジェクト作成は自動化しない。
- 初回セットアップ時は**必要な操作の短縮案内を優先**し、ユーザーが迷った箇所だけ詳しく説明する。
- **秘密情報を「送らなくてもよい」「大丈夫」とだけ表現しない。** 必ず「セキュリティ上、JSON・認証トークン・秘密鍵はチャットに送信してはいけません。本人の端末内で利用してください」と明確に伝える。既に送った場合は認証情報を無効化・再発行する対応を案内する。

## 参照公式資料（次回実施時に再確認）

- Google: https://developers.google.com/youtube/data/guides/auth/server-side-web-apps
- Google: https://developers.google.com/identity/protocols/oauth2/
- Google: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
- Cloudflare: https://developers.cloudflare.com/workers/get-started/guide/
- Cloudflare: https://developers.cloudflare.com/kv/get-started/
- Cloudflare: https://developers.cloudflare.com/workers/wrangler/commands/workers/#secret
