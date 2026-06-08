#!/usr/bin/env python3
"""
Comprime vídeos sem perda visual perceptível usando ffmpeg.

Reduz o tamanho do arquivo de vídeo com configurações otimizadas para
apresentações e compartilhamento no dia a dia do time de comunicação iFood (BEX).

Uso:
    python3 compress_video.py video.mp4
    python3 compress_video.py video.mp4 -o video_comprimido.mp4
    python3 compress_video.py video.mp4 --crf 28 --preset fast
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def format_size(size_bytes: int) -> str:
    """Formata tamanho em bytes para exibição legível."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} bytes"


def compress_video(
    input_path: str,
    output_path: str,
    crf: int = 28,
    preset: str = "fast",
) -> dict:
    """
    Comprime um vídeo usando ffmpeg com libx264.

    Args:
        input_path: Caminho do vídeo original
        output_path: Caminho do vídeo comprimido
        crf: Fator de qualidade (18-28 recomendado; menor = melhor qualidade)
        preset: Velocidade de compressão (ultrafast, fast, medium, slow)

    Returns:
        Dicionário com tamanho original, final e % de redução
    """
    if not os.path.isfile(input_path):
        print(f"Erro: arquivo não encontrado: {input_path}")
        sys.exit(1)

    original_size = os.path.getsize(input_path)

    print(f"📹 Arquivo original: {input_path}")
    print(f"   Tamanho: {format_size(original_size)}")
    print()
    print(f"⚙️  Comprimindo com CRF={crf}, preset={preset}...")
    print(f"   Isso pode levar alguns segundos...")
    print()

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Erro durante a compressão:")
        print(result.stderr[-2000:])  # últimas linhas do erro
        sys.exit(1)

    final_size = os.path.getsize(output_path)
    reduction = (1 - final_size / original_size) * 100

    return {
        "input": input_path,
        "output": output_path,
        "original_size": original_size,
        "final_size": final_size,
        "reduction_pct": reduction,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Comprime vídeos para o time BEX do iFood."
    )
    parser.add_argument("input", help="Arquivo de vídeo a comprimir")
    parser.add_argument(
        "-o", "--output",
        help="Caminho de saída (padrão: mesmo nome com sufixo _compressed)",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=28,
        help="Fator de qualidade: 18 (melhor) a 35 (menor arquivo). Padrão: 28",
    )
    parser.add_argument(
        "--preset",
        default="fast",
        choices=["ultrafast", "superfast", "veryfast", "faster", "fast",
                 "medium", "slow", "slower", "veryslow"],
        help="Velocidade vs compressão (padrão: fast)",
    )

    args = parser.parse_args()

    # Define caminho de saída
    if args.output:
        output_path = args.output
    else:
        p = Path(args.input)
        output_path = str(p.parent / f"{p.stem}_compressed{p.suffix}")

    # Garante que o diretório de saída existe
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    result = compress_video(
        args.input,
        output_path,
        crf=args.crf,
        preset=args.preset,
    )

    # Exibe resultado
    print("✅ Compressão concluída!")
    print()
    print(f"{'Antes:':<12} {format_size(result['original_size'])}")
    print(f"{'Depois:':<12} {format_size(result['final_size'])}")
    print(f"{'Redução:':<12} {result['reduction_pct']:.1f}%")
    print()
    print(f"📁 Arquivo salvo em: {result['output']}")

    if result["reduction_pct"] < 10:
        print()
        print("💡 Dica: o vídeo original já estava bem comprimido.")
        print("   Tente aumentar o CRF (ex: --crf 32) para reduzir mais.")
    elif result["reduction_pct"] > 70:
        print()
        print("⚠️  Redução muito grande. Se a qualidade ficou ruim,")
        print("   tente diminuir o CRF (ex: --crf 23) para melhor qualidade.")


if __name__ == "__main__":
    main()
