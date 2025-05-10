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

#if UNITY_EDITOR
        [UnityEditor.InitializeOnLoadMethod]
#endif
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSplashScreen)]
        public static void BeforeSplashScreen()
        {
            // fpsを固定
            // targetFrameRateの固定は今のところおまじない。
            // fixedDeltaTimeだけ固定すればよい気もする。
            Application.targetFrameRate = 60;
            Time.fixedDeltaTime = 1f / Application.targetFrameRate;

            // fixedDeltaTime以内に処理が終わらない場合どうなるかわからないため
            // 時間の進みを遅くする。
            Time.captureFramerate = Application.targetFrameRate * 4;
        }

#if UNITY_EDITOR
        private List<(
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

            const string inputVrmPathCommandLinePrefix = "--vrm-recorder-input-vrm=";
            const string inputVrmaPathCommandLinePrefix = "--vrma-recorder-input-vrm=";
            const string outputFolderPathCommandLinePrefix = "--vrma-recorder-output-folder=";

            string? inputVrmPath = null;
            string? inputVrmaPath = null;
            string? outputFolderPath = null;

            Debug.LogFormat(
                LogType.Log,
                LogOption.NoStacktrace,
                null,
                "Usage: ./VrmaRecorder"
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
            var vrmInstance = await Vrm10.LoadPathAsync(
                inputVrmPath,
                canLoadVrm0X: true,
                showMeshes: true
            );

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
            await Awaitable.NextFrameAsync();

            Directory.CreateDirectory(outputFolderPath);

            List<(byte[] forwardImage, byte[] topImage, byte[] rightImage)> images = new();
            // for (var i = 0; i < Application.targetFrameRate * 5; i++)
            //{
            images.Add(
                (
                    CreatePngImage(forwardCamera),
                    CreatePngImage(topCamera),
                    CreatePngImage(rightCamera)
                )
            );
            /*
            await Awaitable.FixedUpdateAsync();
            if (i % (Application.targetFrameRate / 2) != 0)
            {
                continue;
            }
            */
            // しばらくは最初のフレームだけ録画
            //break;
            //}

            foreach (var (image, i) in images.Select((image, i) => (image, i)))
            {
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_forward_unity.png"),
                    image.forwardImage
                );
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_top_unity.png"),
                    image.topImage
                );
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_right_unity.png"),
                    image.rightImage
                );
            }

            // これらだけだとリソースリークする。そのうち修正。
            Destroy(vrmInstance.gameObject);
            Destroy(vrmaGltfInstance.gameObject);

            await Awaitable.NextFrameAsync(); // Destroy処理待ち
        }

        private byte[] CreatePngImage(Camera renderCamera)
        {
            var cameraTargetTexture = renderCamera.targetTexture;
            var renderTexture = RenderTexture.GetTemporary(
                Resolution,
                Resolution,
                24,
                RenderTextureFormat.ARGB32
            );
            try
            {
                renderCamera.targetTexture = renderTexture;
                renderCamera.Render();
            }
            finally
            {
                renderCamera.targetTexture = cameraTargetTexture;
            }

            Texture2D? texture = null;
            var activeRenderTexture = RenderTexture.active;
            try
            {
                RenderTexture.active = renderTexture;
                texture = new Texture2D(Resolution, Resolution, TextureFormat.RGB24, false);
                texture.ReadPixels(new Rect(0, 0, Resolution, Resolution), 0, 0);
                texture.Apply();
            }
            catch (Exception)
            {
                if (texture != null)
                {
                    Destroy(texture);
                }
                throw;
            }
            finally
            {
                RenderTexture.active = activeRenderTexture;
                RenderTexture.ReleaseTemporary(renderTexture);
            }

            try
            {
                return texture.EncodeToPNG();
            }
            finally
            {
                Destroy(texture);
            }
        }
    }
}
