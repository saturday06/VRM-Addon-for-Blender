in vec3 position;
uniform mat4 depthMVP;
uniform mat4 obj_matrix;

void main() {
    gl_Position = depthMVP * obj_matrix * vec4(position, 1);
}
