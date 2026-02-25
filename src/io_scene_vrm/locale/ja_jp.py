# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
locale_key = "ja_JP"

translation_dictionary: dict[tuple[str, str], str] = {
    (
        "*",
        "The installed VRM add-on is not compatible with Blender {blender_version}."
        + " Please upgrade the add-on.",
    ): "インストールされているVRMアドオンは、"
    + "Blender {blender_version}には未対応です。\n"
    + "アドオンをアップデートしてください。",
    (
        "*",
        "The installed VRM add-\n"
        + "on is not compatible with\n"
        + "Blender {blender_version}. Please update.",
    ): "インストールされている\n"
    + "VRMアドオンは、Blender {blender_version}\n"
    + "には未対応です。アドオンを\n"
    + "アップデートしてください。",
    (
        "*",
        "The installed VRM add-on is not compatible with Blender {blender_version}."
        + " The VRM may not be exported correctly.",
    ): "インストールされているVRMアドオンは、Blender {blender_version}には未対応です。"
    + "VRMが正しくエクスポートされない可能性があります。",
    (
        "*",
        "VRM add-on is not compatible with Blender {blender_version_cycle}.",
    ): "VRMアドオンはBlenderの{blender_version_cycle}版には未対応です。",
    (
        "*",
        "VRM add-on is\n"
        + "not compatible with\n"
        + "Blender {blender_version_cycle}.",
    ): "VRMアドオンはBlender\n" + "の{blender_version_cycle}版には未対応です。",
    (
        "*",
        "VRM add-on is not compatible with Blender {blender_version_cycle}."
        + " The VRM may not be exported correctly.",
    ): "VRMアドオンはBlenderの{blender_version_cycle}版には未対応です。"
    + "VRMが正しくエクスポートされない可能性があります。",
    (
        "*",
        "The VRM add-on has been updated."
        + " Please restart Blender to apply the changes.",
    ): "VRMアドオンはアップデートされました。"
    + "変更を適用するためにBlenderを再起動してください。",
    (
        "*",
        "The VRM add-on has been\n"
        + "updated. Please restart Blender\n"
        + "to apply the changes.",
    ): "VRMアドオンはアップデート\nされました。"
    + "変更を適用するため\n"
    + "Blenderを再起動してください。",
    ("*", 'Set shading type to "Material"'): "3Dビューをマテリアルプレビューに設定",
    ("*", 'Set view transform to "Standard"'): "ビュー変換を「標準」に設定",
    (
        "*",
        'Set an imported armature display to "Wire"',
    ): "アーマチュアのビューポート表示を「ワイヤーフレーム」に設定",
    (
        "*",
        'Set an imported armature display to show "In-Front"',
    ): "アーマチュアを最前面に表示",
    (
        "*",
        "Set an imported bone shape to default",
    ): "ボーンの形状表示をデフォルトのものにする",
    (
        "*",
        "Enable MToon Outline Preview",
    ): "MToonアウトラインのプレビューを有効にする",
    (
        "*",
        "Enable Preview",
    ): "プレビューを有効にする",
    ("*", "Export Invisible Objects"): "非表示のオブジェクトも含める",
    ("*", "Export Only Selections"): "選択されたオブジェクトのみ",
    ("*", "Enable Advanced Options"): "高度なオプションを有効にする",
    (
        "*",
        "Export All Bone Influences",
    ): "全てのボーンウェイトをエクスポートする",
    (
        "*",
        "By default, 4 bone influences\n"
        + "are exported for each vertex. Many\n"
        + "apps truncate to 4. Increasing it\n"
        + "may cause jagged meshes.",
    ): "デフォルトでは頂点1つにつき\n"
    + "ウエイトを4つエクスポートします。\n"
    + "多くのアプリでは4つに制限する\n"
    + "ため、これを増やすと予期しない\n"
    + "メッシュの変形が発生する可能性が\n"
    + "あります。",
    (
        "*",
        "Don't limit to 4, most viewers truncate to 4, "
        + "so bone movement may cause jagged meshes",
    ): "4つに制限しません。ほとんどのビューアでは4つに制限するため、"
    + "ボーンを動かした際に予期しないメッシュの変形が発生する可能性があります。",
    ("*", "Export Lights"): "ライトをエクスポートする",
    (
        "*",
        "There is no consensus on how\n"
        + "to handle lights in VRM, so it is\n"
        + "impossible to predict what the\n"
        + "outcome will be.",
    ): "VRMにおけるライトの扱いは\n"
    + "現在コンセンサスが無く、どのような\n"
    + "結果になるか予測不能です。",
    ("*", "Export glTF Animations"): "glTFアニメーションをエクスポートする",
    (
        "*",
        "UniVRM does not export\n"
        + "glTF Animations, so it is disabled\n"
        + "by default. Please consider using\n"
        + "VRM Animation.",
    ): "UniVRMがglTFアニメーションを\n"
    + "エクスポートしないのでデフォルトで\n"
    + "無効です。VRMアニメーションの利用\n"
    + "を検討してください。",
    ("*", "Use Sparse Accessors"): "スパースアクセッサを利用する",
    (
        "*",
        "The file size will be reduced,\n"
        + "but it will no longer be readable by\n"
        + "older apps with UniVRM 0.115.0 or\n"
        + "earlier.",
    ): "ファイルサイズが削減されますが\n"
    + "UniVRM 0.115.0以下の古いアプリで\n"
    + "読めなくなります。",
    (
        "*",
        "No errors found. Ready to export VRM.",
    ): "エラーはありませんでした。VRMのエクスポートをすることができます。",
    (
        "*",
        "No errors found. But there are {warning_count} warning(s)."
        + " The output may not be what you expected.",
    ): "エラーはありませんでしたが、{warning_count}件の警告があります。"
    + "期待通りの出力にはならないかもしれません。",
    ("*", "VRM Export"): "VRMエクスポート",
    ("*", "Create VRM Model"): "VRMモデルを作成",
    ("*", "Check VRM Model"): "VRMモデルのチェック",
    (
        "*",
        "Add MToon shader node group",
    ): "MToonシェーダーノードグループを追加",
    ("*", "Extract texture images into the folder"): "テクスチャ画像をフォルダに展開",
    (
        "*",
        "Don't overwrite existing texture image folder",
    ): "既に存在するテクスチャ画像のフォルダを上書きしない",
    (
        "*",
        'Official add-on "glTF 2.0 format" is required. Please enable it.',
    ): "公式アドオン「glTF 2.0 format」が必要です。有効化してください。",
    (
        "*",
        "For more information please check following URL.",
    ): "詳しくは下記のURLを確認してください。",
    (
        "*",
        "Multiple armatures were found. Please select one to export as VRM.",
    ): "複数のアーマチュアが存在します。"
    + "VRMとしてエクスポートするアーマチュアを選択してください。",
    ("*", "Import Anyway"): "インポートします",
    ("*", "Export Anyway"): "エクスポートします",
    (
        "*",
        "There is a high-impact warning. VRM may not export as intended.",
    ): "影響の大きい警告があります。"
    + "意図通りのVRMがエクスポートされないかもしれません。",
    ("*", "A light is required"): "ライトが必要です",
    ("*", "License Confirmation"): "ライセンスの確認",
    (
        "*",
        'This VRM is licensed by VRoid Hub License "Alterations: No".',
    ): "指定されたVRMにはVRoid Hubの「改変: NG」ライセンスが設定されています。",
    (
        "*",
        'This VRM is licensed by UV License with "Remarks".',
    ): "指定されたVRMには特記事項(Remarks)付きのUVライセンスが設定されています。",
    (
        "*",
        'The VRM selects "Other" license but no license url is found.',
    ): "指定されたVRMには「Other」ライセンスが設定されていますが、"
    + "URLが設定されていません。",
    (
        "*",
        '"{url}" is not a valid URL.',
    ): "「{url}」は有効なURLではありません。",
    (
        "*",
        "This VRM is not allowed to be edited. Please check its license",
    ): "このVRMは改変不可に設定されています。ライセンスを確認してください。",
    (
        "*",
        'The vertex "{parent_name}" is set as the parent of "{name}",'
        + " but this is not supported in VRM.",
    ): "「{name}」の親として「{parent_name}」の頂点が設定されていますが、"
    + "VRMでは未対応です。",
    (
        "*",
        '"{lattice}" is set as the {parent_type} for "{name}",'
        + " but this is not supported in VRM.",
    ): "「{name}」の{parent_type}として「{lattice}」が設定されていますが、"
    + "VRMでは未対応です。",
    (
        "*",
        "glTF nodes (mesh, bone) cannot have duplicate names."
        + " {name} is duplicated.",
    ): "glTFノード要素(メッシュ、ボーン)の名前は重複してはいけません。"
    + "「{name}」が重複しています。",
    (
        "*",
        "The same name cannot be used"
        + " for a mesh object and a bone."
        + ' Rename either one whose name is "{name}".',
    ): "メッシュオブジェクトとボーンで同じ名前を使うことができません。"
    + "名前が「{name}」のどちらかの名前を変更してください。",
    (
        "*",
        'The "{name}" mesh has both a non-armature modifier'
        + " and a shape key. However, they cannot coexist"
        + ", so shape keys may not be exported correctly.",
    ): "メッシュ「{name}」に"
    + "アーマチュア以外のモディファイアとシェイプキーが両方設定されていますが、"
    + "それらは共存できないためシェイプキーが正しく出力されないことがあります。",
    (
        "*",
        'Spring "{spring_name1}" and "{spring_name2}" have'
        + ' common bone "{bone_name}".',
    ): "Spring 「{spring_name1}」と「{spring_name2}」が"
    + "「{bone_name}」ボーンを共有しています。",
    (
        "*",
        '"{export_only_selections}" is enabled' + ", but no mesh is selected.",
    ): "「{export_only_selections}」が有効ですが、メッシュが一つも選択されていません。",
    ("*", "There is no mesh to export."): "エクスポート対象のメッシュがありません。",
    (
        "*",
        "VRM exporter needs only one armature not some armatures.",
    ): "VRM出力の際、選択できるアーマチュアは1つのみです。複数選択されています。",
    (
        "*",
        "Required VRM Human Bones",
    ): "VRM必須ボーン",
    (
        "*",
        "Optional VRM Human Bones",
    ): "VRMオプションボーン",
    (
        "*",
        'Required VRM Human Bone "{humanoid_name}" is'
        + " not assigned. Please confirm hierarchy"
        + " of {humanoid_name} and its children."
        + ' "VRM" Panel → "VRM 0.x Humanoid" → {humanoid_name}'
        + " will be empty or displayed in red"
        + " if hierarchy is wrong.",
    ): "VRM必須ボーン「{humanoid_name}」が未割り当てです。"
    + "「VRM」パネルの「VRM 0.x Humanoid」→「VRM必須ボーン」で"
    + "「{humanoid_name}」ボーンの設定をしてください。",
    ("Operator", "<Unassign>"): "<割り当てを解除>",
    ("*", "Remove the bone assignment"): "ボーンの割り当てを解除します。",
    (
        "*",
        'Couldn\'t assign "{bone}" bone'
        + ' to VRM Human Bone "{human_bone}". '
        + 'Confirm hierarchy of "{bone}" and its children. '
        + '"VRM" Panel → "Humanoid" → "{human_bone}" is empty'
        + " if wrong hierarchy.",
    ): "ボーン「{bone}」をVRMヒューマンボーン「{human_bone}」に"
    + "割り当てることができませんでした。"
    + "「VRM」パネルの「VRM 0.x Humanoid」で"
    + "「{human_bone}」ボーンの設定を確認してください。",
    (
        "*",
        'Required VRM Human Bone "{humanoid_name}" is'
        + " not assigned. Please confirm hierarchy"
        + " of {humanoid_name} and its children. "
        + '"VRM" Panel → "Humanoid" → {humanoid_name}'
        + " will be empty or displayed in red"
        + " if hierarchy is wrong.",
    ): "VRM必須ボーン「{humanoid_name}」が未割り当てです。"
    + "「VRM」パネルの「Humanoid」→「VRM必須ボーン」で"
    + "「{humanoid_name}」ボーンの設定をしてください。",
    (
        "*",
        'Please assign Required VRM Human Bone "{name}".',
    ): "VRM必須ボーン「{name}」を割り当ててください。",
    (
        "*",
        'Please assign "{parent_name}"'
        + ' because "{name}" requires it as its child bone.',
    ): "「{parent_name}」を割り当ててください。"
    + "子ボーンである「{name}」の割り当てに必要になります。",
    (
        "*",
        'Non-triangular faces detected in "{name}". '
        + "They will be triangulated automatically.",
    ): "「{name}」のポリゴンに三角形以外のものが含まれます。"
    + "自動的に三角形に分割されます。",
    (
        "*",
        'VRM Human Bone "{child}" needs "{parent}".'
        + " Please confirm"
        + ' "VRM" Panel → "Humanoid"'
        + ' → "Optional VRM Human Bones" → "{parent}".',
    ): "VRMヒューマンボーン「{child}」は「{parent}」が必要です。"
    + "「VRM」パネルの「Humanoid」→「VRMオプションボーン」で"
    + "「{parent}」ボーンの設定をしてください。",
    (
        "*",
        'Object "{name}" contains a negative value for the scale;'
        + " VRM 1.0 does not allow negative values to be specified"
        + " for the scale.",
    ): "オブジェクト「{name}」にスケールにマイナス値が含まれています。"
    + "VRM 1.0ではスケールにマイナス値を指定できません。",
    (
        "*",
        'Node Constraint "{owner_name} / {constraint_name}" has'
        + " a circular dependency",
    ): "ノードコンストレイント「{owner_name} / {constraint_name}」に"
    + "循環依存関係が存在します。",
    ("*", "No armature exists."): "アーマチュアが存在しません。",
    (
        "*",
        'vertex index "{vertex_index}" is no weight'
        + ' in "{mesh_name}".'
        + " Add weight to parent bone automatically.",
    ): "「{mesh_name}」の頂点id「{vertex_index}」にウェイトが乗っていません。"
    + "親ボーンへのウエイトを自動で割り当てます。",
    (
        "*",
        'vertex index "{vertex_index}" has'
        + ' too many (over 4) weight in "{mesh_name}".'
        + " It will be truncated to 4 descending"
        + " order by its weight.",
    ): "「{mesh_name}」の頂点id「{vertex_index}」に影響を与えるボーンが5以上あります。"
    + "重い順に4つまでエクスポートされます。",
    (
        "*",
        '"{material_name}" needs to enable'
        + ' "VRM MToon Material" or connect'
        + " Principled BSDF/MToon_unversioned/TRANSPARENT_ZWRITE"
        + ' to "Surface" directly. Empty material will be exported.',
    ): "マテリアル「{material_name}」は「VRM MToon Material」を有効にするか"
    + "「プリンシプルBSDF」「MToon_unversioned」「TRANSPARENT_ZWRITE」の"
    + "いずれかを直接「サーフェス」に指定してください。空のマテリアルを出力します。",
    (
        "*",
        '"{image_name}" was not found at file path "{image_filepath}". '
        + "Please load the file in Blender.",
    ): '「{image_name}」の画像ファイルが指定ファイルパス「"{image_filepath}"」'
    + "に存在しません。画像を読み込み直してください。",
    (
        "*",
        "firstPersonBone was not found. "
        + 'VRM HumanBone "head" will be used automatically instead.',
    ): "firstPersonBoneが設定されていません。"
    + "代わりにfirstPersonBoneとしてVRMヒューマンボーン「head」を自動で設定します。",
    (
        "*",
        'A mesh named "{mesh_name}" is assigned to a blend'
        + ' shape group named "{blend_shape_group_name}" but'
        + " the mesh will not be exported.",
    ): "Blend Shape Group「{blend_shape_group_name}」にメッシュ「{mesh_name}」が"
    + "割り当てられていますが、そのメッシュはエクスポートされません。",
    (
        "*",
        'A shape key named "{shape_key_name}" in a mesh'
        + ' named "{mesh_name}" is assigned to a blend shape'
        + ' group named "{blend_shape_group_name}" but the'
        + " shape key doesn't exist.",
    ): "Blend Shape Group「{blend_shape_group_name}」にメッシュ"
    + "「{mesh_name}」のシェイプキー「{shape_key_name}」が割り当てられていますが、"
    + "そのようなシェイプキーは存在しません。",
    (
        "*",
        'need "{expect_node_type}" input' + ' in "{shader_val}" of "{material_name}".',
    ): "「{material_name}」の「{shader_val}」には、"
    + "「{expect_node_type}」を直接つないでください。",
    (
        "*",
        'Image in material "{material_name}" is not set.' + " Please add an image.",
    ): "マテリアル「{material_name}」に"
    + "テクスチャが設定されていないimageノードがあります。"
    + "削除か画像を設定してください。",
    ("*", "Symmetrize VRoid Bone Names on X-Axis"): "VRoidのボーン名をX軸対称化",
    (
        "*",
        "Make VRoid bone names X-axis mirror editable",
    ): "VRoidのボーン名をX軸対称編集が可能な名前に変換",
    ("*", "Current Pose"): "現在のポーズ",
    ("*", "Save Bone Mappings"): "ボーンの対応を保存",
    ("*", "Load Bone Mappings"): "ボーンの対応を読み込み",
    (
        "*",
        "All Required VRM Human Bones have been assigned.",
    ): "全てのVRM必須ボーンの割り当てが行われました。",
    (
        "*",
        "There are unassigned Required VRM Human Bones. Please assign all.",
    ): "未割り当てのVRM必須ボーンが存在します。"
    + "全てのVRM必須ボーンを割り当ててください。",
    ("Operator", "Automatic Bone Assignment"): "ボーンの自動割り当て",
    ("Operator", "Preview MToon 0.0"): "MToon 0.0のプレビュー",
    ("Operator", "VRM Humanoid"): "VRMヒューマノイド",
    ("Operator", "VRM License Confirmation"): "VRM利用条件の確認",
    ("Operator", "Required VRM Human Bones Assignment"): "VRM必須ボーンの設定",
    (
        "*",
        "Conditions exported as Roll Constraint\n"
        + " - {copy_rotation}\n"
        + " - Enabled\n"
        + " - No Vertex Group\n"
        + " - {axis} is one of X, Y and Z\n"
        + " - No Inverted\n"
        + " - {mix} is {add}\n"
        + " - {target} is {local_space}\n"
        + " - {owner} is {local_space}\n"
        + " - No circular dependencies\n"
        + " - The one at the top of the list of\n"
        + "   those that meet all the conditions\n",
    ): "Roll Constraintになる条件\n"
    + " - {copy_rotation}\n"
    + " - 有効状態\n"
    + " - 頂点グループの指定無し\n"
    + " - {axis}はXYZのどれか一つを指定\n"
    + " - 反転は無し\n"
    + " - {mix}は{add}\n"
    + " - {target}は{local_space}\n"
    + " - {owner}は{local_space}\n"
    + " - 循環依存関係が存在しない\n"
    + " - 複数が条件を満たす場合は一番上にあるもの\n",
    (
        "*",
        "Conditions exported as Aim Constraint\n"
        + " - {damped_track}\n"
        + " - Enabled\n"
        + " - Target Bone {head_tail} is 0\n"
        + " - No Follow Target Bone B-Bone\n"
        + " - No circular dependencies\n"
        + " - The one at the top of the list of\n"
        + "   those that meet all the conditions\n",
    ): "Aim Constraintになる条件\n"
    + " - {damped_track}\n"
    + " - 有効状態\n"
    + " - ターゲットボーンの{head_tail}が0\n"
    + " - ターゲットボーンのBボーンには従わない\n"
    + " - 循環依存関係が存在しない\n"
    + " - 複数が条件を満たす場合は一番上にあるもの\n",
    (
        "*",
        "Conditions exported as Rotation Constraint\n"
        + " - {copy_rotation}\n"
        + " - Enabled\n"
        + " - No Vertex Group\n"
        + " - {axis} is X, Y and Z\n"
        + " - No Inverted\n"
        + " - {mix} is {add}\n"
        + " - {target} is {local_space}\n"
        + " - {owner} is {local_space}\n"
        + " - No circular dependencies\n"
        + " - The one at the top of the list of\n"
        + "   those that meet all the conditions\n",
    ): "Rotation Constraintになる条件\n"
    + " - {copy_rotation}\n"
    + " - 有効状態\n"
    + " - 頂点グループの指定無し\n"
    + " - {axis}はXYZ全て指定\n"
    + " - 反転は無し\n"
    + " - {mix}は{add}\n"
    + " - {target}は{local_space}\n"
    + " - {owner}は{local_space}\n"
    + " - 循環依存関係が存在しない\n"
    + " - 複数が条件を満たす場合は一番上にあるもの\n",
    ("*", "Axis Translation on Export"): "エクスポート時の軸の変換",
    (
        "*",
        "Offset and Scale are ignored in VRM 0.0.",
    ): "VRM 0.0ではオフセットとスケールは無視されます。",
    (
        "*",
        'Material "{name}" {texture}\'s Offset and Scale are' + " ignored in VRM 0.0.",
    ): "VRM 0.0ではマテリアル「{name}」の{texture}のオフセットとスケールは"
    + "無視されます。",
    (
        "*",
        "Offset and Scale in VRM 0.0 are" + " the values of the Lit Color Texture.",
    ): "VRM 0.0でのオフセットとスケールはLit Colorテクスチャの値になります。",
    (
        "*",
        'Material "{name}" {texture}\'s Offset and Scale'
        + " in VRM 0.0 are the values of"
        + " the Lit Color Texture.",
    ): "VRM 0.0でのマテリアル「name」の{texture}のオフセットとスケールは"
    + "Lit Colorテクスチャの値になります。",
    (
        "*",
        'It is recommended to set "{colorspace}"'
        + ' to "{input_colorspace}" for "{texture_label}"',
    ): "{texture_label}の{input_colorspace}には「{colorspace}」の設定が推奨されます",
    (
        "*",
        'It is recommended to set "{colorspace}"'
        + ' to "{input_colorspace}" for "{texture_label}"'
        + ' in Material "{name}".',
    ): "マテリアル{name}の{texture_label}の{input_colorspace}には"
    + "「{colorspace}」の設定が推奨されます。",
    (
        "*",
        "VRM Material",
    ): "VRMマテリアル",
    (
        "*",
        "Enable VRM MToon Material",
    ): "VRM MToonマテリアルを有効にする",
    (
        "*",
        "Export Shape Key Normals",
    ): "シェイプキー法線をエクスポートする",
    (
        "*",
        'The "Screen Coordinates" display is not yet implemented.\n'
        + 'It is displayed in the same way as "World Coordinates".',
    ): "「Screen Coordinates」の表示は未実装です\n"
    + "「World Coordinates」と同じ表示をします",
    (
        "*",
        "How to export this material to VRM.\n"
        + "Meet one of the following conditions.\n"
        + " - VRM MToon Material is enabled\n"
        + ' - Connect the "Surface" to a "Principled BSDF"\n'
        + ' - Connect the "Surface" to a "MToon_unversioned"\n'
        + ' - Connect the "Surface" to a "TRANSPARENT_ZWRITE"\n'
        + " - Others that are compatible with the glTF 2.0 add-on export\n",
    ): "VRMにこのマテリアルをエクスポートする方法\n"
    + "次のいずれかの条件を満たしてください。\n"
    + " - VRM MToonマテリアルが有効\n"
    + " - 「サーフェス」に「プリンシプルBSDF」を指定\n"
    + " - 「サーフェス」に「MToon_unversioned」を指定\n"
    + " - 「サーフェス」に「TRANSPARENT_ZWRITE」を指定\n"
    + " - その他、glTF 2.0アドオンのエクスポートに対応しているもの\n",
    (
        "*",
        "Enable Animation",
    ): "アニメーションを有効にする",
    ("*", "Armature not found"): "アーマチュアが見つかりませんでした",
    (
        "*",
        "Please assign required human bones",
    ): "必須のヒューマンボーンの割り当ててください",
    ("*", "Please set the version of VRM to 1.0"): "VRMのバージョンを1.0にしてください",
    (
        "*",
        "VRM Animation export requires a VRM 1.0 armature",
    ): "VRM Animationのエクスポートには、VRM 1.0のアーマチュアが必要です",
    (
        "*",
        "VRM Animation import requires a VRM 1.0 armature",
    ): "VRM Animationのインポートには、VRM 1.0のアーマチュアが必要です",
    ("*", "Armature to be exported"): "エクスポート対象のアーマチュア",
    (
        "*",
        (
            "Animations to be exported\n"
            + "- Humanoid bone rotations\n"
            + "- Humanoid hips bone translations\n"
            + "- Expression preview value\n"
            + "- Look At preview target translation\n"
        ),
    ): (
        "エクスポートされるアニメーション\n"
        + "- Humanoidボーンの回転値\n"
        + "- Humanoid Hipsボーンの移動値\n"
        + "- Expressionのプレビュー値\n"
        + "- Look Atプレビューターゲットの移動値\n"
    ),
    ("*", "Armature to be animated"): "アニメーション適用対象のアーマチュア",
    (
        "*",
        "https://vrm-addon-for-blender.info/en-us/animation/",
    ): "https://vrm-addon-for-blender.info/ja-jp/animation/",
    ("Operator", "Open help in a Web Browser"): "Webブラウザでヘルプを開く",
    ("*", "Allow Non-Humanoid Rig"): "人型以外のリグを許可する",
    (
        "*",
        "VRMs exported as Non-Humanoid\n"
        + "Rigs can not have animations applied\n"
        + "for humanoid avatars.",
    ): (
        "人型以外のリグでVRMエクスポートを\n"
        + "すると、人型アバター用のアニメーションが\n"
        + "適用されません。"
    ),
    (
        "*",
        "This armature will be exported but not as a humanoid."
        + " It cannot have animations applied"
        + " for humanoid avatars.",
    ): "アーマチュアは人型では無いリグでエクスポートされます。"
    + "人型アバター用のアニメーションが適用されません。",
    (
        "Operator",
        "Blender 4.2 Material Upgrade Warning",
    ): "Blender 4.2でのマテリアルアップグレードの警告",
    (
        "*",
        'Updating to Blender 4.2 may unintentionally change the "{alpha_mode}"'
        + ' of some MToon materials to "{transparent}".\n'
        + 'This was previously implemented using the material\'s "{blend_mode}"'
        + " but since that setting was removed in Blender 4.2.\n"
        + 'In the current VRM add-on, the "{alpha_mode}" function has been'
        + " re-implemented using a different method. However, it\n"
        + "was not possible"
        + " to implement automatic migration of old settings values because those"
        + " values could no longer be read.\n"
        + 'Please check the "{alpha_mode}" settings for materials that have'
        + " MToon enabled.\n"
        + "Materials that may be affected are as follows:",
    ): "Blender 4.2へのアップデートに伴い、一部のMToonマテリアルの"
    + "「{alpha_mode}」設定が意図せず「{transparent}」に変化している\n"
    + "可能性があります。当該機能は今までマテリアルの「{blend_mode}」設定で"
    + "実装されていましたが、Blender 4.2からその設定が\n"
    + "削除されたためです。"
    + "現在のVRMアドオンでは「{alpha_mode}」の機能は別の方式で再実装"
    + "されましたが、古い設定値の自動移行は、\n"
    + "古い設定値自体がもう読めないため実装が不可能でした。"
    + "MToonが有効なマテリアルの「{alpha_mode}」設定の確認をお願いします。\n"
    + "影響のある可能性のあるマテリアルは次の通りです。",
    (
        "Operator",
        "File Compatibility Warning",
    ): "ファイルの互換性の警告",
    (
        "*",
        "The current file is not compatible with the running Blender.\n"
        + "The current file was created in Blender {file_version}, but the running"
        + " Blender version is {app_version}.\n"
        + "This incompatibility may result in data loss or corruption.",
    ): "現在のファイルは実行中のBlenderと互換性がありません。\n"
    + "現在のファイルはBlender {file_version}で作られたファイルですが、"
    + "起動中のBlenderの\n"
    + "バージョンは{app_version}のため互換性ありません。そのため、"
    + "一部のデータが消えたり\n"
    + "壊れたりすることがあります。",
    ("VrmAddon", "Open Documentation"): "関連ドキュメントを開く",
    (
        "*",
        "The current file is not compatible with the installed VRM Add-on.\n"
        + "The current file was created in VRM Add-on {file_addon_version}, but the"
        + " installed\n"
        + "VRM Add-on version is {installed_addon_version}. This incompatibility\n"
        + "may result in data loss or corruption.",
    ): "現在のファイルはインストール済みのVRMアドオンと互換性がありません。\n"
    + "現在のファイルはVRMアドオンのバージョン{file_addon_version}で作られた"
    + "ファイルですが、\nインストール済みのVRMアドオンのバージョンは"
    + "{installed_addon_version}のため互換性がありません。\n"
    + "そのため、一部のデータが消えたり壊れたりすることがあります。",
    (
        "Operator",
        "VRM Add-on Compatibility Warning",
    ): "VRMアドオンの互換性の警告",
    (
        "Operator",
        "Bone Assignment Diagnostics",
    ): "ボーン割り当ての診断",
    (
        "*",
        "Shows the cause of the bone assignment error"
        " or the reason why none of the bone assignment candidates exist.",
    ): "ボーン割り当てのエラーの原因や、"
    + "ボーンの割り当て候補が存在しない理由を表示します。",
    (
        "*",
        'Assignment of the VRM Human Bone "{vrm_human_bone}"',
    ): "VRMヒューマンボーン「{vrm_human_bone}」の割り当て",
    (
        "*",
        'The bone "{bone_name}" of the armature "{armature_object_name}"'
        + ' can be assigned to the VRM Human Bone "{human_bone_name}".',
    ): "アーマチュア「{armature_object_name}」のボーン「{bone_name}」は"
    "VRMヒューマンボーン「{human_bone_name}」へ割り当てることができます。",
    (
        "*",
        'The bone "{bone_name}" of the armature "{armature_object_name}"'
        + ' cannot be assigned to the VRM Human Bone "{human_bone_name}".',
    ): "アーマチュア「{armature_object_name}」のボーン「{bone_name}」は"
    + "VRMヒューマンボーンの「{human_bone_name}」へ割り当てることができません。",
    (
        "*",
        'The armature "{armature_object_name}" does not have any bones'
        + ' that can be assigned to the VRM Human Bone "{human_bone_name}".',
    ): "アーマチュア「{armature_object_name}」にはVRMヒューマンボーン"
    + "「{human_bone_name}」へ割り当てることができるボーンが存在しません。",
    (
        "*",
        'Being a descendant of the bone "{bpy_bone}" assigned'
        + ' to the VRM Human Bone "{human_bone}"',
    ): "VRMヒューマンボーン「{human_bone}」に割り当てられているボーン"
    + "「{bpy_bone}」の子孫",
    (
        "*",
        'The bone assigned to the VRM Human Bone "{human_bone}" must'
        + " be descendants of the bones assigned \nto the VRM human"
        + ' bone "{parent_human_bone}". However, it cannot retrieve'
        + " bone candidates because there\nis an error in the"
        + ' assignment of the VRM Human Bone "{parent_human_bone}".'
        + " Please resolve the error in the\nassignment of the VRM"
        + ' Human Bone "{parent_human_bone}" first.',
    ): "VRMヒューマンボーン「{human_bone}」へ割り当てるボーンは、VRMヒューマンボーン"
    + "「{parent_human_bone}」に割り当てるボーンの\n子孫である必要があります。しかし、"
    + "VRMヒューマンボーン「{parent_human_bone}」に割り当てエラーがあるためボーンの"
    + "候補を取得できません。\n先にVRMヒューマンボーン「{parent_human_bone}」の"
    + "割り当てのエラーを解消してください。",
    (
        "*",
        'Sharing the root bone with the bone "{bpy_bone}" assigned'
        + ' to the VRM Human Bone "{human_bone}"',
    ): "VRMヒューマンボーン「{human_bone}」に割り当てられているボーン「{bpy_bone}」と"
    + "ルートボーンを共有している",
    (
        "*",
        'Being an ancestor of the bone "{bpy_bone}" assigned'
        + ' to the VRM Human Bone "{human_bone}"',
    ): "VRMヒューマンボーン「{human_bone}」に割り当てられているボーン"
    + "「{bpy_bone}」の祖先",
    (
        "*",
        'Not being an ancestor of the bone "{bpy_bone}" assigned'
        + ' to the VRM Human Bone "{human_bone}"',
    ): "VRMヒューマンボーン「{human_bone}」に割り当てられているボーン"
    + "「{bpy_bone}」の祖先では無い",
    (
        "*",
        "Bones that meet all of the following conditions will be "
        + "candidates for assignment:",
    ): "次の条件を全て満たすボーンが割り当て候補になります。",
    (
        "*",
        "Failed to export VRM.",
    ): "VRMのエクスポートに失敗しました。",
    (
        "*",
        "Failed to export VRM Animation.",
    ): "VRM Animationのエクスポートに失敗しました。",
    (
        "*",
        "Failed to import VRM.",
    ): "VRMのインポートに失敗しました。",
    (
        "*",
        "Failed to import VRM Animation.",
    ): "VRM Animationのインポートに失敗しました。",
    (
        "Operator",
        "Save Error Message",
    ): "エラーメッセージを保存",
    ("Operator", "Open Support Site"): "サポートサイトを開く",
    (
        "*",
        "Automatic T-Pose Conversion is enabled."
        + " There is a setting"
        + ' in "VRM" panel → "VRM 0.x Humanoid" → "T-Pose".',
    ): "自動Tポーズ化が有効です。"
    + "「VRM」パネルの「VRM 0.x Humanoid」→「T-Pose」に設定があります。",
    (
        "*",
        "Automatic T-Pose Conversion is enabled."
        + " There is a setting"
        + ' in "VRM" panel → "Humanoid" → "T-Pose".',
    ): "自動Tポーズ化が有効です。"
    + "「VRM」パネルの「Humanoid」→「T-Pose」に設定があります。",
    (
        "*",
        '<Please use "VRM Material" panel instead>',
    ): "「VRMマテリアル」パネルを使用してください",
    (
        "*",
        "https://github.com/vrm-c/vrm-specification/blob/c24d76d99a18738dd2c266be1c83f089064a7b5e/specification/VRMC_vrm-1.0/humanoid.md#humanoid-bone-parent-child-relationship",
    ): "https://github.com/vrm-c/vrm-specification/blob/c24d76d99a18738dd2c266be1c83f089064a7b5e/specification/VRMC_vrm-1.0/humanoid.ja.md#ヒューマノイドボーンの親子関係",
    ("Operator", "Restore Shape Key Assignments"): "シェイプキーの割り当てを復元する",
    (
        "Operator",
        "Assign Auto-Detected Shape Keys",
    ): "自動検出されたシェイプキーを割り当て",
    ("Operator", "Assign VRChat Shape Keys"): "VRChatシェイプキーを割り当て",
    ("Operator", "Assign MMD Shape Keys"): "MMDのシェイプキーを割り当て",
    (
        "Operator",
        "Assign Ready Player Me Shape Keys",
    ): "Ready Player Meのシェイプキーを割り当て",
    (
        "Operator",
        "Add ARkit / PerfectSync Custom Expressions",
    ): "ARkit / PerfectSyncのカスタムExpressionを追加",
}
