"""
🎯 VALIDAÇÃO SCALPING 5 MINUTOS - Dados Reais
Testa o novo motor de scalping em timeframe de 5min
"""

import requests
import time
import statistics
import sys
sys.path.append('/app/backend')

from scalping_engine import ScalpingEngine, Candle, SignalType

CRYPTOCOMPARE_API = "https://min-api.cryptocompare.com/data/v2"

def get_5min_data(symbol="BTC", limit=2000):
    """Busca dados de 5 MINUTOS"""
    try:
        print(f"🔄 Buscando dados de 5min para {symbol}...")
        
        url = f"{CRYPTOCOMPARE_API}/histominute"
        params = {
            "fsym": symbol,
            "tsym": "USD",
            "limit": limit,
            "aggregate": 5  # 5 minutos
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
                
                print(f"✅ {len(candles)} candles de 5min obtidos")
                return candles
        
        print(f"❌ Erro ao buscar dados")
        return None
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None


def simulate_scalp_trade(signal, entry, sl, tp1, tp2, candles_after):
    """Simula trade de scalping (rápido)"""
    if not candles_after or len(candles_after) < 2:
        return 'NEUTRAL', 0, 'insufficient_data'
    
    # Scalping = saída rápida (máximo 10 candles = 50 min)
    max_candles = min(len(candles_after), 10)
    
    position = 1.0
    total_profit = 0
    tp1_hit = False
    
    if signal == SignalType.CALL:
        for i, candle in enumerate(candles_after[:max_candles]):
            # Stop loss
            if candle.low <= sl:
                loss = (sl - entry) * position
                total_profit += loss
                return 'LOSS', total_profit, f'stop_candle_{i}'
            
            # TP2 (home run)
            if not tp1_hit and candle.high >= tp2:
                profit = (tp2 - entry) * position
                total_profit += profit
                return 'WIN', total_profit, f'tp2_candle_{i}'
            
            # TP1 (fechar 70%)
            if not tp1_hit and candle.high >= tp1:
                profit = (tp1 - entry) * 0.7
                total_profit += profit
                position = 0.3
                tp1_hit = True
        
        # Time exit (fechar no final)
        final = candles_after[max_candles-1].close
        remaining = (final - entry) * position
        total_profit += remaining
        
        return ('WIN' if total_profit > 0 else 'LOSS'), total_profit, 'time_exit'
    
    elif signal == SignalType.PUT:
        for i, candle in enumerate(candles_after[:max_candles]):
            # Stop loss
            if candle.high >= sl:
                loss = (entry - sl) * position
                total_profit += loss
                return 'LOSS', total_profit, f'stop_candle_{i}'
            
            # TP2
            if not tp1_hit and candle.low <= tp2:
                profit = (entry - tp2) * position
                total_profit += profit
                return 'WIN', total_profit, f'tp2_candle_{i}'
            
            # TP1
            if not tp1_hit and candle.low <= tp1:
                profit = (entry - tp1) * 0.7
                total_profit += profit
                position = 0.3
                tp1_hit = True
        
        final = candles_after[max_candles-1].close
        remaining = (entry - final) * position
        total_profit += remaining
        
        return ('WIN' if total_profit > 0 else 'LOSS'), total_profit, 'time_exit'
    
    return 'NEUTRAL', 0, 'no_signal'


def backtest_scalping(candles, asset_name):
    """Backtest scalping em 5min"""
    print(f"\n{'='*80}")
    print(f"📊 BACKTEST SCALPING 5MIN: {asset_name}")
    print(f"{'='*80}\n")
    
    engine = ScalpingEngine()
    
    results = []
    window = 100  # Janela menor para scalping
    step = 5  # Mais granular
    
    print(f"📈 Total candles: {len(candles)}")
    print(f"🔄 Processando...\n")
    
    for i in range(0, len(candles) - window - 15, step):
        analysis_window = candles[i:i+window]
        future_candles = candles[i+window:i+window+15]
        
        signal_data = engine.analyze(analysis_window, 10000)
        
        if signal_data.signal in [SignalType.CALL, SignalType.PUT]:
            outcome, profit, reason = simulate_scalp_trade(
                signal_data.signal,
                signal_data.entry_price,
                signal_data.stop_loss,
                signal_data.take_profit_1,
                signal_data.take_profit_2,
                future_candles
            )
            
            results.append({
                'signal': signal_data.signal.value,
                'score': signal_data.score,
                'outcome': outcome,
                'profit': profit
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
    print("🎯 VALIDAÇÃO SCALPING - TIMEFRAME 5 MINUTOS")
    print("   Motor otimizado para scalping rápido")
    print("="*80 + "\n")
    
    assets = [("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("BNB", "BNB")]
    
    all_results = {}
    
    for symbol, name in assets:
        candles = get_5min_data(symbol, 2000)
        
        if candles and len(candles) >= 150:
            results = backtest_scalping(candles, name)
            
            if results:
                metrics = calculate_metrics(results)
                all_results[name] = metrics
                
                print(f"\n✅ RESULTADOS {name} (5min):")
                print(f"   Trades: {metrics['total']}")
                print(f"   Wins: {metrics['wins']} | Losses: {metrics['losses']}")
                print(f"   🎯 WIN RATE: {metrics['win_rate']:.1f}%")
                print(f"   💰 Lucro: ${metrics['total_profit']:.2f}")
                print(f"   📊 PF: {metrics['profit_factor']:.2f}")
                print(f"   ⭐ Score Médio: {metrics['avg_score']:.1f}")
        
        time.sleep(2)
    
    # RESUMO
    print(f"\n{'='*80}")
    print(f"📊 RESUMO FINAL - SCALPING 5MIN")
    print(f"{'='*80}\n")
    
    if all_results:
        total_trades = sum(m['total'] for m in all_results.values())
        total_wins = sum(m['wins'] for m in all_results.values())
        total_losses = sum(m['losses'] for m in all_results.values())
        
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
        total_profit = sum(m['total_profit'] for m in all_results.values())
        avg_pf = statistics.mean([m['profit_factor'] for m in all_results.values() if m['profit_factor'] > 0])
        
        print(f"📈 ESTATÍSTICAS GLOBAIS (5MIN):")
        print(f"   Total Trades: {total_trades}")
        print(f"   Vencedores: {total_wins}")
        print(f"   Perdedores: {total_losses}")
        print(f"\n🎯 WIN RATE GERAL: {overall_wr:.1f}%")
        print(f"💰 Lucro Total: ${total_profit:.2f}")
        print(f"📊 Profit Factor Médio: {avg_pf:.2f}")
        
        print(f"\n{'─'*80}")
        print(f"📊 DESEMPENHO POR ATIVO:")
        print(f"{'─'*80}\n")
        
        for name, m in all_results.items():
            print(f"{name}:")
            print(f"   WR: {m['win_rate']:.1f}% | Trades: {m['total']} | Lucro: ${m['total_profit']:.2f} | PF: {m['profit_factor']:.2f}")
        
        print(f"\n{'─'*80}")
        print(f"🎯 AVALIAÇÃO:")
        print(f"{'─'*80}\n")
        
        if overall_wr >= 60 and total_profit > 0:
            print(f"🎉 EXCELENTE! Win rate {overall_wr:.1f}% >= 60%")
            print(f"✅ Sistema de scalping FUNCIONA em 5min!")
            print(f"✅ Lucro de ${total_profit:.2f} validado")
        elif overall_wr >= 50 and total_profit > 0:
            print(f"✅ BOM! Win rate {overall_wr:.1f}% >= 50%")
            print(f"✅ Sistema é lucrativo em 5min")
        elif total_profit > 0 and avg_pf > 1.5:
            print(f"✅ LUCRATIVO! Mesmo com WR {overall_wr:.1f}%")
            print(f"✅ Profit Factor {avg_pf:.2f} compensa")
        else:
            print(f"⚠️ Precisa mais otimização")
            print(f"   WR: {overall_wr:.1f}% | Lucro: ${total_profit:.2f}")
    
    print(f"\n{'='*80}")
    print("✅ VALIDAÇÃO SCALPING 5MIN COMPLETA")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
