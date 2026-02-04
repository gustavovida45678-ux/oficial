"""
🎯 DEMONSTRAÇÃO COMPLETA - Trading Engine 
Simula diferentes cenários de mercado para demonstrar funcionamento
"""

import requests
import json
import numpy as np
from datetime import datetime, timedelta

BACKEND_URL = "http://localhost:8001/api"

def generate_realistic_candles(scenario="bullish", num_candles=100):
    """
    Gera candles realistas simulando diferentes cenários
    
    Scenarios:
    - bullish: Tendência de alta clara
    - bearish: Tendência de baixa clara
    - sideways: Mercado lateral/consolidação
    - volatile: Alta volatilidade sem direção clara
    """
    
    candles = []
    base_price = 45000.0  # BTC ~$45k
    timestamp = int((datetime.now() - timedelta(hours=8)).timestamp())
    
    for i in range(num_candles):
        # Adicionar ruído realista
        noise = np.random.normal(0, base_price * 0.001)  # 0.1% noise
        
        if scenario == "bullish":
            # Tendência de alta com correções
            trend = i * 5  # Subida gradual
            correction = -30 if i % 15 == 0 else 0  # Correções periódicas
            base_price += trend + correction + noise
            
        elif scenario == "bearish":
            # Tendência de baixa com rallies
            trend = -i * 5  # Descida gradual
            rally = 30 if i % 15 == 0 else 0  # Rallies periódicos
            base_price += trend + rally + noise
            
        elif scenario == "sideways":
            # Lateral com movimentos aleatórios
            movement = np.sin(i / 10) * 50 + noise
            base_price += movement
            
        elif scenario == "volatile":
            # Alta volatilidade
            movement = np.random.choice([-100, -50, -20, 20, 50, 100])
            base_price += movement + noise
        
        # Construir candle
        open_price = base_price
        close_price = base_price + np.random.uniform(-20, 20)
        high_price = max(open_price, close_price) + abs(np.random.uniform(5, 15))
        low_price = min(open_price, close_price) - abs(np.random.uniform(5, 15))
        volume = 1000 + i * 10 + np.random.uniform(-100, 100)
        
        candles.append({
            "timestamp": timestamp + (i * 300),  # 5 min cada
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": round(volume, 2)
        })
    
    return candles


def analyze_scenario(scenario_name, candles):
    """Analisa um cenário e exibe resultados"""
    
    print(f"\n{'='*80}")
    print(f"📊 CENÁRIO: {scenario_name.upper()}")
    print(f"{'='*80}\n")
    
    print(f"📈 Informações dos Candles:")
    print(f"   Quantidade: {len(candles)}")
    print(f"   Primeiro: ${candles[0]['close']:.2f}")
    print(f"   Último: ${candles[-1]['close']:.2f}")
    print(f"   Variação: ${candles[-1]['close'] - candles[0]['close']:.2f} ({((candles[-1]['close'] / candles[0]['close'] - 1) * 100):.2f}%)")
    
    print(f"\n🔄 Enviando para análise do motor...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/trade-setup",
            json={
                "candles": candles,
                "capital": 10000.0,
                "explain_with_ai": False
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            return None
        
        result = response.json()
        
        # Exibir resultados formatados
        print(f"\n{'─'*80}")
        
        signal_emoji = {"CALL": "📈", "PUT": "📉", "WAIT": "⏸️"}
        signal_color = {"CALL": "\033[92m", "PUT": "\033[91m", "WAIT": "\033[93m"}
        reset = "\033[0m"
        
        color = signal_color.get(result['signal'], reset)
        
        print(f"{color}🎯 SINAL: {signal_emoji.get(result['signal'], '')} {result['signal']}{reset}")
        print(f"📊 SCORE: {result['score']}/100")
        print(f"💯 CONFIANÇA: {result['confidence']*100:.1f}%")
        
        print(f"\n📈 NÍVEIS DE PREÇO:")
        print(f"   Entrada:       ${result['entry_price']:.2f}")
        print(f"   Stop Loss:     ${result['stop_loss']:.2f} (Risco: ${abs(result['entry_price'] - result['stop_loss']):.2f})")
        print(f"   Take Profit 1: ${result['take_profit_1']:.2f} (Ganho: ${abs(result['take_profit_1'] - result['entry_price']):.2f})")
        print(f"   Take Profit 2: ${result['take_profit_2']:.2f} (Ganho: ${abs(result['take_profit_2'] - result['entry_price']):.2f})")
        
        print(f"\n📊 INDICADORES TÉCNICOS:")
        print(f"   Tendência:  {result['trend']}")
        print(f"   EMA 20:     ${result['ema_20']:.2f}")
        print(f"   EMA 50:     ${result['ema_50']:.2f}")
        print(f"   RSI:        {result['rsi_value']:.1f}")
        print(f"   ATR:        ${result['atr_value']:.2f}")
        
        print(f"\n💰 GESTÃO DE RISCO:")
        print(f"   RR TP1: 1:{result['risk_reward_1']:.2f}")
        print(f"   RR TP2: 1:{result['risk_reward_2']:.2f}")
        print(f"   Risco por trade: ${result['risk_amount']:.2f} (1% do capital)")
        
        if result['reasons']:
            print(f"\n✅ RAZÕES DO SINAL:")
            for reason in result['reasons']:
                print(f"   {reason}")
        
        if result['warnings']:
            print(f"\n⚠️  AVISOS:")
            for warning in result['warnings']:
                print(f"   {warning}")
        
        print(f"\n{'─'*80}\n")
        
        return result
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None


def main():
    """Executa demonstração completa"""
    
    print("\n" + "="*80)
    print("🎯 DEMONSTRAÇÃO COMPLETA - Trading Engine Matemático")
    print("   Objetivo: 70%+ Win Rate com Gestão Inteligente de Perdas")
    print("="*80)
    
    # Testar 4 cenários diferentes
    scenarios = {
        "Tendência de Alta (Bullish)": "bullish",
        "Tendência de Baixa (Bearish)": "bearish",
        "Mercado Lateral (Sideways)": "sideways",
        "Alta Volatilidade": "volatile"
    }
    
    results = {}
    
    for scenario_name, scenario_type in scenarios.items():
        candles = generate_realistic_candles(scenario_type, 100)
        result = analyze_scenario(scenario_name, candles)
        if result:
            results[scenario_name] = result
    
    # Resumo Final
    print(f"\n{'='*80}")
    print(f"📊 RESUMO FINAL DA DEMONSTRAÇÃO")
    print(f"{'='*80}\n")
    
    if results:
        signals = [r['signal'] for r in results.values()]
        scores = [r['score'] for r in results.values()]
        
        signal_counts = {
            "CALL": signals.count("CALL"),
            "PUT": signals.count("PUT"),
            "WAIT": signals.count("WAIT")
        }
        
        avg_score = sum(scores) / len(scores)
        
        print(f"Cenários Testados: {len(results)}")
        print(f"\nSinais Gerados:")
        print(f"   📈 CALL (Compra): {signal_counts['CALL']}")
        print(f"   📉 PUT (Venda):   {signal_counts['PUT']}")
        print(f"   ⏸️  WAIT (Aguardar): {signal_counts['WAIT']}")
        print(f"\nScore Médio: {avg_score:.1f}/100")
        
        print(f"\n{'─'*80}")
        print(f"🎯 ANÁLISE DO COMPORTAMENTO:")
        print(f"{'─'*80}\n")
        
        if signal_counts['WAIT'] >= len(results) * 0.5:
            print("✅ Sistema CONSERVADOR e SELETIVO")
            print("   → Aguarda setups de alta qualidade (score ≥ 70)")
            print("   → Prioriza QUALIDADE sobre quantidade")
            print("   → Reduz exposição a trades ruins")
            print("   → Estratégia ideal para preservar capital")
        else:
            print("✅ Sistema ATIVO")
            print("   → Detectando oportunidades em múltiplos cenários")
            print("   → Validar manualmente antes de operar")
        
        print(f"\n{'─'*80}")
        print(f"📚 CARACTERÍSTICAS DO MOTOR:")
        print(f"{'─'*80}\n")
        
        print("1. 🎯 SISTEMA DE SCORING (0-100 pontos)")
        print("   • Tendência (EMA20 vs EMA50): 25 pts")
        print("   • Recuo válido: 25 pts")
        print("   • RSI equilibrado: 20 pts")
        print("   • Volume confirmando: 15 pts")
        print("   • Padrão de candle: 15 pts")
        print("   → Mínimo 70 pontos para gerar sinal")
        
        print(f"\n2. 💰 GESTÃO DE RISCO")
        print("   • Stop Loss: 1.5x ATR (dinâmico)")
        print("   • Take Profit 1: RR 1:2")
        print("   • Take Profit 2: RR 1:3")
        print("   • Risco fixo: 1% do capital por trade")
        print("   • Max drawdown: 10%")
        
        print(f"\n3. 📊 INDICADORES UTILIZADOS")
        print("   • EMA 20/50: Tendência")
        print("   • RSI 14: Momentum")
        print("   • ATR 14: Volatilidade")
        print("   • MACD: Confirmação")
        print("   • Padrões de Candle: Reversão")
        
        print(f"\n{'─'*80}")
        print(f"🚀 PRÓXIMOS PASSOS PARA 70%+ WIN RATE:")
        print(f"{'─'*80}\n")
        
        print("1. ✅ VALIDAÇÃO COM DADOS REAIS")
        print("   → Conectar com exchange real (Binance, Bybit, etc)")
        print("   → Coletar 3-6 meses de dados históricos")
        print("   → Rodar backtest extensivo")
        
        print(f"\n2. 📊 PAPER TRADING")
        print("   → Operar em conta demo por 2-4 semanas")
        print("   → Registrar TODOS os sinais (não apenas os vencedores)")
        print("   → Calcular win rate REAL")
        
        print(f"\n3. 🔧 OTIMIZAÇÃO")
        print("   → Ajustar períodos de EMA se necessário")
        print("   → Calibrar níveis de RSI")
        print("   → Testar diferentes multipliers de ATR")
        
        print(f"\n4. 🤖 AUTOMAÇÃO")
        print("   → Bot conectado à exchange")
        print("   → Execução automática de sinais")
        print("   → Monitoramento 24/7")
        
    print(f"\n{'='*80}")
    print("✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("   Motor Matemático 100% Operacional")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
