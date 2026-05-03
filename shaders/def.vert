#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;
in vec3 p3d_Normal;

out vec2 texcoord;
out vec3 world_normal;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoord = p3d_MultiTexCoord0;
    world_normal = normalize(mat3(p3d_ModelMatrix) * p3d_Normal);
}