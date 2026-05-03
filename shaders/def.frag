#version 140

in vec2 texcoord;
in vec3 world_normal;
out vec4 fragColor;

uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform vec3 light_direction;
uniform float tod;

void main() {
    float value = max(0, (dot(light_direction, world_normal)+1)/2);
    float lighting = 0.25 + value * (.5 + .75*tod);
    vec4 color = texture(p3d_Texture0, texcoord) * p3d_ColorScale;
    color.rgb *= lighting;
    fragColor = color;
}
