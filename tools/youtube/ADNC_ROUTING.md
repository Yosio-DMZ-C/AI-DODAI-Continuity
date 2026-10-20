# AD&C / YouTube操作ルーティング v0.3

## 初回認証・未接続時の標準プロセス（追加 2026-10-20）

1. **毎回** Google Auth Platform / YouTube Data API / Cloudflare Workers の公式資料をWeb検索し、確認日と更新された項目を短く記録。過去のUI名称を未検証で押し付けない。
2. `check_connection` が利用可能なら最初に実行。`ready` なら設定作業を提案せず、そのままチャンネルIDと非公開指定を検査。未接続なら下記の案内をユーザーへ提示。
3. **ユーザー向けの第一声**：「初回だけGoogle CloudでAPI・OAuth設定を行い、Cloudflare Workerへ安全に接続します。次の公式画面から順に操作してください。秘密鍵・トークン・JSONをチャットへ貼らないでください。**わからないところは教えてください。現在の画面に合わせて案内します。**」
4. `INITIAL_AUTH_GUIDE.md` に沿って **一度に短い工程だけ**提示する。ユーザーが途中で困ったら、その画面の実際のラベルを確認し、手順差分を修正。長いコマンド一括提示を初手で行わない。
5. Google CloudのTesting+ExternalはRefresh Tokenが通常7日で期限切れ。継続運用はプロジェクト公開ステータス・確認要件を検証。期限切れ時は `setup_once.py` を再実行、秘密情報は出力しない。
6. CloudflareへのSecret登録とプライベートプラグインのChatGPTへの接続は利用者が明示操作。**実機の認証・投稿は未実行なら未実行と報告**。
7. 接続後 `check_connection` → `list_uploaded_videos` → `upload_private_from_drive` （ユーザーが投稿指示した場合）→ `private_verified` → 管理画面で人間に公開判断を渡す。

## チャット実行時

1. **チャンネルを作りたい / 作れない**：`channel.html` に案内する。YouTubeではチャンネル作成のAPIはなく公式画面で人間が作る。iPhoneでPC版サイト案内。過去の事例では名前に `|` があると登録に失敗したため、まず `AD&C - AI-DODAI & Continuity` など区切り記号を変更して試す。ただし`|`がYouTube一般禁止文字と断定しない。必ず最後に「チャンネル開設ナビ」へのリンクを再提示する。
2. **動画をアップロード**：MCP接続済・`check_connection`で`ready`かつDrive動画IDが確認できる場合のみ `upload_private_from_drive`。未接続なら `videos.html` を提示し手動選択＋OAuthを案内。**チャットへの依頼は動画の非公開登録だけ**。
3. **アップロード直後**：動画ID・URL・公開状態の取得が成功したら **「非公開アップロード済み。公開範囲とURLは動画管理ページから確認・更新してください」** と `videos.html` を提示。
4. **限定公開・公開へ変更**：必ず管理ページ（またはYouTube Studio）で人間が手動選択。チャットMCP側に勝手に公開できるツールを置かない。
5. **URLがほしい**：`list_uploaded_videos` などでURL取得後、`private` のURLは第三者閲覧不可と伝える。レビュー共有が目的なら人間の `unlisted` 変更後の視聴確認を推奨。
6. **チャットへ結果を返す**：「実際に呼び出したツール」と「確認した公開範囲」を区別する。未認証・未デプロイを成功扱いしない。

## UIと安全性

- ページは **2枚に分離**：開設 `channel.html`／動画 `videos.html`。元の配色・入力欄・ボタンのパターンを踏襲。
- 既存元ファイル `ADNC_YouTube_iPhone_Navi_v0.1.html` は変更しない。
- ブラウザはユーザー操作を要するOAuthを使用。バックグラウンド自動投稿を偽装しない。
- Workerはアップロード時privateに固定。DriveファイルID以外の外部URLを受け付けない。毎回同じrequest_keyを使い、結果不明時は自動再試行せず調査する。
- OAuthやMCP用秘密情報をGitHub、ブラウザlocalStorage、AD&C共有KBに保存しない。
