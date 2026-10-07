// Syrup melt: content slowly drips downward in streaks + woozy sideways sway
uniform vec4 uM;  // x melt, y time, z bass, w kick
out vec4 fragColor;
float h(float n){ return fract(sin(n)*43758.5453); }
float vnoise(float x){ float i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f); return mix(h(i), h(i+1.0), f); }
void main(){
    vec2 uv = vUV.st;
    float m = uM.x, t = uM.y;
    float streak = vnoise(uv.x*38.0 + t*0.15);            // per-column drip speed
    float drip = m * (0.0015 + 0.006*streak*streak) * (1.0 + 1.5*uM.z);
    uv.y += drip;                                          // pull content down
    uv.x += sin(uv.y*9.0 + t*1.3) * 0.0025 * m * (1.0 + uM.w*2.0);   // sway
    vec4 c = texture(sTD2DInputs[0], uv);
    // slight vertical smear so drips look liquid
    c = max(c, texture(sTD2DInputs[0], uv + vec2(0.0, 0.004*m*streak)) * 0.9);
    fragColor = TDOutputSwizzle(c);
}
