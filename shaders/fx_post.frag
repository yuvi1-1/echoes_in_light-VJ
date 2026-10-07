// FX POST - Echoes in Light VJ
// snare glitch slices, kick zoom, chromatic split, woozy sway + double vision (syrup scenes),
// unsharp-mask sharpening, hat grain, build-up 16th strobe, drop flash, breakdown mood, vignette
uniform vec4 uA;   // x snare, y drop/new-song flash, z tension, w time
uniform vec4 uB;   // x hat, y kick, z breakdown, w beat position (count + phase)
uniform vec4 uC;   // x melt amount, y vocals (mid band), z bass
out vec4 fragColor;
float hash(float n){ return fract(sin(n)*43758.5453123); }
vec3 tex(vec2 p){ return texture(sTD2DInputs[0], p).rgb; }
void main(){
    vec2 uv = vUV.st;
    float t = uA.w;
    // woozy whole-frame sway (syrup scenes only)
    uv += vec2(sin(uv.y*3.0 + t*0.9), cos(uv.x*2.5 + t*0.7)) * 0.0035 * uC.x;
    // glitch: horizontal slice displacement on snares
    float slice = floor(uv.y*28.0);
    float g = step(0.55, hash(slice + floor(t*24.0))) * uA.x;
    uv.x += (hash(slice*3.7 + floor(t*31.0)) - 0.5) * 0.10 * g;
    // kick zoom punch
    vec2 c = uv - 0.5;
    uv = 0.5 + c*(1.0 - 0.035*uB.y - 0.05*uA.y);
    // chromatic split radiating from centre
    float split = 0.002 + 0.012*uA.x + 0.006*uB.y + 0.02*uA.y + 0.006*uA.z;
    vec2 dir = c*split*2.0;
    vec3 col = vec3(tex(uv + dir).r, tex(uv).g, tex(uv - dir).b);
    // unsharp mask: keeps edges crisp after trails and glow
    vec2 px = uTD2DInfos[0].res.xy;
    vec3 blur = (tex(uv + vec2(px.x,0.0)) + tex(uv - vec2(px.x,0.0)) + tex(uv + vec2(0.0,px.y)) + tex(uv - vec2(0.0,px.y))) * 0.25;
    col = max(col + (col - blur) * 1.1, 0.0);
    // double vision: drifting ghost copy, stronger with vocals (syrup scenes)
    vec2 gofs = vec2(sin(t*0.7), cos(t*0.53)) * (0.006 + 0.018*uC.y) * uC.x;
    col = max(col, tex(uv + gofs) * 0.35 * uC.x);
    // hat sparkle grain
    col += (hash(dot(uv, vec2(12.9898,78.233))*437.0 + t) - 0.5) * 0.05 * uB.x;
    // build-up: strobe on 16th notes, ramps in with tension
    float s16 = step(0.5, fract(uB.w*4.0));
    col *= 1.0 - smoothstep(0.55, 1.0, uA.z) * s16 * 0.85;
    // drop / new song: white flash
    col = mix(col, vec3(1.0), clamp(uA.y*uA.y*0.9, 0.0, 1.0));
    // breakdown: moody, desaturated
    float l = dot(col, vec3(0.299,0.587,0.114));
    col = mix(col, vec3(l)*vec3(0.75,0.85,1.0), uB.z*0.55);
    // vignette
    col *= 1.0 - 1.1*dot(c,c);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
