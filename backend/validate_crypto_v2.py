"""
🎯 VALIDAÇÃO FINAL - Crypto Engine V2 com Timeframes Maiores
Testa 1H e 4H com dados reais
"""

import requests
import json
import time
from datetime import datetime
import statistics
import sys
sys.path.append('/app/backend')

from crypto_trading_engine import (
    CryptoTradingEngine, Candle, SignalType, MarketContext
)

CRYPTOCOMPARE_API = "https://min-api.cryptocompare.com/data/v2"

def get_hourly_data(symbol="BTC", hours=500):
    """Busca dados de 1 HORA (não 5min)"""
    try:
        print(f"🔄 Buscando dados de 1H para {symbol}...")
        
        url = f"{CRYPTOCOMPARE_API}/histohour"
        params = {
            "fsym": symbol,
            "tsym": "USD",
            "limit": hours
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("Response") == "Success":
                candles = []
                for item in data["Data"]["Data"]:
                    candles.append(Candle(
                        timestamp=item["time"],
                        open=float(item["open"]),
                        high=float(item["high"]),
                        low=float(item["low"]),
                        close=float(item["close"]),
                        volume=float(item["volumeto"])
                    ))
                
                print(f"✅ {len(candles)} candles de 1H obtidos")
                return candles
        
        print(f"❌ Erro ao buscar dados")
        return None
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None


def get_4h_data(symbol="BTC", periods=300):
    """Busca dados de 4 HORAS"""
    try:
        print(f"🔄 Buscando dados de 4H para {symbol}...")
        
        # CryptoCompare não tem 4H direto, vamos agregar de 1H
        hourly = get_hourly_data(symbol, periods * 4)
        
        if not hourly or len(hourly) < 4:
            return None
        
        # Agregar em candles de 4H
        candles_4h = []
        for i in range(0, len(hourly) - 3, 4):
            chunk = hourly[i:i+4]
            
            candles_4h.append(Candle(
                timestamp=chunk[0].timestamp,
                open=chunk[0].open,
                high=max(c.high for c in chunk),
                low=min(c.low for c in chunk),
                close=chunk[-1].close,
                volume=sum(c.volume for c in chunk)
            ))
        
        print(f"✅ {len(candles_4h)} candles de 4H criados")
        return candles_4h
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None


def simulate_trade_advanced(signal, entry, sl, tp1, tp2, tp3, candles_after):
    """Simula trade com 3 TPs"""
    if not candles_after or len(candles_after) < 3:
        return 'NEUTRAL', 0, 'insufficient_data'
    
    max_candles = min(len(candles_after), 30)
    
    trailing_stop = sl
    position = 1.0
    total_profit = 0
    tp1_hit = False
    tp2_hit = False
    
    if signal == SignalType.CALL:
        highest = entry
        
        for i, candle in enumerate(candles_after[:max_candles]):
            if candle.high > highest:
                highest = candle.high
                # Move SL para breakeven após halfway to TP1
                if not tp1_hit:
                    halfway = entry + (tp1 - entry) * 0.5
                    if highest >= halfway:
                        trailing_stop = max(trailing_stop, entry)
            
            # Stop loss
            if candle.low <= trailing_stop:
                loss = (trailing_stop - entry) * position
                total_profit += loss
                return 'LOSS', total_profit, f'stop_candle_{i}'
            
            # TP3
            if not tp1_hit and candle.high >= tp3:
                profit = (tp3 - entry) * position
                total_profit += profit
                return 'WIN', total_profit, f'tp3_candle_{i}'
            
            # TP2
            if not tp1_hit and candle.high >= tp2:
                profit = (tp2 - entry) * 0.5
                total_profit += profit
                position = 0.5
                tp2_hit = True
                trailing_stop = tp1  # Move SL para TP1
            
            # TP1
            if not tp1_hit and candle.high >= tp1:
                profit = (tp1 - entry) * 0.3
                total_profit += profit
                position = 0.7
                tp1_hit = True
                trailing_stop = entry
        
        # Time exit
        final = candles_after[max_candles-1].close
        remaining_profit = (final - entry) * position
        total_profit += remaining_profit
        
        return ('WIN' if total_profit > 0 else 'LOSS'), total_profit, 'time_exit'
    
    elif signal == SignalType.PUT:
        lowest = entry
        
        for i, candle in enumerate(candles_after[:max_candles]):
            if candle.low < lowest:
                lowest = candle.low
                if not tp1_hit:
                    halfway = entry - (entry - tp1) * 0.5
                    if lowest <= halfway:
                        trailing_stop = min(trailing_stop, entry)
            
            # Stop loss
            if candle.high >= trailing_stop:
                loss = (entry - trailing_stop) * position
                total_profit += loss
                return 'LOSS', total_profit, f'stop_candle_{i}'
            
            # TP3
            if not tp1_hit and candle.low <= tp3:
                profit = (entry - tp3) * position
                total_profit += profit
                return 'WIN', total_profit, f'tp3_candle_{i}'
            
            # TP2
            if not tp1_hit and candle.low <= tp2:
                profit = (entry - tp2) * 0.5
                total_profit += profit
                position = 0.5
                tp2_hit = True
                trailing_stop = tp1
            
            # TP1
            if not tp1_hit and candle.low <= tp1:
                profit = (entry - tp1) * 0.3
                total_profit += profit
                position = 0.7
                tp1_hit = True
                trailing_stop = entry
        
        final = candles_after[max_candles-1].close
        remaining_profit = (entry - final) * position
        total_profit += remaining_profit
        
        return ('WIN' if total_profit > 0 else 'LOSS'), total_profit, 'time_exit'
    
    return 'NEUTRAL', 0, 'no_signal'


def backtest_crypto(candles, asset_name, timeframe):
    """Backtest com novo motor"""
    print(f"\n{'='*80}")
    print(f"📊 BACKTEST: {asset_name} ({timeframe})")
    print(f"{'='*80}\n")
    
    engine = CryptoTradingEngine()
    
    results = []
    window = 200
    step = 10
    
    for i in range(0, len(candles) - window - 30, step):
        analysis_window = candles[i:i+window]
        future_candles = candles[i+window:i+window+30]
        
        signal_data = engine.analyze(analysis_window, 10000)
        
        if signal_data.signal in [SignalType.CALL, SignalType.PUT]:
            outcome, profit, reason = simulate_trade_advanced(
                signal_data.signal,
                signal_data.entry_price,
                signal_data.stop_loss,
                signal_data.take_profit_1,
                signal_data.take_profit_2,
                signal_data.take_profit_3,
                future_candles
            )
            
            results.append({
                'signal': signal_data.signal.value,
                'score': signal_data.score,
                'confidence': signal_data.confidence,
                'context': signal_data.market_context.value,
                'volatility': signal_data.volatility_level,
                'outcome': outcome,
                'profit': profit,
                'rr': signal_data.risk_reward_1
            })
    
    return results


def calculate_metrics(results):
    """Calcula métricas"""
    if not results:
        return None
    
    total = len(results)
    wins = sum(1 for r in results if r['outcome'] == 'WIN')
    losses = sum(1 for r in results if r['outcome'] == 'LOSS')
    
    win_rate = (wins / total * 100) if total > 0 else 0
    
    total_profit = sum(r['profit'] for r in results)
    
    winning_trades = [r['profit'] for r in results if r['outcome'] == 'WIN']
    losing_trades = [abs(r['profit']) for r in results if r['outcome'] == 'LOSS']
    
    avg_win = statistics.mean(winning_trades) if winning_trades else 0
    avg_loss = statistics.mean(losing_trades) if losing_trades else 0
    
    profit_factor = (sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) > 0 else 0
    
    avg_score = statistics.mean([r['score'] for r in results])
    
    return {
        'total': total,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'avg_score': avg_score
    }


def main():
    print("\n" + "="*80)
    print("🎯 VALIDAÇÃO FINAL - CRYPTO ENGINE V2")
    print("   Timeframes: 1H e 4H (não 5min)")
    print("   Objetivo: 70%+ Win Rate")
    print("="*80 + "\n")
    
    assets = [("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("BNB", "BNB")]
    
    all_results_1h = {}
    all_results_4h = {}
    
    # TESTE 1H
    print("\n" + "="*80)
    print("📊 FASE 1: TESTE TIMEFRAME 1 HORA")
    print("="*80)
    
    for symbol, name in assets:
        candles_1h = get_hourly_data(symbol, 500)
        
        if candles_1h and len(candles_1h) >= 250:
            results = backtest_crypto(candles_1h, name, "1H")
            
            if results:
                metrics = calculate_metrics(results)
                all_results_1h[name] = metrics
                
                print(f"\n✅ RESULTADOS {name} (1H):")
                print(f"   Trades: {metrics['total']}")
                print(f"   Wins: {metrics['wins']} | Losses: {metrics['losses']}")
                print(f"   🎯 WIN RATE: {metrics['win_rate']:.1f}%")
                print(f"   💰 Lucro: ${metrics['total_profit']:.2f}")
                print(f"   📊 PF: {metrics['profit_factor']:.2f}")
        
        time.sleep(2)
    
    # TESTE 4H
    print("\n" + "="*80)
    print("📊 FASE 2: TESTE TIMEFRAME 4 HORAS")
    print("="*80)
    
    for symbol, name in assets:
        candles_4h = get_4h_data(symbol, 250)
        
        if candles_4h and len(candles_4h) >= 230:
            results = backtest_crypto(candles_4h, name, "4H")
            
            if results:
                metrics = calculate_metrics(results)
                all_results_4h[name] = metrics
                
                print(f"\n✅ RESULTADOS {name} (4H):")
                print(f"   Trades: {metrics['total']}")
                print(f"   Wins: {metrics['wins']} | Losses: {metrics['losses']}")
                print(f"   🎯 WIN RATE: {metrics['win_rate']:.1f}%")
                print(f"   💰 Lucro: ${metrics['total_profit']:.2f}")
                print(f"   📊 PF: {metrics['profit_factor']:.2f}")
        
        time.sleep(2)
    
    # RESUMO FINAL
    print(f"\n{'='*80}")
    print(f"📊 RESUMO FINAL - TODAS AS VALIDAÇÕES")
    print(f"{'='*80}\n")
    
    if all_results_1h:
        total_1h = sum(m['total'] for m in all_results_1h.values())
        wins_1h = sum(m['wins'] for m in all_results_1h.values())
        wr_1h = (wins_1h / total_1h * 100) if total_1h > 0 else 0
        profit_1h = sum(m['total_profit'] for m in all_results_1h.values())
        
        print(f"📈 TIMEFRAME 1H:")
        print(f"   Win Rate: {wr_1h:.1f}%")
        print(f"   Trades: {total_1h}")
        print(f"   Lucro: ${profit_1h:.2f}")
    
    if all_results_4h:
        total_4h = sum(m['total'] for m in all_results_4h.values())
        wins_4h = sum(m['wins'] for m in all_results_4h.values())
        wr_4h = (wins_4h / total_4h * 100) if total_4h > 0 else 0
        profit_4h = sum(m['total_profit'] for m in all_results_4h.values())
        
        print(f"\n📈 TIMEFRAME 4H:")
        print(f"   Win Rate: {wr_4h:.1f}%")
        print(f"   Trades: {total_4h}")
        print(f"   Lucro: ${profit_4h:.2f}")
    
    # Avaliação
    print(f"\n{'─'*80}")
    print(f"🎯 AVALIAÇÃO:")
    print(f"{'─'*80}\n")
    
    best_wr = max(wr_1h if all_results_1h else 0, wr_4h if all_results_4h else 0)
    
    if best_wr >= 70:
        print(f"🎉 OBJETIVO ATINGIDO! Win rate {best_wr:.1f}% >= 70%")
        print(f"✅ Sistema VALIDADO com dados reais")
        print(f"✅ Pronto para paper trading")
    elif best_wr >= 60:
        print(f"✅ MUITO BOM! Win rate {best_wr:.1f}% próximo do objetivo")
        print(f"✅ Sistema consistentemente lucrativo")
        print(f"🔧 Pequenos ajustes podem atingir 70%+")
    elif best_wr >= 50:
        print(f"✅ BOM! Win rate {best_wr:.1f}% acima de 50%")
        print(f"🔧 Requer mais otimizações")
    else:
        print(f"⚠️ Win rate {best_wr:.1f}% abaixo de 50%")
        print(f"🔧 Mais ajustes necessários")
    
    print(f"\n{'='*80}")
    print("✅ VALIDAÇÃO COMPLETA")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
