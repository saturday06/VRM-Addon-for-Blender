layout(triangles) in;
layout(triangle_strip, max_vertices = 3) out;
uniform mat4 depthMVP;
uniform mat4 projectionMatrix;
uniform mat4 viewProjectionMatrix;
uniform mat4 normalWorldToViewMatrix;
uniform float aspect;
uniform mat4 obj_matrix;
uniform float is_outline;
uniform float OutlineWidthMode;

uniform float OutlineWidth;
uniform float OutlineScaleMaxDistance;
uniform sampler2D OutlineWidthTexture;

in vec4 posa[3];
in vec2 uva[3];
in vec3 na[3];
in vec3 rtangent[3];

out vec2 uv;
out vec3 n;
out vec3 tangent;
out vec3 bitangent;
out vec4 shadowCoord;

void main() {
    // clang-format off
    mat4 biasMat4 = mat4(
        0.5, 0.0, 0.0, 0.0,
        0.0, 0.5, 0.0, 0.0,
        0.0, 0.0, 0.5, 0.0,
        0.5, 0.5, 0.5, 1.0
    );
    // clang-format on

    mat4 depthBiasMVP = biasMat4 * depthMVP;

    if (is_outline == 0) {
        for (int i = 0; i < 3; i++) {
            uv = uva[i];
            n = na[i];
            tangent = rtangent[i];
            bitangent = normalize(cross(n, tangent));
            gl_Position = viewProjectionMatrix * obj_matrix * posa[i];
            shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
            EmitVertex();
        }
        EndPrimitive();
    } else {
        if (OutlineWidthMode == 1) {  // world space outline
            for (int i = 2; i >= 0; i--) {
                uv = uva[i];
                n = na[i];
                tangent = rtangent[i];
                float outlinewidth_tex = texture(OutlineWidthTexture, uv).r;
                gl_Position = viewProjectionMatrix * obj_matrix *
                              (posa[i] + vec4(na[i], 0) * OutlineWidth *
                                             outlinewidth_tex * 0.01);
                shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                EmitVertex();
            }
            EndPrimitive();
        } else if (OutlineWidthMode == 2) {  // screen space outline
            for (int i = 2; i >= 0; i--) {
                uv = uva[i];
                n = na[i];
                tangent = rtangent[i];
                gl_Position = viewProjectionMatrix * obj_matrix * posa[i];
                vec3 view_normal =
                    normalize(mat3(normalWorldToViewMatrix) * na[i]);
                vec3 extend_dir =
                    normalize(mat3(projectionMatrix) * view_normal);
                extend_dir =
                    extend_dir * min(gl_Position.w, OutlineScaleMaxDistance);
                extend_dir.y = extend_dir.y * aspect;
                float outlinewidth_tex = texture(OutlineWidthTexture, uv).r;
                gl_Position.xy += extend_dir.xy * 0.01 * OutlineWidth *
                                  outlinewidth_tex *
                                  clamp(1 - abs(view_normal.z), 0.0, 1.0);
                shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                EmitVertex();
            }
            EndPrimitive();
        } else {  // nothing come here ...maybe.
            for (int i = 0; i < 3; i++) {
                uv = uva[i];
                n = na[i];
                tangent = rtangent[i];
                bitangent = normalize(cross(n, tangent));
                gl_Position = viewProjectionMatrix * obj_matrix * posa[i];
                shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                EmitVertex();
            }
            EndPrimitive();
        }
    }
}
