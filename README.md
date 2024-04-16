# GPT4Motion: Scripting Physical Motions in Text-to-Video Generation via Blender-Oriented GPT Planning

<video src="./assets/videos/Comparison_A basketball free falls in the air.mp4"
loop="" autoplay="" controls="" width="70%">
  Comparison of the video results generated by different text-to-video models with the prompt \textit{``A basketball free falls in the air"}. 
</video>

*We introduce GPT4Motion, a training-free framework that leverages the planning capability of large language models such as GPT, the physical simulation strength of Blender, and the excellent image generation ability of text-to-image diffusion models to enhance the quality of video synthesis.*



[****Paper****](**https://arxiv.org/abs/2311.12631**) | [****Project Website****](**https://gpt4motion.github.io/**) 


Jiaxi Lv\*, Yi Huang\*, Mingfu Yan\*, Jiancheng Huang, Jianzhuang Liu Yifan Liu, Yafei Wen, Xiaoxin Chen, Shifeng Chen

Shenzhen Institute of Advanced Technology, Chinese Academy of Sciences,  University of Chinese Academy of Sciences, VIVO AI Lab



## News!!!

* 2024-04-16  We released the code for GPT4Motion. 

* 2024-04-09  GPT4Motion was accepted by the CVPR 2024 PBDL workshop! 

* 2023-11-28  GPT4Motion was covered by [Synced]([GPT-4+物理引擎加持扩散模型，生成视频逼真、连贯、合理 | 机器之心 (jiqizhixin.com)](https://www.jiqizhixin.com/articles/2023-11-28-2)).

* 2023-11-22  GPT4Motion was recommended by [AK](https://twitter.com/_akhaliq/status/1727172666455413187) and included in [Hugging Face's daily papers]([Paper page - GPT4Motion: Scripting Physical Motions in Text-to-Video Generation via Blender-Oriented GPT Planning (huggingface.co)](https://huggingface.co/papers/2311.12631)). 

* 2023-11-21  The GPT4Motion paper was uploaded to [arXiv]([[2311.12631\] GPT4Motion: Scripting Physical Motions in Text-to-Video Generation via Blender-Oriented GPT Planning (arxiv.org)](https://arxiv.org/abs/2311.12631)).

## Overview

![image](./assets/imgs/framework.jpg)

First, the user prompt is inserted into our designed prompt template. Then, the Python script generated by GPT-4 drives the Blender physics engine to simulate the corresponding motion, producing sequences of edge maps and depth maps. Finally, two ControlNets are employed to constrain the physical motion of video frames generated by Stable Diffusion, where a temporal consistency constraint is designed to enforce the coherence among frames.


## Performance

### Comparisons with Baselines

<video src="./assets/videos/Comparison_A white flag flaps in the wind.mp4"
loop="" autoplay="" controls="" width="70%">
  Comparison of the video results generated by different text-to-video models with the prompt \textit{``A white flag flaps in the wind"}. 
</video>

Comparison of the video results generated by different text-to-video models with the prompt *"A white flag flaps in the wind"*.

<video src="./assets/videos/Comparison_Water flows into a white mug on a table, top-down view.mp4"
loop="" autoplay="" controls="" width="70%">
  Comparison of the video results generated by different text-to-video models with the prompt \textit{``Water flows into a white mug on a table, top-down view"}. 
</video>

Comparison of the video results generated by different text-to-video models with the prompt *"Water flows into a white mug on a table, top-down view*.



### Controlling Physical Properties

<video src="./assets/videos/GPT4Motion_Basketball drop and collision.mp4"
loop="" autoplay="" controls="" width="70%">
</video>

GPT4Motion's results on basketball drop and collision. 



<video src="./assets/videos/GPT4Motion_A white flag flags in light or the or strong wind.mp4"
loop="" autoplay="" controls="" width="70%">
</video>

GPT4Motion's results on "A white flag flags in light or the or strong wind".

<video src="./assets/videos/GPT4Motion_A white T-shirt flutters in light or the or strong wind.mp4"
loop="" autoplay="" controls="" width="70%">
</video>

GPT4Motion's results on "A white T-shirt flutters in light or the or strong wind".

<video src="./assets/videos/GPT4Motion_Water or Viscous or Very viscous flows into a white mug on a table, top-down view.mp4"
loop="" autoplay="" controls="" width="70%">
</video>

GPT4Motion's results on "Water or Viscous or Very viscous flows into a white mug on a table, top-down view".



## Directory of our code

For ease of reading, we list our directory structure.

```
├── data
│   └── basketball
│       └── A basketball free falls in the air
│           ├── depth
│           │   ├── depth_0000.png
│           │   └── ... (more depth images)
│           └── freestyle
│               ├── canny_0000.png
│               └── ... (more canny images)
├── PhysicsGeneration
│   ├── BlenderTool
│   │   ├── assets
│   │   │   └── basketball.obj
│   │   ├── __init__.py
│   │   └── utils.py
│   ├── prompt_for_GPT4.txt
│   └── script.py
├── README.MD
└── VideoGeneration
    ├── config
    │   └── basketball.yaml
    ├── main.py
    ├── requirements.txt
    └── utils
        ├── Cross_Frame_Attention.py
        ├── __init__.py
        └── utils_all.py
```
- `data`: This directory stores the data used in the project.
  - `basketball`: A subdirectory specifically for basketball-related data.
    - `A basketball free falls in the air`: Contains data for a scenario where a basketball is free-falling.
      - `depth`: Contains depth images.
      - `freestyle`: Contains canny images.
- `PhysicsGeneration`: This directory contains the complete prompt for GPT-4 and the code to obtain depth maps and edge maps rendered through Blender.
- `VideoGeneration`: This directory contains the code for generating a video using depth maps and edge maps generated by Blender.

## Reproducing Our Work

### Generation of Motion Edge Maps and Depth Maps with GPT-4 and Blender

Please install **Blender 3.6** according to https://www.blender.org/download/. 

```shell
cd PhysicsGeneration
```
Please copy the prompt from "prompt_for_GPT4.txt" to GPT-4 and add the following prefix to the Python code generated by GPT-4:
```Python
import bpy
import os
import math
import random
from random import uniform
import mathutils

from sys import path
path.append(bpy.path.abspath("./"))
from BlenderTool.utils import *

ASSETS_PATH = 'BlenderTool/assets/'
```
You will get a Python file like "script.py", please use the following commands to generate the edge and depth maps:
```shell
blender -b -P script.py
```
The generated edge maps and depth maps are saved are saved in "../data/new/" folder.

### Video Generation

Please move to the "VideoGeneration" folder and install the corresponding environment:

```shell
cd ../VideoGeneration/
conda create -n GPT4Motion python=3.9
conda activate GPT4Motion
pip install -r requirements.txt
```

You can generate videos based on our pre-existing depth and edge maps by following the instructions below:

```shell
python main.py config/basketball.yaml
```
The generated results are shown below:

<video src="./assets/videos/GPT4Motion_A basketball free falls in the air.mp4"
loop="" autoplay="" controls="" width="70%" >
  Comparison_A basketball free falls in the air.mp4
</video>