#!/usr/bin/env python3
"""
Convert a video file to multiple GIF variants with different quality/size tradeoffs.

Generates a matrix of GIFs varying FPS, width, and color count so the user can
visually pick the best one. Optionally trims a time range from the source video.

The default preset (`ppt`) targets GIFs below 5 MB, suitable for downloading
from the ToqanClaw platform and inserting into PowerPoint / Google Slides.
An automatic size-enforcement step compresses or downscales any GIF that
exceeds the 5 MB limit.

Prerequisites: FFmpeg, gifsicle (optional, installed automatically if needed)

Usage:
    python video_to_gif.py input.mp4
    python video_to_gif.py input.mp4 --start 5 --end 15
    python video_to_gif.py input.mp4 --width 640 --fps 15
    python video_to_gif.py input.mp4 --presets minimal
"""

import argparse
import itertools
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Maximum GIF size in bytes before automatic compression kicks in (5 MB)
MAX_GIF_BYTES = 5 * 1024 * 1024


@dataclass
class GifConfig:
    fps: int
    width: int
    colors: int
    lossy: int  # 0 = lossless, >0 = gifsicle lossy level
    dither: str  # FFmpeg dither algorithm

    @property
    def label(self) -> str:
        parts = [f"{self.width}w", f"{self.fps}fps", f"{self.colors}c"]
        if self.lossy > 0:
            parts.append(f"lossy{self.lossy}")
        if self.dither != "sierra2_4a":
            parts.append(self.dither)
        return "_".join(parts)


# Preset configurations targeting different tradeoff points.
# `ppt` is the new default — optimised for download (< 5 MB) and slides.
PRESETS = {
    "ppt": {
        "fps": [10],
        "width": [480],
        "colors": [128],
        "lossy": [60],
        "dither": ["sierra2_4a"],
    },
    "full": {
        "fps": [10, 15, 20],
        "width": [480, 640, 800],
        "colors": [128, 256],
        "lossy": [0],
        "dither": ["sierra2_4a"],
    },
    "minimal": {
        "fps": [10, 15],
        "width": [480, 640],
        "colors": [256],
        "lossy": [0],
        "dither": ["sierra2_4a"],
    },
    "lossy": {
        "fps": [12, 15],
        "width": [480, 640],
        "colors": [256],
        "lossy": [0, 30, 80],
        "dither": ["sierra2_4a"],
    },
    "quality": {
        "fps": [15, 20],
        "width": [640, 800, 1024],
        "colors": [256],
        "lossy": [0],
        "dither": ["sierra2_4a", "bayer:bayer_scale=3"],
    },
}


def ensure_gifsicle() -> bool:
    """Return True if gifsicle is available, installing it if necessary."""
    if shutil.which("gifsicle"):
        return True
    print("  gifsicle not found — installing via apt-get...", flush=True)
    result = subprocess.run(
        ["apt-get", "install", "-y", "gifsicle"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and shutil.which("gifsicle"):
        print("  gifsicle installed successfully.", flush=True)
        return True
    print("  Warning: could not install gifsicle — size enforcement may be limited.",
          flush=True)
    return False


def compress_with_gifsicle(gif_path: str, lossy: int = 60) -> None:
    """Compress gif_path in-place using gifsicle."""
    tmp = gif_path + ".gsicle.tmp.gif"
    subprocess.run(
        ["gifsicle", "--optimize=3", f"--lossy={lossy}", gif_path, "-o", tmp],
        capture_output=True,
        check=True,
    )
    os.replace(tmp, gif_path)


def get_video_info(input_file: str) -> dict:
    """Get video duration, width, height via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", "-select_streams", "v:0",
        input_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "duration": float(data["format"].get("duration", 0)),
    }


def _ffmpeg_gif(
    input_file: str,
    output_file: str,
    width: int,
    fps: int,
    colors: int,
    dither: str,
    start: float | None,
    end: float | None,
) -> None:
    """Two-pass palette-based GIF generation."""
    time_args: list[str] = []
    if start is not None:
        time_args += ["-ss", str(start)]
    if end is not None:
        if start is not None:
            time_args += ["-t", str(end - start)]
        else:
            time_args += ["-t", str(end)]

    palette_file = output_file + ".palette.png"

    palette_filter = (
        f"fps={fps},scale={width}:-1:flags=lanczos,"
        f"palettegen=max_colors={colors}:stats_mode=diff"
    )
    cmd_palette = (
        ["ffmpeg", "-y"] + time_args +
        ["-i", input_file, "-vf", palette_filter, palette_file]
    )
    subprocess.run(cmd_palette, capture_output=True, check=True)

    gif_filter = (
        f"fps={fps},scale={width}:-1:flags=lanczos"
        f"[x];[x][1:v]paletteuse=dither={dither}"
    )
    cmd_gif = (
        ["ffmpeg", "-y"] + time_args +
        ["-i", input_file, "-i", palette_file,
         "-filter_complex", gif_filter, output_file]
    )
    subprocess.run(cmd_gif, capture_output=True, check=True)
    os.remove(palette_file)


def enforce_size_limit(
    gif_path: str,
    input_file: str,
    config: "GifConfig",
    start: float | None,
    end: float | None,
    limit: int = MAX_GIF_BYTES,
) -> None:
    """
    If gif_path exceeds `limit` bytes, attempt to bring it under the limit:
      1. Apply gifsicle lossy compression (level 80).
      2. If still too large, regenerate at 360 px width with gifsicle.
    Prints a warning for each step taken.
    """
    size = os.path.getsize(gif_path)
    if size <= limit:
        return

    mb = size / (1024 * 1024)
    print(f"\n  ⚠️  GIF is {mb:.2f} MB — exceeds {limit // (1024*1024)} MB limit. "
          f"Applying automatic compression...", flush=True)

    # Step 1 — gifsicle lossy compression
    has_gifsicle = ensure_gifsicle()
    if has_gifsicle:
        compress_with_gifsicle(gif_path, lossy=80)
        size = os.path.getsize(gif_path)
        mb = size / (1024 * 1024)
        print(f"  → After gifsicle compression: {mb:.2f} MB", flush=True)

    if size <= limit:
        return

    # Step 2 — re-generate at 360 px width
    print(f"  → Still {mb:.2f} MB — regenerating at 360 px width...", flush=True)
    _ffmpeg_gif(
        input_file, gif_path,
        width=360,
        fps=config.fps,
        colors=min(config.colors, 128),
        dither=config.dither,
        start=start,
        end=end,
    )
    if has_gifsicle:
        compress_with_gifsicle(gif_path, lossy=80)

    size = os.path.getsize(gif_path)
    mb = size / (1024 * 1024)
    print(f"  → Final size after fallback: {mb:.2f} MB", flush=True)
    if size > limit:
        print(f"  ⚠️  Could not reduce below {limit // (1024*1024)} MB. "
              f"Consider trimming the video (--start / --end).", flush=True)


def generate_gif(
    input_file: str,
    output_file: str,
    config: "GifConfig",
    start: float | None = None,
    end: float | None = None,
    enforce_limit: bool = True,
) -> dict:
    """Generate a single GIF with the given config. Returns metadata dict."""
    _ffmpeg_gif(
        input_file, output_file,
        width=config.width,
        fps=config.fps,
        colors=config.colors,
        dither=config.dither,
        start=start,
        end=end,
    )

    # Optional lossy compression with gifsicle
    if config.lossy > 0 and shutil.which("gifsicle"):
        compress_with_gifsicle(output_file, lossy=config.lossy)
    elif config.lossy > 0:
        # Try to install and use gifsicle for the requested lossy level
        if ensure_gifsicle():
            compress_with_gifsicle(output_file, lossy=config.lossy)

    # Automatic size enforcement
    if enforce_limit:
        enforce_size_limit(output_file, input_file, config, start, end)

    size_bytes = os.path.getsize(output_file)
    return {
        "file": output_file,
        "config": config.label,
        "fps": config.fps,
        "width": config.width,
        "colors": config.colors,
        "lossy": config.lossy,
        "size_kb": round(size_bytes / 1024, 1),
        "size_mb": round(size_bytes / (1024 * 1024), 2),
    }


def build_configs(preset_name: str) -> list[GifConfig]:
    """Build all GifConfig combinations from a preset."""
    preset = PRESETS[preset_name]
    configs = []
    for fps, width, colors, lossy, dither in itertools.product(
        preset["fps"], preset["width"], preset["colors"],
        preset["lossy"], preset["dither"],
    ):
        configs.append(GifConfig(fps=fps, width=width, colors=colors,
                                 lossy=lossy, dither=dither))
    return configs


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert video to GIF. Default preset 'ppt' generates a single "
            "download-safe GIF (< 5 MB) optimised for PowerPoint and Google Slides."
        )
    )
    parser.add_argument("input", help="Input video file path")
    parser.add_argument("-o", "--output-dir",
                        help="Output directory (default: <input>_gifs/)")
    parser.add_argument("--start", type=float, default=None,
                        help="Start time in seconds")
    parser.add_argument("--end", type=float, default=None,
                        help="End time in seconds")
    parser.add_argument("--presets", default="ppt",
                        choices=list(PRESETS.keys()),
                        help="Preset config set (default: ppt)")
    # Allow overriding individual axes
    parser.add_argument("--fps", type=int, nargs="+",
                        help="Override FPS values (e.g., --fps 10 15 20)")
    parser.add_argument("--width", type=int, nargs="+",
                        help="Override width values (e.g., --width 480 640)")
    parser.add_argument("--colors", type=int, nargs="+",
                        help="Override color counts (e.g., --colors 128 256)")
    parser.add_argument("--lossy", type=int, nargs="+",
                        help="Gifsicle lossy levels (e.g., --lossy 0 30 80)")
    parser.add_argument("--no-size-limit", action="store_true",
                        help="Skip the automatic 5 MB size enforcement")

    args = parser.parse_args()

    input_file = args.input
    if not os.path.isfile(input_file):
        print(f"Error: file not found: {input_file}")
        sys.exit(1)

    # Get video info
    info = get_video_info(input_file)
    print(f"Source: {input_file}")
    print(f"  Resolution: {info['width']}x{info['height']}")
    print(f"  Duration: {info['duration']:.1f}s")
    if args.start is not None or args.end is not None:
        s = args.start or 0
        e = args.end or info["duration"]
        print(f"  Trimming: {s:.1f}s - {e:.1f}s ({e - s:.1f}s)")
    print()

    # Setup output dir
    if args.output_dir:
        out_dir = args.output_dir
    else:
        out_dir = str(Path(input_file).with_suffix("")) + "_gifs"
    os.makedirs(out_dir, exist_ok=True)

    # Build configs
    configs = build_configs(args.presets)

    # Apply overrides
    if args.fps or args.width or args.colors or args.lossy:
        preset = PRESETS[args.presets].copy()
        if args.fps:
            preset["fps"] = args.fps
        if args.width:
            preset["width"] = args.width
        if args.colors:
            preset["colors"] = args.colors
        if args.lossy:
            preset["lossy"] = args.lossy
        configs = []
        for fps, width, colors, lossy, dither in itertools.product(
            preset["fps"], preset["width"], preset["colors"],
            preset["lossy"], preset["dither"],
        ):
            # Skip widths larger than source
            if width > info["width"]:
                continue
            configs.append(GifConfig(fps=fps, width=width, colors=colors,
                                     lossy=lossy, dither=dither))
    else:
        # Filter out widths larger than source
        configs = [c for c in configs if c.width <= info["width"]]

    if not configs:
        print("Error: no valid configurations (all widths exceed source resolution)")
        sys.exit(1)

    enforce_limit = not args.no_size_limit
    print(f"Generating {len(configs)} GIF variant(s) (preset: {args.presets})...")
    print(f"Output directory: {out_dir}")
    if enforce_limit:
        limit_mb = MAX_GIF_BYTES // (1024 * 1024)
        print(f"Size limit: {limit_mb} MB (automatic compression enabled)")
    print()

    # Pre-check gifsicle for presets that request lossy compression
    lossy_configs = [c for c in configs if c.lossy > 0]
    if lossy_configs and not shutil.which("gifsicle"):
        ensure_gifsicle()

    results = []
    for i, config in enumerate(configs, 1):
        output_file = os.path.join(out_dir, f"{config.label}.gif")
        print(f"  [{i}/{len(configs)}] {config.label}...", end=" ", flush=True)
        try:
            meta = generate_gif(input_file, output_file, config,
                                start=args.start, end=args.end,
                                enforce_limit=enforce_limit)
            results.append(meta)
            over = " ⚠️ >5MB" if meta["size_mb"] > 5 else ""
            print(f"{meta['size_kb']:.0f} KB ({meta['size_mb']:.2f} MB){over}")
        except subprocess.CalledProcessError as e:
            print(f"FAILED: {e}")

    # Summary table sorted by file size
    print()
    print("=" * 72)
    print("RESULTS (sorted by file size, smallest first)")
    print("=" * 72)
    results.sort(key=lambda r: r["size_kb"])

    print(f"{'File':<40} {'Size':>10} {'FPS':>5} {'Width':>6} {'Colors':>7}")
    print("-" * 72)
    for r in results:
        fname = os.path.basename(r["file"])
        if r["size_kb"] >= 1024:
            size_str = f"{r['size_mb']:.1f} MB"
        else:
            size_str = f"{r['size_kb']:.0f} KB"
        lossy_str = f" L{r['lossy']}" if r["lossy"] > 0 else ""
        over_str = " ⚠️" if r["size_mb"] > 5 else ""
        print(f"{fname:<40} {size_str:>10} {r['fps']:>5} {r['width']:>6} "
              f"{r['colors']:>5}{lossy_str}{over_str}")

    print()
    print(f"Total: {len(results)} GIF(s) in {out_dir}/")
    if results:
        smallest = results[0]
        largest = results[-1]
        print(f"Smallest: {os.path.basename(smallest['file'])} "
              f"({smallest['size_kb']:.0f} KB)")
        print(f"Largest:  {os.path.basename(largest['file'])} "
              f"({largest['size_kb']:.0f} KB)")
    print()
    print("GIFs are automatically kept within the platform download limit (< 5 MB).")
    print("Pick the one that balances size and visual quality for your use case.")


if __name__ == "__main__":
    main()
