uniform vec3 lightpos;
uniform vec3 viewDirection;
uniform vec3 viewUpDirection;
uniform mat4 viewProjectionMatrix;
uniform mat4 normalWorldToViewMatrix;
uniform float is_outline;
uniform float is_cutout;

uniform float CutoffRate;
uniform float BumpScale;
uniform float ReceiveShadowRate;
uniform float ShadeShift;
uniform float ShadeToony;
uniform float RimLightingMix;
uniform float RimFresnelPower;
uniform float RimLift;
uniform float ShadingGradeRate;
uniform float LightColorAttenuation;
uniform float IndirectLightIntensity;
uniform float OutlineWidth;
uniform float OutlineScaleMaxDistance;
uniform float OutlineLightingMix;
uniform float UV_Scroll_X;
uniform float UV_Scroll_Y;
uniform float UV_Scroll_Rotation;
uniform float OutlineWidthMode;
uniform float OutlineColorMode;

uniform float isDebug;

uniform vec4 DiffuseColor;
uniform vec4 ShadeColor;
uniform vec4 EmissionColor;
uniform vec4 RimColor;
uniform vec4 OutlineColor;

uniform sampler2D depth_image;
uniform sampler2D MainTexture;
uniform sampler2D ShadeTexture;
uniform sampler2D NormalmapTexture;
uniform sampler2D ReceiveShadow_Texture;
uniform sampler2D ShadingGradeTexture;
uniform sampler2D Emission_Texture;
uniform sampler2D SphereAddTexture;
uniform sampler2D RimTexture;
uniform sampler2D OutlineWidthTexture;
uniform sampler2D UV_Animation_Mask_Texture;

in vec2 uv;
in vec3 n;
in vec3 tangent;
in vec3 bitangent;
in vec4 shadowCoord;

out vec4 FragColor;

vec4 color_linearlize(vec4 color) {
    vec4 linear_color = color;
    for (int i = 0; i < 3; i++) {
        if (linear_color[i] <= 0.04045) {
            linear_color[i] = linear_color[i] / 12.92;
        } else {
            linear_color[i] = pow((linear_color[i] + 0.055) / 1.055, 2.4);
        }
    }
    for (int i = 0; i < 3; i++) {
        linear_color[i] = pow(color[i], 2.2);
    }
    return linear_color;
}

vec4 color_sRGBlize(vec4 color) {
    vec4 sRGB_color = color;
    for (int i = 0; i < 3; i++) {
        if (sRGB_color[i] <= 0.0031308) {
            sRGB_color[i] = sRGB_color[i] * 12.92;
        } else {
            sRGB_color[i] = 1.055 * pow(sRGB_color[i], 1.0 / 2.4) - 0.055;
        }
    }
    for (int i = 0; i < 3; i++) {
        sRGB_color[i] = pow(color[i], 1 / 2.2);
    }
    return sRGB_color;
}

void main() {
    // clang-format off
    float debug_unused_float = 0.00001 * (
        CutoffRate +
        BumpScale +
        ReceiveShadowRate +
        ShadeShift +
        ShadeToony +
        RimLightingMix +
        RimFresnelPower +
        RimLift +
        ShadingGradeRate +
        LightColorAttenuation +
        IndirectLightIntensity +
        OutlineWidth +
        OutlineScaleMaxDistance +
        OutlineLightingMix +
        UV_Scroll_X +
        UV_Scroll_Y +
        UV_Scroll_Rotation +
        OutlineWidthMode +
        OutlineColorMode
    );
    vec4 debug_unused_tex =
        // texture( depth_image,uv) +
        texture(MainTexture, uv) +
        texture(ShadeTexture, uv) +
        texture(NormalmapTexture, uv) +
        texture(ReceiveShadow_Texture, uv) +
        texture(ShadingGradeTexture, uv) +
        texture(Emission_Texture, uv) +
        texture(SphereAddTexture, uv) +
        texture(RimTexture, uv) +
        texture(OutlineWidthTexture, uv) +
        texture(UV_Animation_Mask_Texture, uv);
    vec4 debug_unused_vec4 =
        vec4(0.00001) *
        debug_unused_tex *
        debug_unused_float *
        shadowCoord *
        vec4(viewUpDirection, 1);
    mat4 debug_unused_mat4 = mat4(0.00001) * normalWorldToViewMatrix;
    debug_unused_vec4 *=
        DiffuseColor +
        ShadeColor +
        EmissionColor +
        RimColor +
        OutlineColor +
        vec4(tangent + bitangent + viewDirection + lightpos, 1);
    debug_unused_vec4 = debug_unused_mat4 * debug_unused_vec4;
    // clang-format on

    // start true main
    float const_less_val = 0.00001;
    vec3 light_dir = normalize(lightpos);
    vec2 mainUV = uv;
    vec4 col = texture(MainTexture, mainUV);
    if (is_cutout == 1 && col.a * DiffuseColor.a < CutoffRate)
        discard;

    vec3 output_color = vec3(0, 0, 0);
    vec3 outline_col = col.rgb;

    vec3 mod_n = n;
    vec3 normalmap = texture(NormalmapTexture, mainUV).rgb * 2 - 1;
    for (int i = 0; i < 3; i++) {
        mod_n[i] = dot(vec3(tangent[i], bitangent[i], n[i]), normalmap);
    }
    mod_n = normalize(mod_n);
    float dotNL = dot(light_dir, mod_n);

    float is_shine = dotNL;
    float shadow_bias = 0.02 * tan(acos(dot(n, light_dir)));
    if (texture(depth_image, shadowCoord.xy).z < shadowCoord.z - shadow_bias) {
        is_shine = 0;
    }

    // Decide albedo color rate from Direct Light
    float shadingGrade =
        1 - ShadingGradeRate * (1.0 - texture(ShadingGradeTexture, mainUV).r);
    float lightIntensity = dotNL;
    lightIntensity = lightIntensity * 0.5 + 0.5;
    lightIntensity = lightIntensity * is_shine;
    lightIntensity = lightIntensity * shadingGrade;
    lightIntensity = lightIntensity * 2.0 - 1.0;
    float maxIntensityThreshold = mix(1, ShadeShift, ShadeToony);
    float minIntensityThreshold = ShadeShift;
    float lerplightintensity = (lightIntensity - minIntensityThreshold) /
        max(const_less_val, (maxIntensityThreshold - minIntensityThreshold));
    lightIntensity = clamp(lerplightintensity, 0.0, 1.0);

    vec4 lit = color_linearlize(DiffuseColor) *
        color_linearlize(texture(MainTexture, mainUV));
    vec4 shade = color_linearlize(ShadeColor) *
        color_linearlize(texture(ShadeTexture, mainUV));
    vec3 albedo = mix(shade.rgb, lit.rgb, lightIntensity);

    output_color = albedo;
    outline_col = albedo;

    // Direct light
    vec3 lighting = vec3(1.0);  // light color
    lighting = mix(lighting,
        vec3(max(const_less_val, max(lighting.r, max(lighting.g, lighting.b)))),
        LightColorAttenuation);
    // lighting *= min(0,dotNL) +1;
    // lighting *= is_shine;
    output_color *= lighting;
    outline_col *= lighting;

    //未実装@Indirect Light

    // parametric rim
    vec3 p_rim_color =
        pow(clamp(1.0 - dot(mod_n, viewDirection) + RimLift, 0.0, 1.0),
            RimFresnelPower) *
        color_linearlize(RimColor).rgb *
        color_linearlize(texture(RimTexture, mainUV)).rgb;
    output_color += p_rim_color;

    // matcap
    vec3 world_cam_up = viewUpDirection;
    vec3 world_view_up = normalize(
        world_cam_up - viewDirection * dot(viewDirection, world_cam_up));
    vec3 world_view_left = normalize(cross(world_view_up, viewDirection));
    vec2 matcap_uv =
        vec2(dot(world_view_left, mod_n), dot(world_view_up, mod_n)) * 0.5 +
        0.5;
    vec4 matcap_color = color_linearlize(texture(SphereAddTexture, matcap_uv));

    output_color += matcap_color.rgb;

    // emission
    vec3 emission = color_linearlize(texture(Emission_Texture, mainUV)).rgb *
        color_linearlize(EmissionColor).rgb;
    output_color += emission;

    if (is_outline == 0) {
        FragColor = color_sRGBlize(vec4(output_color, lit.a));
    } else {  // is_outline in (1,2)//world or screen
        if (OutlineColorMode == 0) {
            FragColor = color_sRGBlize(
                color_linearlize(OutlineColor) + debug_unused_vec4);
        } else {
            FragColor = color_sRGBlize(vec4(color_linearlize(OutlineColor).rgb *
                    color_linearlize(
                        vec4(
                            mix(vec3(1.0), outline_col, OutlineLightingMix), 1))
                        .rgb,
                1));
        }
    }
    if (isDebug == 1.0) {
        FragColor = vec4(mod_n * 0.5 + 0.5, lit.a);
        // FragColor = vec4(n*0.5+0.5,lit.a);
    }
}
