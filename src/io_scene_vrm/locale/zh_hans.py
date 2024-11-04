import bpy

# https://projects.blender.org/blender/blender/commit/0ce02355c1d0fb676167b7070870c8b5ef6ce048
locale_key = "zh_CN" if bpy.app.version < (4, 0) else "zh_HANS"

translation_dictionary: dict[tuple[str, str], str] = {
    #
    # Dear 空想幻灵 (@uitcis), who contributed the Simplified Chinese translation, or
    # anyone who is interested in the translation.
    #
    # Simplified Chinese translation has been temporarily disabled. This is to comply
    # with the license requirements of the Blender Extensions platform.
    #
    # Please check the URL below for more details:
    # https://github.com/saturday06/VRM-Addon-for-Blender/issues/627
    #
}
