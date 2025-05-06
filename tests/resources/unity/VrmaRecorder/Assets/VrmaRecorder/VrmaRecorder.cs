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
        private const int Resolution = 512;

        [SerializeField]
        private Camera? _forwardCamera;

        [SerializeField]
        private Camera? _topCamera;

        [SerializeField]
        private Camera? _rightCamera;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSplashScreen)]
        public static void BeforeSplashScreen()
        {
            Application.targetFrameRate = 6;
        }

#if UNITY_EDITOR
        private (
            string inputVrmPath,
            string inputVrmaPath,
            string outputFolderPath
        ) ReadEditorArgs()
        {
            var inputVrmPath = Path.Combine(Application.dataPath, "..", "debug_robot.vrm");
            var inputVrmaPath = UnityEditor.EditorUtility.OpenFilePanel(
                "Open VRMA",
                Application.dataPath,
                "vrma"
            );
            var outputFolderPath = Path.Combine(
                Application.dataPath,
                "..",
                "..",
                "..",
                "..",
                "temp"
            );
            return (inputVrmPath, inputVrmaPath, outputFolderPath);
        }
#endif

        private (
            string inputVrmPath,
            string inputVrmaPath,
            string outputFolderPath
        )? ReadStandaloneArgs()
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

            return (inputVrmPath, inputVrmaPath, outputFolderPath);
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
                await StartRecording(
                    args.inputVrmPath,
                    args.inputVrmaPath,
                    args.outputFolderPath,
                    _forwardCamera ?? throw new NullReferenceException(nameof(_forwardCamera)),
                    _topCamera ?? throw new NullReferenceException(nameof(_topCamera)),
                    _rightCamera ?? throw new NullReferenceException(nameof(_rightCamera))
                );
                Application.Quit(0);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Application.Quit(1);
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
            vrmaAnimation.Play(vrmaAnimation.clip.name);

            Directory.CreateDirectory(outputFolderPath);

            List<(byte[] forwardImage, byte[] topImage, byte[] rightImage)> images = new();
            for (var i = 0; i < Application.targetFrameRate * 5; i++)
            {
                await Awaitable.EndOfFrameAsync();
                images.Add(
                    (
                        CreatePngImage(forwardCamera),
                        CreatePngImage(topCamera),
                        CreatePngImage(rightCamera)
                    )
                );
            }

            foreach (var (image, i) in images.Select((image, i) => (image, i)))
            {
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_forward.png"),
                    image.forwardImage
                );
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_top.png"),
                    image.topImage
                );
                await File.WriteAllBytesAsync(
                    Path.Combine(outputFolderPath, $"{i:D2}_right.png"),
                    image.rightImage
                );
            }
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
