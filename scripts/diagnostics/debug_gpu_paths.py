import nvidia.cudnn
import nvidia.cublas
import os
from pathlib import Path

print(f"nvidia.cudnn file: {nvidia.cudnn.__file__}")
print(f"nvidia.cublas file: {nvidia.cublas.__file__}")

try:
    cudnn_dir = Path(nvidia.cudnn.__file__).parent
    print(f"cudnn dir: {cudnn_dir}")
    if (cudnn_dir / 'bin').exists():
        dll_path = cudnn_dir / 'bin' / 'cudnn_ops64_9.dll'
        print(f"cudnn_ops64_9.dll exists: {dll_path.exists()}")
        print(f"Path: {dll_path}")

except Exception as e:
    print(f"Error checking cudnn: {e}")

try:
    cublas_dir = Path(nvidia.cublas.__file__).parent
    print(f"cublas dir: {cublas_dir}")
    print(f"cublas bin exists: {(cublas_dir / 'bin').exists()}")
except Exception as e:
    print(f"Error checking cublas: {e}")
