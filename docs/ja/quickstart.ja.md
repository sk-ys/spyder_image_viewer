# Spyder Image Viewer Plugin - クイックスタート

約 5 分で使い始められます。

## 1. インストール

```bash
cd spyder_image_viewer
pip install .
```

## 2. Spyder再起動

```bash
spyder
```

## 3. テスト配列を作成

Spyderコンソールで実行：

```python
import numpy as np

img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
img10 = np.random.randint(0, 256, (100, 100, 10), dtype=np.uint8)
```

## 4. Image Viewerで開く

1. 変数エクスプローラーで変数をクリック
2. `Image Viewer` ドックを確認
3. ズームとチャネル切り替えをテスト

## 便利な確認項目

- ズームを `3000%` にする
- `Show Pixels` を有効化
- ホバーで `Coord（座標）` + `Intensity/Value（輝度値/値）` を表示
- 3チャネル以上で `full` のとき、Order: `RGB/BGR` を切り替え可能

## よくある問題

### `No module named spyder_image_viewer`

```bash
pip install .
```

このエラーは、プラグインが現在のPython環境に未インストールのときに発生します。

### プラグインが見つからない

以下を開く：

`View -> Docks -> Image Viewer`

### 配列が拒否される

サポートされている形状を使用：

- `(H, W)`
- `(H, W, C)` ここで `C >= 1`

## 次のドキュメント

- `docs/ja/development_guide.ja.md`
- `docs/quickstart.md`


