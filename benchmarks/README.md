# io-scene-vrm-benchmarks

Benchmarks for VRM format / VRM Add-on for Blender. Real-time results can be
viewed on [CodSpeed](https://codspeed.io/saturday06/VRM-Addon-for-Blender).

## Usage

### Command to run all benchmarks

```sh
uv run pytest
```

### Command to run individual benchmarks and get detailed profiling information

```sh
uv run pytest --benchmark-cprofile=cumtime src/io_scene_vrm_benchmarks/spring_bone_benchmark_test.py
```
