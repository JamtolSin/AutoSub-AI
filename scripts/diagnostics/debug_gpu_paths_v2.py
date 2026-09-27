import importlib.util
from pathlib import Path

libs = [
    ("nvidia.cudnn", "bin"),
    ("nvidia.cublas", "bin")
]

for lib_name, sub_dir in libs:
    try:
        spec = importlib.util.find_spec(lib_name)
        if spec and spec.submodule_search_locations:
            lib_path = Path(spec.submodule_search_locations[0])
            dll_path = lib_path / sub_dir
            print(f"{lib_name} path: {lib_path}")
            print(f"{lib_name} bin exists: {dll_path.exists()}")
            if lib_name == "nvidia.cudnn":
                target_dll = dll_path / 'cudnn_ops64_9.dll'
                print(f"cudnn_ops64_9.dll exists: {target_dll.exists()}")
                print(f"Target Path: {target_dll}")
        else:
            print(f"Could not find spec for {lib_name}")
    except Exception as e:
        print(f"Error checking {lib_name}: {e}")
