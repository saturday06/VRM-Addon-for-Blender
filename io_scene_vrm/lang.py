import bpy

translation_dictionary = {
    "ja_JP": {
        ("*", "Export invisible objects"): "非表示のオブジェクトも含める",
        ("*", "Export only selections"): "選択されたオブジェクトのみ",
        ("*", "MToon preview"): "MToonのプレビュー",
        ("*", "No error. Ready for export VRM"): "エラーはありませんでした。VRMのエクスポートをすることができます",
        ("*", "VRM Export"): "VRMエクスポート",
        ("*", "Validate VRM model"): "VRMモデルのチェック",
        ("*", "Extract texture images into the folder"): "テクスチャ画像をフォルダに展開",
        (
            "*",
            'Official add-on "glTF 2.0 format" is required. Please enable it.',
        ): "公式アドオン「glTF 2.0 format」が必要です。有効化してください。",
        ("*", "Try experimental VRM component UI"): "実験中のVRMコンポーネントUIを試す",
    }
}


def support(en_message: str, ja_message: str) -> str:
    # for fake-bpy-module
    if not bpy.app.translations:
        return en_message

    if bpy.app.translations.locale == "ja_JP":
        return ja_message
    return en_message
