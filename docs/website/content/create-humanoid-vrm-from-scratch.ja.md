---
title: "人型のVRMモデルを作る"
description: "VRM Add-on for Blender: 人型のVRMモデルを作る"
---

シンプルな人型のVRMモデルを作ります。

<img src="../../images/humanoid.gif">

Blenderを起動したら、3Dビューポートにマウスカーソルを置き、 `n` キーを押してください。

<img src="../images/humanoid1.png">

すると右側からサイドバーが開くので `VRM` のタブを選択し `VRMモデルを作成` ボタンを押してください。

<img src="../images/humanoid2.png">

するとVRM出力に適したアーマチュアが自動で作られます。アーマチュアとは3Dモデルのボーンの構造を
表すデータで、このアドオンではVRMの人型の骨格を表すためにアーマチュアを使います。

<img src="../images/humanoid3.png">

デフォルトで置いてある立方体を胴体にします。ただこのままでは胴体とするには大きすぎるので、まずは右上の `シーンコレクション` から `Cube` を選択、次にサイドバーの`アイテム` から `寸法` を選び、値を全て `0.4 m` にします。これで胴体として使えそうな大きさになります。

<img src="../images/humanoid4.png">

胴体をアーマチュアのボーンに関連付けます。右下の四角いアイコンのタブを選び、 `関係` から `ペアレント` を `アーマチュア` または `Armature` にし、 `親タイプ` を`ボーン` とし、`親ボーン` を `spine` に設定してください。胴体が3Dモデルの腰あたりに移動します。

<img src="../images/humanoid5.png">

次は頭を作ります。3Dビューポートで `Shift + A` を押すと追加メニューが出るので `メッシュ` → `UV球` と選んでください。

<img src="../images/humanoid6.png">

`球` あるいは `Sphere` が追加されます。

<img src="../images/humanoid7.png">

これを頭として使いたいのですが、大きすぎるので縮小します。右上の `シーンコレクション` から `球` あるいは `Sphere` を選択、次にサイドバーの `アイテム` から `寸法` を選び、値を全て `0.5 m` にします。

<img src="../images/humanoid8.png">

この球をアーマチュアのボーンに関連付けます。右下の四角いアイコンのタブを選び、 `関係` から `ペアレント` を `アーマチュア` または `Armature` にし、 `親タイプ` を`ボーン` とし、 `親ボーン` を `head` に設定してください。球が3Dモデルの頭あたりに移動します。

<img src="../images/humanoid9.png">

次は手足を追加します。3Dビューポートで `Shift + A` を押すと追加メニューが出るので `メッシュ` → `ICO球`と選んでください。

<img src="../images/humanoid10.png">

`ICO球` あるいは `Icosphere` が追加されますが、同時に3Dビューポート左下に `> ICO球を追加` という表示が出ます。こちらをクリックします。

<img src="../images/humanoid11.png">

すると、新しく追加するICO球の設定をすることができます。半径が大きすぎると感じたので、半径の値を `0.1 m` に変更します。

<img src="../images/humanoid12.png">

ICO球を手足のアーマチュアのボーンに関連付けます。右下の四角いアイコンのタブを選び、 `関係` から `ペアレント` を `アーマチュア` または `Armature` にし、`親タイプ`を `ボーン` とし、`親ボーン` を `upper_arm.L` に設定してください。球が3Dモデルの左ひじあたりに移動します。

<img src="../images/humanoid13.png">

先ほどと同様にICO球を追加し、次は `hand.L` ボーンに関連付けます。左手あたりにICO球が配置されます。

<img src="../images/humanoid14.png">

同様に、今度は `upper_arm.R` ボーンに関連付けます。

<img src="../images/humanoid15.png">

同様に `hand.R` ボーンに関連付けます。

<img src="../images/humanoid16.png">

同様に `upper_leg.L` ボーンに関連付けます。

<img src="../images/humanoid17.png">

同様に `lower_leg.L` ボーンに関連付けます。

<img src="../images/humanoid18.png">

同様に `upper_leg.R` ボーンに関連付けます。

<img src="../images/humanoid19.png">

最後に `lower_leg.R` ボーンに関連付けます。

<img src="../images/humanoid20.png">

このモデルをVRMとして保存します。メニューの `ファイル` → `エクスポート` → `VRM` を選択します。

<img src="../images/simple2.png">

ファイル保存用のウィンドウが出るので、ファイル名と保存先を入力し `Export VRM` を押します。

<img src="../images/simple3.png">

成功するとVRMファイルが指定された場所に保存されます。

<img src="../../images/humanoid.gif">

## 関連リンク

- [トップページ]({{< ref "/" >}})
- [シンプルなVRMモデルを作る]({{< ref "create-simple-vrm-from-scratch" >}})
