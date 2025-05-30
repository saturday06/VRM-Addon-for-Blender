---
title: VRM Add-on for Blender
description: VRM Add-on for BlenderはBlenderにVRMのインポート、エクスポートや編集機能を追加するアドオンです。
aside: false
outline: false
prev: false
next: false
---

<style>
  img[src$=".gif"], img[src^="data:image/gif;"] {
    max-width: 175px; /* テーブルタグで横スクロールバーが出ないように調整 */
  }
</style>

![](top.png)

VRM Add-on for
Blenderは、BlenderにVRMのインポート、エクスポートや編集機能を追加するアドオンです。バージョン2.93から4.4のBlenderに対応しています。

## ダウンロード

- Blender 4.2以上をお使いの場合
  [Blender Extensions Platform](https://extensions.blender.org/add-ons/vrm)
  経由でダウンロードをお願いします。
- Blender 2.93から4.1をお使いの場合はこちら: <DownloadLinkJa />\
  <small>[過去のバージョン一覧](https://github.com/saturday06/VRM-Addon-for-Blender/releases)</small>

## 使い方

| [アドオンのインストール](installation/)                 | [シンプルなVRMモデルを作る](create-simple-vrm-from-scratch/)      | [人型のVRMモデルを作る](create-humanoid-vrm-from-scratch/)            |
| ------------------------------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------- |
| [![](/assets/images/installation.gif)](installation/)   | [![](/assets/images/simple.gif)](create-simple-vrm-from-scratch/) | [![](/assets/images/humanoid.gif)](create-humanoid-vrm-from-scratch/) |
| [物理ベースのマテリアル設定](material-pbr/)             | [アニメ風のマテリアル設定](material-mtoon/)                       | [VRMアニメーション](animation/)                                       |
| [![](/assets/images/material_pbr.gif)](material-pbr/)   | [![](/assets/images/material_mtoon.gif)](material-mtoon/)         | [![](/assets/images/animation.gif)](animation/)                       |
| [Pythonスクリプトによる自動化](scripting-api/)          | [改造するには](development/)                                      |                                                                       |
| [![](/assets/images/scripting_api.gif)](scripting-api/) | [![](/assets/images/animation.gif)](development/)                 |                                                                       |

## 概要

BlenderにVRMのインポートやエクスポート、VRM
Humanoidの追加などのVRM関連機能を追加するアドオンです。バグ報告、機能要望、Pull
Request等歓迎します。[バージョン 0.79](https://github.com/iCyP/VRM_IMPORTER_for_Blender2_8/releases/tag/0.79)以降の開発を作者である[@iCyP](https://github.com/iCyP)さんから引き継ぎました。
