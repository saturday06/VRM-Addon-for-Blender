# Changelog

## [3.17.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.16.1...v3.17.0) (2025-11-28)


### 🚀 Features

* adjust progress value calculation based on Blender version ([6f86818](https://github.com/saturday06/VRM-Addon-for-Blender/commit/6f86818ebf7e1c05455eec4e893945c843b05ca2))
* make VRM 1.0 the default for the third anniversary ([dd490e9](https://github.com/saturday06/VRM-Addon-for-Blender/commit/dd490e9c4d6d9ae91f2bfebf2dfd0009ab80fdf5))
* support blender 5.0 ([0ef59cd](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0ef59cd2d6e51195b303c16e0ef5dceea0241c01))
* support vrm0 legacy unlit shaders ([ae0ce39](https://github.com/saturday06/VRM-Addon-for-Blender/commit/ae0ce39547ca94e47822203a069ee9680804a704))
* trigger release workflow ([1e7293a](https://github.com/saturday06/VRM-Addon-for-Blender/commit/1e7293a3f1f461635c4ad91f1875136162486b54))


### 🐛 Bug Fixes

* adjusted the change threshold for previews of expressions with isBinary enabled ([f2ffac3](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f2ffac37b538601a84ca24fb5455a0fa5cb5ed47))
* **deps:** lock file maintenance regular dependency updates ([#1093](https://github.com/saturday06/VRM-Addon-for-Blender/issues/1093)) ([cd1a83a](https://github.com/saturday06/VRM-Addon-for-Blender/commit/cd1a83ac5e1f37778ea665cfb17692e28a2f8546))
* **deps:** lock file maintenance regular dependency updates ([#1095](https://github.com/saturday06/VRM-Addon-for-Blender/issues/1095)) ([cbe92d1](https://github.com/saturday06/VRM-Addon-for-Blender/commit/cbe92d165b0d35981e33c3cb647e134eb84b9c7e))
* fix a bug in Blender 5.0 where textures duplicated during VRM1 export ([514e7e7](https://github.com/saturday06/VRM-Addon-for-Blender/commit/514e7e79f49a73f43703668478503ff34be2af17))
* fix a bug that _ALPHABLEND_ON is incorrectly enabled in Blender 4.2 and later ([a9d21b4](https://github.com/saturday06/VRM-Addon-for-Blender/commit/a9d21b41f92eda5fc40b8168bde5dbe591c56389))
* fix a bug that invisible modifiers would become visible on VRM import ([52e583c](https://github.com/saturday06/VRM-Addon-for-Blender/commit/52e583caf465a95f688096ca895b001a35d88956))
* fix an issue where VRM0 morph target names were not displayed in some applications ([9c956b8](https://github.com/saturday06/VRM-Addon-for-Blender/commit/9c956b89235427a78c3e8d5353943ba26c24c4b0))
* fix export error on Blender 2.93 ([10d3a57](https://github.com/saturday06/VRM-Addon-for-Blender/commit/10d3a57bf86aaade94ae01d2f66901225350a4f6))
* fix export error when vertex weights are in certain situations ([53775d7](https://github.com/saturday06/VRM-Addon-for-Blender/commit/53775d78c1798fc6dfedd0fb05057e18f4e8e738))
* fix resource leak on import VRM ([b6caea7](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b6caea7ae275b15c3a7f23e562f4a524e3716c6b))
* fixed a bug where a single outline material could be shared across multiple base materials ([fc6752f](https://github.com/saturday06/VRM-Addon-for-Blender/commit/fc6752f0260ac5e7f300f3bf32ceecd135a454f8))
* fixed a bug where referenced Non-Deform bones were not exported ([e725b50](https://github.com/saturday06/VRM-Addon-for-Blender/commit/e725b502e1f0df78bdd4a4b5ceddfdb2539cb90a))
* fixed an issue where temporary armature might remain after VRM export ([fe9fc0e](https://github.com/saturday06/VRM-Addon-for-Blender/commit/fe9fc0e950d6204c7277bedc237ab662d42e869b))
* slightly reduces performance issues with the list view in Blender 4.5. ([cb70239](https://github.com/saturday06/VRM-Addon-for-Blender/commit/cb7023981c0268ef5b56254d9732d82424866f6e))
* trigger release pipeline ([2ec0e8e](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2ec0e8eff6098c29eaecb1eb969ac767543a79eb))
* trigger release pipeline ([05a6733](https://github.com/saturday06/VRM-Addon-for-Blender/commit/05a6733ecfe76500ba005a9f7451c6e3f2d6d691))
* trigger release process ([2e8a4fc](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2e8a4fc7af826e308d4dca68db313fd4fb317622))
* trigger release workflow ([82c2c68](https://github.com/saturday06/VRM-Addon-for-Blender/commit/82c2c68207a01ab4a9d9ae37d6aa2632031b111e))
* trigger release workflow ([5aa88dc](https://github.com/saturday06/VRM-Addon-for-Blender/commit/5aa88dc095fefab5d1541bb3cb8772d819bdf0ec))

## [3.16.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.15.0...v3.16.0) (2025-11-08)


### 🚀 Features

* support blender 5.0 ([0ef59cd](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0ef59cd2d6e51195b303c16e0ef5dceea0241c01))


### 🐛 Bug Fixes

* fixed a bug where a single outline material could be shared across multiple base materials ([fc6752f](https://github.com/saturday06/VRM-Addon-for-Blender/commit/fc6752f0260ac5e7f300f3bf32ceecd135a454f8))

## [3.15.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.14.1...v3.15.0) (2025-10-19)


### 🚀 Features
* streamlining the migration of old .blend files ([0065169](https://github.com/saturday06/VRM-Addon-for-Blender/commit/00651695ef55812d59cf5e9418cdf7c419746103))
* preparations for future blender support ([b79ca1d](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b79ca1d231756d9646b9148c4407eabb846f12bf), [73872ea](https://github.com/saturday06/VRM-Addon-for-Blender/commit/73872ea6601fbb07710f28a29f11240244d82380), [16204c8](https://github.com/saturday06/VRM-Addon-for-Blender/commit/16204c89db4793831c0c4ac5e788dfe73be4ee6d))
* setting up an automated benchmarking environment ([d348315](https://github.com/saturday06/VRM-Addon-for-Blender/commit/d348315b09ce7a403be9dd1727f3e7b901090835))

## [3.14.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.14.0...v3.14.1) (2025-09-28)


### 🐛 Bug Fixes

* adjusted the change threshold for previews of expressions with isBinary enabled ([f2ffac3](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f2ffac37b538601a84ca24fb5455a0fa5cb5ed47))

## [3.14.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.13.3...v3.14.0) (2025-09-22)


### 🚀 Features

* make VRM 1.0 the default for the third anniversary ([dd490e9](https://github.com/saturday06/VRM-Addon-for-Blender/commit/dd490e9c4d6d9ae91f2bfebf2dfd0009ab80fdf5))

### 🐛 Bug Fixes

* reduce max memory usage during VRM0 export ([9f466c0](https://github.com/saturday06/VRM-Addon-for-Blender/commit/9f466c068645209c8b020b4b398bfe30ac20e7c9))

## [3.13.3](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.13.2...v3.13.3) (2025-09-14)


### 🐛 Bug Fixes

* fix a bug that invisible modifiers would become visible on VRM import ([52e583c](https://github.com/saturday06/VRM-Addon-for-Blender/commit/52e583caf465a95f688096ca895b001a35d88956))

## [3.13.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.13.1...v3.13.2) (2025-09-14)


### 🐛 Bug Fixes

* fix resource leak on import VRM ([b6caea7](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b6caea7ae275b15c3a7f23e562f4a524e3716c6b))

## [3.13.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.13.0...v3.13.1) (2025-09-07)


### 🐛 Bug Fixes

* fix an issue where VRM0 morph target names were not displayed in some applications ([9c956b8](https://github.com/saturday06/VRM-Addon-for-Blender/commit/9c956b89235427a78c3e8d5353943ba26c24c4b0))

## [3.13.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.11.5...v3.13.0) (2025-09-02)

### 🐛 Bug Fixes

* fix a bug where isolated collider objects could sometimes occur ([c791d2f](https://github.com/saturday06/VRM-Addon-for-Blender/commit/c791d2f1033e58143a428e3853b5ffc9045d3cef))

## [3.11.5](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.11.4...v3.11.5) (2025-08-31)


### 🐛 Bug Fixes

* fix an issue where temporary armature might remain after VRM export ([fe9fc0e](https://github.com/saturday06/VRM-Addon-for-Blender/commit/fe9fc0e950d6204c7277bedc237ab662d42e869b))

## [3.11.4](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.11.2...v3.11.4) (2025-08-23)


### 🚀 Features

* improve bone name matching algorithm ([b3125fd](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b3125fda54b2ec2efd197c889f26573d02e66ca9))

## [3.11.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.11.1...v3.11.2) (2025-08-18)


### 🐛 Bug Fixes

* fix export error when vertex weights are in certain situations ([53775d7](https://github.com/saturday06/VRM-Addon-for-Blender/commit/53775d78c1798fc6dfedd0fb05057e18f4e8e738))

## [3.11.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.11.0...v3.11.1) (2025-08-16)


### 🐛 Bug Fixes

* fix a bug that _ALPHABLEND_ON is incorrectly enabled in Blender 4.2 and later ([a9d21b4](https://github.com/saturday06/VRM-Addon-for-Blender/commit/a9d21b41f92eda5fc40b8168bde5dbe591c56389))
  * Special thanks to **ontokyo** (https://qiita.com/ontokyo/items/ed6d684fde3179128286)


## [3.11.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.10.2...v3.11.0) (2025-08-16)


### 🚀 Features

* support vrm0 legacy unlit shaders ([ae0ce39](https://github.com/saturday06/VRM-Addon-for-Blender/commit/ae0ce39547ca94e47822203a069ee9680804a704))


### 🐛 Bug Fixes

* slightly reduces performance issues with the list view in Blender 4.5. ([cb70239](https://github.com/saturday06/VRM-Addon-for-Blender/commit/cb7023981c0268ef5b56254d9732d82424866f6e))

## [3.10.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.10.1...v3.10.2) (2025-08-11)


### 🐛 Bug Fixes

* fix export error on Blender 2.93 ([10d3a57](https://github.com/saturday06/VRM-Addon-for-Blender/commit/10d3a57bf86aaade94ae01d2f66901225350a4f6))
* fix a bug where referenced Non-Deform bones were not exported ([e725b50](https://github.com/saturday06/VRM-Addon-for-Blender/commit/e725b502e1f0df78bdd4a4b5ceddfdb2539cb90a))

## [3.10.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.9.2...v3.10.1) (2025-07-30)

### 🐛 Bug Fixes

* fixed potential bugs that could occur at startup ([886b97](https://github.com/saturday06/VRM-Addon-for-Blender/commit/886b97c1b8e74a15ddd4b2269a7c8fdbc0374c64))

### 📈 Performance Improvements

* improved performance of detecting the need to add outline modifiers ([469935](https://github.com/saturday06/VRM-Addon-for-Blender/commit/46993585111010ae91782552aa09775ed2ea1b04))

## [3.9.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.9.1...v3.9.2) (2025-07-25)


### 🐛 Bug Fixes

* fix a bug that prevented VRM0 export under certain conditions ([f590a3e](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f590a3e302152c33c6b72b31442c3b23398b8940))
* fix a crash due to circular access of shader nodes ([76c15d0](https://github.com/saturday06/VRM-Addon-for-Blender/commit/76c15d05000f6ce2453531650214fd17502c14f9))

## [3.9.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.9.0...v3.9.1) (2025-07-19)


### 🐛 Bug Fixes

* Mesh Assignment -&gt; Shape Key Assignment ([9da9694](https://github.com/saturday06/VRM-Addon-for-Blender/commit/9da969408bbbdd88e550b60f2fc5731da79506c0))

## [3.9.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.8.0...v3.9.0) (2025-07-19)


### 🚀 Features

* add option to automatically include MToon shader node group ([b994b59](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b994b5904be59e57c26451788ab6864bdd163534))
* add restore mesh assignments functionality ([f72ca66](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f72ca66782cdda0d8e6cbe8107e4de63961f68ce))

## [3.8.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.7.5...v3.8.0) (2025-07-13)


### 🚀 Features

* automatic application of modifiers when exporting VRM1 ([3e0b562](https://github.com/saturday06/VRM-Addon-for-Blender/commit/3e0b56240b4167bfa5d582fe23df0c470b142595))


### 🐞 Bug Fixes

* fix possible index error on export VRM0 ([c61bfea](https://github.com/saturday06/VRM-Addon-for-Blender/commit/c61bfeac8818c46214f4515444fe140922007972))

## [3.7.5](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.7.4...v3.7.5) (2025-07-05)


### 🐞 Bug Fixes

* fixed a bug where the parent of the spring bone1 collider was not updated ([ae45306](https://github.com/saturday06/VRM-Addon-for-Blender/commit/ae45306c2e5f3c9230a27e6d72443561b3547425))

## [3.7.4](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.7.3...v3.7.4) (2025-06-28)

### 🚀 Features

* add ue4humanoid and bip001 mappings ([#939](https://github.com/saturday06/VRM-Addon-for-Blender/pull/939)) by [@elbadcode](https://github.com/elbadcode)

## [3.7.3](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.7.2...v3.7.3) (2025-06-22)


### 🐞 Bug Fixes

* fixed a bug in Blender 4.5 that caused temporary objects to remain on import ([1980f84](https://github.com/saturday06/VRM-Addon-for-Blender/commit/1980f841485020c7eddd9e024df687f203ddae6b))

## [3.7.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.7.1...v3.7.2) (2025-06-18)


### 🐞 Bug Fixes

* don't create gltf scene collections by default in blender 4.5 beta ([af4a971](https://github.com/saturday06/VRM-Addon-for-Blender/commit/af4a9712f934a885648f93dd8e130deda86b4162))

## [3.7.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.7.0...v3.7.1) (2025-06-15)


### 🐞 Bug Fixes

* fixed a bug that KHR_materials_emissive_strength was not read when importing VRM1 ([5549c58](https://github.com/saturday06/VRM-Addon-for-Blender/commit/5549c5877735b93a2ef5c19aebe97b6507c35d76))
* MatCap display now matches UniVRM ([19b944b](https://github.com/saturday06/VRM-Addon-for-Blender/commit/19b944bb595d9af9c301906b049456258ee975d4))

## [3.7.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.6.2...v3.7.0) (2025-06-13)


### 🚀 Features

* support blender 4.5 ([4da6719](https://github.com/saturday06/VRM-Addon-for-Blender/commit/4da67198e824afb58e0fab73b5129a5f25e6375a))

## [3.6.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.6.1...v3.6.2) (2025-06-04)


### 🐞 Bug Fixes

* fix random crash ([d636f92](https://github.com/saturday06/VRM-Addon-for-Blender/commit/d636f92fcf420e7ad63a40c20f1c743d976eb0db) [75abd47](https://github.com/saturday06/VRM-Addon-for-Blender/commit/75abd47599f625af08a3e94f6343dc3cc8d6abc0))

## [3.6.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.6.0...v3.6.1) (2025-06-02)


### 🐞 Bug Fixes

* fix resource leak on export ([4dea36a](https://github.com/saturday06/VRM-Addon-for-Blender/commit/4dea36a749abc6dde06aee81a24bf65192b61233))

## [3.6.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.5.0...v3.6.0) (2025-06-01)


### 🚀 Features

* warn unsupported parenting ([0d8b8bd](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0d8b8bd457747be31efc52091b10fbdc78074c3a))
* hides personal information when import/export errors occur ([f9c861f](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f9c861ff7a8b04f2f874e7aaefb0a80fc236870c))
* small optimization ([0cd6e21](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0cd6e2191101d43ad4dd0d5c35b5bd740d1b585a) [5eab625](https://github.com/saturday06/VRM-Addon-for-Blender/commit/5eab62560cb0591f6b458e5ba1a75593c1de804e) [1b2d718](https://github.com/saturday06/VRM-Addon-for-Blender/commit/1b2d7187ee501ad2350e44f318afa36a4c457d5a))

### 🐞 Bug Fixes

* fix empty list's button alignment ([fb6016c](https://github.com/saturday06/VRM-Addon-for-Blender/commit/fb6016c8bca3ef03f8cf13ecbaacd14ec0f4e55d))


### 📝 Documentation

* cleanup links ([668e31b](https://github.com/saturday06/VRM-Addon-for-Blender/commit/668e31b2a689cb1d01c1c10e8272510a341714ac))

## [3.5.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.4.2...v3.5.0) (2025-05-21)


### 🚀 Features

* implemented a dialog that displays errors during import and export ([2fd7e6f](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2fd7e6f2b7b9a51052979801da97cd8eeddaa0d0))

## [3.4.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.4.1...v3.4.2) (2025-05-14)


### 🐞 Bug Fixes

* fix invalid spring json output on export under certain conditions ([597c323](https://github.com/saturday06/VRM-Addon-for-Blender/commit/597c3232544e3635a3a361e8f6b64f136695e5e2))

## [3.4.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.4.0...v3.4.1) (2025-05-13)


### 🐞 Bug Fixes

* fix invalid spring joint ordering on export under certain conditions ([5814740](https://github.com/saturday06/VRM-Addon-for-Blender/commit/5814740e168e1475721d317b1f8203a8bbfa75b1))

## [3.4.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.3.2...v3.4.0) (2025-05-11)


### 🚀 Features

* VRM Animation input and output are now as similar as possible to UniVRM ([75ebc21](https://github.com/saturday06/VRM-Addon-for-Blender/commit/75ebc2177a49166d84a37f978595583e51597314))

## [3.3.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.3.1...v3.3.2) (2025-05-08)


### 🐞 Bug Fixes

* prevent mesh duplication on export ([45d8943](https://github.com/saturday06/VRM-Addon-for-Blender/commit/45d894307a957fbcd2fff596b2c329409f79819e))

## [3.3.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.3.0...v3.3.1) (2025-05-06)


### 🐞 Bug Fixes

* fix invalid partial humanoid bone animation export ([a616799](https://github.com/saturday06/VRM-Addon-for-Blender/commit/a6167996833c6c577f7d06abb4d9151641dab3e5))

## [3.3.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.2.0...v3.3.0) (2025-05-03)


### 🚀 Features

* human bone assignment diagnostics ([7f2eebd](https://github.com/saturday06/VRM-Addon-for-Blender/commit/7f2eebdbc20d1a61a321e18d2ccd2ae48f4a4c17))
<img width="973" alt="diagnostics" src="https://github.com/user-attachments/assets/9081376c-7926-4274-8491-d4bfdb9e657e" />


## [3.2.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.1.0...v3.2.0) (2025-05-02)


### 🚀 Features

* add advanced option's description ([4a62a3c](https://github.com/saturday06/VRM-Addon-for-Blender/commit/4a62a3c637ee60eff14793aa0a145315e23a25b3))


### 🐞 Bug Fixes

* release flow updates ([c204dde](https://github.com/saturday06/VRM-Addon-for-Blender/commit/c204ddec9dfbffc9f7edc7047ec733ea472d02b9))

## [3.1.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.0.1...v3.1.0) (2025-04-20)


### 🚀 Features

* add VRoid mapping config ([2c3d10f](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2c3d10f64d9929ac5cdc105703222187ded1978f))


### 🐞 Bug Fixes

* improve unnatural English phrases ([d77b673](https://github.com/saturday06/VRM-Addon-for-Blender/commit/d77b673ea968f6358060fde5ec7601bd81351c7e)) ([7e095dc](https://github.com/saturday06/VRM-Addon-for-Blender/commit/7e095dc89eda288cb24bc12b7e99c426e8171a6a)) ([d82b0da](https://github.com/saturday06/VRM-Addon-for-Blender/commit/d82b0daebcbbce841bfeb4d3deec577bbb03af6c)) ([80a1d48](https://github.com/saturday06/VRM-Addon-for-Blender/commit/80a1d48bc185e845958acb34290950cb536c8968)) ([4c24fc1](https://github.com/saturday06/VRM-Addon-for-Blender/commit/4c24fc1efb2b00da009206ce2807ae5bde2381f3))

## [3.0.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v3.0.0...v3.0.1) (2025-04-17)


### 🐞 Bug Fixes

* adjust line wrapping to pass formatting check ([1e4db97](https://github.com/saturday06/VRM-Addon-for-Blender/commit/1e4db97e7dd8e87d6bbc033f6d02dbc3fb95cdf1))
* improve English text in error and information messages ([f874231](https://github.com/saturday06/VRM-Addon-for-Blender/commit/f874231b290d778677781da6e5d835aceffaf89f))
* improve English text in error and information messages (cont) ([7b33b92](https://github.com/saturday06/VRM-Addon-for-Blender/commit/7b33b92082786095f8ba612758b609f8acc7d974))


### 📝 Documentation

* improve contribution wording in README ([94786b2](https://github.com/saturday06/VRM-Addon-for-Blender/commit/94786b2372a808aed24721351a5908f903fa27ba))
* improve contribution wording in README ([1b739df](https://github.com/saturday06/VRM-Addon-for-Blender/commit/1b739df64ff4e8486782ff89a537d4ac7484729e))

## [3.0.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.40.0...v3.0.0) (2025-04-14)

### 💥 Breaking Change

Introduce "MToon" shader node group instead of "MToon_unversioned" ([b6dd21d](https://github.com/saturday06/VRM-Addon-for-Blender/commit/b6dd21d1268e08d52facb5efa567c324b0432f76))

The "MToon_unversioned" shader node group, which was left in place for
compatibility, is no longer added. Instead, a new "MToon" shader node
group will be added.

The "MToon_unversioned" will not be removed and will continue to be
included with the add-on. Alternatively, it can be obtained from
https://github.com/saturday06/VRM-Addon-for-Blender/blob/v2.40.0/src/io_scene_vrm/common/mtoon0.blend

## [2.40.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.39.0...v2.40.0) (2025-04-10)


### 🚀 Features

* partial humanoid bone animation export support ([c3ef297](https://github.com/saturday06/VRM-Addon-for-Blender/commit/c3ef2974245ab71b7efbb88c918a664007ff0b41))
* remove bone tip to root filter ([4b421dc](https://github.com/saturday06/VRM-Addon-for-Blender/commit/4b421dc95048b0fbad328140fdc3bf9770a4cd8b))


### 🐞 Bug Fixes

* fix initialization error on startup mode is not an object mode ([2ff1392](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2ff139218d1478282bbfde9f180556beac65851e))
* restore bone selection on apply t-pose ([7a15c53](https://github.com/saturday06/VRM-Addon-for-Blender/commit/7a15c533b68e5ca3b761a06ea2cba88f906b7bb5))

## [2.39.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.38.0...v2.39.0) (2025-04-05)


### 🚀 Features

* improved spring bone animation performance ([0bcef8](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0bcef80a9ad10286426a41a8c00eb2b783ff932e))

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

* Remove workaround for 'Bone.use_deform' expot bug in Blender 4.4 ([6bbd3ca98](https://github.com/saturday06/VRM-Addon-for-Blender/commit/6bbd3ca98f66e9ba4601c7116f8f2ad6e53d48da))
* Fix scene duplication bug when pasting mtoon enabled objects in Blender 3.5.1 or earlier ([6e9ff94](https://github.com/saturday06/VRM-Addon-for-Blender/commit/6e9ff94c0f8922ba2cbb63a5f42696afa63cbec5))

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

* fix export error during automatic modifier application ([48f526b](https://github.com/saturday06/VRM-Addon-for-Blender/commit/48f526b8ca98992f7df1beb19a72a648911506cf))

## [2.33.0](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.32.2...v2.33.0) (2024-12-15)


### 🚀 Features

* skip blender 3.1.2 workaround in new blender ([0dc0b72](https://github.com/saturday06/VRM-Addon-for-Blender/commit/0dc0b721cbd59e166bde35d867a7cf673ff51864))


### 🐞 Bug Fixes

* prevent skinned mesh node parenting to make gltf validator happy ([1222f26](https://github.com/saturday06/VRM-Addon-for-Blender/commit/1222f2647d3959005fcba4e59a0797188d30008f))

## [2.32.2](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.32.1...v2.32.2) (2024-12-10)


### 🐞 Bug Fixes

* add workaround for non-weighted skinned mesh export error ([a47a0d2](https://github.com/saturday06/VRM-Addon-for-Blender/commit/a47a0d289ea07527da24e63072601ed05eaae357))
* unexpected constrained node rotation on export ([90809f0](https://github.com/saturday06/VRM-Addon-for-Blender/commit/90809f03bd3f07a5b8747e56802cd927a425ed73))

## [2.32.1](https://github.com/saturday06/VRM-Addon-for-Blender/compare/v2.32.0...v2.32.1) (2024-12-07)


### 🐞 Bug Fixes

* fix the bug that VRM export causes unexpected constrained bone rotation ([2425087](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2425087a43b3f29f05a69fbf23745c2590cf54c8))


### 📝 Documentation

* remove unnecessary notice ([24532bf](https://github.com/saturday06/VRM-Addon-for-Blender/commit/24532bf55d9a38420b731dd0d9637207cb57cff2))

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

### 🚀 Features

* improve Simplified Chinese translation (https://github.com/saturday06/VRM-Addon-for-Blender/pull/653 by uitcis)

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

### 💣 Breaking Changes

* [change the license from "MIT" to "MIT OR GPL-3.0-or-later](https://github.com/saturday06/VRM-Addon-for-Blender/commit/a8ecfabb724731c2ae262bf59f7acc9ff964e74d) 
* [temporary disable Simplified Chinese translation for the Blender Extensions platform](https://github.com/saturday06/VRM-Addon-for-Blender/commit/324c093a0c407ee7182a14b1885830e408be6912) 
```
For anyone who is interested in the Simplified Chinese translation.

Simplified Chinese translation has been temporarily disabled. This is to comply
with the license requirements of the Blender Extensions platform.

Please check the URL below for more details:
https://github.com/saturday06/VRM-Addon-for-Blender/issues/627
```

* [temporary revert the English translation improvement for the Blender Extensions platform](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2593ec2b49215c6883f62febc971bec3cd5f959a) 

### 🚀 Features

* [experimental texture transform bind preview](https://github.com/saturday06/VRM-Addon-for-Blender/pull/552)
* [mtoon outline preview switching](https://github.com/saturday06/VRM-Addon-for-Blender/commit/2d228687638fec0a188a8db303a6257ed1079388)
* [create basic armature on import vrma into an empty workspace](https://github.com/saturday06/VRM-Addon-for-Blender/commit/782f793a13cb871b21b8ba8abf591e3f7c40671f)

### 🐞 Bug Fixes

* [workaround for blender 4.2 multi root armature error](https://github.com/saturday06/VRM-Addon-for-Blender/commit/fe8f06d0452780306595fb87e84cd383df456879)
