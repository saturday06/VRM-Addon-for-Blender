---
title: "VRM Animation（.vrma）のエクスポート"
description: "BlenderからVRM Animation（.vrma）を書き出す方法と含まれるデータを説明します。"
---

メニューの `ファイル` → `エクスポート` → `VRM Animation (.vrma)`
を選択することで、 [VRM Animation](../../animation/)
のエクスポートダイアログが表示されます。

![](1.png)

`保存` ボタンを押すと、シーンに配置されているVRM
1.0に割り当てられているアニメーションのうち、
次に条件に当てはまるものがVRMAファイルとしてエクスポートされます。

- VRM Humanoidボーンに割り当てられているボーンの回転値
- VRM Humanoidボーンのうち、Hipsボーンに割り当てられているボーンの移動値
- VRM Expressionsのプレビューの値
- VRM Look AtのPreview Targetに指定されているオブジェクトの移動値
