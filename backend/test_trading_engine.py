"""
Script de teste para o Trading Engine
Testa análise de setup com dados simulados
"""

import requests
import json
from datetime import datetime, timedelta

# URL do backend
BASE_URL = "http://localhost:8001/api"

# Gerar candles de teste (simulando tendência de alta)
def generate_test_candles(num_candles=100, trend="bullish"):
    """Gera candles simulados para teste"""
    candles = []
    base_price = 1.1850
    timestamp = int(datetime.now().timestamp())
    
    for i in range(num_candles):
        if trend == "bullish":
            # Tendência de alta com pequenas correções
            base_price += 0.0001 * (1 + (i % 5 == 0) * -2)
        elif trend == "bearish":
            # Tendência de baixa
            base_price -= 0.0001 * (1 + (i % 5 == 0) * -2)
        else:
            # Lateral
            base_price += 0.0001 * ((i % 2) * 2 - 1)
        
        open_price = base_price
        high_price = base_price + 0.00015
        low_price = base_price - 0.00010
        close_price = base_price + (0.00005 if trend == "bullish" else -0.00005)
        volume = 1000 + (i * 10)
        
        candles.append({
            "timestamp": timestamp + (i * 60),  # 1 min cada
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume
        })
    
    return candles


def test_trade_setup():
    """Testa o endpoint /trade-setup"""
    print("\n" + "="*80)
    print("🎯 TESTE: Trading Engine - Análise de Setup")
    print("="*80 + "\n")
    
    # Gerar candles de teste (tendência de alta)
    candles = generate_test_candles(100, trend="bullish")
    
    print(f"📊 Gerados {len(candles)} candles de teste (tendência de alta)")
    print(f"   Primeiro: {candles[0]['close']:.5f}")
    print(f"   Último: {candles[-1]['close']:.5f}")
    print(f"   Variação: {(candles[-1]['close'] - candles[0]['close']):.5f}")
    print()
    
    # Fazer requisição
    payload = {
        "candles": candles,
        "capital": 10000.0,
        "explain_with_ai": False  # Primeiro sem IA para ser mais rápido
    }
    
    print("🔄 Enviando candles para análise...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/trade-setup",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ ANÁLISE COMPLETA:\n")
            print(f"{'='*80}")
            print(f"🎯 SINAL: {result['signal']}")
            print(f"📊 SCORE: {result['score']}/100")
            print(f"💯 CONFIANÇA: {result['confidence']*100:.1f}%")
            print(f"{'='*80}\n")
            
            print(f"📈 NÍVEIS DE PREÇO:")
            print(f"   Entrada:      {result['entry_price']:.5f}")
            print(f"   Stop Loss:    {result['stop_loss']:.5f}")
            print(f"   Take Profit 1: {result['take_profit_1']:.5f}")
            print(f"   Take Profit 2: {result['take_profit_2']:.5f}")
            print()
            
            print(f"📊 INDICADORES TÉCNICOS:")
            print(f"   Tendência:  {result['trend']}")
            print(f"   EMA 20:     {result['ema_20']:.5f}")
            print(f"   EMA 50:     {result['ema_50']:.5f}")
            print(f"   RSI:        {result['rsi_value']:.1f}")
            print(f"   ATR:        {result['atr_value']:.5f}")
            print()
            
            print(f"💰 GESTÃO DE RISCO:")
            print(f"   Risk/Reward TP1: 1:{result['risk_reward_1']:.2f}")
            print(f"   Risk/Reward TP2: 1:{result['risk_reward_2']:.2f}")
            print(f"   Risco por trade: ${result['risk_amount']:.2f}")
            print()
            
            print(f"✅ RAZÕES DO SINAL:")
            for reason in result['reasons']:
                print(f"   {reason}")
            print()
            
            if result['warnings']:
                print(f"⚠️  AVISOS:")
                for warning in result['warnings']:
                    print(f"   {warning}")
                print()
            
            print("\n" + "="*80)
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("="*80 + "\n")
            
            return True
        else:
            print(f"\n❌ ERRO: Status {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO ao chamar API: {str(e)}")
        return False


def test_backtest():
    """Testa o endpoint /backtest"""
    print("\n" + "="*80)
    print("📊 TESTE: Backtest do Trading Engine")
    print("="*80 + "\n")
    
    # Gerar mais candles para backtest
    candles = generate_test_candles(200, trend="bullish")
    
    print(f"📊 Gerados {len(candles)} candles para backtest")
    print()
    
    payload = {
        "candles": candles,
        "initial_capital": 10000.0
    }
    
    print("🔄 Executando backtest...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/backtest",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ RESULTADOS DO BACKTEST:\n")
            print(f"{'='*80}")
            print(f"📊 TRADES EXECUTADOS: {result['total_trades']}")
            print(f"✅ Vencedores: {result['wins']}")
            print(f"❌ Perdedores: {result['losses']}")
            print(f"🎯 WIN RATE: {result['win_rate']:.1f}%")
            print(f"{'='*80}\n")
            
            print(f"💰 PERFORMANCE FINANCEIRA:")
            print(f"   Capital Inicial:  ${result['initial_capital']:.2f}")
            print(f"   Capital Final:    ${result['final_capital']:.2f}")
            print(f"   Lucro/Prejuízo:   ${result['profit']:.2f}")
            print(f"   Retorno:          {result['profit_pct']:.2f}%")
            print(f"   Profit Factor:    {result['profit_factor']:.2f}")
            print()
            
            print("\n" + "="*80)
            print("✅ BACKTEST CONCLUÍDO COM SUCESSO!")
            print("="*80 + "\n")
            
            return True
        else:
            print(f"\n❌ ERRO: Status {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO ao chamar API: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n🚀 Iniciando Testes do Trading Engine\n")
    
    # Teste 1: Análise de Setup
    success1 = test_trade_setup()
    
    # Teste 2: Backtest
    if success1:
        success2 = test_backtest()
    
    print("\n🏁 Testes Finalizados\n")
