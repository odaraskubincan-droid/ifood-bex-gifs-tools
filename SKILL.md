---
name: ifood-bex-gifs-tools
description: Ferramentas de mídia para o time de Comunicação BEX do iFood: converte vídeos em GIF animado, comprime vídeos pesados e converte/comprime imagens para uso em apresentações PowerPoint e Google Slides. Use esta skill sempre que o usuário mencionar GIF, vídeo para apresentação, comprimir vídeo ou imagem, converter JPG para PNG ou PNG para JPG, reduzir tamanho de arquivo de mídia, ou precisar de conteúdo visual otimizado para slides — mesmo que a palavra "BEX" não apareça na solicitação.
---

# 🎬 iFood BEX — Ferramentas de GIF e Mídia

Ferramentas práticas para o time de Comunicação do iFood (BEX) preparar materiais visuais para apresentações, campanhas e compartilhamento interno.

> **Pré-requisitos:** `ffmpeg` e Python 3 devem estar instalados.  
> Para `image_tools.py`, instale Pillow: `pip install Pillow`  
> Para `video_to_gif.py`, use `uv run --python 3.12` (inclui todas as dependências automaticamente).

---

## 🗂️ O que esta skill faz

| Ferramenta | O que resolve |
|-----------|---------------|
| **Vídeo → GIF** | Transforma um trecho de vídeo em GIF animado pronto para slides |
| **Comprimir vídeo** | Reduz o tamanho de um vídeo sem perda visual visível |
| **Converter/comprimir imagem** | Converte JPG ↔ PNG e reduz peso de imagens para apresentações |

---

## 1. 🎥 Vídeo → GIF

Converte um vídeo (mp4, mov, etc.) em GIF otimizado para PowerPoint e Google Slides.

> **✅ GIFs são gerados automaticamente dentro do limite de download da plataforma (abaixo de 5 MB).**  
> O script detecta GIFs grandes e aplica compressão automática (gifsicle) ou redução de largura.  
> Se o gifsicle não estiver instalado, o script instala automaticamente.

### Uso básico

```bash
# Converter o vídeo inteiro com preset padrão ppt (< 5 MB garantido)
uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py meu_video.mp4

# Converter apenas os primeiros 10 segundos (recomendado para slides)
uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py meu_video.mp4 --end 10

# Converter um trecho específico (ex: do segundo 5 ao 15)
uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py meu_video.mp4 --start 5 --end 15

# Salvar em pasta específica
uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py meu_video.mp4 --end 10 -o /tmp/meus_gifs/
```

### Preset padrão: `ppt` — otimizado para download

O novo preset padrão `ppt` foi projetado especificamente para garantir GIFs abaixo de 5 MB:

- **FPS:** 10
- **Largura:** 480 px
- **Cores:** 128
- **Compressão lossy:** nível 60 (via gifsicle)
- **Verificação automática:** se o GIF ainda exceder 5 MB, compressão adicional e/ou redução para 360 px são aplicadas automaticamente

```bash
# Usando o preset padrão ppt (recomendado para a plataforma)
uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py meu_video.mp4 --presets ppt
```

### Outros presets disponíveis

```bash
# Comparação de 4 variantes rápidas
uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py meu_video.mp4 \
  --presets minimal --end 10 -o /tmp/gifs/
```

| Preset | Para que serve |
|--------|---------------|
| **`ppt`** | **Padrão — 1 variante leve (< 5 MB), pronta para download** |
| `minimal` | 4 variantes rápidas — bom para slides |
| `full` | 18 variantes — comparação completa |
| `quality` | Foco em resolução alta |
| `lossy` | Foco em tamanho mínimo |

### Desativar o limite automático

```bash
# Caso você precise de GIFs maiores (ex: uso local, sem limite de download)
uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py meu_video.mp4 \
  --presets full --no-size-limit
```

---

## 2. 📦 Comprimir Vídeo

Reduz o tamanho de vídeos pesados sem perda visual perceptível. Ideal para vídeos que precisam ser enviados por e-mail, WhatsApp ou inseridos em apresentações.

### Uso básico

```bash
# Comprime com configuração padrão (CRF 28, preset fast)
python3 skills/ifood-bex-gifs-tools/scripts/compress_video.py meu_video.mp4

# Salvar com nome específico
python3 skills/ifood-bex-gifs-tools/scripts/compress_video.py meu_video.mp4 -o video_menor.mp4

# Melhor qualidade (arquivo maior)
python3 skills/ifood-bex-gifs-tools/scripts/compress_video.py meu_video.mp4 --crf 23

# Arquivo menor (qualidade um pouco mais baixa)
python3 skills/ifood-bex-gifs-tools/scripts/compress_video.py meu_video.mp4 --crf 32
```

### O que esperar

```
📹 Arquivo original: meu_video.mp4
   Tamanho: 45.2 MB

⚙️  Comprimindo com CRF=28, preset=fast...

✅ Compressão concluída!

Antes:       45.2 MB
Depois:      12.8 MB
Redução:     71.7%

📁 Arquivo salvo em: meu_video_compressed.mp4
```

### Guia de qualidade (CRF)

| CRF | Qualidade | Tamanho | Quando usar |
|-----|-----------|---------|-------------|
| 18-22 | Excelente | Grande | Arquivo máster, edição |
| 23-27 | Boa | Médio | Apresentações importantes |
| **28** | **Boa** | **Pequeno** | **Padrão recomendado** |
| 29-35 | Aceitável | Pequeno | Compartilhamento rápido |

---

## 3. 🖼️ Converter e Comprimir Imagens

Converte entre formatos de imagem e comprime para uso em slides.

### Converter JPG → PNG

```bash
python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py foto.jpg --convert jpg2png
```

### Converter PNG → JPG

```bash
python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py logo.png --convert png2jpg
```

### Comprimir uma imagem

```bash
# Compressão padrão (qualidade 75 — boa para slides)
python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py foto.jpg --compress

# Qualidade maior (arquivo um pouco maior)
python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py foto.jpg --compress --quality 85

# Comprimir várias imagens de uma vez
python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py *.jpg --compress

# Salvar em local específico
python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py foto.jpg --compress -o /tmp/foto_menor.jpg
```

### Guia de qualidade para imagens

| Qualidade | Quando usar |
|-----------|-------------|
| 60-70 | E-mail, WhatsApp — prioridade no tamanho |
| **75** | **Slides — padrão recomendado** |
| 80-85 | Slides com texto pequeno ou detalhes finos |
| 90-95 | Impressão, arquivo permanente |

---

## 🎯 Tabela de Referência Rápida

| O que quero fazer | Comando |
|---|---|
| Vídeo → GIF (padrão < 5 MB) | `uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py video.mp4` |
| Vídeo → GIF (10 seg) | `uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py video.mp4 --end 10` |
| Vídeo → GIF (trecho) | `uv run --python 3.12 skills/ifood-bex-gifs-tools/scripts/video_to_gif.py video.mp4 --start 5 --end 15` |
| Comprimir vídeo | `python3 skills/ifood-bex-gifs-tools/scripts/compress_video.py video.mp4` |
| Comprimir vídeo (saída específica) | `python3 skills/ifood-bex-gifs-tools/scripts/compress_video.py video.mp4 -o saida.mp4` |
| Comprimir imagem | `python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py foto.jpg --compress` |
| Comprimir várias imagens | `python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py *.jpg --compress` |
| JPG → PNG | `python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py foto.jpg --convert jpg2png` |
| PNG → JPG | `python3 skills/ifood-bex-gifs-tools/scripts/image_tools.py logo.png --convert png2jpg` |

---

## 💡 Dicas para PowerPoint e Google Slides

### GIFs em apresentações

- **Tamanho ideal:** 480px de largura, 10fps — GIFs leves e prontos para download
- **Duração recomendada:** até 10-15 segundos (GIFs muito longos ficam pesados)
- **Transparência:** GIFs não suportam fundo transparente — use fundo branco ou da cor do slide
- **Como inserir no PowerPoint:** Inserir → Imagens → selecionar o `.gif`
- **Para autoplay:** No PowerPoint, o GIF inicia automaticamente ao exibir o slide

### Vídeos em apresentações

- **Tamanho ideal para e-mail:** abaixo de 10 MB
- **Tamanho para slides:** abaixo de 50 MB (o PowerPoint aceita até ~100 MB)
- **Formato:** MP4 é o mais compatível com PowerPoint e Google Slides
- **Após comprimir**, reinsira o vídeo no slide (não apenas substitua o arquivo)

### Imagens em apresentações

- **PNG:** prefira para logos, ícones e imagens com texto (preserva bordas nítidas)
- **JPG:** prefira para fotos e imagens complexas (ocupa menos espaço)
- **Qualidade 75-80** é o ponto ideal para slides — invisível ao olho, mas muito menor
- **Dica:** comprima as imagens antes de inserir no slide para manter o arquivo .pptx leve

---

## 🛠️ Instalação de dependências

```bash
# Instalar Pillow (para image_tools.py)
pip install Pillow

# Verificar se ffmpeg está instalado
ffmpeg -version

# Verificar se uv está instalado (para video_to_gif.py)
uv --version
```

Se `ffmpeg` não estiver instalado:
```bash
# Ubuntu / Debian / WSL
sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg
```

O `gifsicle` é instalado automaticamente pelo script quando necessário.
