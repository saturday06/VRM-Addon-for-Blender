# VRM_IMPORTER_for_Blender2.8
- current :for blender 2.81
- mesh import : done 
- material import : wip forever
- export : spec0.0 export may be possible.

# 機能
 - VRM import
    - vrmの物理拡張などの設定はblender内蔵テキストエディタに出力、アーマチュアのオブジェクトカスタムプロパティにそのパスが書かれます
    - モデルライセンスはアーマチュアのオブジェクトカスタムプロパティに出力されます
    - humanoidボーン属性はVRM　HELPERタブからアクセス可能です
    - これらはVRMエクスポート時に利用されます（詳しくは下部の図を参照
 - VRM 向けシェーダーノードグループ追加(※モックアップ程度の出来)(GLTF,MToon_unversioned,TransparentZwrite)
 - VRM 向けhumanoid Armature 追加(これを使わないとexport出来ません)（絶対に出来ないとは言ってないけど圧倒的に楽）
 - VRM0.0(のような何かの) export 完全ではないので、出力後にuniVRMを通してください。（他形式でuniVRMに渡すより物理やマテリアル、blendshape_groupの情報が多く残るのでマシ程度にお考え下さい
 - VRM　export チュートリアル（japanese）
   https://www.nicovideo.jp/watch/sm36033523
# function
- VRM import
- Add VRM like shader as Node Group (Please use these node group and direct link it to TEX_IMAGE,RGBA,VALUE and Material output Nodes for export)
- Add humanoid armature for VRM(Tpose, reqwired bone, and append custom properties to need export VRM (reference to VRM extensions textblock ,and bone tagging))
- VRM0.0 export (not complete function ,but easy to bridge uniVRM. )

# GLTF extension implements
 - KHR_materials_unlit : OK
 - KHR_materials_pbrSpecularGlossiness: NO
 - KHR_texture_transform : NO
 - KHR_draco_mesh_compression: CAN'T
 - KHR_techniques_webgl: IGNORE
 - KHR_lights_punctual: IGNORE
 - VENDER'S extension : NO without VRM

 # Spec
<img src="./web/spec.jpg" />
