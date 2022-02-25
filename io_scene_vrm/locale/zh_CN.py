locale_key = "zh_CN"

translation_dictionary = {
    ("*", "Export Invisible Objects"): "导出不可见对象",
    ("*", "Export Only Selections"): "导出仅选中项",
    ("*", "No error. Ready for export VRM"): "无错误可导出",
    ("*", "VRM Export"): "导出VRM",
    ("*", "Create VRM Model"): "创建VRM",
    ("*", "Validate VRM Model"): "验证VRM模型",
    ("*", "Extract texture images into the folder"): "导出图像到文件夹",
    (
        "*",
        'Official add-on "glTF 2.0 format" is required. Please enable it.',
    ): "请保证glTF 2.0 插件打开",
    ("*", "For more information please check following URL."): "更多的信息请检查下方链接",
    ("*", "Import Anyway"): "坚持导入",
    ("*", "A light is required"): "需要灯光",
    ("*", "License Confirmation"): "许可确认",
    (
        "*",
        'Is this VRM allowed to edited? Please check its "{json_key}" value.',
    ): "允许被编辑吗？请检查「{json_key}」。",
    (
        "*",
        'This VRM is licensed by VRoid Hub License "Alterations: No".',
    ): "此VRM附加VRoid Hub许可的「禁止修改」许可。",
    (
        "*",
        'This VRM is licensed by UV License with "Remarks".',
    ): "此VRM附加UV许可的「再分发」许可。",
    (
        "*",
        'The VRM selects "Other" license but no license url is found.',
    ): "此VRM附加其他许可 但是未找到许可链接。",
    (
        "*",
        'The VRM is licensed by "{license_name}". No derivative works are allowed.',
    ): "此VRM附加「{license_name}」许可。允许任何衍生作品。",
    (
        "*",
        "Nodes(mesh,bones) require unique names for VRM export. {name} is duplicated.",
    ): "glTFノNodes(mesh,bones) 骨骼需要唯一名字。「{name}」重复。",
    ("*", 'There are not an object on the origin "{name}"'): "「{name}」原点座標无对象",
    (
        "*",
        "Only one armature is required for VRM export. Multiple armatures found.",
    ): "VRM导出只需要一个骨架。检测到负数选择。",
    (
        "*",
        "VRM Required Bones",
    ): "VRM必须的骨骼",
    (
        "*",
        "VRM Optional Bones",
    ): "VRM可选的骨骼",
    (
        "*",
        'Required VRM Bone "{humanoid_name}" is not assigned. Please confirm'
        + ' "VRM" Panel → "VRM 0.x Humanoid" → "VRM Required Bones" → "{humanoid_name}".',
    ): "VRM必须的「{humanoid_name}」未设定。"
    + "「VRM」面板的「VRM 0.x Humanoid」→「VRM必要骨骼」で「{humanoid_name}」设定正确。",
    (
        "*",
        'Faces must be Triangle, but not face in "{name}" or '
        + "it will be triangulated automatically.",
    ): "必须为三角面但是在「{name}」未检测到。会被自动三角化。",
    ("*", "Please add ARMATURE to selections"): "庆为所选项添加骨架",
    (
        "*",
        'vertex index "{vertex_index}" is no weight in "{mesh_name}". '
        + "Add weight to parent bone automatically.",
    ): "「{mesh_name}」的顶点id「{vertex_index}」无权重。"
    + "自动添加权重到父级骨骼。",
    (
        "*",
        'vertex index "{vertex_index}" has too many(over 4) weight in "{mesh_name}". '
        + "It will be truncated to 4 descending order by its weight.",
    ): "「{mesh_name}」的顶点id「{vertex_index}」有太多权重(over 4)。"
    + "按照权重缩减到4。",
    (
        "*",
        '"{material_name}" needs to connect {groups} to "Surface" directly. '
        + "Empty material will be exported.",
    ): "「{material_name}」需要通过{groups}直接指定到面。"
    + "空材质会被导出。",
    (
        "*",
        '"{image_name}" is not found in file path "{image_filepath}". '
        + "Please load file of it in Blender.",
    ): '「{image_name}」在「"{image_filepath}"」未找到'
    + "请加载文件到Blender。",
    (
        "*",
        "firstPersonBone is not found. "
        + 'Set VRM HumanBone "head" instead automatically.',
    ): "firstPersonBone未找到。"
    + "firstPersonBone 设置 VRM HumanBone「head」取代自动设定。",
    (
        "*",
        'mesh "{mesh_name}" doesn\'t have shape key. '
        + 'But blend shape group needs "{shape_key_name}" in its shape key.',
    ): "blend shape groupが参照しているメッシュ「{mesh_name}」のシェイプキー「{shape_key_name}」が存在しません。",
    (
        "*",
        'mesh "{mesh_name}" doesn\'t have "{shape_key_name}" shape key. '
        + "But blend shape group needs it.",
    ): "メッシュ「{mesh_name}」无「{shape_key_name}」形态键。"
    + " 但是blend shape group 需要它。",
    (
        "*",
        'need "{expect_node_type}" input in "{shader_val}" of "{material_name}"',
    ): "需要在「{material_name}」的「{shader_val}」中输入、「{expect_node_type}」请直接连接。 ",
    (
        "*",
        'image in material "{material_name}" is not put. Please set image.',
    ): "「{material_name}」有一个没有设置纹理的图像节点。请删除或设置图片。",
    ("*", "Simplify VRoid Bones"): "简化VRoid骨骼名",
    ("*", "Current Pose"): "現在のポーズ",
    ("*", "Save Bone Mappings"): "保存映射文件",
    ("*", "Load Bone Mappings"): "加载映射文件",
    ("Operator", "Preview MToon"): "预览MToon",
    ("Operator", "VRM Humanoid"): "VRM Humanoid",
    ("Operator", "VRM License Confirmation"): "VRM使用用条件确认",
}
