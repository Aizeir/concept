#version 330

uniform sampler2D tex;
in vec2 texcoord;
out vec4 fragColor;
uniform bool underwater;


void main() {
    vec4 color = texture(tex, texcoord);

    if (underwater) {
        color = vec4(1.0 - color.rgb, 1);
    }
    else {
        color = vec4(color.rgb,1);
    }

    fragColor = vec4(color.rgb, 1.0);
}