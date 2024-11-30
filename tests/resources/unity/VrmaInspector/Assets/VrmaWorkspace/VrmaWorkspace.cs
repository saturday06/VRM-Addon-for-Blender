// SPDX-License-Identifier: MIT OR GPL-3.0-or-later

using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UniGLTF;
using UnityEngine;
using UniVRM10;
using UnityEngine.InputSystem;

namespace VrmaWorkspace
{
    public class VrmaWorkspace : MonoBehaviour
    {
        private Vrm10Instance? _vrm10Instance;
        private RuntimeGltfInstance? _vrmaInstance;
        private string? _vrmaPath;
        private byte[]? _vrmaBytes;

        private void Start()
        {
            _ = LoadVrma(interactive: true);
        }

        private void OnApplicationFocus(bool hasFocus)
        {
            if (!hasFocus)
            {
                return;
            }

            _ = LoadVrma(interactive: false);
        }

        private async Task LoadVrma(bool interactive)
        {
            UnityEngine.Debug.LogFormat("Loading Vrma interactive={0} ...", interactive);
            /*
            var vrmPath = Path.Combine(Application.streamingAssetsPath, "Example.vrm");
            Debug.LogFormat("VRM: {0}", vrmPath);
            _vrm10Instance = await Vrm10.LoadPathAsync(
                vrmPath,
                canLoadVrm0X: true,
                showMeshes: false
            );
            if (_vrm10Instance == null)
            {
                Debug.LogWarning("LoadPathAsync is null");
                return;
            }
            // vrm10Instance.Runtime.VrmAnimation
            var runtimeGltfInstance = _vrm10Instance.GetComponent<RuntimeGltfInstance>();
                // runtimeGltfInstance.ShowMeshes();
                runtimeGltfInstance.EnableUpdateWhenOffscreen();
            */

            _vrmaPath ??= ReadVrmaPath(interactive: interactive);
            if (_vrmaPath == null)
            {
                if (interactive)
                {
                    UnityEngine.Debug.LogError($"No path");
                }
                return;
            }

            var vrmaBytes = await File.ReadAllBytesAsync(_vrmaPath);
            if (_vrmaBytes != null)
            {
                if (vrmaBytes.SequenceEqual(_vrmaBytes))
                {
                    UnityEngine.Debug.LogFormat($"Not updated: {_vrmaPath}");
                    return;
                }
            }
            _vrmaBytes = vrmaBytes;

            _vrmaInstance?.Dispose();

            Debug.Log($"Loading Vrma from {_vrmaPath}");

            using GltfData data = new AutoGltfFileParser(_vrmaPath).Parse();
            using var loader = new VrmAnimationImporter(data);
            _vrmaInstance = await loader.LoadAsync(new ImmediateCaller());
            // var _a = _vrmaInstance.GetComponent<Vrm10AnimationInstance>();
            // _vrm10Instance.Runtime.VrmAnimation = a;
            _vrmaInstance.GetComponent<Animation>().Play();
        }

        /*
        private void Update()
        {
            var mouse = Mouse.current;
            if (mouse.leftButton.wasPressedThisFrame)
            {
                _vrmaPath = null;
                _vrmaBytes = null;
                _ = LoadVrma(interactive: true);
            }
        }
        */

#if UNITY_EDITOR
        private static string? ReadVrmaPath(bool interactive)
        {
            if (!interactive)
            {
                return null;
            }
            var path = UnityEditor.EditorUtility.OpenFilePanel(
                "Open VRMA", "", "vrma"
            );
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
            {
                return null;
            }
            return path;
        }
#else
        private static string? ReadVrmaPath()
        {
            var vrmaBasePath = Path.Combine(
                Application.streamingAssetsPath,
                "External",
                "VRMA_MotionPack",
                "vrma"
            );
            var vrmaPath = Path.Combine(vrmaBasePath, "VRMA_01.vrma");
            if (!File.Exists(vrmaPath))
            {
                Debug.LogWarning("Please setup vrma file. See README.txt for details.");
                return null;
            }
            return vrmaPath;
        }
#endif
    }
}
