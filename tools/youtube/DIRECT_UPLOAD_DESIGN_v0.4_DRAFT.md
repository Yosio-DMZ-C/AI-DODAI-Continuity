# AD&C YouTube 動画保存・共有方式 v0.4（設計草案）

更新日: 2026-10-20
状態: **設計のみ / 実装と実サービス検査は未完了**（既存Draft PR #21を維持）

## 目的（ユーザー確認済み）
- YouTubeを動画の配信・視聴・共有先として使い、**Google Driveへの動画保存を必須にしない**。
- AD&Cチャットから投稿を依頼する。YouTube投稿は **非公開(private)で固定**、公開／限定公開の選択は人間に渡す。
- Google Driveを一時経由した場合、YouTube側への取り込みを確認後、元のDrive動画を整理・削除して容量負担を下げる。
- 一般利用者への案内はシンプルに。YouTubeチャンネル開設ナビと動画管理ページは別ページとし、UIを揃える。

## 実装状況と入力経路（重要）

| 経路 | 利用場面 | 現状 | 必要な追加 |
|---|---|---|---|
| A. ローカル動画 → ブラウザ管理ページ → YouTube | PCやスマホで動画を持つ利用者。**Drive不要** | `videos.html` + `videos.js` が候補実装済み。Google実機認証・投稿テストは未実施 | OAuth、ブラウザ・端末実機テスト、処理ステータス確認 |
| B. チャットに動画添付 → YouTube | **最終目標。** ChatGPTから添付動画を直接指示 | **未実装**。現行MCPはチャット添付の動画バイト列を受け取れない。添付だけで自動投稿できるとは言わない | ChatGPTからMCPへの実ファイル受け渡し方式（短命認証付き転送・対応file URI等）の成立検証と実装 |
| C. Google Drive上の既存動画 → MCP Worker → YouTube | すでにDriveにある素材をチャットから登録 | `upload_private_from_drive` は実装候補。Worker未配置／実投稿未検証。現状Drive **readonly** | 実認証、チャンネル照合、アップロード、処理確認。後述するDrive整理機能の権限と操作を別途設計 |

**標準の利用者体験は A または B、C は既存動画を扱う補助手段**。ユーザーにDriveへのアップロードを強制しない。

## 標準状態遷移

1. `source_selected` : 動画原本の所在（local/chat/Drive）とタイトル等を指定。
2. `upload_requested` : 本人の投稿指示を受けたときだけ実行。投稿先チャンネルID照合、冪等キーで二重投稿を防止。
3. `uploading` → `youtube_private_created`: `videos.insert` で `privacyStatus=private` を指定。APIレスポンスだけをもって完了とみなさない。
4. `processed_private_verified`: YouTube `videos.list` で動画ID、公開状態、アップロード・処理状況を再確認。処理中なら保留。
5. `awaiting_human_publication`: 人間に管理画面を提示。「この画面から公開範囲を更新してください」。動画一覧、URLコピー、限定公開/公開変更。
6. `drive_cleanup_eligible` (Cのみ): YouTube側の動画が成功・処理済みであること、元DriveファイルIDとの紐付け、所有・権限を検査。
7. `drive_trashed` (Cのみ、**明示的に設定した自動整理ポリシー**に該当するとき): 復元可能なゴミ箱移動。失敗・未確認・ユーザー未承認時は保持。初期試験での永久削除禁止。

**公開範囲の変更と元Driveファイルの削除は別の判断**。Driveの整理ポリシーが明示されていれば公開判断前にゴミ箱へ移せる設計も可能だが、投稿処理完了を先に確認し、まず実動画による安全検証を行う。

## Drive整理の安全条件（まだコードには未実装）

- YouTube動画がID取得済み、privateで処理完了。元ファイルの対象IDを処理台帳に記録。中断・不明時は削除せず `needs_manual_check`。
- **そのジョブで使用した元のDrive動画のみ**を対象にする。フォルダ一括削除や既存共有ファイルの削除はしない。
- 本人が「投稿成功した一時動画を自動でゴミ箱へ移す」方針を有効化した場合に限る（最初の実行試験は保持）。
- ゴミ箱移動にはDriveの追加書込権限が必要。現在の `drive.readonly` ではできない。権限は必要最小限とし、OAuth再同意を伴う仕様変更前に説明する。
- ゴミ箱移動は `files.update(..., {trashed:true})`、永久削除用 `files.delete` は使用しない。
- チャット/リポジトリ/共有KBにはOAuth token、client secret、秘密ZIPを載せない。

## YouTubeを共有先に使う際の限界

- **Private**: 原則、所有者または個別に許可された利用者のみ視聴。単に動画URLをAIや他人へ送っても再生できない。
- **Unlisted（限定公開）**: URLを知る相手は視聴でき、転送・再共有もできる。秘匿性が必要な個人・企業情報には不向き。
- **Public**: 広く検索・視聴可能。利用者が明示的に選んだ場合に限る。
- YouTubeは動画の閲覧・配信プラットフォームであり、**元MP4の長期原本保管や可逆なファイルストレージではない**。YouTube側で動画が再エンコードされ、元の編集用素材や元ファイルを復元できることは保証しない。マスター映像は別途バックアップを推奨。
- APIでの公開変更はプロジェクトの監査・APIポリシーの制限を受ける可能性があり、**限定公開への変更が実際に可能かを実検証するまで保証しない**。
- ChatGPT以外のAIがYouTube URLの**映像そのものを再生・視認できるとは限らない**。共有できたこととレビューできたことを分ける。

## 今回のGoogle Cloud認証の進行

利用者は `WPGARankking` Google CloudプロジェクトをAD&C用途として使用する意向を表明済み。
YouTube Data API v3、Drive APIの有効化は利用者申告で済み。Google Auth Platformの概要画面表示まで確認済み。
次は「対象（Audience）」画面を開いて外部／テストユーザーの実設定を確認し、OAuthクライアント作成へ進む。

## 実施順序

1. 現在のOAuth初回設定を完了して **A: Driveを通さないブラウザからのprivate動画登録** を試す。
2. 公開範囲変更／URLコピーの人間UIが正常に動作することを検証する。
3. C: DriveからのMCPを初回接続し、実際にprivate投稿できることを検査する。
4. Cの元Drive一時動画を対象に、ユーザー許可後でゴミ箱移動の安全試験を行う。
5. B: チャット添付直結を別試験として検証・実装。現行ツールが持つファイル受渡しの制約を実測する。

## 公式資料（操作案内前に都度再確認）
- YouTube upload: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
- YouTube動画閲覧範囲: https://support.google.com/youtube/answer/157177?hl=ja
- YouTube API動画リソース・監査関連: https://developers.google.com/youtube/v3/docs/videos?hl=ja
- Google Driveゴミ箱操作: https://developers.google.com/workspace/drive/api/guides/delete

案内末尾の定型文: **「わからないところは教えてください。現在の画面に合わせて案内します。」**
