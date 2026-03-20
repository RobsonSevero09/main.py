import os
import re
import json
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify
import google.generativeai as genai
import googlemaps
import requests

app = Flask(__name__)

# ==============================================================================
# 🔐 1. SEGURANÇA E CONFIGURAÇÕES (Variáveis de Ambiente)
# ==============================================================================
# Configure estas chaves no painel da Railway (Variables)
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")
GMAPS_API_KEY = os.environ.get("GMAPS_API_KEY")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

genai.configure(api_key=GENAI_API_KEY)
gmaps = googlemaps.Client(key=GMAPS_API_KEY)

# ==============================================================================
# 💰 2. TABELA DE PREÇOS OFICIAL (Inversores DEYE)
# ==============================================================================
TABELA_SOLAR = [
    {"kwh": 390,  "pwp": 2.92,  "avista": 9990.00,  "120x": 297.00, "nome": "Starter"},
    {"kwh": 600,  "pwp": 4.09,  "avista": 11990.00, "120x": 357.00, "nome": "Econômico"},
    {"kwh": 850,  "pwp": 5.85,  "avista": 15490.00, "120x": 461.00, "nome": "Família"},
    {"kwh": 1200, "pwp": 8.19,  "avista": 21900.00, "120x": 650.00, "nome": "Mansão"},
    {"kwh": 2100, "pwp": 15.21, "avista": 33990.00, "120x": 1012.00, "nome": "Comercial"},
]

# ==============================================================================
# 🤖 3. OS 9 ROBÔS INTEGRADOS
# ==============================================================================

class RoboOlheiro:
    def ler_conta(self, imagem_data, tentativa=1):
        """Lógica Blindada com json.loads e Retry"""
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = "Analise a fatura Energisa PB. Extraia kWh e Valor Total. Responda APENAS um JSON: {'kwh': 0.0, 'valor': 0.0}. Se estiver ilegível, responda 'ERRO_VISAO'."
            
            response = model.generate_content([prompt, imagem_data])
            texto_limpo = response.text.strip()
            
            # Busca o JSON dentro do texto (segurança contra textos extras da IA)
            match = re.search(r'\{.*\}', texto_limpo, re.DOTALL)
            
            if match:
                return json.loads(match.group()) # SEGURO: Usando json.loads
            
            if "ERRO_VISAO" in texto_limpo and tentativa < 2:
                return self.ler_conta(imagem_data, tentativa + 1)
            
            return {"erro": "ERRO_VISAO"}
        except Exception as e:
            return {"erro": f"ERRO_SISTEMA: {str(e)}"}

class RoboCacador:
    def validar_local(self, lat, lng):
        try:
            res = gmaps.reverse_geocode((lat, lng))
            bairro = "Patos"
            for c in res[0]['address_components']:
                if 'sublocality' in c['types']: bairro = c['long_name']
            
            # Prioridade para bairros com mais sol e telhados bons
            score = 95 if bairro in ["Noé Trajano", "Jatobá", "Belo Horizonte", "Centro"] else 75
            return bairro, score
        except:
            return "Patos (Centro)", 50

class RoboApresentador:
    def realizar_estudo(self, kwh, valor_conta):
        kit = next((x for x in TABELA_SOLAR if x['kwh'] >= kwh), TABELA_SOLAR[-1])
        # Cálculo de 20 anos com inflação energética média
        economia_estimada = (valor_conta * 240) * 1.35
        return {
            "kit": kit,
            "economia": economia_estimada,
            "comissao": kit['avista'] * 0.10
        }

class RoboAtendente:
    def saudar(self, nome, bairro):
        """Saudação com Clima Real de Patos-PB via OpenWeather"""
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q=Patos,BR&appid={WEATHER_API_KEY}&units=metric&lang=pt_br"
            clima = requests.get(url).json()
            temp = clima['main']['temp']
            
            if temp > 33:
                clima_msg = f"O sol tá castigando hoje em Patos, fazendo {temp}°C! ☀️"
            else:
                clima_msg = f"Clima bom em Patos hoje, fazendo {temp}°C. 🌤️"
            
            return f"E aí, {nome}! {clima_msg} Ótima hora pra transformar esse calor no bairro {bairro} em economia!"
        except:
            return f"Fala, {nome}! O sol aí no {bairro} tá valendo ouro hoje. Vamos economizar?"

class RoboRelatorio:
    def salvar_venda(self, nome, bairro, kit, comissao):
        arquivo = 'carteira_solar_patos.csv'
        nova_linha = {
            "Data_Hora": [datetime.now().strftime("%d/%m/%Y %H:%M")],
            "Cliente": [nome],
            "Bairro": [bairro],
            "Kit": [kit],
            "Comissao_Prevista": [comissao]
        }
        df = pd.DataFrame(nova_linha)
        header = not os.path.exists(arquivo)
        df.to_csv(arquivo, mode='a', index=False, header=header, sep=';', encoding='utf-8-sig')

class RoboSupervisor:
    def checar_dados(self, dados):
        return True if dados.get('nome') and (dados.get('imagem_url') or dados.get('kwh_manual')) else False

class RoboJuridico:
    def info_garantia(self):
        return "🛡️ Garantia de Fábrica: 10 anos no Inversor DEYE e 25 anos nos painéis."

class RoboCripto:
    def mascarar_dados(self, dado):
        return f"***{str(dado)[-4:]}"

class RoboReativador:
    def mensagem_followup(self, nome):
        return f"Oi {nome}! Passando para lembrar que o sol de Patos não tira férias. Vamos garantir sua economia?"

# ==============================================================================
# 🏛️ 4. MOTOR DE EXECUÇÃO (API FLASK)
# ==============================================================================

# Instanciando a Equipe Solar
olheiro = RoboOlheiro(); cacador = RoboCacador(); apresentador = RoboApresentador()
atendente = RoboAtendente(); relatorio = RoboRelatorio(); juridico = RoboJuridico()

@app.route('/atendimento-solar/v5', methods=['POST'])
def processar_venda():
    dados = request.json
    nome_cliente = dados.get('nome', 'Cliente Amigo')
    
    # 1. Localizar Cliente
    bairro, score = cacador.validar_local(dados.get('lat'), dados.get('lng'))
    saudacao = atendente.saudar(nome_cliente, bairro)
    
    # 2. Ler Fatura (Via IA com Segurança)
    # n8n deve enviar a imagem em 'imagem_buffer'
    leitura = olheiro.ler_conta(dados.get('imagem_buffer'))
    
    if "erro" in leitura:
        return jsonify({
            "resposta": f"{saudacao}\n\nPutz, não consegui ler bem a foto. 😕 Consegue mandar outra mais nítida?"
        })

    # 3. Gerar Proposta e Registrar comissão
    estudo = apresentador.realizar_estudo(leitura['kwh'], leitura['valor'])
    relatorio.salvar_venda(nome_cliente, bairro, estudo['kit']['nome'], estudo['comissao'])
    garantia = juridico.info_garantia()
    
    # 4. Resposta Final para o WhatsApp
    texto_proposta = (
        f"{saudacao}\n\n"
        f"✅ *Análise Completa:*\n"
        f"- Gasto Mensal: R$ {leitura['valor']:.2f}\n"
        f"- Kit Sugerido: DEYE {estudo['kit']['nome']}\n"
        f"- Parcela Estimada: 120x de R$ {estudo['kit']['120x']:.2f}\n"
        f"🚀 *Sua economia em 20 anos: R$ {estudo['economia']:,.2f}*\n\n"
        f"{garantia}\n\n"
        f"Podemos agendar sua vistoria gratuita?"
    )
    
    return jsonify({
        "status": "sucesso",
        "texto": texto_proposta,
        "score": score,
        "internos": {"comissao": estudo['comissao']}
    })

if __name__ == '__main__':
    # Configuração para rodar na Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
