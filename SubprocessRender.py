bl_info = {
    "name": "Subprocess Render",
    "author": "Shelby Jueden",
    "version": (0,8),
    "blender": (2,78,0),
    "description": "Use subprocesses to split render load.",
    "warning": "Requires install of ffmpy to join files",
    "category": "Render",
}


import bpy
import os
from subprocess import Popen
from pprint import pprint


class SubprocessRenderProperties(bpy.types.PropertyGroup):
    '''Subprocess Render  settings'''
    thread_count = bpy.props.IntProperty(name="Thread Count", default=4)

class SubprocessRenderPanel(bpy.types.Panel):
    '''Properties panel to configure subprocess rendering'''
    bl_idname = "RENDER_PT_youtube_upload"
    bl_label = "Subprocess Render"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        self.layout.label(text="Render Threads:")
        col = layout.column()
        col.prop(scene.subprocess_render,"thread_count")
        col.operator(SubprocessRenderStart.bl_idname)


class SubprocessRenderStart(bpy.types.Operator):
    '''Start thread to upload video'''
    bl_idname = "subprocess_render.start"
    bl_label = "Start Render"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = bpy.context.scene
        frame_ranges = []
        commands = []
        frame_count = scene.frame_end - scene.frame_start
        command = str('blender -b "' + str(bpy.path.abspath(bpy.data.filepath)) + '" -s %d -e %d -a')
        frames_per_thread = int(frame_count / scene.subprocess_render.thread_count)

        # Build commands for subprocesses
        for i in range(0,scene.subprocess_render.thread_count):
            frame_ranges.append([i*frames_per_thread+1,(i+1)*frames_per_thread])
            commands.append(command % (frame_ranges[-1][0],frame_ranges[-1][1]))

        # Set start and end frames explcitly
        frame_ranges[0][0] = scene.frame_start
        frame_ranges[-1][1] = scene.frame_end

        # Begin threads
        processes = [Popen(cmd, shell=True) for cmd in commands]
        for p in processes: p.wait()

        # Render audio
        audio_path=os.path.dirname(bpy.path.abspath(scene.render.filepath))+"/audio.flac"
        bpy.ops.sound.mixdown(filepath=audio_path, container='FLAC', codec='FLAC', bitrate=320)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(SubprocessRenderPanel)
    bpy.utils.register_class(SubprocessRenderProperties)
    bpy.utils.register_class(SubprocessRenderStart)

    bpy.types.Scene.subprocess_render = \
        bpy.props.PointerProperty(type=SubprocessRenderProperties)


def unregister():
    bpy.utils.unregister_class(SubprocessRenderPanel)
    bpy.utils.unregister_class(SubprocessRenderProperties)
    bpy.utils.unregister_class(SubprocessRenderStart)

    del bpy.types.Scene.subprocess_render

if __name__ == "__main__":
    register()

