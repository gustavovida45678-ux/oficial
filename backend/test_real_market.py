"""
🎯 TESTE FINAL COMPLETO - Trading Engine com Dados REAIS

Este script testa o motor de trading com dados reais da Binance
para validar funcionamento e assertividade.
"""

import requests
import json
from datetime import datetime

# Configurações
BACKEND_URL = "http://localhost:8001/api"
BINANCE_API = "https://api.binance.com/api/v3"

def get_binance_candles(symbol="BTCUSDT", interval="5m", limit=100):
    """Busca candles reais da Binance"""
    try:
        url = f"{BINANCE_API}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        candles = []
        for k in data:
            candles.append({
                "timestamp": k[0] // 1000,
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            })
        
        return candles
    except Exception as e:
        print(f"❌ Erro ao buscar dados da Binance: {str(e)}")
        return None


def test_with_real_data():
    """Testa o motor com dados reais de mercado"""
    
    print("\n" + "="*80)
    print("🎯 TESTE FINAL COMPLETO - Trading Engine com Dados REAIS")
    print("="*80 + "\n")
    
    # Lista de pares para testar
    test_pairs = [
        ("BTCUSDT", "5m"),
        ("ETHUSDT", "5m"),
        ("BNBUSDT", "5m")
    ]
    
    results = []
    
    for symbol, interval in test_pairs:
        print(f"\n{'─'*80}")
        print(f"📊 Testando: {symbol} ({interval})")
        print(f"{'─'*80}\n")
        
        # 1. Buscar dados da Binance
        print(f"🔄 Buscando dados da Binance...")
        candles = get_binance_candles(symbol, interval, 100)
        
        if not candles:
            print(f"❌ Falha ao buscar dados para {symbol}")
            continue
        
        print(f"✅ {len(candles)} candles obtidos")
        print(f"   Primeiro: ${candles[0]['close']:.2f}")
        print(f"   Último: ${candles[-1]['close']:.2f}")
        print(f"   Variação: ${candles[-1]['close'] - candles[0]['close']:.2f}")
        
        # 2. Enviar para análise
        print(f"\n🔄 Enviando para análise do motor...")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/trade-setup",
                json={
                    "candles": candles,
                    "capital": 10000.0,
                    "explain_with_ai": False  # Mais rápido sem IA
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                continue
            
            result = response.json()
            
            # 3. Exibir resultados
            print(f"\n{'='*80}")
            print(f"✅ ANÁLISE COMPLETA - {symbol}")
            print(f"{'='*80}\n")
            
            signal_emoji = {
                "CALL": "📈",
                "PUT": "📉",
                "WAIT": "⏸️"
            }
            
            signal_color = {
                "CALL": "\033[92m",  # Verde
                "PUT": "\033[91m",   # Vermelho
                "WAIT": "\033[93m"   # Amarelo
            }
            
            reset_color = "\033[0m"
            color = signal_color.get(result['signal'], reset_color)
            
            print(f"{color}🎯 SINAL: {signal_emoji.get(result['signal'], '')} {result['signal']}{reset_color}")
            print(f"📊 SCORE: {result['score']}/100")
            print(f"💯 CONFIANÇA: {result['confidence']*100:.1f}%")
            print()
            
            print(f"📈 NÍVEIS:")
            print(f"   Entrada:      ${result['entry_price']:.2f}")
            print(f"   Stop Loss:    ${result['stop_loss']:.2f}")
            print(f"   Take Profit 1: ${result['take_profit_1']:.2f}")
            print(f"   Take Profit 2: ${result['take_profit_2']:.2f}")
            print()
            
            print(f"📊 INDICADORES:")
            print(f"   Tendência: {result['trend']}")
            print(f"   RSI: {result['rsi_value']:.1f}")
            print(f"   EMA20: ${result['ema_20']:.2f}")
            print(f"   EMA50: ${result['ema_50']:.2f}")
            print()
            
            print(f"💰 RISCO:")
            print(f"   RR TP1: 1:{result['risk_reward_1']:.2f}")
            print(f"   RR TP2: 1:{result['risk_reward_2']:.2f}")
            print(f"   Risco: ${result['risk_amount']:.2f}")
            print()
            
            if result['reasons']:
                print(f"✅ RAZÕES:")
                for reason in result['reasons']:
                    print(f"   {reason}")
                print()
            
            if result['warnings']:
                print(f"⚠️  AVISOS:")
                for warning in result['warnings']:
                    print(f"   {warning}")
                print()
            
            # Guardar resultado
            results.append({
                "symbol": symbol,
                "signal": result['signal'],
                "score": result['score'],
                "confidence": result['confidence']
            })
            
        except Exception as e:
            print(f"❌ Erro na análise: {str(e)}")
    
    # 4. Resumo Final
    print(f"\n{'='*80}")
    print(f"📊 RESUMO FINAL DOS TESTES")
    print(f"{'='*80}\n")
    
    if results:
        signals_count = {
            "CALL": sum(1 for r in results if r['signal'] == 'CALL'),
            "PUT": sum(1 for r in results if r['signal'] == 'PUT'),
            "WAIT": sum(1 for r in results if r['signal'] == 'WAIT')
        }
        
        avg_score = sum(r['score'] for r in results) / len(results)
        avg_confidence = sum(r['confidence'] for r in results) / len(results) * 100
        
        print(f"Total de testes: {len(results)}")
        print(f"Sinais gerados:")
        print(f"   📈 CALL: {signals_count['CALL']}")
        print(f"   📉 PUT: {signals_count['PUT']}")
        print(f"   ⏸️  WAIT: {signals_count['WAIT']}")
        print()
        print(f"Score médio: {avg_score:.1f}/100")
        print(f"Confiança média: {avg_confidence:.1f}%")
        print()
        
        # Análise
        if signals_count['WAIT'] == len(results):
            print("🎯 Sistema CONSERVADOR: Nenhum sinal gerado (aguardando setups melhores)")
            print("   Isso é BOM! Significa que o motor não está forçando entradas ruins.")
        elif signals_count['WAIT'] >= len(results) * 0.7:
            print("🎯 Sistema SELETIVO: Poucos sinais gerados (foco em qualidade)")
            print("   Excelente! Alta seletividade = maior assertividade esperada.")
        else:
            print("🎯 Sistema ATIVO: Múltiplos sinais detectados")
            print(f"   Validar qualidade: Score médio {avg_score:.1f}/100")
    
    print(f"\n{'='*80}")
    print("✅ TESTES FINALIZADOS")
    print("="*80 + "\n")
    
    print("📝 PRÓXIMOS PASSOS:")
    print("   1. Validar sinais manualmente em gráficos")
    print("   2. Fazer paper trading por 1-2 semanas")
    print("   3. Coletar win rate real antes de operar com dinheiro")
    print("   4. Ajustar parâmetros se necessário")
    print()


if __name__ == "__main__":
    test_with_real_data()
