# Changelog

## [2.40.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.39.0...v2.40.0) (2025-04-09)


### 🚀 Features

* partial humanoid bone animation export support ([c3ef297](https://github.com/saturday06/VRM-Addon-for-Blender/commit/c3ef2974245ab71b7efbb88c918a664007ff0b41))
* remove bone tip to root filter ([4b421dc](https://github.com/saturday06/VRM-Addon-for-Blender/commit/4b421dc95048b0fbad328140fdc3bf9770a4cd8b))


### 🐞 Bug Fixes

* fix initialization error on startup mode is not an object mode ([2ff1392](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2ff139218d1478282bbfde9f180556beac65851e))
* restore bone selection on apply t-pose ([7a15c53](https://github.com/saturday06/VRM-Addon-for-Blender/commit/7a15c533b68e5ca3b761a06ea2cba88f906b7bb5))

## [2.39.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.37.0...v2.39.0) (2025-04-05)


### 🚀 Features

* improved spring bone animation performance ([0bcef80](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0bcef80a9ad10286426a41a8c00eb2b783ff932e))

## [2.37.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.36.0...v2.37.0) (2025-03-31)


### 🚀 Features

* add sparse accessors export option for vrm1 ([723503e](https://github.com/saturday06/VRM-Addon-for-Blender/commit/723503eec0ac5ce291a8dafc537909e80db6d59b))
* automatic upload of release files to extensions.blender.org ([f1106d2](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f1106d2b28c414acd356905b9f2b4caf6f45509d))
* hide advanced options on newly created env ([dff0f64](https://github.com/saturday06/VRM-Addon-for-Blender/commit/dff0f646399e78e8cd332eaeaf4d0c844cbb73dd))
* hide vrm1 export option on the dialog for vrm0 export. ([a8c1ef4](https://github.com/saturday06/VRM-Addon-for-Blender/commit/a8c1ef4fc671bcf20c5ea2068512592dafaf6901))


### 🐞 Bug Fixes

* “Export Lights” and “Export glTF Animations” options not being set correctly ([a492f82](https://github.com/saturday06/VRM-Addon-for-Blender/commit/a492f824ffd92d8f8aafac28c1ad0f6b92d7a660))

## [2.36.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.35.1...v2.36.0) (2025-03-30)


### 🚀 Features

* use slotted actions api in blender 4.4 ([70c17c1](https://github.com/saturday06/VRM-Addon-for-Blender/commit/70c17c10952351ec9b021b43301a5d6c589a3a30))


### 🐞 Bug Fixes

* export error when vertex weights are assigned to non-deform bone in VRM 1.0 ([244bbc1](https://github.com/saturday06/VRM-Addon-for-Blender/commit/244bbc13dc509d2a6cde9cf2ac9f9c04b111b01d))

## [2.35.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.35.0...v2.35.1) (2025-03-29)


### 🐞 Bug Fixes

* scene duplication bug when pasting mtoon enabled objects in Blender 3.5.1 or earlier ([6e9ff94](https://github.com/saturday06/VRM-Addon-for-Blender/commit/6e9ff94c0f8922ba2cbb63a5f42696afa63cbec5))

## [2.35.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.34.1...v2.35.0) (2025-03-17)


### 🚀 Features

* support Blender 4.4 ([0acc889](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0acc8890880b393bd1afc4c7cbf02c475c83b5b7))

## [2.34.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.34.0...v2.34.1) (2025-01-15)


### 🐞 Bug Fixes

* regenerate release archives ([12e75bb](https://github.com/saturday06/VRM-Addon-for-Blender/commit/12e75bbc6576effeb61cfe193a6b2efe7bf695e5))

## [2.34.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.33.1...v2.34.0) (2025-01-14)


### 🚀 Features

* add a setting to export gltf animation or not ([bd5b2d3](https://github.com/saturday06/VRM-Addon-for-Blender/commit/bd5b2d3d0aaa9819969f4721660439a533ec5849))

## [2.33.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.33.0...v2.33.1) (2024-12-18)


### 🐞 Bug Fixes

* export error during automatic modifier application ([48f526b](https://github.com/saturday06/VRM-Addon-for-Blender/commit/48f526b8ca98992f7df1beb19a72a648911506cf))

## [2.33.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.32.2...v2.33.0) (2024-12-15)


### 🚀 Features

* skip blender 3.1.2 workaround in new blender ([0dc0b72](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0dc0b721cbd59e166bde35d867a7cf673ff51864))


### 🐞 Bug Fixes

* prevent skinned mesh node parenting to make gltf validator happy ([1222f26](https://github.com/saturday06/VRM-Addon-for-Blender/commit/1222f2647d3959005fcba4e59a0797188d30008f))

## [2.32.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.32.1...v2.32.2) (2024-12-10)


### 🐞 Bug Fixes

* add workaround for non-weighted skinned mesh export error ([a47a0d2](https://github.com/saturday06/VRM-Addon-for-Blender/commit/a47a0d289ea07527da24e63072601ed05eaae357))
* unexpected constrainted node rotation on export ([90809f0](https://github.com/saturday06/VRM-Addon-for-Blender/commit/90809f03bd3f07a5b8747e56802cd927a425ed73))

## [2.32.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.32.0...v2.32.1) (2024-12-07)


### 🐞 Bug Fixes

* VRM export causes unexpected constrainted bone rotation ([2425087](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2425087a43b3f29f05a69fbf23745c2590cf54c8))


### 📝 Documentation

* remove deunnecessary notice ([24532bf](https://github.com/saturday06/VRM-Addon-for-Blender/commit/24532bf55d9a38420b731dd0d9637207cb57cff2))

## [2.32.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.31.1...v2.32.0) (2024-12-04)


### 🚀 Features

* completely rework vrma import export matrices calculation ([39caa2f](https://github.com/saturday06/VRM-Addon-for-Blender/commit/39caa2f6bc7fd347ad500bc4a4b598e537bd5ffa))
* support drag and drop vrm/vrma import ([756081c](https://github.com/saturday06/VRM-Addon-for-Blender/commit/756081c8b31291399cc583fd27a510ead35f1d62))

## [2.31.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.31.0...v2.31.1) (2024-12-01)


### 🐞 Bug Fixes

* principled bsdf material export error on Blender 4.3 ([94c1e23](https://github.com/saturday06/VRM-Addon-for-Blender/commit/94c1e235bf662847efcb0075a10df7f6d0215606))

## [2.31.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.30.1...v2.31.0) (2024-11-24)


### 🚀 Features

* auto mixamo bone assignment ([ffef2dd](https://github.com/saturday06/VRM-Addon-for-Blender/commit/ffef2dd07bf29c1d29462ada4642f78aa803dc87))

## [2.30.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.30.0...v2.30.1) (2024-11-24)


### 🐞 Bug Fixes

* run ruff formatter ([4a577b1](https://github.com/saturday06/VRM-Addon-for-Blender/commit/4a577b1b77f9731d17ca9535b7d4bb6b70a60e5f))

## [2.30.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.29.0...v2.30.0) (2024-11-22)


### 🚀 Features

* support blender 4.3 ([21ba0f3](https://github.com/saturday06/VRM-Addon-for-Blender/commit/21ba0f3cfe24eaab55c7334cc2f56aa72ceb904a))

## [2.29.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.28.1...v2.29.0) (2024-11-21)


### 🚀 Features

* restore Simplified Chinese translation with the permission of the original author ([b89b6b9](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b89b6b90ae6ee25e5cca3c0f104ed200ff9abe55))

## [2.28.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.28.0...v2.28.1) (2024-11-21)


### 🐞 Bug Fixes

* incorrect mtoon1 to mtoon0 color conversion ([774457d](https://github.com/saturday06/VRM-Addon-for-Blender/commit/774457d075bc7ce6f9b93c06888182f633c93dc8))
* remove unnecessary .blend link ([d55bb32](https://github.com/saturday06/VRM-Addon-for-Blender/commit/d55bb322dee5aae67638642d2790ae23c3a41a9e))

## [2.28.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.27.0...v2.28.0) (2024-11-14)


### 🚀 Features

* mtoon outline preview switching ([2d22868](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2d228687638fec0a188a8db303a6257ed1079388))
* release-please action ([f7b1b68](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f7b1b6894d89ba21cfeaf7727bae9086e51daf74))


### 🐞 Bug Fixes

* paths ([b8157c5](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b8157c54bc21496ed97452526e647fc00d743a72))


### 📝 Documentation

* add release note entry for experimental texture transform bind preview ([6ec9f3b](https://github.com/saturday06/VRM-Addon-for-Blender/commit/6ec9f3bc9aca38b5515abecacca10d6979377911))
* remove deprecated diagrams ([238e77a](https://github.com/saturday06/VRM-Addon-for-Blender/commit/238e77a0b1d7b6af1b9017efe99c0be47b37f602))
* use emojis ([87f32fb](https://github.com/saturday06/VRM-Addon-for-Blender/commit/87f32fb4783f4dfea8bc73830cbfa93f2cedd91b))

## [2.27.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.26.0...v2.27.0) (2024-11-14)


### 🚀 Features

* mtoon outline preview switching ([2d22868](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2d228687638fec0a188a8db303a6257ed1079388))
* release-please action ([f7b1b68](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f7b1b6894d89ba21cfeaf7727bae9086e51daf74))


### 🐞 Bug Fixes

* paths ([b8157c5](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b8157c54bc21496ed97452526e647fc00d743a72))


### 📝 Documentation

* add release note entry for experimental texture transform bind preview ([6ec9f3b](https://github.com/saturday06/VRM-Addon-for-Blender/commit/6ec9f3bc9aca38b5515abecacca10d6979377911))
* remove deprecated diagrams ([238e77a](https://github.com/saturday06/VRM-Addon-for-Blender/commit/238e77a0b1d7b6af1b9017efe99c0be47b37f602))
* use emojis ([87f32fb](https://github.com/saturday06/VRM-Addon-for-Blender/commit/87f32fb4783f4dfea8bc73830cbfa93f2cedd91b))
