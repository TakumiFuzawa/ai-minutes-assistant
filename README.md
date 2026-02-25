# 🎙️ AI議事録生成アシスタント (Ver1.0)

音声ファイルをアップロードするだけで、OpenAIのWhisperとGPTを活用して「文字起こし」から「要約・TODO抽出」までを自動で行うWebアプリケーションです。

## 📺 デモ動作

![アプリのデモ動画](C:\Users\麸澤拓海\Pictures\Screenshots/Animation.gif)

## ✨ 主な機能
- **自動文字起こし**: OpenAI Whisper APIによる高精度な音声解析
- **インテリジェント要約**: 会議の要点とネクストアクション（TODO）を自動抽出
- **スマートUI**: 
  - 直感的なアコーディオン形式の履歴表示
  - **ワンクリック・コピー機能**（要約やTODOを即座に共有可能）
- **クリーンな管理**: 削除時にサーバー上の音声ファイルも自動消去する物理削除機能

## 🛠️ 技術スタック
- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla JS)
- **Database**: SQLite / SQLAlchemy
- **AI**: OpenAI API (Whisper & GPT-4o)

## 🚀 使い方
1. リポジトリをクローン
2. `.env` ファイルを作成し `OPENAI_API_KEY` を設定
3. `pip install -r requirements.txt` でライブラリをインストール
4. `uvicorn main:app --reload` で起動！

## 👤 こだわりポイント
- **ユーザー体験**: 削除時の確認ダイアログや、コピー完了時の視覚的なフィードバックなど、細かな使い勝手にこだわりました。
- **リソース管理**: データベースのレコード削除と連動して、ストレージ内の不要な音声ファイルを物理削除するロジックを実装し、サーバーのクリーンさを保つ設計にしています。
