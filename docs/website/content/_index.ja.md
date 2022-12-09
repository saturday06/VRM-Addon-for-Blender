---
title: "VRM Add-on for Blender"
description: "VRM Add-on for BlenderはBlenderにVRMのインポート、エクスポートや編集機能を追加するアドオンです。"
images: ["ja/images/top.png"]
---

![](images/top.png)

VRM Add-on for BlenderはBlenderにVRMのインポート、エクスポートや編集機能を追加するアドオンです。バージョン2.83以降のBlenderに対応しています。

**[最新版のダウンロード {{< release_ja >}}](https://github.com/saturday06/VRM_Addon_for_Blender/raw/release-archive/VRM_Addon_for_Blender-release.zip)**<small> / [過去のバージョン一覧](https://github.com/saturday06/VRM_Addon_for_Blender/releases)</small>

## 使い方

| [アドオンのインストール]({{< ref "installation" >}}) | [シンプルなVRMモデルを作る]({{< ref "create-simple-vrm-from-scratch" >}}) | [人型のVRMモデルを作る]({{< ref "create-humanoid-vrm-from-scratch" >}}) |
| --- | --- | --- |
| [![](images/installation.png)]({{< ref "installation" >}}) | [![](../../images/simple.gif)]({{< ref "create-simple-vrm-from-scratch" >}}) | [![](../../images/humanoid.gif)]({{< ref "create-humanoid-vrm-from-scratch" >}}) |

## 概要

BlenderにVRMのインポートやエクスポート、VRM Humanoidの追加などのVRM関連機能を追加するアドオンです。バグ報告、機能要望、Pull Request等歓迎します。[バージョン 0.79](https://github.com/saturday06/VRM_Addon_for_Blender/archive/0_79.zip)以降の開発をオリジナル版のメンテナである[@iCyP](https://github.com/iCyP)さんから引き継ぎました。

## インポート

- VRM 0.0のインポート
- 実験的な、VRM 1.0のインポート
- 「テクスチャ画像をフォルダに展開」オプションを有効にすると、100,000フォルダを上限にインポートごとに新たなテクスチャフォルダを作成します。

## 編集

- VRMエクステンションの編集パネル
  !["UI Panel"](images/ui_panel.png)
- VRM向けシェーダーノードグループ(※モックアップ程度の出来)
  - MToon_unversioned
  - TransparentZwrite
- VRM向けHumanoid Armature追加機能
  - (これを使わないとエクスポート出来ません)(絶対に出来ないとは言ってないけど圧倒的に楽)

## エクスポート

- VRM 0.0のエクスポート
- 実験的な、VRM 1.0のエクスポート

## 旧バージョン(1.x)のチュートリアル

### VRM出力チュートリアル

https://qiita.com/iCyP/items/61af0ea93c604e37bed6

### VRM編集の動画チュートリアル

https://www.nicovideo.jp/watch/sm36033523
