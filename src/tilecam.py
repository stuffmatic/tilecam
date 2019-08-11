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
import fractions

bl_info = {
    'name': 'Tilecam',
    'author': 'Per Gantelius',
    'version': (1, 0, 0),
    'blender': (2, 80, 0),
    'location': 'Properties editor > Camera panel > Repeatable Orthographic Viewport',
    'description': 'Sets up orthographic cameras for rendering seamlessly repeatable images',
    'tracker_url': 'https://github.com/stuffmatic/tilecam/issues',
    'wiki_url': 'https://github.com/stuffmatic/tilecam/wiki',
    'support': 'COMMUNITY',
    'category': 'Render'
}
    
isometricElevation = 35.264

class OrthographicTileCameraPanel(bpy.types.Panel):    
    bl_idname = "TILECAM_PT_propspanel"
    bl_label = "Repeatable Orthographic Viewport"    
    bl_space_type = "PROPERTIES"    
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self, context):
        scn = bpy.context.scene
        isIsometric = scn.isIsometric
        l = self.layout
        
        r = l.row()
        r.enabled = not isIsometric
        r.prop(scn, "xPeriod")
        r.prop(scn, "yPeriod")
        r.prop(scn, "elevation")
        
        r = l.row()
        r.prop(scn, "imageSize")
        r.prop(scn, "isIsometric")        
        
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
        isIsometric = scn.isIsometric
        
        if isIsometric:
            elevation = -isometricElevation * math.pi / 180
            xPeriod = 1
            yPeriod = 1
        else:
            elevation = -scn.elevation * math.pi / 180
            xPeriod = scn.xPeriod
            yPeriod = scn.yPeriod
            
        xTileCount = scn.imageSize
     
        cam = scn.camera
        if not cam:
            #no camera. do nothing
            return{'CANCELLED'}
    
        cam.data.type = 'ORTHO'
        cam.data.clip_start = 0.0001
        cam.data.clip_end = 1000
        
        azimuth = math.atan2(yPeriod, xPeriod)
        
        '''
            adjust the elevation so that aspectRatio * width 
            (i.e the image height) is an integer number of pixels
        '''
        imageWidth = scn.render.resolution_x
        #compute the height based on the current elevation
        unadjustedAspectRatio = math.cos(math.pi / 2 + elevation)
        unadjustedHeight = unadjustedAspectRatio * imageWidth
        #round the height to the nearest integer...
        imageHeight = int(unadjustedHeight + 0.5)
        adjustedAspectRatio = imageHeight / float(imageWidth)
        #...and compute an adjusted elevation angle 
        adjustedElevation = math.acos(adjustedAspectRatio) - math.pi / 2
        
        #print("adjusted elevation from", elevation, "to", adjustedElevation)
        #print("width * aspect ratio         =", imageWidth * unadjustedAspectRatio)
        #print("width * adjusted aspect ratio=", imageWidth * adjustedAspectRatio)
    
        #a camera with a unit orientation is looking down the positive
        #y axis to match the blender front view.
        cam.rotation_euler = [math.pi / 2 + adjustedElevation, 0, azimuth]
        
        n = abs(xPeriod) / fractions.gcd(xPeriod, yPeriod)
        cam.data.ortho_scale = xTileCount * n / math.cos(azimuth)

        scn.render.resolution_y = imageHeight
        return {'FINISHED'}        
    
def initSceneProps():
    maxPeriod = 10
    maxTileCount = 10

    bpy.types.Scene.xPeriod = bpy.props.IntProperty(name = "Horizontal period", default = 1, min=1, max=maxPeriod, description="The number of horizontal repetitions per tile")
    bpy.types.Scene.yPeriod = bpy.props.IntProperty(name = "Vertical period", default = 1, min=1, max=maxPeriod, description="The number of vertical repetitions per tile")
    bpy.types.Scene.elevation = bpy.props.FloatProperty(name = "Elevation", default = 45, min=0, max=90, description="The camera elevation, i.e the amount of vertical stretch (90 degrees is top down)")
    bpy.types.Scene.imageSize = bpy.props.IntProperty(name = "Repetition count", default = 1, min=1, max=maxTileCount, description="Controls the number of repeatable tiles in the final image")
    bpy.types.Scene.isIsometric = bpy.props.BoolProperty(name = "Isometric", default = False, description="Override the current orientation settings and produce an isometric view")        

classes = (OrthographicTileCameraPanel, OrthographicTileCameraOperator)

def register():
    initSceneProps()
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
     
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
if __name__ == "__main__":
    register()
