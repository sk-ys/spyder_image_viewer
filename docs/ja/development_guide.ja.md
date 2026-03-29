# Spyder Image Viewer Plugin - 実装ガイド

このドキュメントでは、現在のプラグインアーキテクチャと拡張ポイントについて説明します。

## 現在の構造

```text
spyder_image_viewer/
├── setup.py
├── setup.cfg
├── docs/
│   ├── quickstart.md
│   ├── development_guide.md
│   └── ja/
│       ├── quickstart.ja.md
│       └── development_guide.ja.md
└── spyder_image_viewer/
    ├── plugin.py
    ├── widgets/
    │   └── image_viewer.py
    └── utils/
        └── array_validator.py
```

## コアコンポーネント

## `plugin.py`

- `ImageViewerPlugin` (`SpyderDockablePlugin`) を定義
- Variable Explorer と統合
- `Open in Image Viewer` コンテキストアクション を追加
- 独立したポップアップウィンドウに対応

## `widgets/image_viewer.py`

- メイン UI とレンダリングロジック
- 高速ビューポート専用ペインタ (`_FastImageLabel`)
- ズームモデル (`10%` ～ `3000%`)
- Ctrl+ホイール非線形ズーム
- 高ズームモードでのピクセルグリッド/値オーバーレイ
- 座標と値を表示するホバーツールチップ

## `utils/array_validator.py`

- `is_image_array`: `(H, W)` と `(H, W, C)` (`C >= 1`) に対応
- `normalize_image_array`: 表示データを `uint8` に変換

## レンダリング挙動

- ニアレストネイバー表示 (`SmoothPixmapTransform = False`)
- スクロール + ズームアンカー保持
- オーバーレイは表示ビューポート内のみ描画

## チャネル挙動

- 2D: グレースケールモード
- 3D: `full` + per-channel 選択
- 3チャネル以上の配列では、`full` は先頭3チャネルでカラー画像を描画
- `Order` セレクタで `RGB` / `BGR` を切り替え可能（full モード時）
- Full モードのツールチップは全チャネル値を表示可能

## パッケージング

`setup.py` はプラグインを以下で登録します:

```python
entry_points={
    "spyder.plugins": [
        "image_viewer = spyder_image_viewer.plugin:ImageViewerPlugin",
    ]
}
```

## 推奨開発ワークフロー

1. コードを編集
2. `pip install -e .` (必要に応じて)
3. Spyder を再起動
4. 2D および 3D 配列でテスト (マルチチャネル 3D を含む、例: `C=10`)

## 関連ドキュメント

- `docs/ja/quickstart.ja.md`
- `docs/development_guide.md`

