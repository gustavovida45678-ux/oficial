# PRD - Chat GPT Trading Analyzer

## Problem Statement
Clonar e reproduzir o projeto do repositório GitHub `https://github.com/gustavovida45678-ux/deusnaoeladrao.git` - uma aplicação de chat com IA para análise técnica de gráficos de trading.

## Arquitetura

### Backend (FastAPI)
- **server.py**: API principal com endpoints para chat, análise de imagens e geração de imagens
- **image_annotator.py**: Sistema avançado de anotações visuais profissionais (CALL/PUT, entry zones, SL/TP)
- **MongoDB**: Armazenamento de mensagens do chat

### Frontend (React + Tailwind)
- **App.js**: Componente principal do chat com exibição de cenários CALL/PUT
- **ApiKeySettings.js**: Configurações de API key (Emergent ou própria OpenAI)
- **TradingAlerts.js**: Sistema de alertas automáticos para sinais de trading
- Design "Neural Void" com tema escuro e roxo

### Integrações
- **OpenAI GPT-5.1**: Chat e análise de imagens
- **GPT Image-1**: Geração de imagens
- **emergentintegrations**: Biblioteca para integração com LLMs

## User Personas
1. **Trader**: Analisa gráficos de trading para decisões de CALL/PUT
2. **Investidor**: Busca análises técnicas profissionais via IA

## Core Requirements (Static)
1. ✅ Chat por texto com GPT-5.1 em português
2. ✅ Análise de gráficos de trading com visão computacional
3. ✅ Geração de imagens via IA
4. ✅ Suporte a múltiplas imagens simultâneas
5. ✅ Anotações automáticas em gráficos (CALL/PUT)
6. ✅ Armazenamento de histórico no MongoDB
7. ✅ Configuração de API key customizada
8. ✅ Sistema de alertas automáticos para sinais CALL/PUT
9. ✅ Geração automática de cenários CALL e PUT em imagens separadas

## What's Been Implemented

### Jan 26, 2026 - Sessão 1
- [x] Clone do repositório GitHub
- [x] Configuração de variáveis de ambiente (.env)
- [x] Instalação de dependências (Python/Node)
- [x] Mount de arquivos estáticos para uploads
- [x] Backend 100% funcional
- [x] Frontend funcional
- [x] Integração com GPT-5.1 funcionando
- [x] Geração de imagens funcionando

### Jan 26, 2026 - Sessão 2 (Melhorias de UX)
- [x] Correção do modal de settings (fecha ao clicar fora)
- [x] Sistema de alertas automáticos de trading
  - Detecta sinais CALL/PUT nas respostas da IA
  - Extrai Stop Loss, Take Profit, Confiança, Ativo
  - Notificação visual com animações
  - Som de alerta (ON/OFF toggle)
  - Auto-remoção após 30 segundos

### Jan 26, 2026 - Sessão 3 (Gerador de Imagens Profissional)
- [x] Reescrita completa do image_annotator.py
- [x] Sistema de anotações profissionais estilo TradingView:
  - Entry Zone (retângulo azul semi-transparente)
  - CALL/PUT Entry com setas direcionais
  - Stop Loss e Take Profit com linhas horizontais
  - Trade Signal / Strong Signal labels
  - Barra de confiança visual
  - Info box com parâmetros da operação
  - Exit label (1-2 candles)
- [x] Geração automática de AMBOS cenários (CALL e PUT) para cada gráfico
- [x] Backend atualizado com campos call_annotated_paths e put_annotated_paths
- [x] Frontend com seções visuais distintas:
  - Seção verde (📈 Cenário CALL) com borda verde
  - Seção vermelha (📉 Cenário PUT) com borda vermelha

## Prioritized Backlog

### P0 (Crítico) - Concluído
- Nenhum item pendente

### P1 (Alta Prioridade) - Concluído
- ✅ Modal de settings corrigido
- ✅ Sistema de alertas implementado
- ✅ Gerador de imagens profissional

### P2 (Média Prioridade)
- Adicionar histórico de conversas por sessão
- Exportar análises em PDF
- Persistir configuração de alertas no localStorage
- Adicionar mais padrões de candles na detecção

### Futuros/Enhancement
- Integração com exchanges de trading (Binance, Coinbase)
- Alertas via notificação push do navegador
- Dashboard de análises anteriores
- Backtesting de sinais detectados
- Detecção automática de suportes/resistências no gráfico

## Next Tasks
1. Implementar persistência de configurações de alerta
2. Adicionar filtros de alertas por ativo/confiança
3. Melhorar detecção de padrões de candles
