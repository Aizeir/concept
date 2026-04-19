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
    vec3 color = texture(p3d_Texture0, texcoord).rgb * p3d_ColorScale.rgb * lighting;

    // Sélection
    if (selection[3] == 1 && block_pos == ivec3(selection.xyz)) {
        color *= 0.8;
    }

    fragColor = vec4(color.rgb, 1.0);
}
