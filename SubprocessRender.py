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
import ffmpy
from subprocess import Popen
from pprint import pprint


thread_options = [
    ("1", "All", "Use all available threads", 1),
    ("2", "Only", "Only use this amount of threads", 2),
    ("3", "Except", "Use this many less than all threads", 3),
]

# Reset thread count to max when all is selected
def uiupdate(self,context):
    scene = context.scene
    if scene.subprocess_render.thread_usage == "1":
        scene.subprocess_render.thread_count = scene.render.threads


class SubprocessRenderProperties(bpy.types.PropertyGroup):
    '''Subprocess Render  settings'''
    thread_count = bpy.props.IntProperty(name="Thread Count", default=4,min=1)
    thread_usage = bpy.props.EnumProperty(
        items=thread_options, name = "Thread Setting", default="1",update=uiupdate)
    output_path = bpy.props.StringProperty(name="Output Path", subtype="FILE_PATH", default="//output.avi")
    ffmpeg_options = bpy.props.StringProperty(name="FFmpeg", default="-c:v libx264 -preset:v veryfast -c:a aac -b:a 320k -strict -2")

def clear_frames(scene):
    render_path = os.path.dirname(bpy.path.abspath(scene.render.filepath))
    render_file = os.path.basename(bpy.path.abspath(scene.render.filepath))

    # Reformat blender frame output to ffmpeg frame input
    digits = render_file.count('#')
    split_point = '#' * digits
    start, end = render_file.split(split_point)
    count = len([name for name in os.listdir(render_path) if os.path.isfile(render_path + '/' + name)])

    ffmpeg_image_name = start + '%0' + str(digits) + 'd' + end

    for i in range(0,count):
        try:
            print(bpy.path.abspath(render_path + '/' + start + '%06d' % i + end))
            os.remove(bpy.path.abspath(render_path + '/' + start + '%06d' % i + end))
        except OSError:
            pass



class SubprocessRenderPanel(bpy.types.Panel):
    '''Properties panel to configure subprocess rendering'''
    bl_idname = "RENDER_PT_subproccess_render"
    bl_label = "Subprocess Render"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        row = layout.row()
        row.prop(scene.subprocess_render, "thread_usage", expand=True)
        col = layout.column()
        col.prop(scene.subprocess_render,"thread_count")
        col = layout.column()
        col.prop(scene.subprocess_render,"output_path")
        col.prop(scene.subprocess_render,"ffmpeg_options")
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
        render_path = os.path.dirname(bpy.path.abspath(scene.render.filepath))
        render_file = os.path.basename(bpy.path.abspath(scene.render.filepath))
        command = str('blender -b "' + str(bpy.path.abspath(bpy.data.filepath)) + '" -s %d -e %d -a')

        threads =scene.render.threads
        if scene.subprocess_render.thread_usage == "1":
            threads = scene.render.threads
        elif scene.subprocess_render.thread_usage == "2":
            threads = scene.subprocess_render.thread_count
        elif scene.subprocess_render.thread_usage == "3":
            threads = threads - scene.subprocess_render.thread_count

        frames_per_thread = int(frame_count / threads)
        # Build commands for subprocesses
        for i in range(0,threads):
            frame_ranges.append([i*frames_per_thread+1,(i+1)*frames_per_thread])
            commands.append(command % (frame_ranges[-1][0],frame_ranges[-1][1]))

        # Set start and end frames explicitly
        frame_ranges[0][0] = scene.frame_start
        frame_ranges[-1][1] = scene.frame_end

        clear_frames(scene)
        # Begin threads
        processes = [Popen(cmd, shell=True) for cmd in commands]
        for p in processes: p.wait()

        # Render audio
        audio_path=os.path.dirname(bpy.path.abspath(scene.render.filepath))+"/audio.flac"
        bpy.ops.sound.mixdown(filepath=audio_path, container='FLAC', codec='FLAC', bitrate=320)

        # Reformat blender frame output to ffmpeg frame input
        digits = render_file.count('#')
        split_point = '#' * digits
        start, end = render_file.split(split_point)
        ffmpeg_image_name = start + '%0' + str(digits) + 'd' +  end
        ffmpeg_input_options = '-r ' + str(round(scene.render.fps/scene.render.fps_base,2)) + \
            ' -f image2' + \
            ' -s ' + str(scene.render.resolution_x) + 'x' + str(scene.render.resolution_y)

        try:
            os.remove(bpy.path.abspath(scene.subprocess_render.output_path))
        except OSError:
            pass

        ff = ffmpy.FFmpeg(
            inputs={ render_path + '/' + ffmpeg_image_name : ffmpeg_input_options , audio_path : None },
            outputs={bpy.path.abspath(scene.subprocess_render.output_path): scene.subprocess_render.ffmpeg_options }
        )
        ff.run()

        clear_frames(scene)
        try:
            os.remove(audio_path)
        except OSError:
            pass


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

