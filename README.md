# Novakraft - Transcritor de Reuniões

Sistema que grava/recebe áudio de reuniões, gera transcrição, cria ata formal com planos de ação por departamento e envia PDF por e-mail.

## Estrutura
- `api/index.py` → backend (Gemini + PDF + e-mail)
- `public/index.html` → interface de upload
- `requirements.txt` → dependências
- `vercel.json` → configuração de deploy

## Passos para finalizar
1. Faça upload da logo `1000092084.webp` para a pasta `api/`
2. Na Vercel: importe este repositório e configure as variáveis de ambiente:
   - `GEMINI_API_KEY`
   - `EMAIL_USER`
   - `EMAIL_PASS`
3. Deploy.

Desenvolvido com Grok + GitHub connector.
