using System.IO;
using UniGLTF;
using UnityEngine;
using UniVRM10;

namespace VrmaWorkspace
{
    public class VrmaWorkspace : MonoBehaviour
    {
        private Vrm10Instance? _vrm10Instance;

        private async void Start()
        {
            var vrmaBasePath = Path.Combine(
                Application.streamingAssetsPath,
                "External",
                "VRMA_MotionPack",
                "vrma"
            );
            var vrmPath = Path.Combine(Application.streamingAssetsPath, "Example.vrm");
            var vrmaPath = Path.Combine(vrmaBasePath, "VRMA_01.vrma");
            var _vrmBytes = await File.ReadAllBytesAsync(vrmPath);

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

            using GltfData data = new AutoGltfFileParser(vrmaPath).Parse();
            using var loader = new VrmAnimationImporter(data);
            var instance = await loader.LoadAsync(new ImmediateCaller());
            var a = instance.GetComponent<Vrm10AnimationInstance>();
            // _vrm10Instance.Runtime.VrmAnimation = a;
            instance.GetComponent<Animation>().Play();
        }

        private void Update()
        {
            // _vrm10Instance?.Runtime.Process();
        }
    }
}
