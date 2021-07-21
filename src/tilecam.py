'''
Tilecam
Copyright (C) 2019  Per Gantelius

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/
'''

import bpy
import math

bl_info = {
    'name': 'Tilecam',
    'author': 'Per Gantelius',
    'version': (1, 0, 1),
    'blender': (2, 93, 1),
    'location': 'Properties editor > Camera panel > Repeatable Orthographic Viewport',
    'description': 'Sets up orthographic cameras for rendering seamlessly repeatable images',
    'tracker_url': 'https://github.com/stuffmatic/tilecam/issues',
    'wiki_url': 'https://github.com/stuffmatic/tilecam/wiki',
    'support': 'COMMUNITY',
    'category': 'Render'
}

# The camera elevation in degrees needed to get an isometric projection
ISOMETRIC_ELEVATION = 35.264

class OrthographicTileCameraPanel(bpy.types.Panel):    
    bl_idname = "TILECAM_PT_propspanel"
    bl_label = "Repeatable Orthographic Viewport"    
    bl_space_type = "PROPERTIES"    
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self, context):
        scn = bpy.context.scene
        is_isometric = scn.tilecam_is_isometric
        l = self.layout
        
        r = l.row()
        r.enabled = not is_isometric
        r.prop(scn, "tilecam_x_period")
        r.prop(scn, "tilecam_y_period")
        r.prop(scn, "tilecam_elevation")
        
        r = l.row()
        r.prop(scn, "tilecam_repetition_count")
        r.prop(scn, "tilecam_is_isometric")        
        
        r = l.row()
        r.operator("camera.orthographic_tile_camera")
        
        
    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'CAMERA'
        

class OrthographicTileCameraOperator(bpy.types.Operator):
    bl_idname = "camera.orthographic_tile_camera"    
    bl_label = "Apply"
    
    bl_description = "Applies the settings to the camera"

    def execute(self, context):
        scn = bpy.context.scene
        is_isometric = scn.tilecam_is_isometric
        
        if is_isometric:
            elevation = -ISOMETRIC_ELEVATION * math.pi / 180
            x_period = 1
            y_period = 1
        else:
            elevation = -scn.tilecam_elevation * math.pi / 180
            x_period = scn.tilecam_x_period
            y_period = scn.tilecam_y_period
            
        x_tile_count = scn.tilecam_repetition_count
     
        cam = scn.camera
        if not cam:
            # No camera. do nothing
            return {'CANCELLED'}
    
        cam.data.type = 'ORTHO'
        
        azimuth = math.atan2(y_period, x_period)
        
        # Adjust the elevation so that aspect_ratio * width 
        # (i.e the image height) is an integer number of pixels
        image_width = scn.render.resolution_x
        # 1. Compute the height based on the current elevation
        unadjusted_aspect_ratio = math.cos(math.pi / 2 + elevation)
        unadjusted_height = unadjusted_aspect_ratio * image_width
        # 2. Round the height to the nearest integer...
        image_height = int(unadjusted_height + 0.5)
        adjusted_aspect_ratio = image_height / float(image_width)
        # 3. Compute an adjusted elevation angle 
        adjusted_elevation = math.acos(adjusted_aspect_ratio) - math.pi / 2
        
        # Set the camera orientation. 
        # A camera with a unit orientation is looking down the positive
        # y axis to match the blender front view.
        cam.rotation_euler = [math.pi / 2 + adjusted_elevation, 0, azimuth]
        
        # Compute the orthographic scale of the camera
        n = abs(x_period) / math.gcd(x_period, y_period)
        cam.data.ortho_scale = x_tile_count * n / math.cos(azimuth)
        
        # Set the viewport dimensions
        scn.render.resolution_y = image_height
        
        return {'FINISHED'}        
    
def init_scene_props():
    max_period = 10
    max_tile_count = 10

    bpy.types.Scene.tilecam_x_period = bpy.props.IntProperty(
        name = "Horizontal period", 
        default = 1, 
        min=1, 
        max=max_period, 
        description="The number of horizontal repetitions per tile"
    )
    bpy.types.Scene.tilecam_y_period = bpy.props.IntProperty(
        name = "Vertical period", 
        default = 1, 
        min=1, 
        max=max_period, 
        description="The number of vertical repetitions per tile"
    )
    bpy.types.Scene.tilecam_elevation = bpy.props.FloatProperty(
        name = "Elevation", 
        default = 45, 
        min=0, 
        max=90, 
        description="The camera elevation, i.e the amount of vertical stretch (90 degrees is top down)"
    )
    bpy.types.Scene.tilecam_repetition_count = bpy.props.IntProperty(
        name = "Repetition count", 
        default = 1, 
        min=1, 
        max=max_tile_count, 
        description="Controls the number of repeatable tiles in the viewport"
    )
    bpy.types.Scene.tilecam_is_isometric = bpy.props.BoolProperty(
        name = "Isometric", 
        default = False, 
        description="Override the current orientation settings and produce an isometric view"
    ) 

classes = (OrthographicTileCameraPanel, OrthographicTileCameraOperator)

def register():
    init_scene_props()
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
     
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
if __name__ == "__main__":
    register()
