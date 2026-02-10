# 📊 Dashboard de Leads

Dashboard interativo para análise de leads integrado com Google Sheets, desenvolvido com **Streamlit** e **Plotly**.

## Funcionalidades

| # | Análise | Visualização |
|---|---------|-------------|
| 1 | Quantidade de contatos por qualificação | Cards com métricas |
| 2 | Dia da semana que mais converte | Mapa de calor + gráfico de barras |
| 3 | Qualificação por campanha (utm_campaign) | Gráfico de barras agrupado + tabela |
| 4 | Google Ads: qualificação + termos de pesquisa | Pizza, barras + tabela de termos |
| 5 | CEPs por status de qualificação | Barras empilhadas + tabela completa |

## Pré-requisitos

- Python 3.9+
- Conta Google Cloud com API do Google Sheets habilitada
- Service Account com acesso à planilha

## Instalação Local

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/dashboard-leads.git
cd dashboard-leads

# 2. Crie o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as credenciais
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite o arquivo com suas credenciais do Service Account

# 5. Execute
streamlit run app.py
```

## Configuração do Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto ou selecione um existente
3. Ative as APIs: **Google Sheets API** e **Google Drive API**
4. Crie um **Service Account** (IAM & Admin > Service Accounts)
5. Gere uma chave JSON para o Service Account
6. Compartilhe a planilha com o e-mail do Service Account (permissão de Leitor)
7. Copie o conteúdo do JSON para `.streamlit/secrets.toml`

## Deploy no Streamlit Cloud

1. Suba o repositório no GitHub (sem o `secrets.toml`)
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório
4. Em **App Settings > Secrets**, cole o conteúdo do `secrets.toml`
5. Deploy!

## Estrutura da Planilha

A planilha deve conter os seguintes cabeçalhos:

| Coluna | Descrição |
|--------|-----------|
| data | Data do contato |
| qualificacao | Status: Qualificado, Convertido, Desqualificado, Achei, Não interagiu |
| utm_campaign | Nome da campanha |
| utm_source | Fonte (google, facebook, etc.) |
| utm_term | Termo de pesquisa (Google Ads) |
| cep | CEP do lead |
| *demais colunas* | Dados complementares do lead |

## Tecnologias

- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/python/)
- [gspread](https://docs.gspread.org/)
- [Pandas](https://pandas.pydata.org/)
