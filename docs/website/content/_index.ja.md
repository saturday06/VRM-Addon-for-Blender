---
title: "VRM Add-on for Blender"
description: "VRM Add-on for BlenderはBlenderにVRMのインポート、エクスポートや編集機能を追加するアドオンです。"
images: ["ja/images/top.png"]
---

![](images/top.png)

VRM Add-on for BlenderはBlenderにVRMのインポート、エクスポートや編集機能を追加するアドオンです。バージョン2.83以降のBlenderに対応しています。

**[最新版のダウンロード {{< release_ja >}}](https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip)**<small> / [過去のバージョン一覧](https://github.com/saturday06/VRM-Addon-for-Blender/releases)</small>

## 使い方

| [アドオンのインストール]({{< ref "installation" >}}) | [シンプルなVRMモデルを作る]({{< ref "create-simple-vrm-from-scratch" >}}) | [人型のVRMモデルを作る]({{< ref "create-humanoid-vrm-from-scratch" >}}) |
| --- | --- | --- |
| [![](../../images/installation.gif)]({{< ref "installation" >}}) | [![](../../images/simple.gif)]({{< ref "create-simple-vrm-from-scratch" >}}) | [![](../../images/humanoid.gif)]({{< ref "create-humanoid-vrm-from-scratch" >}}) |

| [物理ベースのマテリアル設定]({{< ref "installation" >}}) | [アニメ風のマテリアル設定]({{< ref "create-simple-vrm-from-scratch" >}}) | |
| --- | --- | --- |
| [![](../../images/material_pbr.gif)]({{< ref "material-pbr" >}}) | [![](../../images/material_mtoon.gif)]({{< ref "material-mtoon" >}}) | ![](../../images/transparent.gif) |

## 概要

BlenderにVRMのインポートやエクスポート、VRM Humanoidの追加などのVRM関連機能を追加するアドオンです。バグ報告、機能要望、Pull Request等歓迎します。[バージョン 0.79](https://github.com/saturday06/VRM-Addon-for-Blender/archive/0_79.zip)以降の開発をオリジナル版のメンテナである[@iCyP](https://github.com/iCyP)さんから引き継ぎました。

## インポート

- VRM 0.0, 1.0のインポート
- 「テクスチャ画像をフォルダに展開」オプションを有効にすると、100,000フォルダを上限にインポートごとに新たなテクスチャフォルダを作成します。

## 編集

- VRMエクステンションの編集パネル
- VRM向けシェーダーノードグループ(※モックアップ程度の出来)
  - MToon_unversioned
  - TransparentZwrite
- VRM向けHumanoid Armature追加機能
  - (これを使わないとエクスポート出来ません)(絶対に出来ないとは言ってないけど圧倒的に楽)

## エクスポート

- VRM 0.0, 1.0のエクスポート
