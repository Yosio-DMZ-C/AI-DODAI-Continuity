---
name: adnc-youtube-private
summary: YouTubeへGoogle Drive上の動画を非公開アップロード、直近動画一覧を取得する。
---
# AD&C YouTube (非公開アップロード限定)

- チャンネル作成は公式画面で行う。開設ナビ `channel.html` に案内。
- チャットから投稿する場合、Drive上の動画ファイルID、タイトル、子ども向けか否かを確認する。
- `list_uploaded_videos` で登録先チャンネルを事前確認し、利用者の意図したチャンネルと一致する場合だけ `upload_private_from_drive` を使用する。
- `request_key` は同一アップロード試行で固定し、結果不明・通信断で別キーを作って自動再実行しない。
- **公開範囲はprivate固定**。後で人間が `videos.html` を開いて限定公開／公開／URLコピーを操作する。
- 投稿後はレスポンスの `private_verified` を確認し、URLと「この画面から更新してください」を付けて `videos.html` を案内。
- ツール未接続／未デプロイの場合は投稿できたと主張せず、ブラウザ版に案内。
