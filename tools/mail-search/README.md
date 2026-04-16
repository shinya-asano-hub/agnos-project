# メール検索ツール

Agnosブランドのメール検索ウェブアプリ。macOSのメールアプリ＋Gmail/Outlookウェブ検索に対応。

## 起動方法

```bash
python3 mail_search_server.py
```

起動後、ブラウザで http://localhost:8877 を開く。

## 機能

- 全画面ローディングアニメーション（Agnos公式ロゴ）
- アカウント切替: 全メール / Gmail / Agnos
- 件名検索（AppleScriptメールアプリ経由）
- Gmail/Outlookウェブ検索ボタン（キーワード自動転送）

## ファイル

- `mail_search.html` - UIフロントエンド
- `mail_search_server.py` - バックエンドサーバー（Python標準ライブラリのみ）

## 技術構成

- ローカルHTTPサーバー（port 8877）
- AppleScriptでメールアプリ検索
- Vanilla JavaScript（フレームワークなし）
