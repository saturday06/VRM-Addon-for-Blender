from .abstract_base_vrm_exporter import AbstractBaseVrmExporter


class Gltf2AddonExporterUserExtension:
    def __init__(self) -> None:
        self.object_name_to_modifier_names = (
            AbstractBaseVrmExporter.hide_mtoon1_outline_geometry_nodes()
        )

    # 引数の数や仕様はglTF 2.0アドオンのバージョンごとに大きく変わるので注意
    def gather_gltf_hook(self, _a: object, _b: object, _c: object, _d: object) -> None:
        AbstractBaseVrmExporter.restore_mtoon1_outline_geometry_nodes(
            self.object_name_to_modifier_names
        )
        self.object_name_to_modifier_names.clear()
