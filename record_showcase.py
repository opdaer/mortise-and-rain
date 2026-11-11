r"""
Deterministic 1920x1080 @ 60fps Showcase Video & Synchronized 48kHz Zen Audio Recorder
for 《墨雨天工 · Mortise & Rain》 (index.html).
"""
import os
import sys
import math
import json
import time
import wave
import http.server
import socketserver
import threading
import subprocess
import numpy as np
from playwright.sync_api import sync_playwright

PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_WAV  = os.path.join(PROJ_DIR, "mortise_and_rain_zen_18s.wav")
OUT_MP4  = os.path.join(PROJ_DIR, "mortise_and_rain_x_showcase_18s.mp4")

FPS = 60
DUR = 18.0
TOTAL_FRAMES = int(round(DUR * FPS))
SR = 48000


def smoothstep(e0: float, e1: float, x: float) -> float:
    u = max(0.0, min(1.0, (x - e0) / max(1e-6, e1 - e0)))
    return u * u * (3.0 - 2.0 * u)


def fft_bandpass(x: np.ndarray, f_lo: float, f_hi: float, sr: int = SR) -> np.ndarray:
    n = len(x)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, d=1.0 / sr)
    bw_lo = max(20.0, f_lo * 0.35)
    bw_hi = max(40.0, f_hi * 0.30)
    low_ramp = np.clip((freqs - (f_lo - bw_lo)) / bw_lo, 0.0, 1.0)
    high_ramp = 1.0 - np.clip((freqs - f_hi) / bw_hi, 0.0, 1.0)
    mask = (low_ramp * low_ramp * (3.0 - 2.0 * low_ramp)) * (high_ramp * high_ramp * (3.0 - 2.0 * high_ramp))
    return np.fft.irfft(spec * mask, n=n)


def synthesize_mortise_zen_wav(wav_path: str):
    """
    Sample-accurate 48kHz 24-bit/16-bit stereo rendition of ZenAudioEngine:
      - Paul Kellet pink-noise rain on glazed tiles (880Hz) & swaying bamboo leaves (3250Hz LFO)
        (gently ducked during Song Ink scroll mode 8.0s-15.5s so Guqin & joinery knocks shine!)
      - Ceramic eave-droplet upward chirps
      - 12-layer (35ms topological stagger) Karplus-Strong waveguide + orthotropic modal woodblock
        [1.0, 2.756, 5.404] mortise-tenon knocks at t=2.50s (disassembly) and t=10.20s (lock-in assembly)
      - Just-Intonation pentatonic Guqin harmonics (宫商角徵羽) on mode transitions & wind bells
    """
    n_samp = int(round(DUR * SR))
    t_arr = np.arange(n_samp, dtype=np.float64) / SR
    rng = np.random.default_rng(20261111)

    stereo = np.zeros((n_samp, 2), dtype=np.float64)

    # 1. Stereo Rain-on-Tile & Bamboo-Leaf Ambience (modulated smoothly by uInkMix)
    ink_env = np.zeros(n_samp, dtype=np.float64)
    for i, t in enumerate(t_arr):
        if t < 7.60:
            ink = 0.0
        elif t < 9.60:
            ink = smoothstep(7.60, 9.60, t)
        elif t < 14.80:
            ink = 1.0
        elif t < 16.60:
            ink = 1.0 - smoothstep(14.80, 16.60, t)
        else:
            ink = 0.0
        ink_env[i] = ink

    rain_env = 1.0 - 0.52 * ink_env  # Quieter poetic mist in Song Ink Scroll mode

    for ch in range(2):
        white = rng.uniform(-1.0, 1.0, n_samp)
        tile_sig = fft_bandpass(white, 540.0, 1420.0, SR) * 0.040
        leaf_mod = 0.78 + 0.22 * np.sin(2.0 * np.pi * 0.16 * t_arr + ch * 1.1)
        leaf_sig = fft_bandpass(white, 2250.0, 4650.0, SR) * 0.024 * leaf_mod
        stereo[:, ch] += (tile_sig + leaf_sig) * rain_env

    # 2. Ceramic Eave-Corner Water Droplet Chirps
    drop_t = 0.32
    while drop_t < DUR - 0.25:
        idx0 = int(drop_t * SR)
        d_len = int(0.068 * SR)
        if idx0 + d_len < n_samp:
            lt = np.arange(d_len, dtype=np.float64) / SR
            base_f = float(rng.uniform(1480.0, 2750.0))
            f_inst = base_f * (0.84 + 0.50 * (lt / 0.045).clip(0.0, 1.0))
            phase = 2.0 * np.pi * np.cumsum(f_inst) / SR
            env = np.minimum(lt / 0.004, 1.0) * np.exp(-lt / 0.018)
            pan = float(rng.uniform(0.25, 0.75))
            atten = 1.0 - 0.65 * ink_env[idx0]
            sig = np.sin(phase) * env * 0.042 * atten
            stereo[idx0:idx0 + d_len, 0] += sig * math.sqrt(1.0 - pan)
            stereo[idx0:idx0 + d_len, 1] += sig * math.sqrt(pan)
        drop_t += float(rng.uniform(0.24, 0.58))

    # 3. Helper: Karplus-Strong Waveguide + Orthotropic Modal Woodblock [1.0, 2.756, 5.404]
    def add_wood_knock(t_sec: float, volume_m3: float, is_locking: bool, gain_scale: float = 1.0, pan: float = 0.5):
        idx0 = int(round(t_sec * SR))
        dur_k = 0.26
        n_k = int(dur_k * SR)
        if idx0 < 0 or idx0 >= n_samp:
            return
        n_fit = min(n_k, n_samp - idx0)
        lt = np.arange(n_fit, dtype=np.float64) / SR

        v_c = max(0.0008, min(0.25, volume_m3))
        f0 = max(145.0, min(880.0, 152.0 * (v_c ** -0.24))) * (1.0 if is_locking else 1.08)

        # Karplus-Strong physical waveguide burst
        period = max(8, int(round(SR / f0)))
        ks = np.zeros(n_fit, dtype=np.float64)
        burst = rng.uniform(-1.0, 1.0, min(period, n_fit)) * np.hanning(min(period, n_fit))
        ks[:len(burst)] = burst
        damp = 0.986 if is_locking else 0.982
        for i in range(period, n_fit):
            ks[i] = damp * 0.5 * (ks[i - period] + ks[i - period + 1])
        ks = fft_bandpass(ks, max(90.0, f0 * 0.75), min(6000.0, f0 * 1.85), SR) * 0.34

        # Orthotropic free-bar woodblock partials (1 : 2.756 : 5.404)
        modes = [1.0, 2.756, 5.404]
        gains = [0.22, 0.105, 0.042]
        decays = [0.125, 0.052, 0.024]
        modal = np.zeros(n_fit, dtype=np.float64)
        for m_idx, (ratio, g, dec) in enumerate(zip(modes, gains, decays)):
            f_curve = f0 * ratio * (1.0 + 0.03 * np.exp(-lt / 0.008))
            ph = 2.0 * np.pi * np.cumsum(f_curve) / SR
            wave_m = np.arcsin(np.sin(ph)) * (2.0 / np.pi) if m_idx == 0 else np.sin(ph)
            env_m = np.minimum(lt / 0.0022, 1.0) * np.exp(-lt / dec)
            modal += wave_m * env_m * g

        voice = (ks + modal) * np.exp(-lt / 0.19) * gain_scale
        stereo[idx0:idx0 + n_fit, 0] += voice * math.sqrt(1.0 - pan)
        stereo[idx0:idx0 + n_fit, 1] += voice * math.sqrt(pan)

    # Disassembly cascade at t = 2.50s (outer-to-inner L12 -> L1, 35ms topological stagger)
    for layer in range(12, 0, -1):
        delay = (12 - layer) * 0.038
        vol = 0.06 / max(1, layer)
        pan = 0.30 + 0.40 * ((layer % 5) / 4.0)
        add_wood_knock(2.50 + delay, vol, is_locking=False, gain_scale=0.72, pan=pan)

    # Hover inspection subtle timber tap at t = 5.65s
    add_wood_knock(5.65, 0.016, is_locking=True, gain_scale=0.65, pan=0.62)

    # Assembly lock-in cascade at t = 10.20s (inner-to-outer L1 -> L12 + resonant mortise shoulder lock!)
    for layer in range(1, 13):
        delay = (layer - 1) * 0.040
        vol = 0.075 / max(1, layer)
        pan = 0.32 + 0.36 * (((12 - layer) % 5) / 4.0)
        # Initial motion + crisp mortise shoulder lock-in (~0.52s after layer release)
        add_wood_knock(10.20 + delay, vol * 0.7, is_locking=False, gain_scale=0.45, pan=pan)
        add_wood_knock(10.74 + delay, vol, is_locking=True, gain_scale=0.82, pan=pan)

    # 4. Just-Intonation Pentatonic Guqin Harmonics (宫商角徵羽)
    pentatonic_hz = [196.0, 220.5, 245.0, 294.0, 330.75, 392.0, 441.0, 490.0, 588.0]

    def add_guqin_harmonic(t_sec: float, note_idx: int, amp_scale: float = 1.0, pan: float = 0.5):
        idx0 = int(round(t_sec * SR))
        dur_g = 3.4
        n_g = int(dur_g * SR)
        if idx0 < 0 or idx0 >= n_samp:
            return
        n_fit = min(n_g, n_samp - idx0)
        lt = np.arange(n_fit, dtype=np.float64) / SR
        freq = pentatonic_hz[note_idx % len(pentatonic_hz)]

        partials = [1.0, 2.0, 3.002, 4.005]
        amps = [0.145, 0.105, 0.052, 0.022]
        durs = [3.1, 2.3, 1.5, 0.95]
        sig = np.zeros(n_fit, dtype=np.float64)
        for p, a, d in zip(partials, amps, durs):
            vib = 1.0 + 0.0032 * np.sin(2.0 * np.pi * 1.15 * lt) * np.exp(-lt / 1.8)
            ph = 2.0 * np.pi * np.cumsum(freq * p * vib) / SR
            env = np.minimum(lt / 0.015, 1.0) * np.exp(-lt / (d * 0.42))
            sig += np.sin(ph) * env * a

        # Warm wooden soundboard body resonance around 220 Hz
        sig = sig + 0.45 * fft_bandpass(sig, 150.0, 340.0, SR)
        sig *= amp_scale
        stereo[idx0:idx0 + n_fit, 0] += sig * math.sqrt(1.0 - pan)
        stereo[idx0:idx0 + n_fit, 1] += sig * math.sqrt(pan)

    # Poetic musical cues synced to visual acts:
    add_guqin_harmonic(0.28, 3, amp_scale=0.82, pan=0.45)   # Opening Rain Night lantern reflection
    add_guqin_harmonic(7.62, 5, amp_scale=0.95, pan=0.42)   # Song Ink Scroll transformation chord (徵 + 宫)
    add_guqin_harmonic(7.86, 7, amp_scale=0.78, pan=0.60)
    add_guqin_harmonic(11.45, 8, amp_scale=0.80, pan=0.52)  # Assembled Song scroll lock-in resonance
    add_guqin_harmonic(14.82, 4, amp_scale=0.85, pan=0.48)  # Return to Rain Night reflections

    # Smooth stereo room tail + click-free loop fades & normalize to ~ -16.5 LUFS (-1.5 dBFS peak)
    fade_in = np.minimum(t_arr / 0.20, 1.0)
    fade_out = np.minimum((DUR - t_arr) / 0.35, 1.0)
    stereo *= (fade_in * fade_out)[:, None]

    peak = float(np.max(np.abs(stereo)))
    if peak > 1e-8:
        stereo = stereo * (0.78 / peak)
    stereo = np.tanh(stereo * 1.12) / np.tanh(1.12) * 0.84

    pcm16 = np.clip(np.round(stereo * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm16.tobytes())
    print(f"[Audio] Wrote synchronized 48kHz stereo Zen WAV -> {wav_path}")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJ_DIR, **kwargs)

    def log_message(self, format, *args):
        pass


def start_local_server():
    httpd = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def main():
    synthesize_mortise_zen_wav(OUT_WAV)

    httpd, port = start_local_server()
    url = f"http://127.0.0.1:{port}/index.html"
    print(f"[Server] Serving {PROJ_DIR} at {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=True,
                args=[
                    "--use-angle=d3d11",
                    "--enable-webgl",
                    "--ignore-gpu-blocklist",
                    "--disable-gpu-vsync",
                ],
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
            )
            page = context.new_page()

            console_errors = []
            page.on("pageerror", lambda err: console_errors.append(str(err)))
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_function("typeof window.renderAt === 'function' && typeof window.getStats === 'function'", timeout=30000)

            stats0 = page.evaluate("window.renderAt(0.0)")
            print("[QA Audit] Initial getStats():", json.dumps({
                "totalMeshes": stats0["totalMeshes"],
                "explodableMeshes": stats0["explodableMeshes"],
                "errorMm": stats0["errorMm"],
                "roofPiercingVertices": stats0["carpentryAudit"]["roofPiercingVertices"],
                "stairPlinthPenetrations": stats0["carpentryAudit"]["stairPlinthPenetrations"],
            }))
            assert stats0["totalMeshes"] == 181, f"Expected 181 total meshes, got {stats0['totalMeshes']}"
            assert stats0["carpentryAudit"]["roofPiercingVertices"] == 0
            assert len(console_errors) == 0, f"Console errors detected: {console_errors}"

            # Set audio badge text to ON for authentic showcase appearance
            page.evaluate("document.getElementById('audio-label').textContent = '声境 · ZEN AUDIO ON';")

            temp_video = os.path.join(PROJ_DIR, "mortise_video_track_tmp.mp4")
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "image2pipe", "-vcodec", "mjpeg", "-r", str(FPS), "-i", "-",
                "-c:v", "libx264", "-preset", "slow", "-crf", "15",
                "-pix_fmt", "yuv420p",
                temp_video,
            ]
            proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

            t0_wall = time.time()
            exploded_triggered = False
            assembled_triggered = False

            for f in range(TOTAL_FRAMES):
                t = f / float(FPS)

                # Trigger analytical spring disassembly at t = 2.50s and lock-in assembly at t = 10.20s
                if not exploded_triggered and t >= 2.50:
                    page.evaluate("window.setExplode(1.0, false)")
                    exploded_triggered = True
                if not assembled_triggered and t >= 10.20:
                    page.evaluate("window.setExplode(0.0, false)")
                    assembled_triggered = True

                # Smooth uInkMix cross-dissolves:
                #   0.00s - 7.60s  : 0.0 (Rain Night PBR + Planar Mirror Reflections)
                #   7.60s - 9.60s  : 0.0 -> 1.0 (Mid-air transformation into Song Dynasty Ink Scroll!)
                #   9.60s - 14.80s : 1.0 (Song Ink Scroll assembly & showcase)
                #   14.80s - 16.60s: 1.0 -> 0.0 (Dissolve back to Rain Night for seamless X loop!)
                if t < 7.60:
                    ink = 0.0
                elif t < 9.60:
                    ink = smoothstep(7.60, 9.60, t)
                elif t < 14.80:
                    ink = 1.0
                elif t < 16.60:
                    ink = 1.0 - smoothstep(14.80, 16.60, t)
                else:
                    ink = 0.0

                # Smooth cinema camera orbit: starts & ends at exact same pose (az=0.465) for seamless X loop!
                loop_phase = math.sin(math.pi * (t / DUR))  # 0.0 at t=0, 1.0 at t=9s, 0.0 at t=18s!
                zoom_in = smoothstep(4.20, 6.20, t) * (1.0 - smoothstep(11.80, 14.20, t))

                page.evaluate(
                    """([t, ink, loopPhase, zoomIn]) => {
                        window.setInkMix(ink);
                        const expAvg = (window.getStats().explodeAvg || 0);
                        const az = 0.465 + 0.52 * loopPhase;
                        const baseR = 19.8 + (25.6 - 19.8) * expAvg - 2.6 * zoomIn;
                        const camY  = 2.82 + (5.55 - 2.82) * expAvg + 0.14 * Math.sin(t * 0.70);
                        const tgtY  = 1.36 + (5.15 - 1.36) * expAvg;
                        window.setCameraPose(
                            [Math.sin(az) * baseR, camY, Math.cos(az) * baseR],
                            [0.0, tgtY, 0.0]
                        );
                        window.renderAt(t);
                    }""",
                    [t, ink, loop_phase, zoom_in],
                )

                jpg_bytes = page.screenshot(type="jpeg", quality=98)
                proc.stdin.write(jpg_bytes)

                if (f + 1) % 180 == 0 or f == TOTAL_FRAMES - 1:
                    elapsed = time.time() - t0_wall
                    print(f"[Render] Frame {f+1}/{TOTAL_FRAMES} (t={t:.2f}s, ink={ink:.2f}) | {((f+1)/max(0.01, elapsed)):.1f} fps")

            proc.stdin.close()
            rc = proc.wait()
            assert rc == 0, f"FFmpeg video encode failed with {rc}"

            # Save 3 QA check screenshots from the new bilingual UI!
            page.evaluate("window.setExplode(0.0, true); window.setInkMix(0.0); window.resetCameraPose(); window.renderAt(1.2);")
            page.screenshot(path=os.path.join(PROJ_DIR, "screenshots", "bilingual_qa_1_rain_night.png"))
            page.evaluate("window.setExplode(1.0, true); window.setInkMix(0.0); window.resetCameraPose(); window.renderAt(6.0);")
            page.screenshot(path=os.path.join(PROJ_DIR, "screenshots", "bilingual_qa_2_exploded.png"))
            page.evaluate("window.setExplode(0.0, true); window.setInkMix(1.0); window.resetCameraPose(); window.renderAt(13.5);")
            page.screenshot(path=os.path.join(PROJ_DIR, "screenshots", "bilingual_qa_3_song_ink.png"))

            assert len(console_errors) == 0, f"Console errors during render: {console_errors}"
            browser.close()

        # Mux video + synchronized 48kHz stereo Zen WAV into final H.264 + AAC 320k MP4
        mux_cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", temp_video,
            "-i", OUT_WAV,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-movflags", "+faststart",
            "-shortest",
            OUT_MP4,
        ]
        subprocess.run(mux_cmd, check=True)
        if os.path.exists(temp_video):
            os.remove(temp_video)

        mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
        print(f"[SUCCESS] Exported 1920x1080 @ 60fps Showcase MP4 -> {OUT_MP4} ({mb:.2f} MiB)")

    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
