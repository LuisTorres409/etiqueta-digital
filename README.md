# Etiquetas Digitais BLE com ESP32 e Dashboard Streamlit

![Sistema de Etiquetas Digitais](https://via.placeholder.com/800x400?text=Sistema+de+Etiquetas+Digitais)

Um sistema completo para exibição e gerenciamento de etiquetas digitais usando ESP32 com comunicação BLE, LCD I2C e um dashboard Streamlit com armazenamento em MongoDB.

## 📌 Visão Geral

Este projeto consiste em:
1. **Firmware ESP32**: Dispositivo que recebe dados via BLE e exibe em um display LCD
2. **Dashboard Streamlit**: Interface web para monitorar e atualizar as etiquetas
3. **Banco de Dados MongoDB**: Armazena o histórico de preços e status dos dispositivos

## 🛠️ Componentes do Sistema

### 1. Firmware ESP32 (`etiqueta.ino`)

O código para a ESP32 que implementa:

#### Funcionalidades BLE
- Cria um servidor BLE com o nome "ETIQUETA-1" (ou outros conforme definido)
- Utiliza o serviço UUID `FFE0` e característica `FFE1`
- Implementa callbacks para conexão/desconexão de dispositivos
- Recebe mensagens via BLE e as processa para exibição no LCD

#### Gerenciamento do LCD
- Utiliza biblioteca `LiquidCrystal_I2C` para comunicação com display 16x2
- Endereço I2C padrão `0x27`
- Formata mensagens recebidas no padrão `"linha1xxxlinha2"`
- Atualiza apenas as linhas que mudaram para evitar flicker

#### Lógica Principal
- Mantém estado de conexão BLE
- Reinicia advertising quando desconectado
- Exibe mensagem inicial "Aguardando BLE"

### 2. Dashboard Streamlit (`Etiquetas.py`)

Interface web com as seguintes funcionalidades:

#### Conexão com MongoDB
- Conecta ao MongoDB local (`mongodb://localhost:27017/`)
- Usa a database `etiquetas_db` e coleção `status_etiquetas`
- Inicializa dados fictícios se o banco estiver vazio

#### Monitoramento BLE
- Escaneia dispositivos BLE a cada 30 segundos
- Identifica etiquetas pelos nomes "ETIQUETA-1", "ETIQUETA-2", "ETIQUETA-3"
- Exibe status online/offline em tempo real

#### Atualização de Preços
- Interface para enviar novos preços via BLE
- Formata mensagens no padrão `"Nome do ProdutoxxxR$XX.XX"`
- Atualiza o banco de dados com novo preço e horário
- Limpa o campo após envio bem-sucedido

### 3. Visualização de Histórico (`Preços Históricos.py`)

Dashboard adicional que mostra:

#### Gráfico de Preços
- Plot interativo com Plotly Express
- Linha do tempo com evolução de preços
- Diferencia produtos por cores
- Marcadores para cada ponto de dados

#### Processamento de Dados
- Converte datas para formato datetime
- Transforma preços em valores numéricos
- Agrega dados de todas as etiquetas

## 🔌 Hardware Necessário

- Placa ESP32 (qualquer variante com BLE)
- Display LCD 16x2 com interface I2C
- Cabos e resistores conforme necessário
- Computador com Bluetooth para o dashboard

## 🚀 Como Usar

### Configuração do ESP32
1. Carregue o sketch `etiqueta.ino` na placa
2. Conecte o display LCD nos pinos I2C (SDA/SCL)
3. Altere `DEVICE_NAME` se desejar múltiplas etiquetas

### Executando o Dashboard
1. Instale as dependências: `pip install -r requirements.txt`
2. Inicie o MongoDB local
3. Execute: `streamlit run Etiquetas.py`
4. Acesse `http://localhost:8501` no navegador

### Visualizando Histórico
1. Execute: `streamlit run historico.py`
2. Acesse `http://localhost:8501` para ver os gráficos

## 📊 Estrutura do Banco de Dados

Cada documento no MongoDB tem a estrutura:
```json
{
  "nome": "ETIQUETA-1",
  "produto": "Nome do Produto",
  "historico_precos": [
    {"preco": "10.99", "data": "2023-01-01"},
    ...
  ],
  "ultima_conexao": "2023-01-01 14:30:00"
}