locale_key = "ja_JP"

translation_dictionary = {
    ("*", "Export Invisible Objects"): "非表示のオブジェクトも含める",
    ("*", "Export Only Selections"): "選択されたオブジェクトのみ",
    ("*", "No error. Ready for export VRM"): "エラーはありませんでした。VRMのエクスポートをすることができます",
    ("*", "VRM Export"): "VRMエクスポート",
    ("*", "Create VRM Model"): "VRMモデルを作成",
    ("*", "Validate VRM Model"): "VRMモデルのチェック",
    ("*", "Extract texture images into the folder"): "テクスチャ画像をフォルダに展開",
    (
        "*",
        'Official add-on "glTF 2.0 format" is required. Please enable it.',
    ): "公式アドオン「glTF 2.0 format」が必要です。有効化してください。",
    ("*", "For more information please check following URL."): "詳しくは下記のURLを確認してください。",
    ("*", "Import Anyway"): "インポートします",
    ("*", "A light is required"): "ライトが必要です",
    ("*", "License Confirmation"): "ライセンスの確認",
    (
        "*",
        'Is this VRM allowed to edited? Please check its "{json_key}" value.',
    ): "指定されたVRMのメタデータ「{json_key}」には独自のライセンスのURLが設定されています。",
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
    ): "指定されたVRMには「Other」ライセンスが設定されていますが、URLが設定されていません。",
    (
        "*",
        'The VRM is licensed by "{license_name}". No derivative works are allowed.',
    ): "指定されたVRMには改変不可ライセンス「{license_name}」が設定されています。改変することはできません。",
    (
        "*",
        "Nodes(mesh,bones) require unique names for VRM export. {name} is duplicated.",
    ): "glTFノード要素(メッシュ、ボーン)の名前は重複してはいけません。「{name}」が重複しています。",
    ("*", 'There are not an object on the origin "{name}"'): "「{name}」が原点座標にありません",
    (
        "*",
        "Only one armature is required for VRM export. Multiple armatures found.",
    ): "VRM出力の際、選択できるアーマチュアは1つのみです。複数選択されています。",
    (
        "*",
        "VRM Required Bones",
    ): "VRM必須ボーン",
    (
        "*",
        "VRM Optional Bones",
    ): "VRMオプションボーン",
    (
        "*",
        'Required VRM Bone "{humanoid_name}" is not assigned. Please confirm'
        + ' "VRM" Panel → "VRM 0.x Humanoid" → "VRM Required Bones" → "{humanoid_name}".',
    ): "VRM必須ボーン「{humanoid_name}」が未割り当てです。"
    + "「VRM」パネルの「VRM 0.x Humanoid」→「VRM必須ボーン」で「{humanoid_name}」ボーンの設定をしてください。",
    (
        "*",
        'Faces must be Triangle, but not face in "{name}" or '
        + "it will be triangulated automatically.",
    ): "「{name}」のポリゴンに三角形以外のものが含まれます。自動的に三角形に分割されます。",
    ("*", "Please add ARMATURE to selections"): "アーマチュアを選択範囲に含めてください",
    (
        "*",
        'vertex index "{vertex_index}" is no weight in "{mesh_name}". '
        + "Add weight to parent bone automatically.",
    ): "「{mesh_name}」の頂点id「{vertex_index}」にウェイトが乗っていません。"
    + "親ボーンへのウエイトを自動で割り当てます。",
    (
        "*",
        'vertex index "{vertex_index}" has too many(over 4) weight in "{mesh_name}". '
        + "It will be truncated to 4 descending order by its weight.",
    ): "「{mesh_name}」の頂点id「{vertex_index}」に影響を与えるボーンが5以上あります。"
    + "重い順に4つまでエクスポートされます。",
    (
        "*",
        '"{material_name}" needs to connect {groups} to "Surface" directly. '
        + "Empty material will be exported.",
    ): "マテリアル「{material_name}」には{groups}のいずれかを直接「サーフェス」に指定してください。"
    + "空のマテリアルを出力します。",
    (
        "*",
        'Image "{image_name}" is not saved. Please save.',
    ): "画像「{image_name}」のBlender上での変更を保存してください。",
    (
        "*",
        '"{image_name}" is not found in file path "{image_filepath}". '
        + "Please load file of it in Blender.",
    ): '「{image_name}」の画像ファイルが指定ファイルパス「"{image_filepath}"」'
    + "に存在しません。画像を読み込み直してください。",
    (
        "*",
        'glTF only supports PNG and JPEG textures but "{image_name}" is "{image_file_format}"',
    ): "glTFはPNGとJPEGのみの対応ですが「{image_name}」は「{image_file_format}」です。",
    (
        "*",
        "firstPersonBone is not found. "
        + 'Set VRM HumanBone "head" instead automatically.',
    ): "firstPersonBoneが設定されていません。"
    + "代わりにfirstPersonBoneとしてVRMヒューマンボーン「head」を自動で設定します。",
    (
        "*",
        'mesh "{mesh_name}" doesn\'t have shape key. '
        + 'But blend shape group needs "{shape_key_name}" in its shape key.',
    ): "blend shape groupが参照しているメッシュ「{mesh_name}」のシェイプキー「{shape_key_name}」が存在しません。",
    (
        "*",
        'mesh "{mesh_name}" doesn\'t have "{shape_key_name}" shape key. '
        + "But blend shape group needs it.",
    ): "メッシュ「{mesh_name}」にはシェイプキー「{shape_key_name}」が存在しません。"
    + "しかし blend shape group の設定はそれを必要としています。",
    (
        "*",
        'need "{expect_node_type}" input in "{shader_val}" of "{material_name}"',
    ): "「{material_name}」の「{shader_val}」には、「{expect_node_type}」を直接つないでください。 ",
    (
        "*",
        'image in material "{material_name}" is not put. Please set image.',
    ): "マテリアル「{material_name}」にテクスチャが設定されていないimageノードがあります。削除か画像を設定してください。",
    ("*", "Simplify VRoid Bones"): "VRoidのボーン名を短くする",
    ("*", "Current Pose"): "現在のポーズ",
    ("*", "Save Bone Mappings"): "ボーンの対応を保存",
    ("*", "Load Bone Mappings"): "ボーンの対応を読み込み",
    ("Operator", "Preview MToon"): "MToonのプレビュー",
    ("Operator", "VRM Humanoid"): "VRMヒューマノイド",
    ("Operator", "VRM License Confirmation"): "VRM利用条件の確認",
}
