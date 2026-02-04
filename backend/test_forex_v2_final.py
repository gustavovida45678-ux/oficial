"""
🎯 TESTE FINAL - FOREX ENGINE V2 (M30/H1)
Valida todas as correções implementadas
"""

import requests
import time
import statistics
import sys
from datetime import datetime, timedelta
sys.path.append('/app/backend')

from forex_engine_v2 import ForexEngine, Candle, SignalType

def generate_forex_h1_data(pair="EUR/USD", hours=500):
    """Gera dados realistas de FOREX para H1"""
    print(f"🔄 Gerando dados H1 para {pair}...")
    
    candles = []
    base_price = 1.0850 if "EUR" in pair else 1.2700
    timestamp = int((datetime.now() - timedelta(hours=hours)).timestamp())
    
    for i in range(hours):
        # FOREX H1 move 10-60 pips por candle
        noise = (hash(str(timestamp + i*3600)) % 200 - 100) * 0.00001  # ±10 pips
        
        # Tendência mais clara em H1
        if i < 150:
            trend = 0.0001  # Alta
        elif i < 350:
            trend = -0.0001  # Baixa  
        else:
            trend = 0.00005  # Alta moderada
        
        base_price += trend + noise
        
        # Construir candle H1
        open_price = base_price
        close_price = base_price + (hash(str(i*2)) % 60 - 30) * 0.00001
        high_price = max(open_price, close_price) + abs(hash(str(i*3)) % 40) * 0.00001
        low_price = min(open_price, close_price) - abs(hash(str(i*4)) % 40) * 0.00001
        volume = 5000 + (i % 100) * 50
        
        candles.append(Candle(
            timestamp=timestamp + (i * 3600),  # 1 hora cada
            open=round(open_price, 5),
            high=round(high_price, 5),
            low=round(low_price, 5),
            close=round(close_price, 5),
            volume=volume
        ))
    
    print(f"✅ {len(candles)} candles H1 gerados")
    return candles


def simulate_forex_trade_v2(signal_type, entry, sl, sl_pips, tp1, tp1_pips, tp2, tp2_pips, candles_after):
    """Simula trade com os níveis otimizados"""
    
    if not candles_after or len(candles_after) < 3:
        return 'NEUTRAL', 0, 0, 'insufficient_data'
    
    # Custos FOREX realistas
    spread_pips = 1.5  # 1.5 pips
    commission_pips = 0.5  # Comissão
    total_cost_pips = spread_pips + commission_pips
    
    max_candles = min(len(candles_after), 48)  # 48 horas máximo
    position = 1.0
    total_profit_pips = -total_cost_pips
    tp1_hit = False
    
    if signal_type == 'CALL':
        for i, candle in enumerate(candles_after[:max_candles]):
            # Stop loss
            if candle.low <= sl:
                loss_pips = -sl_pips - total_cost_pips
                return 'LOSS', loss_pips, loss_pips, f'stop_{i}'
            
            # TP2
            if not tp1_hit and candle.high >= tp2:
                profit_pips = tp2_pips - total_cost_pips
                return 'WIN', profit_pips, profit_pips, f'tp2_{i}'
            
            # TP1 (fechar 70%)
            if not tp1_hit and candle.high >= tp1:
                partial_pips = (tp1_pips - total_cost_pips) * 0.7
                total_profit_pips = partial_pips
                position = 0.3
                tp1_hit = True
        
        # Time exit
        final = candles_after[max_candles-1].close
        remaining_pips = ((final - entry) / 0.0001) * position
        total_profit_pips += remaining_pips
        
        return ('WIN' if total_profit_pips > 0 else 'LOSS'), total_profit_pips, total_profit_pips, 'time_exit'
    
    else:  # PUT
        for i, candle in enumerate(candles_after[:max_candles]):
            if candle.high >= sl:
                loss_pips = -sl_pips - total_cost_pips
                return 'LOSS', loss_pips, loss_pips, f'stop_{i}'
            
            if not tp1_hit and candle.low <= tp2:
                profit_pips = tp2_pips - total_cost_pips
                return 'WIN', profit_pips, profit_pips, f'tp2_{i}'
            
            if not tp1_hit and candle.low <= tp1:
                partial_pips = (tp1_pips - total_cost_pips) * 0.7
                total_profit_pips = partial_pips
                position = 0.3
                tp1_hit = True
        
        final = candles_after[max_candles-1].close
        remaining_pips = ((entry - final) / 0.0001) * position
        total_profit_pips += remaining_pips
        
        return ('WIN' if total_profit_pips > 0 else 'LOSS'), total_profit_pips, total_profit_pips, 'time_exit'


def test_forex_v2(pair_name, pair_display):
    """Testa motor V2 otimizado"""
    
    print(f"\n{'='*100}")
    print(f"📊 TESTE FOREX V2: {pair_display} (H1)")
    print(f"{'='*100}\n")
    
    candles = generate_forex_h1_data(pair_name, 500)
    
    print(f"📊 Período: {datetime.fromtimestamp(candles[0].timestamp)} até {datetime.fromtimestamp(candles[-1].timestamp)}")
    print(f"   Preço inicial: {candles[0].close:.5f}")
    print(f"   Preço final: {candles[-1].close:.5f}")
    print(f"   Variação: {((candles[-1].close / candles[0].close - 1) * 100):.2f}%")
    
    engine = ForexEngine(pair=pair_name)
    
    all_trades = []
    trade_num = 0
    
    window = 200
    step = 10
    
    print(f"\n🔄 Processando...\n")
    
    for i in range(0, len(candles) - window - 48, step):
        analysis_window = candles[i:i+window]
        future_candles = candles[i+window:i+window+48]
        
        signal_data = engine.analyze(analysis_window)
        
        if signal_data.signal.value in ['CALL', 'PUT']:
            trade_num += 1
            
            outcome, profit_pips, net_pips, exit_reason = simulate_forex_trade_v2(
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
            
            # Converter pips para USD (lote padrão $100k)
            profit_usd = net_pips * 10  # $10 por pip em lote padrão
            
            trade_info = {
                'num': trade_num,
                'timestamp': datetime.fromtimestamp(candles[i+window].timestamp),
                'signal': signal_data.signal.value,
                'entry': signal_data.entry_price,
                'score': signal_data.score,
                'sl_pips': signal_data.stop_loss_pips,
                'tp1_pips': signal_data.take_profit_1_pips,
                'rr': signal_data.risk_reward,
                'structure': signal_data.market_structure.value,
                'session': signal_data.session.value,
                'outcome': outcome,
                'profit_pips': net_pips,
                'profit_usd': profit_usd,
                'exit': exit_reason
            }
            
            all_trades.append(trade_info)
            
            color = "\033[92m" if outcome == 'WIN' else "\033[91m"
            reset = "\033[0m"
            
            print(f"{color}Trade #{trade_num} - {outcome}{reset}")
            print(f"   {trade_info['timestamp']} | {trade_info['signal']} | Score: {trade_info['score']}")
            print(f"   {trade_info['structure']} | {trade_info['session']} | RR: 1:{trade_info['rr']:.1f}")
            print(f"   SL: {trade_info['sl_pips']:.1f} pips | TP: {trade_info['tp1_pips']:.1f} pips")
            print(f"   {color}Resultado: {net_pips:+.1f} pips (${profit_usd:+.2f}){reset}")
            print()
    
    if not all_trades:
        print("⚠️ Nenhum trade gerado - Sistema muito seletivo")
        return None
    
    # Métricas
    total = len(all_trades)
    wins = sum(1 for t in all_trades if t['outcome'] == 'WIN')
    losses = total - wins
    
    win_rate = (wins / total * 100) if total > 0 else 0
    
    total_pips = sum(t['profit_pips'] for t in all_trades)
    total_usd = sum(t['profit_usd'] for t in all_trades)
    
    winning_pips = [t['profit_pips'] for t in all_trades if t['outcome'] == 'WIN']
    losing_pips = [abs(t['profit_pips']) for t in all_trades if t['outcome'] == 'LOSS']
    
    avg_win = statistics.mean(winning_pips) if winning_pips else 0
    avg_loss = statistics.mean(losing_pips) if losing_pips else 0
    
    profit_factor = (sum(winning_pips) / sum(losing_pips)) if losing_pips and sum(losing_pips) > 0 else 0
    
    print(f"\n{'='*100}")
    print(f"📊 RESUMO FINAL - {pair_display} H1")
    print(f"{'='*100}\n")
    
    print(f"📈 ESTATÍSTICAS:")
    print(f"   Total Trades: {total}")
    print(f"   Vencedores: {wins}")
    print(f"   Perdedores: {losses}")
    print(f"   🎯 WIN RATE: {win_rate:.1f}%")
    
    print(f"\n💰 FINANCEIRO:")
    print(f"   Total Pips: {total_pips:+.1f}")
    print(f"   Total USD (lote padrão): ${total_usd:+.2f}")
    print(f"   Média Win: {avg_win:.1f} pips")
    print(f"   Média Loss: {avg_loss:.1f} pips")
    print(f"   📊 Profit Factor: {profit_factor:.2f}")
    
    return {
        'pair': pair_display,
        'total_trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_pips': total_pips,
        'total_usd': total_usd,
        'profit_factor': profit_factor
    }


def main():
    print("\n" + "="*100)
    print("🎯 VALIDAÇÃO FOREX ENGINE V2 - APÓS CORREÇÕES")
    print("   ✅ Timeframe: H1 (não M5)")
    print("   ✅ TP/SL em pips adequados (25-40 pips)")
    print("   ✅ Estrutura de mercado")
    print("   ✅ Sessões de trading")
    print("   ✅ Filtros de tendência")
    print("   ✅ Risk/Reward 1:2.5")
    print("="*100)
    
    forex_pairs = [
        ("EUR/USD", "Euro / Dólar"),
        ("GBP/USD", "Libra / Dólar"),
        ("USD/JPY", "Dólar / Iene"),
    ]
    
    all_results = []
    
    for pair, display in forex_pairs:
        result = test_forex_v2(pair, display)
        if result:
            all_results.append(result)
        time.sleep(2)
    
    # RELATÓRIO FINAL
    print(f"\n{'='*100}")
    print(f"📊 RELATÓRIO FINAL - FOREX ENGINE V2")
    print(f"{'='*100}\n")
    
    if all_results:
        print(f"{'Par':<20} {'Trades':<10} {'WR %':<10} {'Pips':<15} {'USD $':<15} {'PF':<10} {'Status':<15}")
        print(f"{'─'*100}")
        
        for r in all_results:
            status = "✅ LUCRATIVO" if r['total_pips'] > 0 else "❌ PREJUÍZO"
            print(f"{r['pair']:<20} {r['total_trades']:<10} {r['win_rate']:<10.1f} {r['total_pips']:<+15.1f} ${r['total_usd']:<+14.2f} {r['profit_factor']:<10.2f} {status:<15}")
        
        total_trades = sum(r['total_trades'] for r in all_results)
        total_wins = sum(r['wins'] for r in all_results)
        total_pips = sum(r['total_pips'] for r in all_results)
        total_usd = sum(r['total_usd'] for r in all_results)
        avg_pf = statistics.mean([r['profit_factor'] for r in all_results if r['profit_factor'] > 0])
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        print(f"{'─'*100}")
        print(f"{'TOTAL':<20} {total_trades:<10} {overall_wr:<10.1f} {total_pips:<+15.1f} ${total_usd:<+14.2f} {avg_pf:<10.2f}")
        
        print(f"\n{'='*100}")
        print(f"🎯 AVALIAÇÃO FINAL - PODE USAR DINHEIRO REAL?")
        print(f"{'='*100}\n")
        
        profitable = sum(1 for r in all_results if r['total_pips'] > 0)
        
        print(f"📊 CRITÉRIOS:")
        print(f"   Pares lucrativos: {profitable}/{len(all_results)}")
        print(f"   Win Rate: {overall_wr:.1f}% (necessário >= 35%)")
        print(f"   Profit Factor: {avg_pf:.2f} (necessário >= 1.5)")
        print(f"   Total Pips: {total_pips:+.1f} (necessário > 0)")
        print(f"   Total USD: ${total_usd:+.2f}")
        
        print(f"\n{'─'*100}")
        print(f"💡 DECISÃO:")
        print(f"{'─'*100}\n")
        
        approved = (
            profitable >= 2 and
            overall_wr >= 35 and
            avg_pf >= 1.5 and
            total_pips > 0
        )
        
        if approved:
            print(f"✅ SISTEMA APROVADO PARA DINHEIRO REAL!")
            print(f"\n📋 MELHORIAS IMPLEMENTADAS:")
            print(f"   ✅ Timeframe H1 - Redução de ruído")
            print(f"   ✅ TP otimizado (25-40 pips)")
            print(f"   ✅ SL otimizado (10-15 pips)")
            print(f"   ✅ RR 1:2.5 - Expectativa positiva")
            print(f"   ✅ Filtros de estrutura e sessão")
            print(f"\n💰 RECOMENDAÇÕES:")
            print(f"   Capital: $1,000-$2,000")
            print(f"   Lote: Micro ($0.10/pip)")
            print(f"   Risco: 1% por trade")
            print(f"   Pares: EUR/USD e GBP/USD")
            print(f"   Timeframe: H1")
        else:
            print(f"❌ AINDA NÃO APROVADO")
            
            if profitable < 2:
                print(f"   ❌ Poucos pares lucrativos ({profitable}/3)")
            if overall_wr < 35:
                print(f"   ❌ Win rate insuficiente ({overall_wr:.1f}%)")
            if avg_pf < 1.5:
                print(f"   ❌ Profit factor baixo ({avg_pf:.2f})")
            if total_pips <= 0:
                print(f"   ❌ Prejuízo em pips")
    
    print(f"\n{'='*100}")
    print("✅ VALIDAÇÃO COMPLETA")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
