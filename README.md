# fah-gpu-species

Work in progress to understand GPU performance on benchmarking task with a view to creating a data-driven specification for GPU species.

GPU species is an 8-bit integer assigned to each distinct device known to F@H and is used to constrain which GPUs can run work for a given project. For example, a project might have the setting `NVIDIAGPUSpecies >= 3`, which means that work units will only be assigned to NVIDIA GPUs with a GPUSpecies of 3 or higher.

## Parsing log files

While it runs, the F@H core writes a file called `science.log` that contains, among other things, GPU device information and timing data useful for assessing the relative performance of GPUs. The script [`parse_science_log.py`](parse_science_log.py) can be used to extract useful information from these files. It can either be used as a library, deserializing to Python dataclasses for further analysis, or as a CLI tool, producing JSON.

### Usage example

```
$ python parse_science_log.py science.log
```

``` json
{
  "fah_core_header": {
    "core": "Core22",
    "type_": "0x22",
    "version": {
      "major": 0,
      "minor": 0,
      "patch": 11
    },
    "author": "Joseph Coffland <joseph@cauldrondevelopment.com>",
    "copyright_": "2020 foldingathome.org",
    "homepage": "https://foldingathome.org/",
    "date": 1593154800,
    "time": "19:49:16",
    "revision": "22010df8a4db48db1b35d33e666b64d8ce48689d",
    "branch": "core22-0.0.11",
    "compiler": "Visual C++ 2015",
    "options": "/TP /nologo /EHa /wd4297 /wd4103 /O2 /Ob3 /Zc:throwingNew /MT",
    "platform": "win32 10",
    "bits": "64",
    "mode": "Release",
    "maintainers": "John Chodera <john.chodera@choderalab.org> and Peter Eastman\n             <peastman@stanford.edu>",
    "args": [
      {
        "key": "dir",
        "val": "01"
      },
      {
        "key": "suffix",
        "val": "01"
      },
      {
        "key": "version",
        "val": "705"
      },
      {
        "key": "lifeline",
        "val": "5148"
      },
      {
        "key": "checkpoint",
        "val": "15"
      },
      {
        "key": "gpu-vendor",
        "val": "nvidia"
      },
      {
        "key": "opencl-platform",
        "val": "0"
      },
      {
        "key": "opencl-device",
        "val": "1"
      },
      {
        "key": "cuda-device",
        "val": "1"
      },
      {
        "key": "gpu",
        "val": "1"
      }
    ]
  },
  "fah_core_log": {
    "version": {
      "major": 0,
      "minor": 0,
      "patch": 11
    },
    "platforms": [
      {
        "info": {
          "profile": "FULL_PROFILE",
          "version": "OpenCL 1.2 CUDA 11.0.126",
          "name": "NVIDIA CUDA",
          "vendor": "NVIDIA Corporation"
        },
        "devices": [
          {
            "name": "P106-090",
            "vendor": "NVIDIA Corporation",
            "version": "OpenCL 1.2 CUDA"
          },
          {
            "name": "P106-090",
            "vendor": "NVIDIA Corporation",
            "version": "OpenCL 1.2 CUDA"
          },
          {
            "name": "P106-090",
            "vendor": "NVIDIA Corporation",
            "version": "OpenCL 1.2 CUDA"
          },
          {
            "name": "P106-090",
            "vendor": "NVIDIA Corporation",
            "version": "OpenCL 1.2 CUDA"
          }
        ]
      },
      {
        "info": {
          "profile": "FULL_PROFILE",
          "version": "OpenCL 2.0 AMD-APP (1800.11)",
          "name": "AMD Accelerated Parallel Processing",
          "vendor": "Advanced Micro Devices, Inc."
        },
        "devices": [
          {
            "name": "Intel(R) Core(TM) i7-3770 CPU @ 3.40GHz",
            "vendor": "GenuineIntel",
            "version": "OpenCL 1.2 AMD-APP (1800.11)"
          }
        ]
      },
      {
        "info": {
          "profile": "FULL_PROFILE",
          "version": "OpenCL 1.2 ",
          "name": "Intel(R) OpenCL",
          "vendor": "Intel(R) Corporation"
        },
        "devices": [
          {
            "name": "Intel(R) Core(TM) i7-3770 CPU @ 3.40GHz",
            "vendor": "Intel(R) Corporation",
            "version": "OpenCL 1.2 (Build 76427)"
          },
          {
            "name": "Intel(R) HD Graphics 4000",
            "vendor": "Intel(R) Corporation",
            "version": "OpenCL 1.2 "
          }
        ]
      }
    ],
    "checkpoint_perfs_ns_day": [
      38.96129152,
      38.96129152,
      38.86139077,
      38.96129152
    ],
    "average_perf_ns_day": 38.9613
  }
}
```
