#version 140

in vec2 texcoord;
in vec3 world_normal;
flat in ivec3 block_pos;
in int block_id;

out vec4 fragColor;

uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform vec3 light_direction;
uniform vec4 selection;

void main() {
    float value = max(0, (dot(light_direction, world_normal)+1)/2);
    float lighting = 0.25 + value * 1.5;
    vec4 color = texture(p3d_Texture0, texcoord) * p3d_ColorScale;
    color.rgb *= lighting;
    // Sélection
    if (selection[3] != -1 && block_pos == ivec3(selection.xyz)) {
        if (selection[3] > 0)
            color.rgb *= (.2 + pow(1-selection[3],.5)*.8);
        else if (selection[3] == 0)
            color.rgb *= .8;
    }

    fragColor = color;
}
