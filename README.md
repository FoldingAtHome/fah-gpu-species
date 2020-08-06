# fah-gpu-analysis

Analysis to understand GPU performance on Folding@home benchmarking tasks. The eventual goal is to create a data-driven automatic assignment of GPU species.

GPU species is an 8-bit unsigned integer (range 0 to 255) assigned to each distinct device known to F@H. It is used to constrain which GPUs can run work for a given project. For example, a project might have the setting `NVIDIAGPUSpecies >= 3`, which means that work units will only be assigned to NVIDIA GPUs with a GPUSpecies of 3 or higher.

See [notebooks](notebooks) for example analyses.

## Installation

```shell
$ python setup.py install
```

## Parsing log files

While it runs, the F@H core writes a log file called `science.log` that contains, among other things, GPU device information and timing data useful for assessing the relative performance of GPUs. The script [`parse_science_log.py`](parse_science_log.py) can be used to extract useful information from these files. It can either be used as a library, deserializing to Python dataclasses for further analysis, or as a CLI tool, producing JSON.

### Usage example

``` shell
$ python parse_science_log.py /path/to/science.log | jq '.fah_core_log'
```

``` json
{
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
```

## Notebooks

To install requirements:

```shell
cd notebooks/
pip install -r requirements.txt
```

