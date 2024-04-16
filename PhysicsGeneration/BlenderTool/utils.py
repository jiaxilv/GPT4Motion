import bpy
import os
import math
import random
from random import uniform
import mathutils

ASSETS_PATH = 'BlenderTool/assets/'

#-------------------------------- 1.Utils Functions, Dont need to be adjusted--------------------------------------------
def set_origin_to_geometry(obj):
    """
    Set the origin of an object to its geometric center.

    :param obj_name: The name of the object to set the origin for.
    """
    # Select the object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # Set the origin to the geometric center of the object
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    # Deselect the object
    obj.select_set(False)

# Rendering and Scene Functions
def set_render_settings(start_frame, end_frame, output_path):
    bpy.context.scene.frame_start = start_frame
    bpy.context.scene.frame_end = end_frame
    bpy.context.scene.render.filepath = output_path
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.use_freestyle = True
    bpy.context.scene.render.line_thickness_mode = 'ABSOLUTE'
    bpy.context.scene.render.line_thickness = 0.75
    bpy.context.view_layer.freestyle_settings.as_render_pass = True
    view_layer = bpy.context.scene.view_layers["ViewLayer"]
    view_layer.use_pass_z = True
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    
def bake_physics():
    """
    Bakes the physics simulation for the current scene's frame range.
    """
    # Ensure we're in object mode
    # bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear any existing baked frames
    bpy.ops.ptcache.free_bake_all()

    # Bake the physics; it automatically uses the scene's frame range
    bpy.ops.ptcache.bake_all(bake=True)


def bake_fluid_sim():
    """
    Configures and bakes a fluid simulation for the domain object named 'Liquid Domain' in Blender.

    The function sets the domain object's viscosity, resolution, mesh generation settings, and bake frame range
    before executing the bake operation.

    Returns:
    - None, but triggers the fluid simulation baking process within Blender.
    """
    # Find the domain object
    domain = bpy.data.objects.get('Liquid Domain')
    # Make sure the domain object is the active object
    bpy.context.view_layer.objects.active = domain
    
    # Exit the function if there is no domain object found
    if not domain:
        print("No domain object named 'Liquid Domain' found.")
        return

    # Set domain resolution and enable mesh generation for the fluid
    domain.modifiers["Fluid"].domain_settings.resolution_max = 48 
    domain.modifiers["Fluid"].domain_settings.use_mesh = True

    # Set the frame range for the fluid simulation bake
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    domain.modifiers["Fluid"].domain_settings.cache_frame_start = start
    domain.modifiers["Fluid"].domain_settings.cache_frame_end = end

    # Bake the fluid simulation
    bpy.ops.fluid.bake_all()

def render_animation():
    
    domain = bpy.data.objects.get('Liquid Domain')
    # Make sure the domain object is the active object
    bpy.context.view_layer.objects.active = domain
    
    # Exit the function if there is no domain object found
    if not domain:
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = 100
    else:
        bpy.context.scene.frame_start = 40
        bpy.context.scene.frame_end = 120
    
    for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
        bpy.context.scene.frame_set(frame)
        bpy.ops.render.render(write_still=True)
        
def setup_compositor(output_path):
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    nodes = tree.nodes
    links = tree.links

    for node in nodes:
        nodes.remove(node)

    render_layers_node = nodes.new(type='CompositorNodeRLayers')
    depth_file_output_node = create_file_output_node(nodes, "Depth", output_path, "depth_")
    normalize_node = create_normalize_node(nodes)

    links.new(render_layers_node.outputs['Depth'], normalize_node.inputs[0])
    links.new(normalize_node.outputs[0], depth_file_output_node.inputs[0])

    canny_file_output_node = create_file_output_node(nodes, "Freestyle", output_path, "canny_")
    links.new(render_layers_node.outputs['Freestyle'], canny_file_output_node.inputs[0])
    
def create_file_output_node(nodes, label, base_path, file_slot_path):
    file_output_node = nodes.new(type='CompositorNodeOutputFile')
    file_output_node.base_path = os.path.join(base_path, label.lower())
    file_output_node.file_slots[0].path = file_slot_path
    os.makedirs(file_output_node.base_path, exist_ok=True)
    return file_output_node

def create_normalize_node(nodes):
    normalize_node = nodes.new('CompositorNodeNormalize')
    normalize_node.name = 'Normalize'
    return normalize_node

def rerender_for_mask(file_output_path):
    file_output_path = os.path.join(file_output_path, "mask")
    os.makedirs(file_output_path, exist_ok=True)
    bpy.context.scene.display.render_aa = 'OFF'
    bpy.context.scene.display.shading.light = 'FLAT'
    bpy.context.scene.display.shading.color_type = 'SINGLE'
    bpy.context.scene.display.shading.single_color = (1, 1, 1)

    # Deselect Freestyle
    bpy.context.scene.render.use_freestyle = False

    # Set World Viewport Display to solid black
    bpy.data.worlds["World"].color = (0, 0, 0)

    # In Compositor, delete all File Outputs and plug Image into a newly added File Output
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    # Clear existing file output nodes
    for node in tree.nodes:
        if node.type == 'OUTPUT_FILE':
            tree.nodes.remove(node)

    # Create new file output node
    output_node = tree.nodes.new(type='CompositorNodeOutputFile')
    output_node.base_path = file_output_path
    output_node.name = "mask"
    output_node.label = "mask_"

    # Get the render layers node
    render_layers_node = tree.nodes.get('Render Layers')
    # Link Image output to the File Output input
    tree.links.new(render_layers_node.outputs['Image'], output_node.inputs[0])

    # Set the object named 'Ground' to not render
    ground = bpy.data.objects.get('GROUND')
    if ground:
        ground.hide_render = True
    render_animation()

def set_cloth_to_denim(cloth_modifier):
    cloth_modifier.settings.quality = 12
    cloth_modifier.settings.mass = 1
    cloth_modifier.settings.tension_stiffness = 40
    cloth_modifier.settings.compression_stiffness = 40
    cloth_modifier.settings.shear_stiffness = 40
    cloth_modifier.settings.bending_stiffness = 10
    cloth_modifier.settings.tension_damping = 25
    cloth_modifier.settings.compression_damping = 25
    cloth_modifier.settings.shear_damping = 25
    cloth_modifier.settings.air_damping = 1

def set_cloth_to_cotton(cloth_modifier):
    cloth_modifier.settings.quality = 5
    cloth_modifier.settings.mass = 0.300
    cloth_modifier.settings.tension_stiffness = 15
    cloth_modifier.settings.compression_stiffness = 15
    cloth_modifier.settings.shear_stiffness = 15
    cloth_modifier.settings.bending_stiffness = 0.500
    cloth_modifier.settings.tension_damping = 5
    cloth_modifier.settings.compression_damping = 5
    cloth_modifier.settings.shear_damping = 5
    cloth_modifier.settings.air_damping = 1.000

def set_cloth_to_leather(cloth_modifier):
    cloth_modifier.settings.quality = 5
    cloth_modifier.settings.mass = 0.300
    cloth_modifier.settings.tension_stiffness = 15
    cloth_modifier.settings.compression_stiffness = 15
    cloth_modifier.settings.shear_stiffness = 15
    cloth_modifier.settings.bending_stiffness = 0.500
    cloth_modifier.settings.tension_damping = 5
    cloth_modifier.settings.compression_damping = 5
    cloth_modifier.settings.shear_damping = 5
    cloth_modifier.settings.air_damping = 1.000

def limit_position(position):

  position = list(position)

  if position[0] < -2.5:
    position[0] = -2.5 
  elif position[0] > 2.5:
    position[0] = 2.5

  if position[1] < -2.5:
    position[1] = -2.5
  elif position[1] > 2.5:
    position[1] = 2.5  

  if position[2] < 0:
    position[2] = 0
  elif position[2] > 5:
    position[2] = 5

  return tuple(position)

#--------------------------------1.Main Functions, need to be adjusted--------------------------------------------

#--------------------------------1.1 Creation Functions, create objects--------------------------------------------

def create_floor(elasticity=1):
    """
    Creates a floor plane in Blender, scales it, and sets it up with collision and rigid body physics.
    The created floor is scaled to be large enough to act as a ground plane for most scenes.

    Do not create floors when the physical scene does not involve floors.

    Parameters:
    - elasticity (float): The restitution or 'bounciness' of the floor. A value of 1 means perfectly elastic, 
                          while 0 means no elasticity. Default is 1.
    """
    bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.scale = (50, 50, 50)
    floor.name = 'GROUND'
    add_collision(floor)
    add_rigid_body(floor, rigid_body_type='PASSIVE', elasticity=elasticity)

def create_object_in_assets(file_path, new_name, position=(0, 0, 5), max_dimension=None):
    """
    Imports a 3D model from a specified file, resizes it proportionally if a max_dimension is provided, renames it, and positions it within the Blender scene.

    Parameters:
    - file_path (str): Path to the .obj or .blend file to import.
    - new_name (str): The new name to assign to the imported object.
    - position (tuple of floats): The desired location (x, y, z) for the object. Defaults to (0, 0, 5).
    - max_dimension (float, optional): If provided, set the object's largest dimension (meter) to this size while maintaining aspect ratio.

    Returns:
    - new_object (Blender Object): The imported and resized object, or None if the import fails.
    """
    # Import the file based on the extension
    # max_dimension = max_dimension*5 if max_dimension else None
    position = limit_position(position)
    file_extension = os.path.splitext(file_path)[-1].lower()
    before_import_objects = set(bpy.data.objects)
    
    if file_extension == '.obj':
        bpy.ops.import_scene.obj(filepath=file_path)
    elif file_extension == '.blend':
        directory = file_path + "\\Collection\\"
        
        # List available collections in the specified blend file
        with bpy.data.libraries.load(file_path) as (data_from, data_to):
            collections = [c for c in data_from.collections if c]

        # Check if there are any collections available
        if collections:
            # Append the first collection in the list
            bpy.ops.wm.append(
                filepath=file_path,
                filename=collections[0],
                directory=directory
            )
    else:
        print("Unsupported file format")
        return None

    after_import_objects = set(bpy.data.objects)
    new_objects = after_import_objects - before_import_objects

    if not new_objects:
        print("No new objects were imported.")
        return None

    # Assume the first object in the list is the one we want if multiple objects are imported
    new_object = list(new_objects)[0]

    set_origin_to_geometry(new_object)
    
    # Rename the active object
    new_object.name = new_name
    target_size = max_dimension
    # Set object dimensions proportionally, if a target size is specified
    if target_size is not None:
        # target_size = target_size * 5
        non_zero_dimensions = [dim for dim in new_object.dimensions if dim > 0.0001] # Consider dimension as zero if it's too small
        if not non_zero_dimensions: # Avoid division by zero or invalid scale factors
            print(f"All dimensions of the object {new_object.name} are zero, cannot resize.")
            return new_object
        
        largest_dimension = max(non_zero_dimensions)
        scale_factor = target_size / largest_dimension

        # Apply scale factors, skipping dimensions that are zero or near zero
        for i, dim in enumerate(new_object.dimensions):
            if dim > 0.0001: # Skip near-zero dimensions to avoid distortion
                new_object.scale[i] *= scale_factor

    # Place the object at the specified position
    new_object.location = position
    
    return new_object
    
def create_camera(location = (-0.165, 15.066, 1.7549), rotation = (math.radians(-86.8), math.radians(180), math.radians(0))):
    """
    Adds a camera to the Blender scene at a specified location with a specified rotation.

    Parameters:
    - location (tuple of floats): The position (x, y, z) of the camera in the scene.
    - rotation (tuple of floats): The rotation (x, y, z) of the camera in Euler angles.

    Unless there is a special request:
    - The camera location is adjusted to (-0.165, 15.066, 1.7549).
    - The camera rotation is adjusted to (math.radians(-86.8), math.radians(180), math.radians(0))
    If the camera is required to be in a top-down view:
    - The camera location is adjusted to (-0.07083, 9.59862 , 14.9201).
    - The camera rotation is adjusted to (math.radians(-140), math.radians(180), math.radians(0))

    Returns:
    - None, but creates a camera object in the scene with the specified location and rotation.
    """
    camera_data = bpy.data.cameras.new(name='MyCamera')
    camera_object = bpy.data.objects.new('MyCamera', camera_data)
    bpy.context.collection.objects.link(camera_object)
    camera_object.location = location
    camera_object.rotation_euler = rotation
    bpy.context.scene.camera = camera_object

def create_cloth(name, size, location, rotation = [math.radians(90), 0 ,0], subdivision = 30, pinned_vertices_indices = None):
    """
    Creates a plane in Blender, sets it up as a cloth simulation object with given parameters, including rotation and subdivision.

    Parameters:
    - name (str): The name for the new cloth object.
    - size (float): The size of the cloth object.
    - location (tuple of floats): The location to place the center of the cloth object in the scene.
    - rotation (list of floats): The rotation of the cloth object in radians, default is [0, 90 degrees on Y-axis, 0].
    - subdivision (int): The number of subdivisions for the cloth mesh, default is 30 for detailed simulation.
    - pinned_vertices_indices (list of ints or None): Indices of vertices to pin, if any.

    Returns:
    - plane (Blender Object): The created plane object with a cloth modifier.

    This function is useful for quickly setting up cloth simulations with custom size, position, rotation, and detail level.
    Vertices can be pinned to create fixed points in the simulation, which is common for simulating hanging fabrics or clothing.
    """
    # Create a plane and rename it
    bpy.ops.mesh.primitive_plane_add(size=size, enter_editmode=False, align='WORLD', location=location)
    plane = bpy.context.active_object
    plane.name = name

    # Rotate the plane to be parallel with the XZ plane
    plane.rotation_euler[0] = rotation[0]
    plane.rotation_euler[1] = rotation[1]  # default 90 degrees in radians on the Y-axis
    plane.rotation_euler[2] = rotation[2]

    # Subdivide the plane
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=subdivision)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Shade smooth
    bpy.ops.object.shade_smooth()

    # Add cloth modifier
    bpy.ops.object.modifier_add(type='CLOTH')
    cloth_modifier = plane.modifiers['Cloth']
    cloth_modifier.collision_settings.use_self_collision = True
    # cloth_modifier.settings.mass = 1.0
    # Pin vertices if specified
    if pinned_vertices_indices:
        vg = plane.vertex_groups.new(name="PinnedGroup")
        vg.add(pinned_vertices_indices, 1.0, 'ADD')
        cloth_modifier.settings.vertex_group_mass = vg.name
        cloth_modifier.settings.pin_stiffness = 1

    return plane

def create_cube(name, size, location):
    """
    Creates a cube in Blender and places it at the specified location.

    Parameters:
    - name (str): The name for the new cube object.
    - size (float): The size of the cube object. This is the length of the edges of the cube.
    - location (tuple of floats): The location to place the center of the cube object in the scene.

    Returns:
    - cube (Blender Object): The created cube object.
    """
    # Create a cube and rename it
    bpy.ops.mesh.primitive_cube_add(size=size, enter_editmode=False, align='WORLD', location=location)
    cube = bpy.context.active_object
    cube.name = name

    # Shade smooth (optional, can remove if a flat shading is preferred)
    bpy.ops.object.shade_smooth()

    return cube

def create_tshirt():
    """
    Imports a T-shirt model from a given file path, setting up cloth physics for the shirt and passive rigid body physics for other objects.

    Parameters:
    - None

    Returns:
    - new_objects (set): A set of the newly imported objects.
    """
    file_path = ASSETS_PATH + "tshirt_1.obj"
    # Import the file based on the extension
    file_extension = os.path.splitext(file_path)[-1].lower()
    before_import_objects = set(bpy.data.objects)
    
    if file_extension == '.obj':
        bpy.ops.import_scene.obj(filepath=file_path)
    elif file_extension == '.blend':
        directory = file_path + "\\Collection\\"
        
        # List available collections in the specified blend file
        with bpy.data.libraries.load(file_path) as (data_from, data_to):
            collections = [c for c in data_from.collections if c]

        # Check if there are any collections available
        if collections:
            # Append the first collection in the list
            bpy.ops.wm.append(
                filepath=file_path,
                filename=collections[0],
                directory=directory
            )
    else:
        print("Unsupported file format")
        return None

    after_import_objects = set(bpy.data.objects)
    new_objects = after_import_objects - before_import_objects

    if not new_objects:
        print("No new objects were imported.")
        return None
    
    for obj in new_objects:
        bpy.context.view_layer.objects.active = obj
        if obj.name.lower() != 'shirt':
            add_rigid_body(obj,rigid_body_type = 'PASSIVE')
            add_collision(obj)
        else:
            bpy.ops.object.modifier_add(type='CLOTH')
            cloth_modifier = obj.modifiers['Cloth']
            cloth_modifier.collision_settings.use_self_collision = True
            set_cloth_to_denim(cloth_modifier)
            add_collision(obj)
    return new_objects


def create_flag(cloth_name):
    """
    Creates a flag with a cloth simulation and a flagpole to which the flag is attached.

    Parameters:
    - cloth_name (str): The name for the new cloth object (flag).

    Returns:
    - flagpole (Blender Object): The created flagpole object.

    The function first creates a flag using the `create_cloth` function. After creation the flag is perpendicular to the camera view.
    """
    
    pinned_vertices_indices = [1, 3]
    cloth_object = create_cloth(cloth_name, size = 4, location = (0, -5, 4), subdivision = 40, pinned_vertices_indices = pinned_vertices_indices)
    cloth_object.scale[0] = 1.5
    add_collision(cloth_object)
    subdiv_modifier = cloth_object.modifiers.new(name="Subdivision", type="SUBSURF")
    subdiv_modifier.levels = 1
    subdiv_modifier.render_levels = 1

    bpy.ops.object.mode_set(mode='OBJECT')
    # Create the flagpole at the origin
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=10, enter_editmode=False, location=(3.1,-5,1.3))

    flagpole = bpy.context.active_object
    flagpole.name = 'Flagpole'
    add_collision(flagpole)

    return flagpole

def create_influid(viscosity_value = None):
    """
    Creates a fluid inflow sphere object and configures the fluid domain in the scene for a liquid simulation.

    Parameters:
    - viscosity_value (float, optional): The viscosity value to be set for the fluid domain. The viscosity value set for the fluid field. If the user prompt does not mention a viscosity value, it does not need to be set to use the default value; viscosity values range in size from 0.001 to 0.035.

    Returns:
    - tuple: A tuple containing the inflow object and the domain object, or (None, None) if the domain object is not found.

    """
    # radius = min(max(0.2, radius), 0.8)
    # print(radius)
    # Create an inflow sphere object
    location = (0,0,8.5) 
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=location)
    inflow = bpy.context.object
    inflow.name = 'Fluid Inflow'
    
    # Set the inflow object as active and add quick liquid simulation
    bpy.context.view_layer.objects.active = inflow
    bpy.ops.object.quick_liquid()
    
    # Configure inflow settings for the fluid simulation
    inflow.modifiers["Fluid"].flow_settings.flow_behavior = 'INFLOW'
    inflow.modifiers["Fluid"].flow_settings.use_initial_velocity = True
    # inflow.modifiers["Fluid"].flow_settings.velocity_coord[2] = 0
    inflow.modifiers["Fluid"].flow_settings.velocity_coord[0] = -2

    # Retrieve and configure the domain object
    domain = bpy.data.objects.get('Liquid Domain')
    if domain:
        domain.dimensions = (7.58, 5.68, 9.24) 
        domain.scale = (3.792, 2.842, 4.618) 
        domain.location[2] = 4.6822
        domain.modifiers["Fluid"].domain_settings.time_scale = 1.25
        # Enable viscosity and set its value
        if viscosity_value:
            viscosity_value = value = max(0.001, min(viscosity_value, 0.035))
            domain.modifiers["Fluid"].domain_settings.use_viscosity = True
            domain.modifiers["Fluid"].domain_settings.viscosity_value = viscosity_value
    else:
        print("No domain object named 'Liquid Domain' found. Please create one before calling this function.")
        return None, None

    return inflow, domain
    
#--------------------------------1.2 Physical Functions, modify objects--------------------------------------------

def add_collision(obj):
    """
    Adds a collision modifier to a Blender object if it does not already have one.

    Parameters:
    - obj (Blender Object): The object to which the collision modifier will be added.

    Returns:
    - None, but the object will have a collision modifier added to it if it wasn't present before.

    This function is used in physics simulations where it's necessary for objects to interact with each other, 
    such as rigid body or soft body simulations. The collision modifier makes the object a collider in the physics 
    simulation, allowing other objects to bounce off or slide along its surface.
    """
    if "Collision" not in obj.modifiers:
        bpy.ops.object.modifier_add(type='COLLISION')

def add_rigid_body(obj, mass=1, elasticity=0.5, rigid_body_type='ACTIVE'):
    """
    Adds a rigid body physics characteristic to a Blender object.
    
    Args:
    - obj (Blender Object): The object to which the rigid body physics will be applied.
    - mass (float): The mass of the object, default is 1.
    - elasticity (float): The restitution (bounciness) of the object, default is 0.5.
    - rigid_body_type (str): The type of rigid body, can be 'ACTIVE' or 'PASSIVE', default is 'ACTIVE'.
    
    Returns:
    - None, but the object is now a rigid body with the specified physics properties.
    
    This function is crucial for physics simulations, defining how the object behaves under physical forces.
    """
    # if mass:
    #     mass = mass * 5 
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = rigid_body_type
    obj.rigid_body.mass = mass
    obj.rigid_body.restitution = elasticity
    obj.rigid_body.collision_shape = 'MESH'

def add_initial_velocity_for_rigid_body(obj, initial_velocity, initial_rotation):
    """
    Add initial velocity and rotation for a rigid body object for physics simulation.
    
    Args:
    - obj (Blender Object): The object to which the initial velocity and rotation will be applied.
    - initial_velocity (tuple of floats): The starting velocity (x, y, z) of the object.
    - initial_rotation (tuple of floats): The starting rotation (x, y, z) in degrees.
    
    Returns:
    - None, but applies keyframes to the object to set its initial state for physics simulation.
    """
    START_FRAME = 0
    STOP_FRAME = 4
    
    # Ensure the mode is Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Apply initial state only if initial velocity or rotation is not zero
    if initial_velocity != (0, 0, 0) or initial_rotation != (0, 0, 0):
        # Set the kinematic property for the rigid body
        obj.rigid_body.kinematic = True
        obj.keyframe_insert(data_path="rigid_body.kinematic", frame=START_FRAME)
        obj.keyframe_insert(data_path='location', frame=START_FRAME)
        obj.keyframe_insert(data_path='rotation_euler', frame=START_FRAME)

        # Calculate the position and rotation at frame 4
        time_step = STOP_FRAME / 24  # Assuming 24 fps, the time step to frame 4 is 1/6 of a second

        # Set new location if initial velocity is not zero
        if initial_velocity != (0, 0, 0):
            new_location = (obj.location.x + initial_velocity[0] * time_step,
                            obj.location.y + initial_velocity[1] * time_step,
                            obj.location.z + initial_velocity[2] * time_step - 9.8 * time_step**2)
            obj.location = new_location
            obj.keyframe_insert(data_path='location', frame=STOP_FRAME)

        # Set new rotation if initial rotation is not zero
        if initial_rotation != (0, 0, 0):
            obj.rotation_euler = [math.radians(angle) for angle in initial_rotation]
            obj.keyframe_insert(data_path='rotation_euler', frame=STOP_FRAME)
        
        # Unset the kinematic property for the rigid body to simulate physics
        obj.rigid_body.kinematic = False
        obj.keyframe_insert(data_path="rigid_body.kinematic", frame=STOP_FRAME)

    
def add_wind_force(direction = (0, math.radians(-90), 0), strength = 2500):
    """
    Creates a wind force field in Blender and sets its strength and direction.

    Parameters:
    - direction (tuple of floats): Euler angles (in radians) specifying the direction of the wind.
    - strength (float): The strength of the wind force.

    Returns:
    - None, but a wind force field object is created and configured in the scene.

    The default wind strength is 2500 unless otherwise specified. If a lower wind strength is required, set it to 500. If a strong wind is required, set it to 5000.
    The default wind direction is (0, math.radians(-90), 0)
    """
    # Create a wind force field
    bpy.ops.object.effector_add(type='WIND', enter_editmode=False, align='WORLD', location=(0, 0, 0))
    wind = bpy.context.active_object
    
    # Set the properties of the wind
    wind.field.strength = strength
    wind.field.flow = 1
    wind.field.noise = 1
    
    # Rotate the wind to blow from the +Z direction to the +X direction
    wind.rotation_euler = direction
    
def add_fluid_effector(obj):
    """
    Adds a fluid effector modifier to an object in Blender to influence the behavior of a fluid simulation.

    Parameters:
    - obj (Blender Object): The object to which the effector modifier will be added.

    This function configures the object as an effector within the fluid simulation, meaning it will affect the fluid's motion and behavior. The effector's geometry is used as an obstacle or guide for the fluid simulation.
    """
    # Set the passed object as the active object in the scene
    bpy.context.view_layer.objects.active = obj
    before_import_objects = set(bpy.data.objects)
    obj.select_set(True)
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})

    after_import_objects = set(bpy.data.objects)
    new_objects = list(after_import_objects - before_import_objects)
    new_objects = new_objects[0]
    
    bpy.context.view_layer.objects.active = new_objects
    new_objects.hide_render = True

    # Scale the duplicate
    bpy.ops.transform.resize(value=(1.145, 1.145, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
    
    # Add a fluid modifier to the object
    bpy.ops.object.modifier_add(type='FLUID')
    
    # Set the fluid modifier type to 'EFFECTOR'
    new_objects.modifiers["Fluid"].fluid_type = 'EFFECTOR'
    
    # Use the object's plane for the effector's initial state
    new_objects.modifiers["Fluid"].effector_settings.use_plane_init = True
    
#--------------------------------1.3 Other Functions--------------------------------------------

def clear_scene():
    """
    Clears all objects from the current Blender scene.
    
    This function selects all objects in the scene and deletes them.
    It is useful when starting a new scene setup or resetting the scene to a blank state.
    
    No inputs or outputs.
    
    Typically called at the beginning of a script when starting a new scene setup.
    """
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def Render_a_video():
    """
    Sets up the render and compositor settings, bakes the necessary physics and fluid simulations,
    and then renders an animation to a specified path.

    The function is pre-configured with a path, start and end frames for the animation.
    """
    path = '../data/new/'
    set_render_settings(start_frame = 0, end_frame = 120, output_path = path)
    setup_compositor(path)
    bake_fluid_sim()
    bake_physics()
    render_animation()