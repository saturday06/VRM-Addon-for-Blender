using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace VrmaRecorder.Editor
{
    public static class StandaloneApplicationBuilder
    {
        [MenuItem("Tools/VrmaRecorder/Build")]
        public static void Build()
        {
            BuildProject(BuildTarget.StandaloneWindows64, ".exe");
            BuildProject(BuildTarget.StandaloneOSX, ".app");
            BuildProject(BuildTarget.StandaloneLinux64, "");
        }

        private static void BuildProject(BuildTarget target, string extension)
        {
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = EditorBuildSettings
                    .scenes
                    .Where(scene => scene.enabled)
                    .Select(scene => scene.path)
                    .ToArray(),
                locationPathName = Path.Combine(
                    Application.dataPath,
                    "..",
                    "Build",
                    target.ToString(),
                    Application.productName + extension
                ),
                target = target,
            });

            if (report.summary.result != BuildResult.Succeeded)
            {
                throw new Exception($"{target}:{report}");
            }
        }
    }
}
