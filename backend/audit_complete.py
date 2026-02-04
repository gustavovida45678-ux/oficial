"""
🔍 AUDITORIA COMPLETA - Verificação com Dados Reais
Testa TUDO com máxima transparência
"""

import requests
import json
import time
from datetime import datetime
import statistics
import sys
sys.path.append('/app/backend')

from scalping_engine import ScalpingEngine, Candle as ScalpCandle, SignalType as ScalpSignal
from crypto_trading_engine import CryptoTradingEngine, Candle as CryptoCandle, SignalType as CryptoSignal

CRYPTOCOMPARE_API = "https://min-api.cryptocompare.com/data/v2"

def get_data(symbol, timeframe, limit):
    """Busca dados reais"""
    try:
        if timeframe == "5m":
            url = f"{CRYPTOCOMPARE_API}/histominute"
            params = {"fsym": symbol, "tsym": "USD", "limit": limit, "aggregate": 5}
        elif timeframe == "1h":
            url = f"{CRYPTOCOMPARE_API}/histohour"
            params = {"fsym": symbol, "tsym": "USD", "limit": limit}
        else:
            return None
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "Success":
                candles = []
                for item in data["Data"]["Data"]:
                    candles.append({
                        "timestamp": item["time"],
                        "open": float(item["open"]),
                        "high": float(item["high"]),
                        "low": float(item["low"]),
                        "close": float(item["close"]),
                        "volume": float(item["volumeto"])
                    })
                return candles
        return None
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None


def simulate_realistic_trade(signal_type, entry, sl, tp1, tp2, candles_after, timeframe):
    """Simula trade com MÁXIMO REALISMO"""
    if not candles_after or len(candles_after) < 3:
        return 'NEUTRAL', 0, 'insufficient_data', []
    
    max_candles = 10 if timeframe == "5m" else 30
    max_candles = min(len(candles_after), max_candles)
    
    # Adicionar custos realistas
    spread_pct = 0.001  # 0.1% spread
    fee_pct = 0.001  # 0.1% taxa
    slippage_pct = 0.0005  # 0.05% slippage
    
    total_cost = (spread_pct + fee_pct + slippage_pct) * entry
    
    position = 1.0
    total_profit = -total_cost  # Começa com custos
    tp1_hit = False
    trade_log = []
    
    if signal_type in ['CALL', 'call']:
        for i, candle in enumerate(candles_after[:max_candles]):
            # Stop loss
            if candle['low'] <= sl:
                loss = (sl - entry) * position - total_cost
                total_profit = loss
                trade_log.append(f"Candle {i}: Hit STOP LOSS at {sl:.2f}")
                return 'LOSS', total_profit, f'stop_candle_{i}', trade_log
            
            # TP2
            if not tp1_hit and candle['high'] >= tp2:
                profit = (tp2 - entry) * position - total_cost
                total_profit = profit
                trade_log.append(f"Candle {i}: Hit TP2 at {tp2:.2f}")
                return 'WIN', total_profit, f'tp2_candle_{i}', trade_log
            
            # TP1
            if not tp1_hit and candle['high'] >= tp1:
                partial_profit = (tp1 - entry) * 0.7 - total_cost * 0.7
                total_profit = partial_profit
                position = 0.3
                tp1_hit = True
                trade_log.append(f"Candle {i}: Hit TP1 at {tp1:.2f}, closed 70%")
        
        # Exit no tempo
        final = candles_after[max_candles-1]['close']
        remaining = (final - entry) * position - total_cost * position
        total_profit += remaining
        trade_log.append(f"Time exit at {final:.2f}")
        
        return ('WIN' if total_profit > 0 else 'LOSS'), total_profit, 'time_exit', trade_log
    
    else:  # PUT
        for i, candle in enumerate(candles_after[:max_candles]):
            if candle['high'] >= sl:
                loss = (entry - sl) * position - total_cost
                total_profit = loss
                trade_log.append(f"Candle {i}: Hit STOP LOSS at {sl:.2f}")
                return 'LOSS', total_profit, f'stop_candle_{i}', trade_log
            
            if not tp1_hit and candle['low'] <= tp2:
                profit = (entry - tp2) * position - total_cost
                total_profit = profit
                trade_log.append(f"Candle {i}: Hit TP2 at {tp2:.2f}")
                return 'WIN', total_profit, f'tp2_candle_{i}', trade_log
            
            if not tp1_hit and candle['low'] <= tp1:
                partial_profit = (entry - tp1) * 0.7 - total_cost * 0.7
                total_profit = partial_profit
                position = 0.3
                tp1_hit = True
                trade_log.append(f"Candle {i}: Hit TP1 at {tp1:.2f}, closed 70%")
        
        final = candles_after[max_candles-1]['close']
        remaining = (entry - final) * position - total_cost * position
        total_profit += remaining
        trade_log.append(f"Time exit at {final:.2f}")
        
        return ('WIN' if total_profit > 0 else 'LOSS'), total_profit, 'time_exit', trade_log


def test_engine_detailed(symbol, name, timeframe):
    """Teste DETALHADO com TODOS os trades mostrados"""
    
    print(f"\n{'='*100}")
    print(f"🔍 AUDITORIA DETALHADA: {name} ({timeframe})")
    print(f"{'='*100}\n")
    
    # Buscar dados
    limit = 500 if timeframe == "1h" else 2000
    raw_data = get_data(symbol, timeframe, limit)
    
    if not raw_data or len(raw_data) < 150:
        print(f"❌ Dados insuficientes")
        return None
    
    print(f"✅ {len(raw_data)} candles reais obtidos")
    print(f"   Período: {datetime.fromtimestamp(raw_data[0]['timestamp'])} até {datetime.fromtimestamp(raw_data[-1]['timestamp'])}")
    print(f"   Preço inicial: ${raw_data[0]['close']:.2f}")
    print(f"   Preço final: ${raw_data[-1]['close']:.2f}")
    
    # Escolher engine
    if timeframe == "5m":
        engine = ScalpingEngine()
        window = 100
        step = 10
        candles = [ScalpCandle(**c) for c in raw_data]
    else:
        engine = CryptoTradingEngine()
        window = 200
        step = 10
        candles = [CryptoCandle(**c) for c in raw_data]
    
    all_trades = []
    trade_num = 0
    
    print(f"\n🔄 Processando {len(raw_data) - window - 30} janelas...\n")
    
    for i in range(0, len(candles) - window - 30, step):
        analysis_window = candles[i:i+window]
        future_candles = [c.__dict__ for c in candles[i+window:i+window+30]]
        
        signal_data = engine.analyze(analysis_window, 10000)
        
        if signal_data.signal.value in ['CALL', 'PUT']:
            trade_num += 1
            
            outcome, profit, exit_reason, trade_log = simulate_realistic_trade(
                signal_data.signal.value,
                signal_data.entry_price,
                signal_data.stop_loss,
                signal_data.take_profit_1,
                signal_data.take_profit_2,
                future_candles,
                timeframe
            )
            
            trade_info = {
                'num': trade_num,
                'timestamp': datetime.fromtimestamp(candles[i+window].timestamp),
                'signal': signal_data.signal.value,
                'entry': signal_data.entry_price,
                'sl': signal_data.stop_loss,
                'tp1': signal_data.take_profit_1,
                'tp2': signal_data.take_profit_2,
                'score': signal_data.score,
                'outcome': outcome,
                'profit': profit,
                'exit_reason': exit_reason,
                'log': trade_log
            }
            
            all_trades.append(trade_info)
            
            # Mostrar trade
            color = "\033[92m" if outcome == 'WIN' else "\033[91m"
            reset = "\033[0m"
            
            print(f"{color}{'─'*100}{reset}")
            print(f"{color}Trade #{trade_num} - {outcome}{reset}")
            print(f"   Data: {trade_info['timestamp']}")
            print(f"   Sinal: {trade_info['signal']} | Score: {trade_info['score']}")
            print(f"   Entry: ${trade_info['entry']:.2f}")
            print(f"   Stop Loss: ${trade_info['sl']:.2f}")
            print(f"   Take Profit 1: ${trade_info['tp1']:.2f}")
            print(f"   Take Profit 2: ${trade_info['tp2']:.2f}")
            print(f"   {color}Resultado: {outcome} | Lucro: ${profit:.2f}{reset}")
            print(f"   Razão saída: {exit_reason}")
            if trade_log:
                print(f"   Log: {' -> '.join(trade_log[:3])}")
            print(f"{color}{'─'*100}{reset}\n")
    
    if not all_trades:
        print("⚠️ Nenhum trade gerado (sistema muito seletivo)")
        return None
    
    # Calcular métricas
    total = len(all_trades)
    wins = sum(1 for t in all_trades if t['outcome'] == 'WIN')
    losses = sum(1 for t in all_trades if t['outcome'] == 'LOSS')
    
    win_rate = (wins / total * 100) if total > 0 else 0
    
    total_profit = sum(t['profit'] for t in all_trades)
    
    winning_profits = [t['profit'] for t in all_trades if t['outcome'] == 'WIN']
    losing_profits = [abs(t['profit']) for t in all_trades if t['outcome'] == 'LOSS']
    
    avg_win = statistics.mean(winning_profits) if winning_profits else 0
    avg_loss = statistics.mean(losing_profits) if losing_profits else 0
    
    profit_factor = (sum(winning_profits) / sum(losing_profits)) if losing_profits and sum(losing_profits) > 0 else 0
    
    max_win = max(winning_profits) if winning_profits else 0
    max_loss = max(losing_profits) if losing_profits else 0
    
    # Sequência de vitórias/derrotas
    max_win_streak = 0
    max_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0
    
    for t in all_trades:
        if t['outcome'] == 'WIN':
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        else:
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)
    
    results = {
        'symbol': symbol,
        'name': name,
        'timeframe': timeframe,
        'total_trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_win': max_win,
        'max_loss': max_loss,
        'profit_factor': profit_factor,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'all_trades': all_trades
    }
    
    # Mostrar resumo
    print(f"\n{'='*100}")
    print(f"📊 RESUMO FINAL - {name} ({timeframe})")
    print(f"{'='*100}\n")
    
    print(f"📈 ESTATÍSTICAS:")
    print(f"   Total de Trades: {total}")
    print(f"   Vencedores: {wins} ({'WIN' if wins > losses else 'ok'})")
    print(f"   Perdedores: {losses}")
    print(f"   🎯 WIN RATE: {win_rate:.1f}%")
    print(f"   Sequência vitórias: {max_win_streak}")
    print(f"   Sequência derrotas: {max_loss_streak}")
    
    print(f"\n💰 FINANCEIRO:")
    print(f"   Lucro Total: ${total_profit:.2f}")
    print(f"   Ganho Médio: ${avg_win:.2f}")
    print(f"   Perda Média: ${avg_loss:.2f}")
    print(f"   Maior Ganho: ${max_win:.2f}")
    print(f"   Maior Perda: ${max_loss:.2f}")
    print(f"   📊 Profit Factor: {profit_factor:.2f}")
    
    if profit_factor > 2.0:
        print(f"   ✅ EXCELENTE Profit Factor!")
    elif profit_factor > 1.5:
        print(f"   ✅ BOM Profit Factor")
    elif profit_factor > 1.0:
        print(f"   ⚠️ Profit Factor aceitável")
    else:
        print(f"   ❌ Profit Factor baixo")
    
    return results


def main():
    print("\n" + "="*100)
    print("🔍 AUDITORIA COMPLETA DO SISTEMA - Verificação com Dados REAIS")
    print("   Todos os trades serão mostrados individualmente")
    print("="*100 + "\n")
    
    test_cases = [
        ("BTC", "Bitcoin", "5m"),
        ("ETH", "Ethereum", "5m"),
        ("BTC", "Bitcoin", "1h"),
        ("ETH", "Ethereum", "1h"),
    ]
    
    all_results = []
    
    for symbol, name, timeframe in test_cases:
        result = test_engine_detailed(symbol, name, timeframe)
        if result:
            all_results.append(result)
        time.sleep(3)
    
    # RELATÓRIO FINAL CONSOLIDADO
    print(f"\n{'='*100}")
    print(f"📊 RELATÓRIO FINAL CONSOLIDADO")
    print(f"={'='*100}\n")
    
    if all_results:
        print(f"{'Ativo':<15} {'TF':<8} {'Trades':<10} {'WR %':<10} {'Lucro':<15} {'PF':<10} {'Status':<15}")
        print(f"{'─'*100}")
        
        for r in all_results:
            status = "✅ LUCRATIVO" if r['total_profit'] > 0 else "❌ PREJUÍZO"
            print(f"{r['name']:<15} {r['timeframe']:<8} {r['total_trades']:<10} {r['win_rate']:<10.1f} ${r['total_profit']:<14.2f} {r['profit_factor']:<10.2f} {status:<15}")
        
        # Totais
        total_trades_all = sum(r['total_trades'] for r in all_results)
        total_wins_all = sum(r['wins'] for r in all_results)
        total_profit_all = sum(r['total_profit'] for r in all_results)
        avg_pf = statistics.mean([r['profit_factor'] for r in all_results if r['profit_factor'] > 0])
        overall_wr = (total_wins_all / total_trades_all * 100) if total_trades_all > 0 else 0
        
        print(f"{'─'*100}")
        print(f"{'TOTAL':<15} {'─':<8} {total_trades_all:<10} {overall_wr:<10.1f} ${total_profit_all:<14.2f} {avg_pf:<10.2f} {'─':<15}")
        
        print(f"\n{'='*100}")
        print(f"🎯 AVALIAÇÃO FINAL")
        print(f"={'='*100}\n")
        
        profitable_count = sum(1 for r in all_results if r['total_profit'] > 0)
        
        print(f"✅ Cenários lucrativos: {profitable_count}/{len(all_results)}")
        print(f"🎯 Win Rate Médio: {overall_wr:.1f}%")
        print(f"💰 Lucro Total: ${total_profit_all:.2f}")
        print(f"📊 Profit Factor Médio: {avg_pf:.2f}")
        
        if total_profit_all > 0 and avg_pf > 1.5:
            print(f"\n✅ SISTEMA VALIDADO!")
            print(f"   Sistema é LUCRATIVO com dados reais")
            print(f"   Profit Factor > 1.5 indica qualidade")
        elif total_profit_all > 0:
            print(f"\n✅ Sistema é lucrativo")
            print(f"   Mas pode melhorar o Profit Factor")
        else:
            print(f"\n⚠️ Sistema precisa ajustes")
            print(f"   Total em prejuízo")
    
    print(f"\n{'='*100}")
    print("✅ AUDITORIA COMPLETA FINALIZADA")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
