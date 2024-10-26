#!/bin/sh

set -eux
shellcheck "$0"

export PYTHONDONTWRITEBYTECODE=1
prefix_name=VRM_Addon_for_Blender

if ! git status; then
  uname -a
  id
  ls -alR
  exit 1
fi

underscore_version=$(ruby -e "puts ARGV[0].sub(/^v/, '').split('.', 3).join('_')" "$RELEASE_TAG_NAME")
version=$(ruby -e "puts ARGV[0].split('_', 3).join('.')" "$underscore_version")
bl_info_version=$(cd src && python3 -c 'import io_scene_vrm; print(str(".".join(map(str, io_scene_vrm.bl_info["version"]))))')
release_postfix=debug

for postfix in "$release_postfix" "$underscore_version"; do
  work_dir=$(mktemp -d)
  base="${prefix_name}-${postfix}"
  cp -r src/io_scene_vrm "${work_dir}/${base}"
  cp -r LICENSE* "${work_dir}/${base}/"
  (
    cd "$work_dir"
    advzip --add --shrink-insane --iter 20 "${prefix_name}-${postfix}.zip" "${base}"
  )
  cp "${work_dir}/${prefix_name}-${postfix}.zip" .
done

mkdir -p ~/.local/blender
if ! tar xf blender.tar.xz -C ~/.local/blender --strip-components=1; then
  echo "Please upgrade archive URL"
  exit 1
fi
export PATH="$HOME/.local/blender:$PATH"
hash -r
test "$HOME/.local/blender/blender" = "$(command -v blender)"
./tools/build_extension.sh
extension_path=$(find extension_output -name "vrm_*_*.zip" | sort | head -n 1)
if [ ! -f "$extension_path" ]; then
  echo "No extension output"
  exit 1
fi
rm -fr ~/.local/blender
hash -r
test "/usr/bin/blender" = "$(command -v blender)"

gh release upload "$RELEASE_TAG_NAME" \
  "${extension_path}#(Blender 4.2 or later) VRM Add-on for Blender Extension ${version} (zip)" \
  "${prefix_name}-${underscore_version}.zip#(Blender 2.93 - 4.1) VRM Add-on for Blender ${version} (zip)"

readme_unzip_dir=$(mktemp -d)
unzip -d "$readme_unzip_dir" "${prefix_name}-${release_postfix}.zip"
readme_base="${readme_unzip_dir}/${prefix_name}-${release_postfix}"
rm "$readme_base/__init__.py"
readme_tar_xz_version=$(ruby -e "puts ARGV[0].split('.', 3).join('_')" "$bl_info_version")
readme_tar_xz_abs_path="${PWD}/${readme_tar_xz_version}.tar.xz"
XZ_OPT='-9e' tar -C "$readme_base" -cvJf "$readme_tar_xz_abs_path" .

archive_branch_dir=$(mktemp -d)
git worktree add "${archive_branch_dir}" release-archive
rm -fr "${archive_branch_dir}/debug"
mkdir -p "${archive_branch_dir}/debug"
cp "${prefix_name}-${release_postfix}.zip" "${archive_branch_dir}/"
if [ "$release_postfix" != "release" ]; then
  cp "$readme_tar_xz_abs_path" "${archive_branch_dir}/debug/"
fi
(
  cd "${archive_branch_dir}"
  git add .
  git config --global user.email "isamu@leafytree.jp"
  git config --global user.name "[BOT] Isamu Mogi"
  git commit -m "docs: release $version [BOT]"
)

readme_branch_dir=$(mktemp -d)
git worktree add "${readme_branch_dir}" README
readme_addon_dir="${readme_branch_dir}/.github/vrm_addon_for_blender_private"
find "$readme_addon_dir" -name "*.zip" -exec rm -v {} \;
find "$readme_addon_dir" -name "*.tar.xz" -exec rm -v {} \;
cp "${readme_tar_xz_abs_path}" "${readme_addon_dir}/"
cp src/io_scene_vrm/__init__.py "$readme_branch_dir/"
github_downloaded_zip_path="${PWD}/readme.zip"
(
  cd "$readme_branch_dir"
  git add .
  git config --global user.email "isamu@leafytree.jp"
  git config --global user.name "[BOT] Isamu Mogi"
  git commit -m "docs: update the latest internal partial code to $GITHUB_SHA [BOT]"
  git archive HEAD --prefix=${prefix_name}-README/ --output="$github_downloaded_zip_path"
)

gh_pages_branch_dir=$(mktemp -d)
git worktree add "${gh_pages_branch_dir}" gh-pages
mkdir -p "${gh_pages_branch_dir}/releases"
cp "${prefix_name}-${release_postfix}.zip" "${gh_pages_branch_dir}/releases/"
(
  cd "$gh_pages_branch_dir"
  git add .
  git config --global user.email "isamu@leafytree.jp"
  git config --global user.name "[BOT] Isamu Mogi"
  git commit -m "docs: deploy the latest release [BOT]"
)

addon_dir="$HOME/.config/blender/4.0/scripts/addons/${prefix_name}-README"
if ! BLENDER_VRM_USE_TEST_EXPORTER_VERSION=true blender \
  --background \
  -noaudio \
  --python-exit-code 1 \
  --python tools/github_code_archive.py -- "$github_downloaded_zip_path" \
  ; then
  find "$addon_dir"
  exit 1
fi

installed_readme_tar_xz_path="${addon_dir}/.github/vrm_addon_for_blender_private/${readme_tar_xz_version}.tar.xz"
if [ -e "$installed_readme_tar_xz_path" ]; then
  echo Failed to remove "$installed_readme_tar_xz_path"
  exit 1
fi

rm -fr "$addon_dir/.github"
rm "$addon_dir/README.md"
find "$addon_dir" -name "__pycache__" -type d -print0 | xargs --null rm -fr

addon_check_unzip_dir=$(mktemp -d)
unzip -d "$addon_check_unzip_dir" "${prefix_name}-${release_postfix}.zip"

diff -ru "$addon_check_unzip_dir/${prefix_name}-${release_postfix}" "$addon_dir"

(
  cd "${archive_branch_dir}"
  git push origin HEAD
)

if [ "$release_postfix" = "release" ]; then
  (
    cd "$readme_branch_dir"
    git push origin HEAD
  )
  (
    cd "$gh_pages_branch_dir"
    git push origin HEAD
  )
fi

gh release edit "$RELEASE_TAG_NAME" --draft=false --latest --prerelease
