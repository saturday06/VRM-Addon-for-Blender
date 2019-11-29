# VRM_IMPORTER_for_Blender2.8
- current :for blender 2.80
- mesh import : done 
- material import : wip forever
- export : spec0.0 export may be possible.

# 機能
 - VRM import
 - VRM 向けシェーダーノードグループ追加(※モックアップ程度の出来)(GLTF,MToon_unversioned,TransparentZwrite)
 - VRM 向けhumanoid Armature 追加(これを使わないとexport出来ません)（絶対に出来ないとは言ってないけど圧倒的に楽）
 - VRM0.0(のような何かの) export 完全ではないので、出力後にuniVRMを通してください。（他形式でuniVRMに渡すより物理やマテリアル、blendshape_groupの情報が多く残るのでマシ程度にお考え下さい

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
 [web/spec.jpg]
