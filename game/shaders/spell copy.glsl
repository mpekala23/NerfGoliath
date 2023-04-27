uniform vec2 pos;

void mainImage(out vec4 fragColor, in vec2 fragCoord) {

    // Normalized pixel coordinates (from 0 to 1)
    vec2 uv = fragCoord/iResolution.xy;
    vec2 npos = pos/iResolution.xy;

    // Position of fragment relative to center of screen
    vec2 rpos = npos - uv;
    // Adjust y by aspect ratio
    rpos.y /= iResolution.x/iResolution.y;

    // How far is the current pixel from the origin (0, 0)
    float distance = length(rpos);
    // Use an inverse 1/distance to set the fade
    float scale = 0.02;
    float fade = 6.6;
    float strength = pow(1.0 / distance * scale, fade);

    // Fade our orange color
    vec3 color = strength * vec3(1.0, 0.5, 0);

    // Tone mapping
    color = 1.0 - exp( -color );

    // Only disturb what we want
    float alpha = distance > 0.1 ? 0.0 : 1.0;

    // Output to the screen
    fragColor = vec4(color, alpha);
}