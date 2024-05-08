from .abstract_base_vrm_exporter import AbstractBaseVrmExporter


class Gltf2AddonExporterUserExtension:
    def __init__(self) -> None:
        self.object_name_to_modifier_names = (
            AbstractBaseVrmExporter.hide_mtoon1_outline_geometry_nodes()
        )

    def gather_gltf_hook(
        self,
        # The number of arguments and specifications vary widely from version to version
        # of the glTF 2.0 add-on.
        _a: object,
        _b: object,
        _c: object,
        _d: object,
    ) -> None:
        AbstractBaseVrmExporter.restore_mtoon1_outline_geometry_nodes(
            self.object_name_to_modifier_names
        )
        self.object_name_to_modifier_names.clear()
