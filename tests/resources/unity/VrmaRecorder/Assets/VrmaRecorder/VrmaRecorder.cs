using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UniGLTF;
using UnityEngine;
using UniVRM10;

namespace VrmaRecorder
{
    public class VrmaRecorder : MonoBehaviour
    {
        private const int Resolution = 256;

        [SerializeField]
        private Camera? _forwardCamera;

        [SerializeField]
        private Camera? _topCamera;

        [SerializeField]
        private Camera? _rightCamera;

        [SerializeField]
        private Shader? _vrm10Mtoon10Shader;

        [SerializeField]
        private Shader? _vrm10UniversalRenderPipelineMtoon10Shader;

        [SerializeField]
        private Shader? _vrmMtoonShader;

        [SerializeField]
        private Shader? _uniGltfUniUnlitShader;

        // https://github.com/vrm-c/UniVRM/blob/v0.131.0/Packages/UniGLTF/Runtime/UniGLTF/IO/MaterialIO/URP/Import/Materials/UrpGltfDefaultMaterialImporter.cs#L22
        // https://github.com/vrm-c/UniVRM/blob/v0.131.0/Packages/UniGLTF/Runtime/UniGLTF/IO/MaterialIO/URP/Import/Materials/UrpGltfPbrMaterialImporter.cs#L23
        [SerializeField]
        private Shader? _universalRenderPipelineLitShader;

        // UniVRM 0.131.0とUnity6.3の組み合わせでBRPとの誤認が発生する
        // https://github.com/vrm-c/UniVRM/blob/v0.131.0/Packages/UniGLTF/Runtime/UniGLTF/IO/MaterialIO/Import/MaterialDescriptorGeneratorUtility.cs#L14-L16
        // https://github.com/vrm-c/UniVRM/blob/v0.131.0/Packages/UniGLTF/Runtime/UniGLTF/IO/MaterialIO/RenderPipelineUtility.cs#L21-L26
        // https://github.com/vrm-c/UniVRM/blob/v0.131.0/Packages/UniGLTF/Runtime/UniGLTF/IO/MaterialIO/BuiltInRP/Import/Materials/BuiltInGltfDefaultMaterialImporter.cs#L21
        [SerializeField]
        private Shader? _standardShader;

#if UNITY_EDITOR
        [UnityEditor.InitializeOnLoadMethod]
#endif
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSplashScreen)]
        public static void BeforeSplashScreen()
        {
            // fpsを固定
            Application.targetFrameRate = 60;
        }

#if UNITY_EDITOR
        private static List<(
            string inputVrmPath,
            string inputVrmaPath,
            string outputFolderPath
        )> ReadEditorArgs()
        {
            var defaultInputVrmPath = Path.Combine(Application.dataPath, "..", "debug_robot.vrm");
            var result = new List<(string, string, string)>();
            var resourceFolderPath = Path.Combine(Application.dataPath, "..", "..", "..");
            foreach (
                var baseFolderPath in new[]
                {
                    Path.Combine(resourceFolderPath, "vrma"),
                    Path.Combine(resourceFolderPath, "blend", "lossless_animation"),
                    Path.Combine(resourceFolderPath, "blend", "lossy_animation"),
                }
            )
            {
                foreach (var inputVrmaPath in Directory.GetFiles(baseFolderPath, "*.vrma"))
                {
                    var inputVrmPath = Path.Combine(
                        baseFolderPath,
                        Path.GetFileNameWithoutExtension(inputVrmaPath) + ".vrm"
                    );
                    if (!File.Exists(inputVrmPath))
                    {
                        inputVrmPath = defaultInputVrmPath;
                    }

                    result.Add(
                        (
                            inputVrmPath,
                            inputVrmaPath,
                            Path.Combine(
                                baseFolderPath,
                                Path.GetFileNameWithoutExtension(inputVrmaPath)
                            )
                        )
                    );
                }
            }

            result.Sort();
            return result;
        }
#endif

        private List<(
            string inputVrmPath,
            string inputVrmaPath,
            string outputFolderPath
        )>? ReadStandaloneArgs()
        {
            Debug.LogFormat(
                LogType.Log,
                LogOption.NoStacktrace,
                null,
                "***** VRM Animation Recorder {0} *****",
                Application.version
            );

            const string inputVrmPathCommandLinePrefix = "--vrma-recorder-input-vrm=";
            const string inputVrmaPathCommandLinePrefix = "--vrma-recorder-input-vrma=";
            const string outputFolderPathCommandLinePrefix = "--vrma-recorder-output-folder=";

            string? inputVrmPath = null;
            string? inputVrmaPath = null;
            string? outputFolderPath = null;

            Debug.LogFormat(
                LogType.Log,
                LogOption.NoStacktrace,
                null,
                "Usage: xvfb-run -a ./VrmaRecorder -batchmode -logfile -"
                    + $" {inputVrmPathCommandLinePrefix}<{nameof(inputVrmPath)}>"
                    + $" {inputVrmaPathCommandLinePrefix}<{nameof(inputVrmaPath)}>"
                    + $" {outputFolderPathCommandLinePrefix}<{nameof(outputFolderPath)}>"
            );

            foreach (var commandLineArg in Environment.GetCommandLineArgs())
            {
                if (commandLineArg.StartsWith(inputVrmPathCommandLinePrefix))
                {
                    inputVrmPath = commandLineArg.Substring(inputVrmPathCommandLinePrefix.Length);
                }

                if (commandLineArg.StartsWith(inputVrmaPathCommandLinePrefix))
                {
                    inputVrmaPath = commandLineArg.Substring(inputVrmaPathCommandLinePrefix.Length);
                }

                if (commandLineArg.StartsWith(outputFolderPathCommandLinePrefix))
                {
                    outputFolderPath = commandLineArg.Substring(
                        outputFolderPathCommandLinePrefix.Length
                    );
                }
            }

            Debug.LogFormat(
                LogType.Log,
                LogOption.NoStacktrace,
                null,
                "Current Options:"
                    + $" {nameof(inputVrmPath)}={inputVrmPath}"
                    + $" {nameof(inputVrmaPath)}={inputVrmaPath}"
                    + $" {nameof(outputFolderPath)}={outputFolderPath}"
            );

            if (inputVrmPath == null)
            {
                Debug.LogFormat(
                    LogType.Log,
                    LogOption.NoStacktrace,
                    null,
                    $"{nameof(inputVrmPath)} is null"
                );
                Application.Quit();
                return null;
            }

            if (inputVrmaPath == null)
            {
                Debug.LogFormat(
                    LogType.Log,
                    LogOption.NoStacktrace,
                    null,
                    $"{nameof(inputVrmaPath)} is null"
                );
                Application.Quit();
                return null;
            }

            if (outputFolderPath == null)
            {
                Debug.LogFormat(
                    LogType.Log,
                    LogOption.NoStacktrace,
                    null,
                    $"{nameof(outputFolderPath)} is null"
                );
                Application.Quit();
                return null;
            }

            return new List<(string inputVrmPath, string inputVrmaPath, string outputFolderPath)>
            {
                (inputVrmPath, inputVrmaPath, outputFolderPath),
            };
        }

        public void Start()
        {
            _ = StartRecording();
        }

        private async Task StartRecording()
        {
            try
            {
#if UNITY_EDITOR
                var args = ReadEditorArgs();
#elif UNITY_STANDALONE
                if (ReadStandaloneArgs() is not { } args)
                {
                    return;
                }
#endif
                foreach (var arg in args)
                {
                    await StartRecording(
                        arg.inputVrmPath,
                        arg.inputVrmaPath,
                        arg.outputFolderPath,
                        _forwardCamera ?? throw new NullReferenceException(nameof(_forwardCamera)),
                        _topCamera ?? throw new NullReferenceException(nameof(_topCamera)),
                        _rightCamera ?? throw new NullReferenceException(nameof(_rightCamera))
                    );
                }

                Application.Quit(0);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Application.Quit(1);
            }
            finally
            {
#if UNITY_EDITOR
                UnityEditor.EditorApplication.isPlaying = false;
#endif
            }
        }

        private async Task StartRecording(
            string inputVrmPath,
            string inputVrmaPath,
            string outputFolderPath,
            Camera forwardCamera,
            Camera topCamera,
            Camera rightCamera
        )
        {
            Debug.LogFormat("StartRecording: {0} {1}",
#if UNITY_EDITOR
                Path.GetRelativePath(Application.dataPath, inputVrmPath),
                Path.GetRelativePath(Application.dataPath, inputVrmaPath)
#else
                inputVrmPath, inputVrmaPath
#endif
            );

            // SpringBoneはデフォルトではTime.deltaTimeを使って動く。
            // VRMのロードはとても重く1フレームの周期に収まらないこともあるため
            // そのままだとSpringBoneの最初のフレームの動きが非決定的になる。
            // これを防ぐため、VRMのロードは時間を止めて行う。
            Time.timeScale = 0;
            await Awaitable.NextFrameAsync();

            // この時点で、Time.deltaTimeはゼロになっているはず
            if (Mathf.Abs(Time.deltaTime) > 0)
            {
                throw new Exception($"Mathf.Abs(Time.deltaTime={Time.deltaTime} > 0)");
            }

            var lookAtTarget = new GameObject("LookAtTarget");

            // VRMとVRMAのロード
            var vrmInstance = await Vrm10.LoadPathAsync(
                inputVrmPath,
                canLoadVrm0X: true,
                showMeshes: true
            );
            // vrmInstance.LookAtTarget = lookAtTarget.transform;
            // vrmInstance.LookAtTargetType = VRM10ObjectLookAt.LookAtTargetTypes.SpecifiedTransform;

            RuntimeGltfInstance vrmaGltfInstance;
            using (var gltf = new AutoGltfFileParser(inputVrmaPath).Parse())
            {
                var vrmaData = new VrmAnimationData(gltf);
                using var vrmaImporter = new VrmAnimationImporter(vrmaData);
                vrmaGltfInstance = await vrmaImporter.LoadAsync(new ImmediateCaller());
            }

            foreach (var visibleRenderer in vrmaGltfInstance.VisibleRenderers)
            {
                visibleRenderer.enabled = false;
            }

            vrmInstance.Runtime.VrmAnimation =
                vrmaGltfInstance.GetComponent<Vrm10AnimationInstance>();
            var vrmaAnimation = vrmaGltfInstance.GetComponent<Animation>();
            var clip = vrmaAnimation.clip;
            clip.wrapMode = WrapMode.Once;
            vrmaAnimation.Play(clip.name);
            Directory.CreateDirectory(outputFolderPath);

            var workingTexture = new Texture2D(Resolution, Resolution, TextureFormat.RGB24, false);
            var workingRenderTexture = RenderTexture.GetTemporary(
                Resolution,
                Resolution,
                24,
                RenderTextureFormat.ARGB32
            );

            await Awaitable.NextFrameAsync();
            // ここから先の処理は、1フレームの周期に収まるようにする

            // この時点で、Time.deltaTimeはゼロ
            if (Mathf.Abs(Time.deltaTime) > 0)
            {
                throw new Exception($"Mathf.Abs(Time.deltaTime={Time.deltaTime} > 0)");
            }

            // 次のフレームから時間が進み、Time.deltaTimeが設定されるようになる。
            Time.timeScale = 1;
            var startTime = Time.time;

            List<(Color32[] forwardImage, Color32[] topImage, Color32[] rightImage)> images = new();
            while (true)
            {
                var duration = Time.time - startTime;
                var done = duration >= Mathf.Min(clip.length, 60);
                if (duration >= images.Count || done)
                {
                    images.Add(
                        (
                            CreateImage(forwardCamera, workingRenderTexture, workingTexture),
                            CreateImage(topCamera, workingRenderTexture, workingTexture),
                            CreateImage(rightCamera, workingRenderTexture, workingTexture)
                        )
                    );
                }

                if (done)
                {
                    break;
                }

                await Awaitable.NextFrameAsync();
            }

            foreach (var path in Directory.GetFiles(outputFolderPath, "*_unity.png"))
            {
                File.Delete(path);
            }

            foreach (var (image, i) in images.Select((image, i) => (image, i)))
            {
                workingTexture.SetPixels32(image.forwardImage);
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_forward_unity.png"),
                    workingTexture.EncodeToPNG()
                );
                workingTexture.SetPixels32(image.topImage);
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_top_unity.png"),
                    workingTexture.EncodeToPNG()
                );
                workingTexture.SetPixels32(image.rightImage);
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_right_unity.png"),
                    workingTexture.EncodeToPNG()
                );
            }

            RenderTexture.ReleaseTemporary(workingRenderTexture);
            Destroy(workingTexture);

            // これらだけだとリソースリークする。そのうち修正。
            Destroy(vrmInstance.gameObject);
            Destroy(vrmaGltfInstance.gameObject);
            Destroy(lookAtTarget);

            await Awaitable.NextFrameAsync(); // Destroy処理待ち
            await Resources.UnloadUnusedAssets();
            GC.Collect();
        }

        private Color32[] CreateImage(
            Camera renderCamera,
            RenderTexture workingRenderTexture,
            Texture2D workingTexture
        )
        {
            var cameraTargetTexture = renderCamera.targetTexture;
            try
            {
                renderCamera.targetTexture = workingRenderTexture;
                renderCamera.Render();
            }
            finally
            {
                renderCamera.targetTexture = cameraTargetTexture;
            }

            var activeRenderTexture = RenderTexture.active;
            try
            {
                RenderTexture.active = workingRenderTexture;
                workingTexture.ReadPixels(new Rect(0, 0, Resolution, Resolution), 0, 0);
                workingTexture.Apply();
            }
            finally
            {
                RenderTexture.active = activeRenderTexture;
            }

            return workingTexture.GetPixels32();
        }
    }
}
