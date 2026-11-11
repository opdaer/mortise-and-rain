# ARCHITECTURE CONTRACT — 《墨雨天工 (Mortise & Rain)》

## 1. Scale, Coordinate System & Zero-Asset Mandate
- **Single-File Self-Contained**: `index.html` only (`Three.js r160` ES module `importmap` + custom GLSL shaders + procedural Web Audio API). **0 external images, 0 external 3D models, 0 external audio files, 0 external fonts.**
- **Metric Millimeter Scale**: `1.000 unit = 1.000 meter` (`0.001 unit = 1 mm`). Right-handed Y-up coordinate system; wet courtyard slate plane anchored at `y = 0.000 m`.
- **Song Dynasty Modular System (宋《营造法式》材分制)**: Standard *cai* section `180 mm × 120 mm` (`0.180 × 0.120 m`), bay span `面阔 = 进深 = 2.640 m` (`x, z = ±1.320 m`), total apex height `5.530 m`.

## 2. Deterministic Time & Control Interface
- **`window.renderAt(t)`**: Evaluates all time-dependent subsystems deterministically at timestamp `t` (in seconds) and renders one complete frame synchronously:
  - Analytical spring disassembly state ($\zeta = 0.74$, `35 ms` topological layer stagger, mortise hard-stop `p >= 0` on lock-in)
  - Camera subtle breathing orbit (`FOV = 28°`)
  - Palace lantern pendulum sway & volumetric halo pulse (`#FF9A3C`)
  - Courtyard bamboo (`竹竿 + 竹枝 + 个字三叶`) & grounded scholar-rock (`湖石坡石`) wind-sway vertex deformation + `customDepthMaterial` swaying shadows (`竹影摇曳`)
  - Eave-corner raindrop bead chains (`屋檐四角成串滑落的雨滴粒子`), falling rain streaks, and organic concentric water puddle ripples
  - Planar mirror reflection passes + Dual post-processing pipeline (`Realistic` / `Song Ink`)
- **Auxiliary Deterministic Hooks** (also bound to interactive UI controls):
  - `window.setExplode(targetRatio, instant = false)` — sets target disassembly ratio `[0.0, 1.0]`
  - `window.setMode(mode, instant = false)` — switches `'realistic'` (Mode A) or `'ink'` (Mode B)
  - `window.setCameraPose(posArr, targetArr)` / `window.resetCameraPose()` — camera preset framing (`FOV = 28°`, ground-clamped `y >= 0.18 m`)
  - `window.getStats()` — returns `{ totalMeshes, explodableMeshes, interactiveCount, fov, cameraY, mode, inkMix, explodeTarget, explodeAvg, errorMm, seDougongScreenBounds, carpentryAudit, layers, fps }`

## 3. Structural Hierarchy (`mortise-tenon-geometry`, 181 Named Meshes)
| Layer | Traditional Elements | Elevation `Y (m)` | Carpentry Joint Geometry | Count |
| :--- | :--- | :--- | :--- | ---: |
| L0 (Grounded) | 三出陛青石台基、压阑石、斜坡垂带石踏跺、覆盆柱础 | `0.000 – 0.600` | Chamfered 3-tier ashlar bluestone plinth + sloped `垂带石` stair cheek stones & stepped `象眼` spandrels + `78×78×72 mm` column-base mortise socket (`管脚卯口`), strictly anchored (`Δ = 0`) | 13 |
| L1 | 四根宋式梭柱 | `0.546 – 3.002` | Upper-1/3 entasis taper, bottom `管脚榫`, `112 mm` column-head `十字卯口` + outer blind plugs, continuous central `馒头榫` core (`2.660 – 3.002 m`) | 4 |
| L2 | 阑额 | `2.660 – 2.840` | Complementary flared dovetail half-tenons (`燕尾半榫`, `±1.280 m`) engaging column-head mortises clear of central `馒头榫` | 4 |
| L3 | 普拍枋 | `2.840 – 2.940` | Corner half-lap cross-notches (`十字刻半搭交`) + square `馒头榫` through-mortise | 4 |
| L4 | 转角铺作 · 栌斗 | `2.940 – 3.120` | Concave *Dou-qi* scoop, bottom `馒头卯眼`, 4 raised *Dou-er* forming `十字卯槽` (`3.048 m` trough floor) | 4 |
| L5 | 第一跳华拱、泥道拱 | `3.048 – 3.243` | Smooth *Juansha* curved soffits seated flush at `3.048 m`, complementary `十字刻半卡口`, tip `暗销凸榫` | 8 |
| L6 | 外跳交互斗、内跳散斗、中心齐心斗 | `3.218 – 3.338` | Seated flush at `3.218 m`; bottom pin mortises + cross/single/45°-diagonal upper mortise troughs (`3.290 m` trough floor) | 20 |
| L7 | 瓜子令拱、第二跳斜华拱、批竹耍头 | `3.290 – 3.512` | Flush `3.290 m` trough seating (`0.00 mm` offset), exact `x = -0.340 m` stepped `3.390 m` cradle + lock mortise for Song *Pizhu* beveled `耍头` (`3.00 mm` clear under `撩檐槫`) | 16 |
| L8 | 令拱散斗、耍头齐心交互斗 | `3.422 – 3.638` | `98 mm` purlin-bearing single troughs (`3.491 m` floor) & `100 mm` 45° corner-beam cradle slots (`3.578 m` floor) | 20 |
| L9 | 撩檐槫（附生头木）、平槫、太平梁、雷公柱 | `3.491 – 4.976` | Curved Song `生头木` riser strip tracking *Fanyu* eave lift, `3.945 m` `平槫` & stepped-collar `太平梁`, hollow-mortised `雷公柱` & suspended `#FF9A3C` palace lantern (`>= 8.64 mm` sheathing soffit clearance) | 11 |
| L10 | 老角梁（大角梁）、子角梁（附檐角风铎） | `3.580 – 4.161` | Smooth lofted profile seated flush (`3.580 m`) in `耍头齐心交互斗`, clearing `平槫` (`+48.41 mm`) & `撩檐槫` (`+17.0 mm`), stepped scarf-lap upturned *Fanyu* `子角梁` | 8 (+4) |
| L11 | 圆椽、飞椽（飞子） | `3.377 – 4.391` | Non-intersecting cylindrical `圆椽` seated on `平槫` & `生头木` + square `飞椽` beneath curved roof sheathing (`0` penetrations) | 40 |
| L12 | 望板、筒板瓦当滴水瓦垄、垂脊、翼角脊饰、攒尖宝顶 | `3.396 – 5.530` | Watertight perimeter-capped Song *Juzhe* (`举折`) + *Fanyu* (`反宇`) sheathing, `交戗`-trimmed barrel/pan tiles, round *Wadang*, pointed *Dishui*, hip ridges & hollow-socketed lotus finial | 29 |
| **Total** | **Independent Named Architectural Meshes** | | **168 Explodable Wood/Tile Meshes + 13 Grounded Stone Meshes (+ 5 Interactive Props)** | **181 (+5)** |

## 4. Analytical Spring Physics (`exploded-animation-spring`)
- Analytical underdamped step response with damping ratio $\zeta = 0.74$, $\omega_n = 7.6\text{ rad/s}$, $\omega_d = \omega_n\sqrt{1-\zeta^2}$:
  $$p(\tau) = p_1 + e^{-\zeta\omega_n\tau}\!\left(\Delta_0\cos(\omega_d\tau) + \frac{v_0 + \zeta\omega_n\Delta_0}{\omega_d}\sin(\omega_d\tau)\right)$$
- **Topological Stagger (`35 ms / layer`), Vertical Plumb Axis & Mortise Hard-Stop**:
  - Disassembly (`target > current`): outer-to-inner (`delay = (12 - layer) * 0.035 s`) along monotonic plumb/radial carpentry axes, guaranteeing zero static, exploded, or mid-flight interpenetrations while preserving live slider momentum.
  - Assembly (`target < current`): inner-to-outer (`delay = (layer - 1) * 0.035 s`) with physical mortise shoulder hard-stop (`p >= 0` at `target = 0`) so components never over-penetrate into bearing troughs.

## 5. Dual Rendering Pipeline & Banned Defaults
- **Strict Palette**: Aged Chinese Fir `#5C3A21` / Chestnut `#3D2616`; Glazed Slate-Cyan Tile `#2B373D`; Rain-Night Mist `#0F171A`; Xuan Paper `#EAE3D2`; Warm Palace Lantern `#FF9A3C`. Zero tourist red/green, zero purple/blue neon.
- **Mode A (Rain Night Realistic)**: Quarter-sawn 3D wood-ring FBM (`clearcoat: 0.35, roughness: 0.42`) & bush-hammered running-bond ashlar bluestone (`剁斧青石`) with Mikkelsen screen-space surface-gradient normal relief, wet glazed tiles (`roughness: 0.18`), 4× MSAA dual-plane mirror reflections (`y = 0.000` courtyard & `y = 0.4805` plinth) with 5-tap wet-slate roughness prefiltering, raindrop ripples & 2-layer eave-corner capillary wave trains, IGN-rotated PCSS soft shadows, volumetric `#FF9A3C` lantern glow, swaying bamboo shadows (`竹影摇曳`), dynamic-DPR `1.35×` HDR supersampling + 4-tap RGSS + post-AgX Edge-Directed FXAA.
- **Mode B (Song Dynasty Ink & Blue-Green Scroll)**: Smooth transition (`inkMix`) to Structure-Tensor **8-sector Anisotropic Kuwahara** painterly filter + mineral azurite/malachite (`石青/石绿`) & unified cool sumi bluestone remap (scene lights neutralized & planar mirror reflections faded cleanly to `0` at `inkMix = 1.0`, bypassing unused reflection/FXAA passes for `>250 FPS`) + domain-warped bark-fiber Xuan paper texture + waterside ripple brushwork (`远水烟波`) + depth-modulated **Sobel/DoG Feibai dry-brush ink outlines**.

## 6. Procedural Zen Audio (`procedural-zen-audio`)
- 100% Web Audio API physical modeling with active polyphony voice-stealing caps: deterministic PRNG continuous rain-on-tile & bamboo-leaf filtered noise + ceramic droplet pings; timber-volume-pitched (`f0 ∝ V^-0.24`, `145 – 980 Hz`) hybrid **sample-accurate fractional-delay Karplus-Strong waveguide + orthotropic modal woodblock** mortise-tenon knocks on layer movement; Just-Intonation pentatonic (`宫商角徵羽`) Guqin harmonics across all 4 corner wind bells and mode switches.
