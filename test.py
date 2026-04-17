from ursina import *

app = Ursina()

shader = Shader(
    language=Shader.GLSL,
    vertex='''
    #version 140

    uniform mat4 p3d_ModelViewProjectionMatrix;
    uniform float time;

    in vec4 p3d_Vertex;

    void main() {
        vec4 pos = p3d_Vertex;
        pos.y += sin(time) * 0.5;
        gl_Position = p3d_ModelViewProjectionMatrix * pos;
    }
    ''',

    fragment='''
    #version 140
    uniform float time;
    out vec4 fragColor;

    void main() {
        fragColor = vec4(time - floor(time), 0.5, 1.0, 1.0);
    }
    '''
)

e = Entity(model='cube', shader=shader)
td = time.time()
def update():
    e.set_shader_input("time", time.time()-td)

app.run()