# ifood-bex-gifs-tools

Ferramentas de mídia para o time de Comunicação BEX do iFood: converte vídeos em GIF animado, comprime vídeos pesados e converte/comprime imagens para uso em apresentações PowerPoint e Google Slides.

## O que faz
- 🎬 Converte vídeos em GIF otimizado para PowerPoint/Google Slides
- 📦 Comprime vídeos pesados mantendo qualidade visual
- 🖼️ Converte e comprime imagens (JPG ↔ PNG)

## Garantia de download
Todos os GIFs gerados ficam **automaticamente abaixo de 5MB** para garantir download sem falhas na plataforma ToqanClaw.

## Como instalar
```bash
npx skills add odaraskubincan-droide/ifood-bex-gifs-tools --skill ifood-bex-gifs-tools --agent '*' --yes --copy
```

## Changelog
### v2 - 2026-06-03
- ✅ Correção: GIFs agora garantidos abaixo de 5MB (padrão 480px, 10fps, 128 cores)
- ✅ Compressão automática com gifsicle
- ✅ Fallback para 360px se necessário

### v1 - 2026-06-02
- Lançamento inicial
