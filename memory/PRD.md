# PRD - Chat GPT Trading Analyzer

## Problem Statement
Clonar e reproduzir o projeto do repositório GitHub `https://github.com/gustavovida45678-ux/deusnaoeladrao.git` - uma aplicação de chat com IA para análise técnica de gráficos de trading.

## Arquitetura

### Backend (FastAPI)
- **server.py**: API principal com endpoints para chat, análise de imagens e geração de imagens
- **image_annotator.py**: Módulo para adicionar anotações visuais nos gráficos (CALL/PUT, suporte/resistência)
- **MongoDB**: Armazenamento de mensagens do chat

### Frontend (React + Tailwind)
- **App.js**: Componente principal do chat
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

## What's Been Implemented

### Jan 26, 2026 - Sessão 1
- [x] Clone do repositório GitHub
- [x] Configuração de variáveis de ambiente (.env)
- [x] Instalação de dependências (Python/Node)
- [x] Mount de arquivos estáticos para uploads
- [x] Backend 100% funcional
- [x] Frontend 98% funcional
- [x] Integração com GPT-5.1 funcionando
- [x] Geração de imagens funcionando

### Jan 26, 2026 - Sessão 2 (Melhorias)
- [x] Correção do modal de settings (fecha ao clicar fora)
- [x] Sistema de alertas automáticos de trading
  - Detecta sinais CALL/PUT nas respostas da IA
  - Extrai Stop Loss, Take Profit, Confiança, Ativo
  - Notificação visual com animações
  - Som de alerta (ON/OFF toggle)
  - Auto-remoção após 30 segundos
  - Indicador de sinal forte (🔥)

## Prioritized Backlog

### P0 (Crítico) - Concluído
- Nenhum item pendente

### P1 (Alta Prioridade) - Concluído
- ✅ Modal de settings corrigido
- ✅ Sistema de alertas implementado

### P2 (Média Prioridade)
- Adicionar histórico de conversas por sessão
- Exportar análises em PDF
- Persistir configuração de alertas no localStorage

### Futuros/Enhancement
- Integração com exchanges de trading (Binance, Coinbase)
- Alertas via notificação push do navegador
- Dashboard de análises anteriores
- Backtesting de sinais detectados

## Next Tasks
1. Implementar persistência de configurações de alerta
2. Adicionar filtros de alertas por ativo/confiança
3. Criar histórico de alertas passados
