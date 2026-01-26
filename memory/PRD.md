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

## What's Been Implemented (Jan 26, 2026)
- [x] Clone do repositório GitHub
- [x] Configuração de variáveis de ambiente (.env)
- [x] Instalação de dependências (Python/Node)
- [x] Mount de arquivos estáticos para uploads
- [x] Backend 100% funcional
- [x] Frontend 98% funcional
- [x] Integração com GPT-5.1 funcionando
- [x] Geração de imagens funcionando

## Prioritized Backlog

### P0 (Crítico) - Concluído
- Nenhum item pendente

### P1 (Alta Prioridade)
- Melhorar tratamento de erros na UI
- Adicionar feedback visual durante upload de imagens

### P2 (Média Prioridade)
- Modal de configurações fecha inconsistentemente ao clicar fora
- Adicionar histórico de conversas por sessão
- Exportar análises em PDF

### Futuros/Enhancement
- Integração com exchanges de trading
- Alertas automáticos de sinais
- Dashboard de análises anteriores

## Next Tasks
1. Corrigir modal de settings (issue menor)
2. Adicionar mais indicadores técnicos na análise
3. Implementar sistema de favoritos para gráficos analisados
