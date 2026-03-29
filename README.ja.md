# Spyder Image Viewer Plugin

Spyder IDE向けの軽量NumPy配列画像ビューアープラグインです。

<table><tr>
<td><img src="docs\images\sample1.png"></td>
<td><img src="docs\images\sample2.png"></td>
</tr></table>

## 注意

このプラグインは、ほぼ100% GitHub Copilot によって生成されました。

## 🎯 特徴

- **軽量・高速**: 従来の変数エクスプローラーの重い表示を回避
- **専用ドックウィジェット**: 変数エクスプローラーとタブで並列表示
- **ズーム機能**: 10% ～ 3000%まで柔軟に拡大・縮小
- **ピクセル値表示**: ズーム時にピクセルの詳細情報を表示
- **配列形状対応**:
  - 2次元配列: H×W
  - 3次元配列: H×W×C（C >= 1、チャネル数制限なし）
- **データ型対応**:
  - uint8, uint16, int32, float32, float64など

## 📋 前提条件

- Python >= 3.7
- Spyder >= 5.0
- NumPy >= 1.19
- QtPy >= 2.0

## 📦 インストール

### オプション1: PyPI からインストール（推奨）

```bash
pip install spyder-image-viewer
```

インストール後、Spyder を再起動するとプラグインが有効になります。

### オプション2: 開発モード（ローカル開発用）

```bash
cd spyder_image_viewer
pip install -e .
```

ソースコードの変更が即座に反映されます。

### オプション3: ソースから標準インストール

```bash
cd spyder_image_viewer
pip install .
```

### インストール検証

再起動後、Spyderで確認：

```
Tools → Preferences → Plugins
```

`Image Viewer` が有効になっているか確認します。

## 🚀 使用方法

### 基本的な使い方

1. Spyderを起動
2. コンソールで画像配列を作成：
   ```python
   import numpy as np
   img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
   ```
3. 変数エクスプローラーで `img` を選択
4. 「Image Viewer」ドックに自動的に表示される

### ズーム操作

| 操作 | 説明 |
|------|------|
| ズームスライダー | 10% ～ 3000%で拡大・縮小 |
| マウスホイール | スクロール |
| Ctrl+ホイール | 非線形ズーム |
| Show Pixels | 一時的に3000%にジャンプして戻す |
| Channel セレクタ（3D） | `full` または per-channel グレースケール |
| ホバーツールチップ | 座標 + intensity/value |

## 🏗️ ディレクトリ構成

```
spyder_image_viewer/
├── setup.py
├── setup.cfg
├── README.md
├── README.ja.md
├── docs/
│   ├── quickstart.md
│   ├── development_guide.md
│   └── ja/
│       ├── quickstart.ja.md
│       └── development_guide.ja.md
├── spyder_image_viewer/
│   ├── plugin.py
│   ├── widgets/
│   │   └── image_viewer.py
│   └── utils/
│       └── array_validator.py
└── tests/
    └── manual_test_image_viewer.py
```

## 📚 ドキュメント

- **docs/quickstart.md** - クイックスタート（英語）
- **docs/development_guide.md** - プラグイン開発ガイド（英語）
- **docs/ja/quickstart.ja.md** - クイックスタート（日本語）
- **docs/ja/development_guide.ja.md** - プラグイン開発ガイド（日本語）

## 🧪 テスト

テストスクリプトを実行：

```bash
python tests/manual_test_image_viewer.py
```

Spyderコンソールで実行：

```python
exec(open('tests/manual_test_image_viewer.py').read())
```

## 🔧 トラブルシューティング

### プラグインが見つからない

1. 再インストール：

```bash
pip uninstall spyder-image-viewer
pip install -e .
```

2. Spyder を完全に再起動します。

3. キャッシュをクリアする場合：

```bash
rm -rf ~/.spyder-py3/
```

### ドックが隠れている

```
View → Docks → Image Viewer
```

### 「Not a valid image array」と表示される

配列の形状を確認：

```python
from spyder_image_viewer.utils import is_image_array
print(is_image_array(your_array))
```

サポート形状：

- 2D: `(H, W)`
- 3D: `(H, W, C)` ここで `C >= 1`

## 🎨 サポート配列形状

| 種別 | 形状 | 説明 |
|------|------|------|
| 2次元配列 | (H, W) | 単一チャネル画像として表示 |
| 3次元配列 | (H, W, C) | C >= 1 の任意チャネル数に対応 |

例: (H, W, 10) のような 10 チャネル配列も表示可能です。

## 📊 データ型サポート

- `uint8` - 8ビット符号なし整数（推奨）
- `uint16` - 16ビット符号なし整数
- `int32` - 32ビット符号付き整数
- `float32` - 32ビット浮動小数点
- `float64` - 64ビット浮動小数点

**浮動小数点配列の場合:**

- [0, 1] 範囲は自動的に [0, 255] にスケール
- [0, 255] 範囲はそのまま使用
- その他の範囲は正規化

## 📝 開発

### プラグインコンポーネント

| ファイル | 説明 |
|---------|------|
| `plugin.py` | Spyderプラグイン定義、Variable Explorer統合 |
| `widgets/image_viewer.py` | UI、ズーム、レンダリングロジック |
| `utils/array_validator.py` | 配列形式チェック・正規化 |

### 開発ワークフロー

1. ソースコードを編集
2. `pip install -e .`（必要な場合）
3. Spyderを再起動
4. 2D/3D配列でテスト

## 📄 ライセンス

MIT License


