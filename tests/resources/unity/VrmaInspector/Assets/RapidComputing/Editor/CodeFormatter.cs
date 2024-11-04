// SPDX-License-Identifier: MIT OR GPL-3.0-or-later
using System.Diagnostics;
using UnityEditor;

namespace RapidComputing
{
    public class CodeFormatter : AssetPostprocessor
    {
        void OnPreprocessAsset()
        {
            if (!assetPath.StartsWith("Assets/") || !assetPath.EndsWith(".cs"))
            {
                return;
            }

            using var process = Process.Start(
                new ProcessStartInfo
                {
                    FileName = "dotnet",
                    ArgumentList = { "csharpier", assetPath },
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                }
            );
        }
    }
}
