"""
🎯 TESTE FINAL - Engine V3 Adaptativo
Valida com dados reais incluindo filtros de crash
"""

import requests
import time
import statistics
import sys
from datetime import datetime
sys.path.append('/app/backend')

from advanced_engine_v3 import AdvancedTradingEngine, Candle, SignalType, MarketCondition

CRYPTOCOMPARE_API = "https://min-api.cryptocompare.com/data/v2"

def get_data(symbol, limit=500):
    """Busca dados 1H"""
    try:
        url = f"{CRYPTOCOMPARE_API}/histohour"
        params = {"fsym": symbol, "tsym": "USD", "limit": limit}
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "Success":
                return [Candle(
                    timestamp=item["time"],
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=float(item["volumeto"])
                ) for item in data["Data"]["Data"]]
        return None
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None


def simulate_trade(signal_type, entry, sl, tp1, tp2, candles_after):
    """Simula trade com custos"""
    if not candles_after or len(candles_after) < 3:
        return 'NEUTRAL', 0, 'insufficient_data'
    
    # Custos realistas
    total_cost = entry * 0.0025  # 0.25%
    
    max_candles = min(len(candles_after), 30)
    position = 1.0
    total_profit = -total_cost
    tp1_hit = False
    
    if signal_type == 'CALL':
        for i, candle in enumerate(candles_after[:max_candles]):
            if candle.low <= sl:
                loss = (sl - entry) * position - total_cost
                return 'LOSS', loss, f'stop_{i}'
            
            if not tp1_hit and candle.high >= tp2:
                profit = (tp2 - entry) * position - total_cost
                return 'WIN', profit, f'tp2_{i}'
            
            if not tp1_hit and candle.high >= tp1:
                partial = (tp1 - entry) * 0.7 - total_cost * 0.7
                total_profit = partial
                position = 0.3
                tp1_hit = True
        
        final = candles_after[max_candles-1].close
        remaining = (final - entry) * position - total_cost * position
        total_profit += remaining
        
        return ('WIN' if total_profit > 0 else 'LOSS'), total_profit, 'time_exit'
    
    else:  # PUT
        for i, candle in enumerate(candles_after[:max_candles]):
            if candle.high >= sl:
                loss = (entry - sl) * position - total_cost
                return 'LOSS', loss, f'stop_{i}'
            
            if not tp1_hit and candle.low <= tp2:
                profit = (entry - tp2) * position - total_cost
                return 'WIN', profit, f'tp2_{i}'
            
            if not tp1_hit and candle.low <= tp1:
                partial = (entry - tp1) * 0.7 - total_cost * 0.7
                total_profit = partial
                position = 0.3
                tp1_hit = True
        
        final = candles_after[max_candles-1].close
        remaining = (entry - final) * position - total_cost * position
        total_profit += remaining
        
        return ('WIN' if total_profit > 0 else 'LOSS'), total_profit, 'time_exit'


def test_engine_v3(symbol, name):
    """Teste completo do Engine V3"""
    
    print(f"\n{'='*100}")
    print(f"🎯 TESTE ENGINE V3 ADAPTATIVO: {name}")
    print(f"{'='*100}\n")
    
    candles = get_data(symbol, 500)
    
    if not candles or len(candles) < 250:
        print("❌ Dados insuficientes")
        return None
    
    print(f"✅ {len(candles)} candles obtidos")
    print(f"   Período: {datetime.fromtimestamp(candles[0].timestamp)} até {datetime.fromtimestamp(candles[-1].timestamp)}")
    print(f"   Preço inicial: ${candles[0].close:.2f}")
    print(f"   Preço final: ${candles[-1].close:.2f}")
    print(f"   Variação: {((candles[-1].close / candles[0].close - 1) * 100):.2f}%")
    
    engine = AdvancedTradingEngine()
    
    all_trades = []
    all_waits = []
    trade_num = 0
    
    window = 200
    step = 10
    
    print(f"\n🔄 Processando...\n")
    
    for i in range(0, len(candles) - window - 30, step):
        analysis_window = candles[i:i+window]
        future_candles = candles[i+window:i+window+30]
        
        signal_data = engine.analyze(analysis_window, 10000)
        
        if signal_data.signal == SignalType.WAIT:
            all_waits.append({
                'reason': signal_data.warnings[0] if signal_data.warnings else 'Unknown',
                'condition': signal_data.market_condition.value
            })
            continue
        
        if signal_data.signal.value in ['CALL', 'PUT']:
            trade_num += 1
            
            outcome, profit, exit_reason = simulate_trade(
                signal_data.signal.value,
                signal_data.entry_price,
                signal_data.stop_loss,
                signal_data.take_profit_1,
                signal_data.take_profit_2,
                future_candles
            )
            
            trade_info = {
                'num': trade_num,
                'timestamp': datetime.fromtimestamp(candles[i+window].timestamp),
                'signal': signal_data.signal.value,
                'entry': signal_data.entry_price,
                'score': signal_data.score,
                'condition': signal_data.market_condition.value,
                'volatility': signal_data.volatility,
                'trend_strength': signal_data.trend_strength,
                'outcome': outcome,
                'profit': profit,
                'exit': exit_reason
            }
            
            all_trades.append(trade_info)
            
            color = "\033[92m" if outcome == 'WIN' else "\033[91m"
            reset = "\033[0m"
            
            print(f"{color}Trade #{trade_num} - {outcome}{reset}")
            print(f"   {trade_info['timestamp']} | {trade_info['signal']} | Score: {trade_info['score']}")
            print(f"   Condição: {trade_info['condition']} | Vol: {trade_info['volatility']:.2f}% | Trend: {trade_info['trend_strength']:.1f}")
            print(f"   Entry: ${trade_info['entry']:.2f} | {color}Lucro: ${profit:.2f}{reset}")
            print()
    
    if not all_trades:
        print("⚠️ Nenhum trade gerado")
        print(f"\n📊 ANÁLISE DOS WAITS:")
        
        if all_waits:
            wait_reasons = {}
            for w in all_waits:
                reason = w['reason']
                wait_reasons[reason] = wait_reasons.get(reason, 0) + 1
            
            print(f"   Total de WAITS: {len(all_waits)}")
            print(f"\n   Motivos:")
            for reason, count in sorted(wait_reasons.items(), key=lambda x: x[1], reverse=True):
                pct = (count / len(all_waits)) * 100
                print(f"      {reason}: {count} ({pct:.1f}%)")
        
        return None
    
    # Métricas
    total = len(all_trades)
    wins = sum(1 for t in all_trades if t['outcome'] == 'WIN')
    losses = total - wins
    
    win_rate = (wins / total * 100) if total > 0 else 0
    
    total_profit = sum(t['profit'] for t in all_trades)
    
    winning_profits = [t['profit'] for t in all_trades if t['outcome'] == 'WIN']
    losing_profits = [abs(t['profit']) for t in all_trades if t['outcome'] == 'LOSS']
    
    avg_win = statistics.mean(winning_profits) if winning_profits else 0
    avg_loss = statistics.mean(losing_profits) if losing_profits else 0
    
    profit_factor = (sum(winning_profits) / sum(losing_profits)) if losing_profits and sum(losing_profits) > 0 else 0
    
    print(f"\n{'='*100}")
    print(f"📊 RESUMO FINAL - {name}")
    print(f"{'='*100}\n")
    
    print(f"📈 ESTATÍSTICAS:")
    print(f"   Total WAITs: {len(all_waits)}")
    print(f"   Total Trades: {total}")
    print(f"   Vencedores: {wins}")
    print(f"   Perdedores: {losses}")
    print(f"   🎯 WIN RATE: {win_rate:.1f}%")
    
    print(f"\n💰 FINANCEIRO:")
    print(f"   Lucro Total: ${total_profit:.2f}")
    print(f"   Ganho Médio: ${avg_win:.2f}")
    print(f"   Perda Média: ${avg_loss:.2f}")
    print(f"   📊 Profit Factor: {profit_factor:.2f}")
    
    # Análise de condições
    trades_by_condition = {}
    for t in all_trades:
        cond = t['condition']
        if cond not in trades_by_condition:
            trades_by_condition[cond] = {'wins': 0, 'losses': 0, 'profit': 0}
        
        if t['outcome'] == 'WIN':
            trades_by_condition[cond]['wins'] += 1
        else:
            trades_by_condition[cond]['losses'] += 1
        
        trades_by_condition[cond]['profit'] += t['profit']
    
    print(f"\n📊 PERFORMANCE POR CONDIÇÃO:")
    for cond, stats in trades_by_condition.items():
        total_cond = stats['wins'] + stats['losses']
        wr_cond = (stats['wins'] / total_cond * 100) if total_cond > 0 else 0
        print(f"   {cond}: WR {wr_cond:.1f}% | Trades: {total_cond} | Lucro: ${stats['profit']:.2f}")
    
    return {
        'name': name,
        'total_trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'profit_factor': profit_factor,
        'total_waits': len(all_waits)
    }


def main():
    print("\n" + "="*100)
    print("🎯 VALIDAÇÃO FINAL - ENGINE V3 COM FILTROS ADAPTATIVOS")
    print("   Sistema com gestão inteligente de perdas")
    print("="*100)
    
    test_cases = [
        ("BTC", "Bitcoin"),
        ("ETH", "Ethereum"),
        ("BNB", "BNB"),
    ]
    
    all_results = []
    
    for symbol, name in test_cases:
        result = test_engine_v3(symbol, name)
        if result:
            all_results.append(result)
        time.sleep(3)
    
    if all_results:
        print(f"\n{'='*100}")
        print(f"📊 RELATÓRIO FINAL CONSOLIDADO")
        print(f"{'='*100}\n")
        
        print(f"{'Ativo':<15} {'Trades':<10} {'WAITs':<10} {'WR %':<10} {'Lucro':<15} {'PF':<10} {'Status':<15}")
        print(f"{'─'*100}")
        
        for r in all_results:
            status = "✅ LUCRATIVO" if r['total_profit'] > 0 else "❌ PREJUÍZO"
            print(f"{r['name']:<15} {r['total_trades']:<10} {r['total_waits']:<10} {r['win_rate']:<10.1f} ${r['total_profit']:<14.2f} {r['profit_factor']:<10.2f} {status:<15}")
        
        total_trades = sum(r['total_trades'] for r in all_results)
        total_wins = sum(r['wins'] for r in all_results)
        total_profit = sum(r['total_profit'] for r in all_results)
        avg_pf = statistics.mean([r['profit_factor'] for r in all_results if r['profit_factor'] > 0])
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        print(f"{'─'*100}")
        print(f"{'TOTAL':<15} {total_trades:<10} {'─':<10} {overall_wr:<10.1f} ${total_profit:<14.2f} {avg_pf:<10.2f}")
        
        print(f"\n{'='*100}")
        print(f"🎯 AVALIAÇÃO FINAL")
        print(f"{'='*100}\n")
        
        profitable = sum(1 for r in all_results if r['total_profit'] > 0)
        
        print(f"✅ Ativos lucrativos: {profitable}/{len(all_results)}")
        print(f"🎯 Win Rate Médio: {overall_wr:.1f}%")
        print(f"💰 Lucro Total: ${total_profit:.2f}")
        print(f"📊 Profit Factor Médio: {avg_pf:.2f}")
        
        if total_profit > 0 and overall_wr >= 50:
            print(f"\n🎉 SISTEMA VALIDADO!")
            print(f"   ✅ Lucrativo: ${total_profit:.2f}")
            print(f"   ✅ Win Rate: {overall_wr:.1f}%")
            print(f"   ✅ Profit Factor: {avg_pf:.2f}")
        elif total_profit > 0:
            print(f"\n✅ Sistema lucrativo mas win rate baixo")
        else:
            print(f"\n⚠️ Sistema ainda precisa ajustes")
    
    print(f"\n{'='*100}")
    print("✅ TESTE COMPLETO FINALIZADO")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
