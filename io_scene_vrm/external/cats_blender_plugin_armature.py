import dataclasses
from typing import Dict, Iterator, List, Optional

import bpy


@dataclasses.dataclass
class CatsArmatureDataEditBone:
    name: str
    original_name: str
    valid: bool = True
    parent: Optional["CatsArmatureDataEditBone"] = None
    children: List["CatsArmatureDataEditBone"] = dataclasses.field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


@dataclasses.dataclass(frozen=True)
class CatsArmaturePoseBone:
    name: str


@dataclasses.dataclass(frozen=True)
class CatsArmaturePoseBones:
    _bones: List[CatsArmaturePoseBone] = dataclasses.field(default_factory=list)

    def __iter__(self) -> Iterator[CatsArmaturePoseBone]:
        return self._bones.__iter__()

    def __len__(self) -> int:
        return len(self._bones)


@dataclasses.dataclass(frozen=True)
class CatsArmaturePose:
    bones: CatsArmaturePoseBones


@dataclasses.dataclass(frozen=True)
class CatsArmatureDataEditBones:
    _edit_bones: List[CatsArmatureDataEditBone] = dataclasses.field(
        default_factory=list
    )

    def __iter__(self) -> Iterator[CatsArmatureDataEditBone]:
        return self._edit_bones.__iter__()

    def __contains__(self, bone_name: str) -> bool:
        if not isinstance(bone_name, str):
            print(f'"{bone_name}" is not str')
            return False
        return any(bone.name == bone_name for bone in self._edit_bones)

    def __len__(self) -> int:
        return len(self._edit_bones)

    def get(self, bone_name: str) -> CatsArmatureDataEditBone:
        for bone in self._edit_bones:
            if bone.name == bone_name:
                return bone
        return CatsArmatureDataEditBone(
            name=bone_name,
            original_name="",
            valid=False,
        )


@dataclasses.dataclass(frozen=True)
class CatsArmatureData:
    edit_bones: CatsArmatureDataEditBones


@dataclasses.dataclass(frozen=True)
class CatsArmature:
    pose: CatsArmaturePose
    data: CatsArmatureData

    @staticmethod
    def create(armature: bpy.types.Armature) -> "CatsArmature":
        pose = CatsArmaturePose(
            bones=CatsArmaturePoseBones(
                _bones=[
                    CatsArmaturePoseBone(name=bone_name)
                    for bone_name in armature.bones.keys()
                ]
            )
        )
        child_name_to_parent: Dict[str, CatsArmatureDataEditBone] = {}
        bones = [bone for bone in armature.bones if not bone.parent]
        cats_bones = []
        while bones:
            bone = bones.pop()
            cats_bone = CatsArmatureDataEditBone(
                name=bone.name,
                original_name=bone.name,
                parent=child_name_to_parent.get(bone.name),
            )
            cats_bones.append(cats_bone)
            for child in bone.children:
                child_name_to_parent[child.name] = cats_bone
                bones.append(child)

        return CatsArmature(
            pose=pose,
            data=CatsArmatureData(
                edit_bones=CatsArmatureDataEditBones(_edit_bones=cats_bones)
            ),
        )

    def cats_name_to_original_name(self) -> Dict[str, str]:
        return {
            edit_bone.name: edit_bone.original_name
            for edit_bone in self.data.edit_bones
        }
