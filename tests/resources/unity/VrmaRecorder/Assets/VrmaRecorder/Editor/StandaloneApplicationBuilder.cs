using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
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

        private static void BuildProject(BuildTarget buildTarget, string extension)
        {
            var buildTargetGroup = BuildPipeline.GetBuildTargetGroup(buildTarget);
            if (!BuildPipeline.IsBuildTargetSupported(buildTargetGroup, buildTarget))
            {
                Debug.LogFormat("*** [{0}] Build Skipped ***", buildTarget);
                return;
            }

            Debug.LogFormat("*** [{0}] Build Started ***", buildTarget);
            var report = BuildPipeline.BuildPlayer(
                new BuildPlayerOptions
                {
                    scenes = EditorBuildSettings
                        .scenes.Where(scene => scene.enabled)
                        .Select(scene => scene.path)
                        .ToArray(),
                    locationPathName = Path.Combine(
                        Application.dataPath,
                        "..",
                        "Build",
                        buildTarget.ToString(),
                        Application.productName + extension
                    ),
                    target = buildTarget,
                }
            );

            if (report.summary.result != BuildResult.Succeeded)
            {
                Debug.LogErrorFormat(
                    "*** [{0}] Build Failed ({1}) {2} ***",
                    buildTarget,
                    report.summary.result,
                    report.SummarizeErrors()
                );
                return;
            }

            Debug.LogFormat("*** [{0}] Build Completed ***", buildTarget);
        }
    }
}
