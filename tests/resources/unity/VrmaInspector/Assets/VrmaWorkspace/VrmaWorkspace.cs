using System.IO;
using UniGLTF;
using UnityEngine;
using UniVRM10;

namespace VrmaWorkspace
{
    public class VrmaWorkspace : MonoBehaviour
    {
        private async void Start()
        {
            var basePath = Path.Combine(Application.streamingAssetsPath, "Temp");
            var vrmPath = Path.Combine(basePath, "input.vrm");
            var vrmaPath = Path.Combine(basePath, "input.vrma");
            var _vrmBytes = await File.ReadAllBytesAsync(vrmPath);
            using GltfData data = new AutoGltfFileParser(vrmaPath).Parse();
            using var loader = new VrmAnimationImporter(data);
            var instance = await loader.LoadAsync(new ImmediateCaller());
            var anim = instance.GetComponent<Vrm10AnimationInstance>();
            // var vrmAnimation = new VrmAnimation(instance.GetComponent<VrmAnimationInstance>());
        }
    }
}
