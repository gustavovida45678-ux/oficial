"""
🎯 TESTE COMPARATIVO - V2 vs V3 OTIMIZADO
Compara resultados antes e depois das melhorias
"""

import requests
import time
import statistics
import sys
from datetime import datetime
sys.path.append('/app/backend')

from forex_engine_v2 import ForexEngine as ForexV2, Candle, SignalType
from forex_engine_v3_optimized import OptimizedForexEngine as ForexV3

def get_real_forex_yahoo(pair="EURUSD=X"):
    """Busca dados reais do Yahoo"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}"
        params = {"range": "3mo", "interval": "1h", "includePrePost": "false"}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quotes = result['indicators']['quote'][0]
                
                candles = []
                for i in range(len(timestamps)):
                    if quotes['close'][i] is not None:
                        candles.append(Candle(
                            timestamp=timestamps[i],
                            open=float(quotes['open'][i]) if quotes['open'][i] else float(quotes['close'][i]),
                            high=float(quotes['high'][i]) if quotes['high'][i] else float(quotes['close'][i]),
                            low=float(quotes['low'][i]) if quotes['low'][i] else float(quotes['close'][i]),
                            close=float(quotes['close'][i]),
                            volume=float(quotes['volume'][i]) if quotes['volume'][i] else 1000.0
                        ))
                
                return candles
        return None
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None


def simulate_trade(signal_type, entry, sl, sl_pips, tp1, tp1_pips, tp2, tp2_pips, candles_after):
    """Simula trade"""
    if not candles_after or len(candles_after) < 3:
        return 'NEUTRAL', 0
    
    total_cost_pips = 2.0
    max_candles = min(len(candles_after), 48)
    position = 1.0
    total_profit_pips = -total_cost_pips
    tp1_hit = False
    
    if signal_type == 'CALL':
        for candle in candles_after[:max_candles]:
            if candle.low <= sl:
                return 'LOSS', -sl_pips - total_cost_pips
            
            if not tp1_hit and candle.high >= tp2:
                return 'WIN', tp2_pips - total_cost_pips
            
            if not tp1_hit and candle.high >= tp1:
                total_profit_pips = (tp1_pips - total_cost_pips) * 0.7
                position = 0.3
                tp1_hit = True
        
        final = candles_after[max_candles-1].close
        remaining = ((final - entry) / 0.0001) * position
        total_profit_pips += remaining
        
        return ('WIN' if total_profit_pips > 0 else 'LOSS'), total_profit_pips
    
    else:  # PUT
        for candle in candles_after[:max_candles]:
            if candle.high >= sl:
                return 'LOSS', -sl_pips - total_cost_pips
            
            if not tp1_hit and candle.low <= tp2:
                return 'WIN', tp2_pips - total_cost_pips
            
            if not tp1_hit and candle.low <= tp1:
                total_profit_pips = (tp1_pips - total_cost_pips) * 0.7
                position = 0.3
                tp1_hit = True
        
        final = candles_after[max_candles-1].close
        remaining = ((entry - final) / 0.0001) * position
        total_profit_pips += remaining
        
        return ('WIN' if total_profit_pips > 0 else 'LOSS'), total_profit_pips


def test_engine(engine, engine_name, candles, pair_name):
    """Testa um motor"""
    print(f"\n{'='*100}")
    print(f"🔬 TESTE: {engine_name}")
    print(f"{'='*100}\n")
    
    all_trades = []
    window = 200
    step = 10
    
    for i in range(0, len(candles) - window - 48, step):
        analysis_window = candles[i:i+window]
        future_candles = candles[i+window:i+window+48]
        
        signal_data = engine.analyze(analysis_window)
        
        if signal_data.signal.value in ['CALL', 'PUT']:
            outcome, profit_pips = simulate_trade(
                signal_data.signal.value,
                signal_data.entry_price,
                signal_data.stop_loss,
                signal_data.stop_loss_pips,
                signal_data.take_profit_1,
                signal_data.take_profit_1_pips,
                signal_data.take_profit_2,
                signal_data.take_profit_2_pips,
                future_candles
            )
            
            all_trades.append({
                'signal': signal_data.signal.value,
                'score': signal_data.score,
                'session': signal_data.session.value,
                'outcome': outcome,
                'profit_pips': profit_pips
            })
    
    if not all_trades:
        print("⚠️ Nenhum trade gerado")
        return None
    
    # Métricas
    total = len(all_trades)
    wins = sum(1 for t in all_trades if t['outcome'] == 'WIN')
    
    win_rate = (wins / total * 100) if total > 0 else 0
    total_pips = sum(t['profit_pips'] for t in all_trades)
    total_usd = total_pips * 10
    
    winning_pips = [t['profit_pips'] for t in all_trades if t['outcome'] == 'WIN']
    losing_pips = [abs(t['profit_pips']) for t in all_trades if t['outcome'] == 'LOSS']
    
    avg_win = statistics.mean(winning_pips) if winning_pips else 0
    avg_loss = statistics.mean(losing_pips) if losing_pips else 0
    
    pf = (sum(winning_pips) / sum(losing_pips)) if losing_pips and sum(losing_pips) > 0 else 0
    
    # Análise por sessão
    sessions_stats = {}
    for t in all_trades:
        sess = t['session']
        if sess not in sessions_stats:
            sessions_stats[sess] = {'wins': 0, 'total': 0}
        
        sessions_stats[sess]['total'] += 1
        if t['outcome'] == 'WIN':
            sessions_stats[sess]['wins'] += 1
    
    print(f"📊 RESULTADOS:")
    print(f"   Total Trades: {total}")
    print(f"   Vencedores: {wins}")
    print(f"   Perdedores: {total - wins}")
    print(f"   🎯 WIN RATE: {win_rate:.1f}%")
    print(f"   💰 Total Pips: {total_pips:+.1f}")
    print(f"   💵 Total USD: ${total_usd:+.2f}")
    print(f"   📊 Profit Factor: {pf:.2f}")
    print(f"   Média Win: {avg_win:.1f} pips")
    print(f"   Média Loss: {avg_loss:.1f} pips")
    
    print(f"\n📊 Por Sessão:")
    for sess, stats in sessions_stats.items():
        wr = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"   {sess}: {wr:.1f}% WR ({stats['wins']}/{stats['total']})")
    
    return {
        'total': total,
        'wins': wins,
        'win_rate': win_rate,
        'total_pips': total_pips,
        'total_usd': total_usd,
        'profit_factor': pf,
        'avg_win': avg_win,
        'avg_loss': avg_loss
    }


def main():
    print("\n" + "="*100)
    print("🎯 TESTE COMPARATIVO - FOREX ENGINE V2 vs V3 OTIMIZADO")
    print("   Melhorias implementadas:")
    print("   ✅ Score mínimo: 70 → 80")
    print("   ✅ Filtro sessão ASIA removida")
    print("   ✅ ATR mínimo: 10 → 15 pips")
    print("   ✅ Confirmação de 2 candles adicionada")
    print("   ✅ Pullback range mais estreito")
    print("="*100)
    
    pairs = [
        ("EURUSD=X", "EUR/USD"),
        ("GBPUSD=X", "GBP/USD"),
    ]
    
    results_v2 = []
    results_v3 = []
    
    for yahoo_pair, forex_pair in pairs:
        print(f"\n{'='*100}")
        print(f"📊 PAR: {forex_pair}")
        print(f"{'='*100}")
        
        candles = get_real_forex_yahoo(yahoo_pair)
        
        if not candles or len(candles) < 250:
            print("⚠️ Dados insuficientes")
            continue
        
        print(f"\n✅ {len(candles)} candles obtidos")
        print(f"   De: {datetime.fromtimestamp(candles[0].timestamp)}")
        print(f"   Até: {datetime.fromtimestamp(candles[-1].timestamp)}")
        
        # Testar V2
        engine_v2 = ForexV2(pair=forex_pair)
        result_v2 = test_engine(engine_v2, "ENGINE V2 (Atual)", candles, forex_pair)
        if result_v2:
            results_v2.append(result_v2)
        
        # Testar V3
        engine_v3 = ForexV3(pair=forex_pair)
        result_v3 = test_engine(engine_v3, "ENGINE V3 (Otimizado)", candles, forex_pair)
        if result_v3:
            results_v3.append(result_v3)
        
        time.sleep(2)
    
    # COMPARAÇÃO FINAL
    print(f"\n{'='*100}")
    print(f"📊 COMPARAÇÃO FINAL: V2 vs V3")
    print(f"{'='*100}\n")
    
    if results_v2 and results_v3:
        # V2 totais
        total_v2 = sum(r['total'] for r in results_v2)
        wins_v2 = sum(r['wins'] for r in results_v2)
        wr_v2 = (wins_v2 / total_v2 * 100) if total_v2 > 0 else 0
        pips_v2 = sum(r['total_pips'] for r in results_v2)
        usd_v2 = sum(r['total_usd'] for r in results_v2)
        pf_v2 = statistics.mean([r['profit_factor'] for r in results_v2 if r['profit_factor'] > 0]) if any(r['profit_factor'] > 0 for r in results_v2) else 0
        
        # V3 totais
        total_v3 = sum(r['total'] for r in results_v3)
        wins_v3 = sum(r['wins'] for r in results_v3)
        wr_v3 = (wins_v3 / total_v3 * 100) if total_v3 > 0 else 0
        pips_v3 = sum(r['total_pips'] for r in results_v3)
        usd_v3 = sum(r['total_usd'] for r in results_v3)
        pf_v3 = statistics.mean([r['profit_factor'] for r in results_v3 if r['profit_factor'] > 0]) if any(r['profit_factor'] > 0 for r in results_v3) else 0
        
        print(f"{'Métrica':<25} {'V2 (Atual)':<20} {'V3 (Otimizado)':<20} {'Melhoria':<15}")
        print(f"{'─'*100}")
        print(f"{'Total Trades':<25} {total_v2:<20} {total_v3:<20} {(total_v3 - total_v2):+d}")
        print(f"{'Win Rate':<25} {wr_v2:<20.1f}% {wr_v3:<20.1f}% {(wr_v3 - wr_v2):+.1f}%")
        print(f"{'Total Pips':<25} {pips_v2:<+20.1f} {pips_v3:<+20.1f} {(pips_v3 - pips_v2):+.1f}")
        print(f"{'Total USD':<25} ${usd_v2:<+19.2f} ${usd_v3:<+19.2f} ${(usd_v3 - usd_v2):+.2f}")
        print(f"{'Profit Factor':<25} {pf_v2:<20.2f} {pf_v3:<20.2f} {(pf_v3 - pf_v2):+.2f}")
        
        print(f"\n{'='*100}")
        print(f"🎯 AVALIAÇÃO FINAL")
        print(f"{'='*100}\n")
        
        if wr_v3 >= 35 and pf_v3 >= 1.5 and pips_v3 > 0:
            print(f"🎉 OBJETIVO ATINGIDO!")
            print(f"   ✅ Win Rate: {wr_v3:.1f}% >= 35%")
            print(f"   ✅ Profit Factor: {pf_v3:.2f} >= 1.5")
            print(f"   ✅ Lucro: ${usd_v3:+.2f}")
            print(f"\n💰 SISTEMA APROVADO PARA PAPER TRADING!")
            print(f"   1. Fazer 30 dias em conta demo")
            print(f"   2. Se manter métricas, usar dinheiro real")
            print(f"   3. Capital inicial: $500-$1,000")
        elif wr_v3 > wr_v2:
            print(f"✅ SISTEMA MELHOROU!")
            print(f"   Win Rate: {wr_v2:.1f}% → {wr_v3:.1f}% (+{(wr_v3-wr_v2):.1f}%)")
            print(f"   Profit Factor: {pf_v2:.2f} → {pf_v3:.2f} (+{(pf_v3-pf_v2):.2f})")
            
            if wr_v3 >= 30:
                print(f"\n⚠️ Faltam apenas {35-wr_v3:.1f}% para atingir objetivo")
                print(f"   Sistema está no caminho certo!")
            else:
                print(f"\n⚠️ Ainda precisa mais otimizações")
        else:
            print(f"⚠️ Sistema não melhorou significativamente")
            print(f"   Considerar outras abordagens")
    
    print(f"\n{'='*100}")
    print("✅ TESTE COMPARATIVO COMPLETO")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
