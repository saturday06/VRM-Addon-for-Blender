---
title: "VRM Add-on for Blender"
description: "VRM Add-on for BlenderはBlenderにVRMのインポート、エクスポートや編集機能を追加するアドオンです。"
images: ["ja/images/top.png"]
---

<style>
main header {
  display: none;
}

main article.prose section :where(p, img):not(:where([class~=not-prose] *)) {
  margin-top: 0;
}
</style>

![](images/top.png)

**[最新版のダウンロード {{< release_ja >}}](https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip)**<small> / [過去のバージョン一覧](https://github.com/saturday06/VRM-Addon-for-Blender/releases)</small>

VRM Add-on for BlenderはBlenderにVRMのインポート、エクスポートや編集機能を追加するアドオンです。バージョン2.83以降のBlenderに対応しています。

## 使い方

| [アドオンのインストール]({{< ref "installation" >}}) | [シンプルなVRMモデルを作る]({{< ref "create-simple-vrm-from-scratch" >}}) | [人型のVRMモデルを作る]({{< ref "create-humanoid-vrm-from-scratch" >}}) |
| --- | --- | --- |
| [![](../../images/installation.gif)]({{< ref "installation" >}}) | [![](../../images/simple.gif)]({{< ref "create-simple-vrm-from-scratch" >}}) | [![](../../images/humanoid.gif)]({{< ref "create-humanoid-vrm-from-scratch" >}}) |

| [物理ベースのマテリアル設定]({{< ref "material-pbr" >}}) | [アニメ風のマテリアル設定]({{< ref "material-mtoon" >}}) | |
| --- | --- | --- |
| [![](../../images/material_pbr.gif)]({{< ref "material-pbr" >}}) | [![](../../images/material_mtoon.gif)]({{< ref "material-mtoon" >}}) | ![](../../images/transparent.gif) |

## 概要

BlenderにVRMのインポートやエクスポート、VRM Humanoidの追加などのVRM関連機能を追加するアドオンです。バグ報告、機能要望、Pull Request等歓迎します。[バージョン 0.79](https://github.com/iCyP/VRM_IMPORTER_for_Blender2_8/releases/tag/0.79)以降の開発を作者である[@iCyP](https://github.com/iCyP)さんから引き継ぎました。

## インポート

- VRM 0.0, 1.0のインポート
- 「テクスチャ画像をフォルダに展開」オプションを有効にすると、100,000フォルダを上限にインポートごとに新たなテクスチャフォルダを作成します。

## 編集

- VRMエクステンションの編集パネル
- VRM向けシェーダーノードグループ(※モックアップ程度の出来)
  - MToon_unversioned
- VRM向けHumanoid Armature追加機能
  - (これを使わないとエクスポート出来ません)(絶対に出来ないとは言ってないけど圧倒的に楽)

## エクスポート

- VRM 0.0, 1.0のエクスポート
