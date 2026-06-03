#!/usr/bin/env python3
"""
Conversão e compressão de imagens para o time BEX do iFood.

Converte entre formatos (JPG ↔ PNG) e comprime imagens mantendo
qualidade visual aceitável para apresentações em PowerPoint e Google Slides.

Requer: Pillow (pip install Pillow)

Uso:
    python3 image_tools.py foto.jpg --convert jpg2png
    python3 image_tools.py logo.png --convert png2jpg
    python3 image_tools.py foto.jpg --compress
    python3 image_tools.py foto.jpg --compress --quality 85
    python3 image_tools.py *.jpg --compress
    python3 image_tools.py imagem.png --compress -o /tmp/imagem_menor.png
"""

import argparse
import glob
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("❌ Erro: Pillow não está instalado.")
    print("   Instale com: pip install Pillow")
    sys.exit(1)


def format_size(size_bytes: int) -> str:
    """Formata tamanho em bytes para exibição legível."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} bytes"


def convert_image(
    input_path: str,
    conversion: str,
    output_path: str | None = None,
) -> dict:
    """
    Converte uma imagem entre formatos JPG e PNG.

    Args:
        input_path: Caminho da imagem original
        conversion: 'jpg2png' ou 'png2jpg'
        output_path: Caminho de saída (opcional)

    Returns:
        Dicionário com caminhos e tamanhos
    """
    p = Path(input_path)
    original_size = os.path.getsize(input_path)

    if conversion == "jpg2png":
        ext = ".png"
    elif conversion == "png2jpg":
        ext = ".jpg"
    else:
        raise ValueError(f"Conversão inválida: {conversion}. Use 'jpg2png' ou 'png2jpg'.")

    if output_path is None:
        output_path = str(p.parent / f"{p.stem}{ext}")

    img = Image.open(input_path)

    if conversion == "png2jpg":
        # PNG pode ter canal alfa — converter para RGB antes de salvar como JPG
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=95)
    else:
        img.save(output_path, "PNG")

    final_size = os.path.getsize(output_path)

    return {
        "input": input_path,
        "output": output_path,
        "original_size": original_size,
        "final_size": final_size,
        "action": "convert",
        "conversion": conversion,
    }


def compress_image(
    input_path: str,
    quality: int = 75,
    output_path: str | None = None,
) -> dict:
    """
    Comprime uma imagem mantendo qualidade visual aceitável.

    Args:
        input_path: Caminho da imagem original
        quality: Qualidade de 1 (mínima) a 95 (máxima). Padrão: 75
        output_path: Caminho de saída (opcional)

    Returns:
        Dicionário com caminhos, tamanhos e % de redução
    """
    p = Path(input_path)
    original_size = os.path.getsize(input_path)
    ext = p.suffix.lower()

    if output_path is None:
        output_path = str(p.parent / f"{p.stem}_compressed{ext}")

    img = Image.open(input_path)

    if ext in (".jpg", ".jpeg"):
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=quality, optimize=True)
    elif ext == ".png":
        # PNG é lossless; usamos quantize para reduzir cores
        img.save(output_path, "PNG", optimize=True)
    elif ext == ".webp":
        img.save(output_path, "WEBP", quality=quality, method=6)
    else:
        # Tenta salvar no mesmo formato
        img.save(output_path, quality=quality, optimize=True)

    final_size = os.path.getsize(output_path)
    reduction = (1 - final_size / original_size) * 100 if original_size > 0 else 0

    return {
        "input": input_path,
        "output": output_path,
        "original_size": original_size,
        "final_size": final_size,
        "reduction_pct": reduction,
        "action": "compress",
    }


def resolve_files(patterns: list[str]) -> list[str]:
    """Expande globs e retorna lista de arquivos existentes."""
    files = []
    for pattern in patterns:
        expanded = glob.glob(pattern)
        if expanded:
            files.extend(expanded)
        elif os.path.isfile(pattern):
            files.append(pattern)
        else:
            print(f"⚠️  Aviso: nenhum arquivo encontrado para '{pattern}'")
    return sorted(set(files))


def print_result(result: dict) -> None:
    """Exibe resultado formatado para o usuário."""
    action = result["action"]
    original = format_size(result["original_size"])
    final = format_size(result["final_size"])

    if action == "convert":
        conv = result["conversion"]
        label = "JPG → PNG" if conv == "jpg2png" else "PNG → JPG"
        print(f"  🔄 {label}: {result['input']} → {result['output']}")
        print(f"     {original} → {final}")
    elif action == "compress":
        reduction = result["reduction_pct"]
        icon = "✅" if reduction > 5 else "ℹ️ "
        print(f"  {icon} Comprimida: {result['input']} → {result['output']}")
        print(f"     {original} → {final}  (−{reduction:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Converte e comprime imagens para o time BEX do iFood."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Arquivo(s) de imagem. Aceita globs como '*.jpg'",
    )
    parser.add_argument(
        "--convert",
        choices=["jpg2png", "png2jpg"],
        help="Converte formato: jpg2png ou png2jpg",
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Comprime a imagem mantendo qualidade visual",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=75,
        help="Qualidade da compressão: 1-95 (padrão: 75). Só afeta JPG/WEBP.",
    )
    parser.add_argument(
        "-o", "--output",
        help="Caminho de saída (só funciona com um único arquivo de entrada)",
    )

    args = parser.parse_args()

    if not args.convert and not args.compress:
        parser.error("Especifique uma ação: --convert jpg2png, --convert png2jpg, ou --compress")

    if args.convert and args.compress:
        parser.error("Use apenas --convert OU --compress por vez, não os dois juntos")

    files = resolve_files(args.files)
    if not files:
        print("❌ Nenhum arquivo de imagem encontrado.")
        sys.exit(1)

    if args.output and len(files) > 1:
        print("❌ -o/--output só pode ser usado com um único arquivo de entrada.")
        sys.exit(1)

    print(f"🖼️  Processando {len(files)} arquivo(s)...\n")

    errors = []
    results = []

    for f in files:
        try:
            if args.convert:
                result = convert_image(f, args.convert, args.output if len(files) == 1 else None)
            else:
                result = compress_image(f, args.quality, args.output if len(files) == 1 else None)

            print_result(result)
            results.append(result)
        except Exception as e:
            print(f"  ❌ Erro em {f}: {e}")
            errors.append(f)

    print()
    print(f"✅ Concluído: {len(results)} arquivo(s) processado(s)", end="")
    if errors:
        print(f", {len(errors)} erro(s)")
    else:
        print("!")

    if results and args.compress:
        total_original = sum(r["original_size"] for r in results)
        total_final = sum(r["final_size"] for r in results)
        if total_original > 0:
            total_reduction = (1 - total_final / total_original) * 100
            print(f"📊 Total: {format_size(total_original)} → {format_size(total_final)}"
                  f"  (−{total_reduction:.1f}%)")


if __name__ == "__main__":
    main()
