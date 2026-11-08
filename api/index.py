import os
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
import google.generativeai as genai
from fpdf import FPDF

app = Flask(__name__)

# Configura Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def gerar_pdf(texto, arquivo_saida):
    pdf = FPDF()
    pdf.add_page()
    
    # Tenta inserir a logo (coloque 1000092084.webp na pasta api/)
    caminho_logo = os.path.join(os.path.dirname(__file__), '1000092084.webp')
    if os.path.exists(caminho_logo):
        try:
            pdf.image(caminho_logo, x=10, y=8, w=40)
            pdf.ln(25)
        except Exception:
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "NOVAKRAFT", ln=True)
            pdf.ln(5)
    else:
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "NOVAKRAFT", ln=True)
        pdf.ln(5)
    
    pdf.set_font("Helvetica", size=11)
    
    for linha in texto.split('\n'):
        # Remove caracteres que o FPDF não lida bem em algumas versões
        linha_limpa = linha.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 7, text=linha_limpa)
        
    pdf.output(arquivo_saida)

def enviar_email(destinatario, assunto, corpo, caminho_anexo):
    remetente = os.environ.get("EMAIL_USER")
    senha = os.environ.get("EMAIL_PASS")
    
    if not remetente or not senha:
        raise ValueError("EMAIL_USER e EMAIL_PASS não configurados")
    
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    
    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
    
    with open(caminho_anexo, "rb") as f:
        anexo = MIMEApplication(f.read(), _subtype="pdf")
        anexo.add_header('Content-Disposition', 'attachment', filename="Plano_Acao_Novakraft.pdf")
        msg.attach(anexo)
        
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(remetente, senha)
    server.send_message(msg)
    server.quit()

@app.route('/api/processar', methods=['POST'])
def processar_reuniao():
    if 'audio' not in request.files:
        return jsonify({"erro": "Arquivo de áudio ausente."}), 400
        
    audio_file = request.files['audio']
    email_departamento = request.form.get('email')
    
    if not email_departamento:
        return jsonify({"erro": "E-mail do departamento é obrigatório."}), 400
    
    with tempfile.TemporaryDirectory() as temp_dir:
        caminho_audio = os.path.join(temp_dir, audio_file.filename or "audio.mp3")
        audio_file.save(caminho_audio)
        
        try:
            # 1. Upload do áudio para o Gemini e geração da ata + planos de ação
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Faz upload do arquivo de áudio
            audio_gemini = genai.upload_file(path=caminho_audio)
            
            prompt = """Aja como secretário executivo da Novakraft.

Com base no áudio da reunião, faça:
1. Uma transcrição resumida e clara dos pontos principais.
2. Uma ata formal da reunião.
3. Extraia planos de ação detalhados, organizados por departamento responsável, com prazos e responsáveis quando mencionados.

Use o formato:

ATA DA REUNIÃO - NOVAKRAFT
Data: [data se mencionada]

PARTICIPANTES / RESUMO:
[resumo]

DECISÕES E PONTOS PRINCIPAIS:
[lista]

PLANOS DE AÇÃO POR DEPARTAMENTO:
- Departamento X:
  - Ação 1 (responsável, prazo)
  - Ação 2

Seja objetivo, formal e use linguagem corporativa em português."""
            
            resposta = model.generate_content([prompt, audio_gemini])
            ata_final = resposta.text
            
            # Limpa o arquivo no Gemini (opcional)
            try:
                genai.delete_file(audio_gemini.name)
            except Exception:
                pass
            
            # 2. Geração do PDF
            caminho_pdf = os.path.join(temp_dir, "ata_reuniao.pdf")
            gerar_pdf(ata_final, caminho_pdf)
            
            # 3. Envio do e-mail
            corpo_email = (
                "Olá,\n\n"
                "Segue em anexo a ata e o plano de ação correspondente à última reunião da Novakraft.\n\n"
                "Atenciosamente,\nSistema de Gestão Novakraft"
            )
            enviar_email(
                email_departamento,
                "Novakraft: Nova Ata e Plano de Ação",
                corpo_email,
                caminho_pdf
            )
            
            return jsonify({
                "status": "sucesso",
                "mensagem": "Reunião processada, PDF gerado e e-mail enviado com sucesso."
            })
            
        except Exception as e:
            return jsonify({"erro": f"Erro no processamento: {str(e)}"}), 500

# Necessário para a Vercel
if __name__ == "__main__":
    app.run()
