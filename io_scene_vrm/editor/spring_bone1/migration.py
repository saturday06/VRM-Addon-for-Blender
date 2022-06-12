import bpy


def migrate_blender_object(armature: bpy.types.Object) -> None:
    ext = armature.data.vrm_addon_extension
    if tuple(ext.addon_version) >= (2, 3, 27):
        return

    for collider in ext.spring_bone1.colliders:
        bpy_object = collider.get("blender_object")
        if isinstance(bpy_object, bpy.types.Object):
            collider.bpy_object = bpy_object
        if "blender_object" in collider:
            del collider["blender_object"]


def migrate(armature: bpy.types.Object) -> None:
    migrate_blender_object(armature)
