# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy

# https://projects.blender.org/blender/blender/commit/0ce02355c1d0fb676167b7070870c8b5ef6ce048
locale_key = "zh_CN" if bpy.app.version < (4, 0) else "zh_HANS"

translation_dictionary: dict[tuple[str, str], str] = {
    (
        "*",
        "The installed VRM add-on is not compatible with Blender {blender_version}."
        + " Please upgrade the add-on.",
    ): "已安装的 VRM 附加组件有"
    + "Blender {blender_version}尚不支持。。\n"
    + "更新附加组件。",
    (
        "*",
        "The installed VRM add-\n"
        + "on is not compatible with\n"
        + "Blender {blender_version}. Please update.",
    ): "已安装\n"
    + "VRM 附加组件是 Blender {blender_version}\n"
    + "尚不支持。 插件。\n"
    + "请更新。",
    (
        "*",
        "The installed VRM add-on is not compatible with Blender {blender_version}."
        + " The VRM may not be exported correctly.",
    ): "已安装的 VRM 附加组件与 Blender {blender_version} 不兼容。"
    + "可能无法正确导出 VRM。",
    (
        "*",
        "VRM add-on is not compatible with Blender {blender_version_cycle}.",
    ): "VRM 附加组件尚未与 {blender_version_cycle} 版本的 Blender 兼容。",
    (
        "*",
        "VRM add-on is\n"
        + "not compatible with\n"
        + "Blender {blender_version_cycle}.",
    ): "VRM 附加组件Blender\n" + "尚未支持 {blender_version_cycle} 版本的 。",
    (
        "*",
        "VRM add-on is not compatible with Blender {blender_version_cycle}."
        + " The VRM may not be exported correctly.",
    ): "VRM 附加组件与 {blender_version_cycle} 版本的 Blender 尚不兼容。"
    + "可能无法正确导出 VRM。",
    (
        "*",
        "The VRM add-on has been updated."
        + " Please restart Blender to apply the changes.",
    ): "已更新 VRM 附加组件。" + "重启 Blender 以应用更改。",
    (
        "*",
        "The VRM add-on has been\n"
        + "updated. Please restart Blender\n"
        + "to apply the changes.",
    ): "VRM 附加组件\n已更新。" + "要应用更改\n" + "Blender重新启动。",
    ("*", 'Set shading type to "Material"'): "将 3D 视图设置为材质预览",
    ("*", 'Set view transform to "Standard"'): "将视图转换设置为 “标准”",
    (
        "*",
        'Set an imported armature display to "Wire"',
    ): "将armature视口显示设置为 “线框”",
    (
        "*",
        'Set an imported armature display to show "In-Front"',
    ): "armature显示在最前面",
    (
        "*",
        "Set an imported bone shape to default",
    ): "默认显示骨骼形状。",
    (
        "*",
        "Enable MToon Outline Preview",
    ): "允许MToon轮廓线预览",
    ("*", "Export Invisible Objects"): "包括隐藏对象",
    ("*", "Export Only Selections"): "仅选定对象",
    ("*", "Enable Advanced Options"): "启用高级选项",
    ("*", "Don't overwrite existing texture folder"): "不要覆盖现有纹理文件夹",
    (
        "*",
        "Export All Bone Influences",
    ): "导出所有骨骼重量",
    (
        "*",
        "Don't limit to 4, most viewers truncate to 4, "
        + "so bone movement may cause jagged meshes",
    ): "不限于四个。 大多数观众将自己限制为四人，因为、"
    + "移动骨骼时可能会发生意外的网格变形。",
    ("*", "Export Lights"): "输出灯光",
    (
        "*",
        "No error. Ready for export VRM",
    ): "未发现任何错误。。可导出 VRM",
    (
        "*",
        "No error. But there're {warning_count} warning(s)."
        + " The output may not be what you expected.",
    ): "没有错误。、{warning_count}有关于此的警告。。" + "输出结果可能与预期不同。",
    ("*", "VRM Export"): "VRM 输出",
    ("*", "Create VRM Model"): "创建 VRM 模型",
    ("*", "Check as VRM Model"): "按VRM 模型标准检查",
    ("*", "Extract texture images into the folder"): "将纹理图像解压到文件夹中。",
    (
        "*",
        'Official add-on "glTF 2.0 format" is required. Please enable it.',
    ): "需要使用 glTF 2.0 格式的官方插件。 请激活它",
    (
        "*",
        "For more information please check following URL.",
    ): "如需了解更多信息，请查看下面的 URL。",
    (
        "*",
        "Multiple armatures were found. Please select one to export as VRM.",
    ): "存在多个armatures。。" + "选择要导出为 VRM 的armatures。",
    ("*", "Import Anyway"): "强制导入",
    ("*", "Export Anyway"): "强制导出",
    (
        "*",
        "There is a high-impact warning. VRM may not export as intended.",
    ): "有影响较大的警告。。" + "VRM 可能无法按预期输出。",
    ("*", "A light is required"): "需要照明。",
    ("*", "License Confirmation"): "许可确认。",
    (
        "*",
        'Is this VRM allowed to edited? Please check its "{json_key}" value.',
    ): "指定 VRM 的元数据「{json_key}」值" + "已设置了唯一的许可证 URL。。",
    (
        "*",
        'This VRM is licensed by VRoid Hub License "Alterations: No".',
    ): "指定的 VRM 具有 VRoid Hub 的许可「改変: 禁止」。。",
    (
        "*",
        'This VRM is licensed by UV License with "Remarks".',
    ): "指定的 VRM 具有 UV License的许可(Remarks)。",
    (
        "*",
        'The VRM selects "Other" license but no license url is found.',
    ): "指定的 VRM 具有「Other」许可证规定、" + "未设置 URL。",
    (
        "*",
        'The VRM is licensed by "{license_name}".'
        + " No derivative works are allowed.",
    ): "指定 VRM 的不可修改许可证。「{license_name}」设置为。" + "不允许衍生作品。。",
    (
        "*",
        "Nodes(mesh,bones) require unique names for VRM export."
        + " {name} is duplicated.",
    ): "glTF 节点元素(网格,骨骼)名称不得重复。。" + "「{name}」是重复的。。",
    (
        "*",
        'There are not an object on the origin "{name}"',
    ): "原点坐标上无对象「{name}」",
    (
        "*",
        "The same name cannot be used"
        + " for a mesh object and a bone."
        + ' Rename either one whose name is "{name}".',
    ): "网格对象和骨骼不能使用相同的名称。" + "名称：「{name}」更改以下名称之一。",
    (
        "*",
        'The "{name}" mesh has both a non-armature modifier'
        + " and a shape key. However, they cannot coexist"
        + ", so shape keys may not be export correctly.",
    ): "网格「{name}」に"
    + "non-armature修改器和形态键都已设置，但、"
    + "它们不能共存，形态键可能无法正确输出。",
    (
        "*",
        'Spring "{spring_name1}" and "{spring_name2}" have'
        + ' common bone "{bone_name}".',
    ): "Spring 「{spring_name1}」と「{spring_name2}」が"
    + "「{bone_name}」有共用骨骼。",
    (
        "*",
        '"{export_only_selections}" is enabled' + ", but no mesh is selected.",
    ): "「{export_only_selections}」是有效的，但没有选择任何网格。",
    ("*", "There is no mesh to export."): "无网格可导出。",
    (
        "*",
        "Only one armature is required for VRM export." + " Multiple armatures found.",
    ): "只能为 VRM 输出选择一个armatures。 可多次选择。",
    (
        "*",
        'Required VRM Bone "{humanoid_name}" is'
        + " not assigned. Please confirm hierarchy"
        + " of {humanoid_name} and its children."
        + ' "VRM" Panel → "VRM 0.x Humanoid" → {humanoid_name}'
        + " will be empty or displayed in red"
        + " if hierarchy is wrong",
    ): "VRM必须的骨骼「{humanoid_name}」是未指定的。。"
    + "「VRM」面板「VRM 0.x Humanoid」→「VRM必须的骨骼」将为空或显示为红色"
    + "「{humanoid_name}」如果层次结构有误。",
    (
        "*",
        'Couldn\'t assign "{bone}" bone'
        + ' to VRM Humanoid Bone: "{human_bone}". '
        + 'Confirm hierarchy of "{bone}" and its children. '
        + '"VRM" Panel → "Humanoid" → "{human_bone}" is empty'
        + " if wrong hierarchy",
    ): "骨骼「{bone}」到 VRM 骨「{human_bone}」无法分配。"
    + "「VRM」面板「VRM 0.x Humanoid」で"
    + "「{human_bone}」检查骨骼设置。",
    (
        "*",
        'Required VRM Bone "{humanoid_name}" is'
        + " not assigned. Please confirm hierarchy"
        + " of {humanoid_name} and its children. "
        + '"VRM" Panel → "Humanoid" → {humanoid_name}'
        + " will be empty or displayed in red"
        + " if hierarchy is wrong",
    ): "VRM必须的骨骼「{humanoid_name}」是未指定的。。"
    + "「VRM」面板「Humanoid」→「VRM必须的骨骼」将为空或显示为红色"
    + "「{humanoid_name}」如果层次结构有误。",
    (
        "*",
        'Please assign Required VRM Bone "{name}".',
    ): "请分配所需的 VRM 骨 「{name}」。",
    (
        "*",
        'Please assign "{parent_name}"'
        + ' because "{name}" requires it as its child bone.',
    ): "「{parent_name}」指定。" + "因为「{name}」需要将其作为子骨骼。。",
    (
        "*",
        'Non-tri faces detected in "{name}". ' + "will be triangulated automatically.",
    ): "「{name}」包含三角形以外的多边形。" + "自动划分为三角形。",
    (
        "*",
        'VRM Bone "{child}" needs "{parent}".'
        + " Please confirm"
        + ' "VRM" Panel → "Humanoid"'
        + ' → "VRM Optional Bones" → "{parent}".',
    ): "VRM骨骼「{child}」需要「{parent}」。"
    + "「VRM」面板「Humanoid」→「VRM可选的骨骼」で"
    + "「{parent}」骨骼設定。",
    (
        "*",
        'Object "{name}" contains a negative value for the scale;'
        + " VRM 1.0 does not allow negative values to be specified"
        + " for the scale.",
    ): "对象「{name}」中的缩放为负数。" + "VRM 1.0不允许指定负值。",
    (
        "*",
        'Node Constraint "{owner_name} / {constraint_name}" has'
        + " a circular dependency",
    ): "ノードコンストレイント「{owner_name} / {constraint_name}」に"
    + "存在循环依赖关系。。",
    ("*", "No armature exists."): "骨架不存在。。",
    (
        "*",
        'vertex index "{vertex_index}" is no weight'
        + ' in "{mesh_name}".'
        + " Add weight to parent bone automatically.",
    ): "「{mesh_name}」的頂点id「{vertex_index}」未加权。" + "自动为父骨骼分配权重。。",
    (
        "*",
        'vertex index "{vertex_index}" has'
        + ' too many (over 4) weight in "{mesh_name}".'
        + " It will be truncated to 4 descending"
        + " order by its weight.",
    ): "「{mesh_name}」的頂点id「{vertex_index}」有 5 块或更多骨骼影响到。"
    + "最多 4 个，按重度顺序导出。",
    (
        "*",
        '"{material_name}" needs to enable'
        + ' "VRM MToon Material" or connect'
        + " Principled BSDF/MToon_unversioned/TRANSPARENT_ZWRITE"
        + ' to "Surface" directly. Empty material will be exported.',
    ): "「{material_name}」需要启用「VRM MToon Material」或者链接"
    + "「原理化BSDF」「MToon_unversioned」「TRANSPARENT_ZWRITE」の"
    + "直接向 “表面 ”指定其中之一。 输出空材质。。",
    (
        "*",
        '"{image_name}" is not found in file path "{image_filepath}". '
        + "Please load file of it in Blender.",
    ): '「{image_name}」指定文件路径中的图像文件。「"{image_filepath}"」'
    + "图像不存在于 请重新加载图像。。",
    (
        "*",
        "firstPersonBone is not found. "
        + 'Set VRM HumanBone "head" instead automatically.',
    ): "firstPersonBone未设置。。"
    + "自动设置将 VRM humanborn「head」改为 firstPersonBone。。",
    (
        "*",
        'A mesh named "{mesh_name}" is assigned to a blend'
        + ' shape group named "{blend_shape_group_name}" but'
        + " the mesh will not be exported",
    ): "Blend Shape Group「{blend_shape_group_name}」有一个网格「{mesh_name}」"
    + "已分配、但网格未导出",
    (
        "*",
        'A shape key named "{shape_key_name}" in a mesh'
        + ' named "{mesh_name}" is assigned to a blend shape'
        + ' group named "{blend_shape_group_name}" but the'
        + " shape key doesn't exist.",
    ): "名为 「{shape_key_name}」的形态键在网格"
    + " 「{mesh_name}」 已被分配给混合形状"
    + "但是此形态键不存在",
    (
        "*",
        'need "{expect_node_type}" input' + ' in "{shader_val}" of "{material_name}"',
    ): "「{material_name}」的「{shader_val}」需要、"
    + "「{expect_node_type}」直接连接。 ",
    (
        "*",
        'image in material "{material_name}" is not put.' + " Please set image.",
    ): "材质「{material_name}」"
    + "有一个没有设置纹理的图像节点。"
    + "删除或设置图像。",
    ("*", "Symmetrize VRoid Bone Names on X-Axis"): "VRoid 骨骼名称的 X 轴对称性",
    (
        "*",
        "Make VRoid bone names X-axis mirror editable",
    ): "将 VRoid 骨骼名称转换为 X 轴对称可编辑名称",
    ("*", "Current Pose"): "当前姿势",
    ("*", "Save Bone Mappings"): "保存骨骼对应关系",
    ("*", "Load Bone Mappings"): "加载骨骼对应关系",
    (
        "*",
        "All VRM Required Bones have been assigned.",
    ): "所有 VRM 必需骨骼分配都已完成。",
    (
        "*",
        "There are unassigned VRM Required Bones. Please assign all.",
    ): "存在未分配的 VRM 必需骨骼。" + "分配所有 VRM 必需骨骼。",
    ("Operator", "Automatic Bone Assignment"): "自动骨骼分配",
    ("Operator", "Export VRM"): "导出 VRM",
    ("Operator", "Import VRM"): "导入 VRM",
    ("Operator", "Preview MToon 0.0"): "MToon 0.0预览",
    ("Operator", "VRM Humanoid"): "VRM人形",
    ("Operator", "VRM License Confirmation"): "查看 VRM 使用条款",
    ("Operator", "VRM Required Bones Assignment"): "配置 VRM 必需骨骼",
    (
        "*",
        "Conditions exported as Roll Constraint\n"
        + " - Copy Rotation\n"
        + " - Enabled\n"
        + " - No Vertex Group\n"
        + " - Axis is one of X, Y and Z\n"
        + " - No Inverted\n"
        + " - Mix is Add\n"
        + " - Target is Local Space\n"
        + " - Owner is Local Space\n"
        + " - No circular dependencies\n"
        + " - The one at the top of the list of\n"
        + "   those that meet all the conditions\n",
    ): "约束导出为转动约束\n"
    + " - 复制旋转\n"
    + " - 启用\n"
    + " - 未指定顶点组\n"
    + " - 指定 XYZ 的一个轴\n"
    + " - 不可逆转\n"
    + " - 混合添加\n"
    + " - 目标是局部空间\n"
    + " - 由局部空间拥有\n"
    + " - 循环依赖关系不存在\n"
    + " - 满足所有条件的\n",
    (
        "*",
        "Conditions exported as Aim Constraint\n"
        + " - Damped Track\n"
        + " - Enabled\n"
        + " - Target Bone Head/Tail is 0\n"
        + " - No Follow Target Bone B-Bone\n"
        + " - No circular dependencies\n"
        + " - The one at the top of the list of\n"
        + "   those that meet all the conditions\n",
    ): "约束导出为动画约束\n"
    + " - 阻尼轨道\n"
    + " - 启用状态\n"
    + " - 目标骨头的头部/Tail is 0\n"
    + " - 不遵循目标骨骼的 B 骨\n"
    + " - 循环依赖关系不存在\n"
    + " - 满足所有条件的\n",
    (
        "*",
        "Conditions exported as Rotation Constraint\n"
        + " - Copy Rotation\n"
        + " - Enabled\n"
        + " - No Vertex Group\n"
        + " - Axis is X, Y and Z\n"
        + " - No Inverted\n"
        + " - Mix is Add\n"
        + " - Target is Local Space\n"
        + " - Owner is Local Space\n"
        + " - No circular dependencies\n"
        + " - The one at the top of the list of\n"
        + "   those that meet all the conditions\n",
    ): "约束导出为旋转约束\n"
    + " - 复制旋转\n"
    + " - 启用状态\n"
    + " - 未指定顶点组\n"
    + " - 所有轴均以 XYZ 表示。\n"
    + " - 不可逆转\n"
    + " - 混合添加\n"
    + " - 目标是局部空间\n"
    + " - 由局部空间拥有\n"
    + " - 循环依赖关系不存在\n"
    + " - 满足所有条件的\n",
    ("*", "Axis Translation on Export"): "导出时转换轴",
    (
        "*",
        "Offset and Scale are ignored in VRM 0.0",
    ): "偏移和缩放在 VRM 0.0 中被忽略",
    (
        "*",
        'Material "{name}" {texture}\'s Offset and Scale are' + " ignored in VRM 0.0",
    ): "VRM 0.0材质「{name}」的{texture}的偏移和缩放将被忽略",
    (
        "*",
        "Offset and Scale in VRM 0.0 are" + " the values of the Lit Color Texture",
    ): "VRM 0.0 中的偏移和缩放是 Lit Color Texture 的值",
    (
        "*",
        'Material "{name}" {texture}\'s Offset and Scale'
        + " in VRM 0.0 are the values of"
        + " the Lit Color Texture",
    ): "VRM 0.0材质「name」的{texture}的偏移和缩放为" + "Lit Color Texture的值",
    (
        "*",
        'It is recommended to set "{colorspace}"'
        + ' to "{input_colorspace}" for "{texture_label}"',
    ): "对于{texture_label}中的{input_colorspace}，建议设置“{colorspace}”",
    (
        "*",
        'It is recommended to set "{colorspace}"'
        + ' to "{input_colorspace}" for "{texture_label}"'
        + ' in Material "{name}"',
    ): "材质{name}的{texture_label}的{input_colorspace}"
    + "建议使用「{colorspace}」的设定。",
    (
        "*",
        "VRM Material",
    ): "VRM材质",
    (
        "*",
        "Enable VRM MToon Material",
    ): "启用VRM MToon材质",
    (
        "*",
        "Export Shape Key Normals",
    ): "导出形态键法线",
    (
        "*",
        'The "Screen Coordinates" display is not yet implemented.\n'
        + 'It is displayed in the same way as "World Coordinates".',
    ): "「Screen Coordinates」尚未实施\n" + "与「World Coordinates」具有相同的显示",
    (
        "*",
        "How to export this material to VRM.\n"
        + "Meet one of the following conditions.\n"
        + " - VRM MToon Material is enabled\n"
        + ' - Connect the "Surface" to a "Principled BSDF"\n'
        + ' - Connect the "Surface" to a "MToon_unversioned"\n'
        + ' - Connect the "Surface" to a "TRANSPARENT_ZWRITE"\n'
        + " - Others that are compatible with the glTF 2.0 add-on export\n",
    ): "如何将此材料导出到 VRM\n"
    + "必须满足以下条件之一。\n"
    + " - VRM MToon材质启用\n"
    + " - 指定「Surface」到「Principled BSDF」\n"
    + " - 指定「Surface」到「MToon_unversioned」\n"
    + " - 指定「Surface」到「TRANSPARENT_ZWRITE」\n"
    + " - 其他与glTF 2.0附加组件导出兼容的组件\n",
    (
        "*",
        "Enable Animation",
    ): "使动画有效",
    (
        "*",
        "Armature not found",
    ): "未找到骨架",
    (
        "*",
        "Please assign required human bones",
    ): "请分配所需的人形骨骼",
    ("*", "Please set the version of VRM to 1.0"): "将 VRM 版本设置为 1.0",
    (
        "*",
        "VRM Animation export requires a VRM 1.0 armature",
    ): "VRM 动画导出需要 VRM 1.0 骨架",
    (
        "*",
        "VRM Animation import requires a VRM 1.0 armature",
    ): "VRM 动画导入需要 VRM 1.0 骨架",
    ("*", "Armature to be exported"): "要导出的骨架",
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
        + "- 人形骨骼旋转值\n"
        + "- Humanoid Hips骨骼运动值\n"
        + "- 表情的预览值\n"
        + "- Look At预览目标移动值\n"
    ),
    ("*", "Armature to be animated"): "动画的骨骼",
    (
        "*",
        "https://vrm-addon-for-blender.info/en/animation/",
    ): "https://vrm-addon-for-blender.info/ja/animation/",
    ("Operator", "Open help in a Web Browser"): "在 Web 浏览器中打开“帮助”",
    ("*", "Allow Non-Humanoid Rig"): "允许使用非人形骨骼",
    (
        "*",
        "VRMs exported as Non-Humanoid\n"
        + "Rigs can not have animations applied\n"
        + "for humanoid avatars.",
    ): ("作为 非人形 导出VRM\n" + "无法应用动画\n" + "于人形avatar。"),
    (
        "*",
        "This armature will be exported but not as humanoid."
        + " It can not have animations applied"
        + " for humanoid avatars.",
    ): "这个骨架会导出但是不是作为人形。" + "人形avatars的动画不适用。",
    (
        "Operator",
        "Blender 4.2 Material Upgrade Warning",
    ): "Blender 4.2材质升级警告",
    (
        "*",
        'Updating to Blender 4.2 may unintentionally change the "{alpha_mode}"'
        + ' of some MToon materials to "{transparent}".\n'
        + 'This was previously implemented using the material\'s "{blend_mode}"'
        + " but since that setting was removed in Blender 4.2.\n"
        + 'In the current VRM add-on, the "{alpha_mode}" function has been'
        + " re-implemented using a different method. However, it"
        + "was not possible"
        + " to implement automatic migration of old settings values because those"
        + " values could no longer be read.\n"
        + 'Please check the "{alpha_mode}" settings for materials that have'
        + " MToon enabled.\n"
        + "Materials that may be affected are as follows:",
    ): "升级到 Blender 4.2可能会无意间改变一些MOOT材质的"
    + "「{alpha_mode}」为「{transparent}」\n"
    + "这是以前使用材质的“{blend_mode}实现的"
    + "但由于该设置在Blender 4.2中被删除\n"
    + "現在的VRM插件，这个「{alpha_mode}」功能使用其他方式实现"
    + "但是无法自动迁移旧的配置 因为这些参数无法读取了\n"
    + "请检查材质「{alpha_mode}」设置中。"
    + "具有MToon启动\n"
    + "可能受影响的材质如下。",
    #####################################################新建VR弹窗翻译
    (
        "*",
        "Add VRM Humanoid",
    ): "添加VRM人形Humanoid",
    (
        "*",
        "wip_with_template_mesh",
    ): "带有模板网格的WIP",
    (
        "*",
        "Bone tall",
    ): "骨骼高度",
    (
        "*",
        "head_ratio",
    ): "头部比例",
    (
        "*",
        "head_width_ratio",
    ): "头部宽度比例",
    (
        "*",
        "aging_ratio",
    ): "老化比例",
    (
        "*",
        "eye_depth",
    ): "眼睛深度",
    (
        "*",
        "shoulder_in_width",
    ): "肩内宽",
    (
        "*",
        "shoulder_width",
    ): "肩宽",
    (
        "*",
        "arm_length_ratio",
    ): "臂长比例",
    (
        "*",
        "hand_ratio",
    ): "手比例",
    (
        "*",
        "finger_1_2_ratio",
    ): "手指第一与二节比例",
    (
        "*",
        "finger_2_3_ratio",
    ): "手指第二与三节比例",
    (
        "*",
        "leg_length_ratio",
    ): "腿长比例",
    (
        "*",
        "leg_width_ratio",
    ): "腿宽比例",
    (
        "*",
        "leg_size",
    ): "腿大小",
    ###############################侧面板
    # Meta
    (
        "*",
        "Thumbnail:",
    ): "缩略图 Thumbnail:",
    (
        "*",
        "Contact Information",
    ): "联系信息",
    (
        "*",
        "Contact Information about the avatar",
    ): "关于此角色的联系信息",
    (
        "*",
        "Allowed User",
    ): "许可用户",
    (
        "*",
        "Only Author",
    ): "仅作者",
    (
        "*",
        "Explicitly Licensed Person",
    ): "明确获得许可的人",
    (
        "*",
        "Everyone",
    ): "所有人",
    (
        "*",
        "Allowed user of the avatar",
    ): "允许使用该角色的用户",
    (
        "*",
        "Allow",
    ): "允许",
    (
        "*",
        "Disallow",
    ): "禁止",
    (
        "*",
        "undefined",
    ): "未定义",
    (
        "*",
        "Violent Usage",
    ): "暴力用途",
    (
        "*",
        "Sexual Usage",
    ): "性用途",
    (
        "*",
        "Commercial Usage",
    ): "商业用途",
    (
        "*",
        "Other Permission URL",
    ): "其他许可链接",
    (
        "*",
        "Redistribution Prohibited",
    ): "禁止再分发",
    # Humanoid
    (
        "*",
        "VRM Required Bones",
    ): "VRM必须的骨骼",
    (
        "*",
        "Head:",
    ): "头部 Head:",
    (
        "*",
        "Neck:",
    ): "颈部 Neck:",
    (
        "*",
        "Chest:",
    ): "胸骨 Chest:",
    (
        "*",
        "Spine:",
    ): "腰骨 Spine:",
    (
        "*",
        "Hips:",
    ): "臀部 Hips:",
    (
        "*",
        "Upper Arm:",
    ): "上臂 Upper Arm:",
    (
        "*",
        "Lower Arm:",
    ): "前臂 Lower Arm:",
    (
        "*",
        "Hand:",
    ): "手 Hand:",
    (
        "*",
        "Upper Leg:",
    ): "大腿 Upper Leg:",
    (
        "*",
        "Lower Leg:",
    ): "小腿 Lower Leg:",
    (
        "*",
        "Foot:",
    ): "脚 Foot:",
    (
        "*",
        "VRM Optional Bones",
    ): "VRM可选的骨骼",
    (
        "*",
        "Eye:",
    ): "眼睛 Eye:",
    (
        "*",
        "Jaw:",
    ): "下巴 Jaw:",
    (
        "*",
        "Shoulder:",
    ): "肩膀 Shoulder:",
    (
        "*",
        "Upper Chest:",
    ): "上胸部 Upper Chest:",
    (
        "*",
        "Toes:",
    ): "脚趾 Toes:",
    (
        "*",
        "Left Thumb:",
    ): "左拇指 Left Thumb:",
    (
        "*",
        "Left Index:",
    ): "左食指 Left Index:",
    (
        "*",
        "Left Middle:",
    ): "左中指 Left Middle:",
    (
        "*",
        "Left Ring:",
    ): "左无名指 Left Ring:",
    (
        "*",
        "Left Little:",
    ): "左小指 Left Little:",
    (
        "*",
        "Right Thumb:",
    ): "右拇指 Right Thumb:",
    (
        "*",
        "Right Index:",
    ): "右食指 Right Index:",
    (
        "*",
        "Right Middle:",
    ): "右中指 Right Middle:",
    (
        "*",
        "Right Ring:",
    ): "右无名指 Right Ring:",
    (
        "*",
        "Right Little:",
    ): "右小指 Right Little:",
    (
        "*",
        "Arm",
    ): "胳膊 Arm",
    (
        "*",
        "Arm Stretch",
    ): "手臂伸展 Arm Stretch",
    (
        "*",
        "Upper Arm Twist",
    ): "上臂扭转 Upper Arm Twist",
    (
        "*",
        "Lower Arm Twist",
    ): "前臂扭转 Lower Arm Twist",
    (
        "*",
        "Leg",
    ): "腿 Leg",
    (
        "*",
        "Leg Stretch",
    ): "腿部伸展 Leg Stretch",
    (
        "*",
        "Upper Leg Twist",
    ): "大腿扭转 Upper Leg Twist",
    (
        "*",
        "Lower Leg Twist",
    ): "小腿扭转 Lower Leg Twist",
    (
        "*",
        "Feet Spacing",
    ): "脚间距 Feet Spacing",
    # Blender Shape
    (
        "*",
        "Is Binary",
    ): "是二进制的",
    (
        "*",
        "Use binary change in the blendshape group",
    ): "在混合形状组中使用二进制更改",
    (
        "*",
        "Blink",
    ): "眨眼 Blink",
    (
        "*",
        "Joy",
    ): "高兴 Joy",
    (
        "*",
        "Angry",
    ): "生气 Angry",
    (
        "*",
        "Sorrow",
    ): "悲伤 Sorrow",
    (
        "*",
        "Fun",
    ): "有趣 Fun",
    (
        "*",
        "Look Up",
    ): "向上看 Look Up",
    (
        "*",
        "Look Down",
    ): "向下看 Look Down",
    (
        "*",
        "Look Left",
    ): "向左看 Look Left",
    (
        "*",
        "Look Right",
    ): "向右看 Look Right",
    (
        "*",
        "Blink_L",
    ): "左眼眨眼 Blink_L",
    (
        "*",
        "Blink_R",
    ): "右眼眨眼 Blink_R",
    (
        "*",
        "Binds",
    ): "绑定 Binds",
    (
        "*",
        "Material Values",
    ): "材质值 Material Values",
    # First Person
    (
        "*",
        "First Person Bone Offset",
    ): "第一人称骨骼偏移",
    (
        "*",
        "Offset from the first person bone to follow the first person camera.",
    ): "从第一人称骨骼到跟随第一人称摄像头的偏移",
    (
        "*",
        "Look At Type Name",
    ): "注视对象类型名",
    (
        "*",
        "Mesh Annotations",
    ): "网格注释",
    (
        "*",
        "Look At Horizontal Inner",
    ): "注视水平向内",
    (
        "*",
        "Look At Horizontal Outer",
    ): "注视水平向外",
    (
        "*",
        "Look At Vertical Up",
    ): "注视垂直向上",
    (
        "*",
        "Look At Vertical Down",
    ): "注视垂直向下",
    # Spring Bone
    (
        "*",
        "Spring Bone Groups",
    ): "弹簧骨骼组 Spring Bone Groups",
    (
        "*",
        "Collider Groups",
    ): "碰撞器组 Collider Groups",
}
