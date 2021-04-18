in vec3 position;
in vec3 normal;
in vec2 rawuv;
in vec3 rawtangent;
out vec4 posa;
out vec2 uva;
out vec3 na;
out vec3 rtangent;

void main() {
    na = normal;
    uva = rawuv;
    gl_Position = vec4(position, 1);
    posa = gl_Position;
    rtangent = rawtangent;
}
