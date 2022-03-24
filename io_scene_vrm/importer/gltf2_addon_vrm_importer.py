import base64
import contextlib
import math
import os.path
import shutil
import struct
import tempfile
import traceback

import bgl
import bpy
import mathutils

from ..common import gltf
from ..common.char import INTERNAL_NAME_PREFIX
from .abstract_base_vrm_importer import AbstractBaseVrmImporter
from .gltf2_addon_importer_user_extension import Gltf2AddonImporterUserExtension
from .vrm_parser import ParseResult, remove_unsafe_path_chars


class RetryUsingLegacyVrmImporter(Exception):
    pass


class Gltf2AddonVrmImporter(AbstractBaseVrmImporter):
    def __init__(
        self,
        context: bpy.types.Context,
        parse_result: ParseResult,
        extract_textures_into_folder: bool,
        make_new_texture_folder: bool,
    ) -> None:
        super().__init__(
            context, parse_result, extract_textures_into_folder, make_new_texture_folder
        )
        self.import_id = Gltf2AddonImporterUserExtension.update_current_import_id()
        self.temp_object_name_count = 0

    def import_vrm(self) -> None:
        wm = bpy.context.window_manager

        def prog(z: int) -> int:
            wm.progress_update(z)
            return z + 1

        wm.progress_begin(0, 11)
        try:
            i = 1
            affected_object = self.scene_init()
            i = prog(i)
            self.import_gltf2_with_indices()
            if self.extract_textures_into_folder:
                i = prog(i)
                self.extract_textures()
            i = prog(i)
            self.use_fake_user_for_thumbnail()
            i = prog(i)
            self.connect_bones()
            i = prog(i)
            self.make_material()
            i = prog(i)
            self.attach_vrm_attributes()
            i = prog(i)
            self.cleaning_data()
            i = prog(i)
            self.finishing(affected_object)
        finally:
            wm.progress_end()
            Gltf2AddonImporterUserExtension.clear_current_import_id()

    def import_gltf2_with_indices(self) -> None:
        with open(self.parse_result.filepath, "rb") as f:
            json_dict, body_binary = gltf.parse_glb(f.read())

        for key in ["nodes", "materials", "meshes"]:
            if key not in json_dict or not isinstance(json_dict[key], list):
                continue
            for index, value in enumerate(json_dict[key]):
                if not isinstance(value, dict):
                    continue
                if "extras" not in value or not isinstance(value["extras"], dict):
                    value["extras"] = {}
                value["extras"].update({self.import_id + key.capitalize(): index})
                if (
                    key == "nodes"
                    and "mesh" in value
                    and isinstance(value["mesh"], int)
                ):
                    value["extras"].update({self.import_id + "Meshes": value["mesh"]})

        legacy_image_name_prefix = self.import_id + "Image"
        if isinstance(json_dict.get("images"), list):
            for image_index, image in enumerate(json_dict["images"]):
                if not isinstance(image, dict):
                    continue
                if not isinstance(image.get("name"), str) or not image["name"]:
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/709630548cdc184af6ea50b2ff3ddc5450bc0af3/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L54
                    image["name"] = f"Image_{image_index}"
                image["name"] = (
                    legacy_image_name_prefix + str(image_index) + "_" + image["name"]
                )

        if isinstance(json_dict.get("meshes"), list):
            for mesh in json_dict["meshes"]:
                if (
                    isinstance(mesh.get("extras"), dict)
                    and isinstance(mesh["extras"].get("targetNames"), list)
                ) or not isinstance(mesh["primitives"], list):
                    continue
                for primitive in mesh["primitives"]:
                    if (
                        not isinstance(primitive, dict)
                        or not isinstance(primitive.get("extras"), dict)
                        or not isinstance(primitive["extras"].get("targetNames"), list)
                    ):
                        continue
                    if mesh.get("extras") is None:
                        mesh["extras"] = {}
                    mesh["extras"]["targetNames"] = primitive["extras"]["targetNames"]
                    break

        if (
            isinstance(json_dict.get("textures"), list)
            and len(json_dict["textures"]) > 0
        ):
            primitives = []

            for texture_index, _ in enumerate(json_dict["textures"]):
                if not isinstance(json_dict.get("buffers"), list):
                    json_dict["buffers"] = []
                position_buffer_index = len(json_dict["buffers"])
                position_buffer_bytes = struct.pack(
                    "<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0
                )
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(position_buffer_bytes).decode("ascii"),
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                texcoord_buffer_index = len(json_dict["buffers"])
                texcoord_buffer_bytes = struct.pack("<6f", 0.0, 0.0, 1.0, 0.0, 0.0, 1.0)
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(texcoord_buffer_bytes).decode("ascii"),
                        "byteLength": len(texcoord_buffer_bytes),
                    }
                )

                if not isinstance(json_dict.get("bufferViews"), list):
                    json_dict["bufferViews"] = []
                position_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": position_buffer_index,
                        "byteOffset": 0,
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                texcoord_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": texcoord_buffer_index,
                        "byteOffset": 0,
                        "byteLength": 24,
                    }
                )

                if not isinstance(json_dict.get("accessors"), list):
                    json_dict["accessors"] = []
                position_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": position_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC3",
                        "componentType": bgl.GL_FLOAT,
                        "count": 3,
                        "min": [0, 0, 0],
                        "max": [1, 1, 0],
                    }
                )
                texcoord_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": texcoord_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC2",
                        "componentType": bgl.GL_FLOAT,
                        "count": 3,
                    }
                )

                if not isinstance(json_dict.get("materials"), list):
                    json_dict["materials"] = []
                tex_material_index = len(json_dict["materials"])
                json_dict["materials"].append(
                    {
                        "name": self.temp_object_name(),
                        "emissiveTexture": {"index": texture_index},
                    }
                )
                primitives.append(
                    {
                        "attributes": {
                            "POSITION": position_accessors_index,
                            "TEXCOORD_0": texcoord_accessors_index,
                        },
                        "material": tex_material_index,
                    }
                )

            if not isinstance(json_dict.get("meshes"), list):
                json_dict["meshes"] = []
            tex_mesh_index = len(json_dict["meshes"])
            json_dict["meshes"].append(
                {"name": self.temp_object_name(), "primitives": primitives}
            )

            if not isinstance(json_dict.get("nodes"), list):
                json_dict["nodes"] = []
            tex_node_index = len(json_dict["nodes"])
            json_dict["nodes"].append(
                {"name": self.temp_object_name(), "mesh": tex_mesh_index}
            )

            if not isinstance(json_dict.get("scenes"), list):
                json_dict["scenes"] = []
            json_dict["scenes"].append(
                {"name": self.temp_object_name(), "nodes": [tex_node_index]}
            )

        if isinstance(json_dict.get("scenes"), list) and isinstance(
            json_dict.get("nodes"), list
        ):
            nodes = json_dict["nodes"]
            skins = json_dict.get("skins", [])
            for scene in json_dict["scenes"]:
                if not isinstance(scene.get("nodes"), list):
                    continue

                all_node_indices = list(scene["nodes"])
                referenced_node_indices = list(scene["nodes"])
                search_node_indices = list(scene["nodes"])
                while search_node_indices:
                    search_node_index = search_node_indices.pop()
                    if not isinstance(search_node_index, int):
                        continue
                    all_node_indices.append(search_node_index)
                    if search_node_index < 0 or len(nodes) <= search_node_index:
                        continue
                    node = nodes[search_node_index]
                    if isinstance(node.get("mesh"), int):
                        referenced_node_indices.append(search_node_index)
                    if isinstance(node.get("skin"), int):
                        referenced_node_indices.append(search_node_index)
                        if node["skin"] < 0 or len(skins) <= node["skin"]:
                            continue
                        skin = skins[node["skin"]]
                        if isinstance(skin.get("skeleton"), int):
                            referenced_node_indices.append(skin["skeleton"])
                        if isinstance(skin.get("joints"), list):
                            referenced_node_indices.extend(skin["joints"])
                    if isinstance(node.get("children"), list):
                        search_node_indices.extend(node["children"])

                retain_node_indices = list(dict.fromkeys(all_node_indices))  # distinct
                for referenced_node_index in referenced_node_indices:
                    if referenced_node_index in retain_node_indices:
                        retain_node_indices.remove(referenced_node_index)

                if not retain_node_indices:
                    continue

                if not isinstance(json_dict.get("buffers"), list):
                    json_dict["buffers"] = []
                position_buffer_index = len(json_dict["buffers"])
                position_buffer_bytes = struct.pack(
                    "<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0
                )
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(position_buffer_bytes).decode("ascii"),
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                joints_buffer_index = len(json_dict["buffers"])
                joints_buffer_bytes = struct.pack(
                    "<12H", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                )
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(joints_buffer_bytes).decode("ascii"),
                        "byteLength": len(joints_buffer_bytes),
                    }
                )
                weights_buffer_index = len(json_dict["buffers"])
                weights_buffer_bytes = struct.pack(
                    "<12f", 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
                )
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(weights_buffer_bytes).decode("ascii"),
                        "byteLength": len(weights_buffer_bytes),
                    }
                )

                if not isinstance(json_dict.get("bufferViews"), list):
                    json_dict["bufferViews"] = []
                position_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": position_buffer_index,
                        "byteOffset": 0,
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                joints_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": joints_buffer_index,
                        "byteOffset": 0,
                        "byteLength": len(joints_buffer_bytes),
                    }
                )
                weights_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": weights_buffer_index,
                        "byteOffset": 0,
                        "byteLength": len(weights_buffer_bytes),
                    }
                )

                if not isinstance(json_dict.get("accessors"), list):
                    json_dict["accessors"] = []
                position_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": position_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC3",
                        "componentType": bgl.GL_FLOAT,
                        "count": 3,
                        "min": [0, 0, 0],
                        "max": [1, 1, 0],
                    }
                )
                joints_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": joints_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC4",
                        "componentType": bgl.GL_UNSIGNED_SHORT,
                        "count": 3,
                    }
                )
                weights_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": weights_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC4",
                        "componentType": bgl.GL_FLOAT,
                        "count": 3,
                    }
                )

                primitives = [
                    {
                        "attributes": {
                            "POSITION": position_accessors_index,
                            "JOINTS_0": joints_accessors_index,
                            "WEIGHTS_0": weights_accessors_index,
                        }
                    }
                ]

                if not isinstance(json_dict.get("meshes"), list):
                    json_dict["meshes"] = []
                skin_mesh_index = len(json_dict["meshes"])
                json_dict["meshes"].append(
                    {"name": self.temp_object_name(), "primitives": primitives}
                )

                if not isinstance(json_dict.get("skins"), list):
                    json_dict["skins"] = []
                skin_index = len(json_dict["skins"])
                json_dict["skins"].append({"joints": list(retain_node_indices)})

                if not isinstance(json_dict.get("nodes"), list):
                    json_dict["nodes"] = []
                skin_node_index = len(json_dict["nodes"])
                json_dict["nodes"].append(
                    {
                        "name": self.temp_object_name(),
                        "mesh": skin_mesh_index,
                        "skin": skin_index,
                    }
                )

                scene["nodes"].append(skin_node_index)

        if self.parse_result.spec_version_number < (1, 0):
            bone_heuristic = "FORTUNE"
        else:
            bone_heuristic = "TEMPERANCE"
        full_vrm_import_success = False
        with tempfile.TemporaryDirectory() as temp_dir:
            indexed_vrm_filepath = os.path.join(temp_dir, "indexed.vrm")
            with open(indexed_vrm_filepath, "wb") as file:
                file.write(gltf.pack_glb(json_dict, body_binary))
            try:
                bpy.ops.import_scene.gltf(
                    filepath=indexed_vrm_filepath,
                    import_pack_images=True,
                    bone_heuristic=bone_heuristic,
                )
                full_vrm_import_success = True
            except RuntimeError:
                traceback.print_exc()
                print(
                    f'ERROR: Failed to import "{indexed_vrm_filepath}"'
                    + f' generated from "{self.parse_result.filepath}" using glTF 2.0 Add-on'
                )
                self.cleanup_gltf2_with_indices()
        if not full_vrm_import_success:
            # Some VRMs have broken animations.
            # https://github.com/vrm-c/UniVRM/issues/1522
            # https://github.com/saturday06/VRM_Addon_for_Blender/issues/58
            if "animations" in json_dict:
                del json_dict["animations"]
            with tempfile.TemporaryDirectory() as temp_dir:
                indexed_vrm_filepath = os.path.join(temp_dir, "indexed.vrm")
                with open(indexed_vrm_filepath, "wb") as file:
                    file.write(gltf.pack_glb(json_dict, body_binary))
                try:
                    bpy.ops.import_scene.gltf(
                        filepath=indexed_vrm_filepath,
                        import_pack_images=True,
                        bone_heuristic=bone_heuristic,
                    )
                except RuntimeError as e:
                    traceback.print_exc()
                    print(
                        f'ERROR: Failed to import "{indexed_vrm_filepath}"'
                        + f' generated from "{self.parse_result.filepath}" using glTF 2.0 Add-on'
                        + " without animations key"
                    )
                    self.cleanup_gltf2_with_indices()
                    if self.parse_result.spec_version_number >= (1, 0):
                        raise e
                    raise RetryUsingLegacyVrmImporter() from e

        extras_node_index_key = self.import_id + "Nodes"
        for obj in bpy.context.selectable_objects:
            data = obj.data
            if not isinstance(data, bpy.types.Armature):
                continue
            for bone_name, bone in data.bones.items():
                bone_node_index = bone.get(extras_node_index_key)
                if not isinstance(bone_node_index, int):
                    continue
                if 0 <= bone_node_index < len(self.parse_result.json_dict["nodes"]):
                    node = self.parse_result.json_dict["nodes"][bone_node_index]
                    node["name"] = bone_name
                del bone[extras_node_index_key]
                self.bone_names[bone_node_index] = bone_name
                if (
                    self.armature is not None
                    or bone_node_index != self.parse_result.hips_node_index
                ):
                    continue
                if (
                    self.parse_result.spec_version_number < (1, 0)
                    and obj.rotation_mode == "QUATERNION"
                ):
                    obj.rotation_quaternion.rotate(
                        mathutils.Euler((0.0, 0.0, math.pi), "XYZ")
                    )
                    if bpy.context.object is not None:
                        bpy.ops.object.mode_set(mode="OBJECT")
                    bpy.ops.object.select_all(action="DESELECT")
                    obj.select_set(True)
                    previous_active = bpy.context.view_layer.objects.active
                    try:
                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.transform_apply(
                            location=False, rotation=True, scale=False, properties=False
                        )
                    finally:
                        bpy.context.view_layer.objects.active = previous_active
                self.armature = obj

        extras_mesh_index_key = self.import_id + "Meshes"
        for obj in bpy.context.selectable_objects:
            data = obj.data
            if not isinstance(data, bpy.types.Mesh):
                continue
            mesh_index = obj.data.get(extras_mesh_index_key)
            if not isinstance(mesh_index, int):
                mesh_index = obj.get(extras_mesh_index_key)
                if not isinstance(mesh_index, int):
                    continue
                del obj[extras_mesh_index_key]
                self.meshes[mesh_index] = obj
            else:
                del obj.data[extras_mesh_index_key]
                self.meshes[mesh_index] = obj

        extras_material_index_key = self.import_id + "Materials"
        for material in bpy.data.materials:
            if self.is_temp_object_name(material.name):
                material.name = (
                    INTERNAL_NAME_PREFIX + material.name
                )  # TODO: Remove it permanently
                continue
            material_index = material.get(extras_material_index_key)
            if not isinstance(material_index, int):
                continue
            del material[extras_material_index_key]
            self.gltf_materials[material_index] = material

        for image in list(bpy.data.images):
            image_index = image.get(self.import_id)
            if not isinstance(image_index, int) and image.name.startswith(
                legacy_image_name_prefix
            ):
                image_index_str = "".join(
                    image.name.split(legacy_image_name_prefix)[1:]
                ).split("_", maxsplit=1)[0]
                with contextlib.suppress(ValueError):
                    image_index = int(image_index_str)
            if not isinstance(image_index, int):
                continue
            if 0 <= image_index < len(json_dict["images"]):
                # image.nameはインポート時に勝手に縮められてしまうことがあるので、jsonの値から復元する
                indexed_image_name = json_dict["images"][image_index].get("name")
                if isinstance(
                    indexed_image_name, str
                ) and indexed_image_name.startswith(legacy_image_name_prefix):
                    indexed_image_name = "_".join(indexed_image_name.split("_")[1:])
                if indexed_image_name:
                    image.name = indexed_image_name
                else:
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/709630548cdc184af6ea50b2ff3ddc5450bc0af3/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L54
                    image.name = f"Image_{image_index}"
            else:
                image.name = "_".join(image.name.split("_")[1:])

            self.images[image_index] = image

        if bpy.context.object is not None and bpy.context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        for obj in list(bpy.data.objects):
            if self.is_temp_object_name(obj.name):
                obj.select_set(True)
                bpy.ops.object.delete()

        for material in list(bpy.data.materials):
            if self.is_temp_object_name(material.name) and material.users == 0:
                print(material.name)
                bpy.data.materials.remove(material)

        armature = self.armature
        if armature is None:
            raise Exception("Failed to read VRM Humanoid")

    def cleanup_gltf2_with_indices(self) -> None:
        if (
            self.context.view_layer.objects.active is not None
            and self.context.view_layer.objects.active.mode != "OBJECT"
        ):
            bpy.ops.object.mode_set(mode="OBJECT")
        meshes_key = self.import_id + "Meshes"
        nodes_key = self.import_id + "Nodes"
        remove_objs = []
        for obj in list(self.context.scene.collection.objects):
            if isinstance(obj.data, bpy.types.Armature):
                for bone in obj.data.bones:
                    if nodes_key in bone:
                        remove_objs.append(obj)
                        break
                continue

            if isinstance(obj.data, bpy.types.Mesh) and (
                nodes_key in obj.data
                or meshes_key in obj.data
                or self.is_temp_object_name(obj.data.name)
            ):
                remove_objs.append(obj)
                continue

            if (
                nodes_key in obj
                or meshes_key in obj
                or self.is_temp_object_name(obj.name)
            ):
                remove_objs.append(obj)

        bpy.ops.object.select_all(action="DESELECT")
        for obj in remove_objs:
            obj.select_set(True)
        bpy.ops.object.delete()

        retry = True
        while retry:
            retry = False
            for obj in bpy.data.objects:
                if obj in remove_objs and not obj.users:
                    retry = True
                    bpy.data.objects.remove(obj, do_unlink=True)

    def temp_object_name(self) -> str:
        self.temp_object_name_count += 1
        return f"{self.import_id}Temp_{self.temp_object_name_count}_"

    def is_temp_object_name(self, name: str) -> bool:
        return name.startswith(f"{self.import_id}Temp_")

    def extract_textures(self) -> None:
        dir_path = os.path.abspath(self.parse_result.filepath) + ".textures"
        if self.make_new_texture_folder:
            for i in range(100001):
                checking_dir_path = dir_path if i == 0 else f"{dir_path}.{i}"
                if not os.path.exists(checking_dir_path):
                    os.mkdir(checking_dir_path)
                    dir_path = checking_dir_path
                    break

        for image_index, image in self.images.items():
            original_image_path = image.filepath_from_user()
            if not os.path.exists(original_image_path):
                continue
            image_name = os.path.basename(original_image_path)
            image_type = image.file_format.lower()
            if len(image_name) >= 100:
                new_image_name = "texture_too_long_name_" + str(image_index)
                print(f"too long name image: {image_name} is named {new_image_name}")
                image_name = new_image_name

            image_name = remove_unsafe_path_chars(image_name)
            image_path = os.path.join(dir_path, image_name)
            if not image_name.lower().endswith("." + image_type.lower()):
                image_path += "." + image_type
            if not os.path.exists(image_path):
                image.unpack(method="WRITE_ORIGINAL")
                with contextlib.suppress(IOError, shutil.SameFileError):
                    shutil.copyfile(original_image_path, image_path)
                    image.filepath = image_path
                    image.reload()
            else:
                written_flag = False
                for i in range(100000):
                    root, ext = os.path.splitext(image_name)
                    second_image_name = root + "_" + str(i) + ext
                    image_path = os.path.join(dir_path, second_image_name)
                    if not os.path.exists(image_path):
                        image.unpack(method="WRITE_ORIGINAL")
                        shutil.copyfile(image.filepath_from_user(), image_path)
                        image.filepath = image_path
                        image.reload()
                        written_flag = True
                        break
                if not written_flag:
                    print(
                        "There are more than 100000 images with the same name in the folder."
                        + f" Failed to write file: {image_name}"
                    )
