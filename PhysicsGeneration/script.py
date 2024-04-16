import bpy
import os
import math
import random
from random import uniform
import mathutils

from sys import path
path.append(bpy.path.abspath("./"))
from BlenderTool.utils import *

# --------------------------------Script-------------------------------------------


import math

# Predefined asset path
# ASSETS_PATH = "path_to_assets_directory"

# Step 1: Clear the Scene
clear_scene()

# Step 2: Create the Floor
create_floor(elasticity=1.0) # A bit of bounce for realism

# Step 3: Import the Basketball Model
basketball_path = ASSETS_PATH + "basketball.obj"
basketball = create_object_in_assets(file_path=basketball_path, new_name="Basketball", position=(0, 0, 4.8), max_dimension=0.24*5) # Standard basketball size is about 24cm in diameter, and here it is scaled up to improve visibility

# Step 4: Setting Up the Basketball
add_collision(basketball)
add_rigid_body(basketball, mass=0.62*5, elasticity=0.825) # Standard basketball mass is about 0.62kg, and here it is scaled up to enhance physical interaction

# Step 5: Create a Camera
create_camera()

# Step 6: Render the Video
Render_a_video()
