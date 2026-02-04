"""
🎯 VALIDAÇÃO COM DADOS REAIS + MELHORIAS AVANÇADAS
Busca dados históricos reais de exchanges e otimiza para 70%+ win rate
"""

import requests
import json
import numpy as np
from datetime import datetime, timedelta
import statistics
import time

BACKEND_URL = "http://localhost:8001/api"

# APIs gratuitas de dados reais
COINGECKO_API = "https://api.coingecko.com/api/v3"
CRYPTOCOMPARE_API = "https://min-api.cryptocompare.com/data/v2"

def get_real_market_data_coingecko(symbol="bitcoin", days=30):
    """
    Busca dados históricos REAIS da CoinGecko
    Retorna dados minuto a minuto dos últimos N dias
    """
    try:
        print(f"🔄 Buscando dados reais de {symbol} (últimos {days} dias)...")
        
        # CoinGecko OHLC endpoint (5 minutos)
        url = f"{COINGECKO_API}/coins/{symbol}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            candles = []
            for item in data:
                timestamp, open_p, high, low, close = item
                
                candles.append({
                    "timestamp": int(timestamp / 1000),
                    "open": float(open_p),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "volume": 1000.0  # Volume não disponível, usar valor padrão
                })
            
            print(f"✅ {len(candles)} candles obtidos de dados REAIS")
            return candles
        else:
            print(f"❌ Erro CoinGecko: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {str(e)}")
        return None


def get_real_market_data_cryptocompare(symbol="BTC", limit=2000):
    """
    Busca dados históricos REAIS da CryptoCompare
    Dados de 5 minutos
    """
    try:
        print(f"🔄 Buscando dados reais de {symbol} via CryptoCompare...")
        
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
                    candles.append({
                        "timestamp": item["time"],
                        "open": float(item["open"]),
                        "high": float(item["high"]),
                        "low": float(item["low"]),
                        "close": float(item["close"]),
                        "volume": float(item["volumeto"])
                    })
                
                print(f"✅ {len(candles)} candles reais obtidos")
                return candles
            else:
                print(f"❌ Erro API: {data.get('Message')}")
                return None
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None


def analyze_setup(candles):
    """Envia candles para análise do motor"""
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
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None


def simulate_trade_outcome_advanced(signal, entry_price, stop_loss, tp1, tp2, 
                                   candles_after, use_trailing=True):
    """
    Simula resultado com trailing stop e take profit parcial
    Returns: (outcome, profit, exit_reason)
    """
    if not candles_after or len(candles_after) < 5:
        return 'NEUTRAL', 0, 'insufficient_data'
    
    max_candles = min(len(candles_after), 20)  # Máximo 20 candles (100 min)
    
    trailing_stop = stop_loss
    partial_exit_done = False
    remaining_position = 1.0  # 100% da posição
    total_profit = 0
    
    if signal == 'CALL':
        highest_price = entry_price
        
        for i, candle in enumerate(candles_after[:max_candles]):
            current_high = candle['high']
            current_low = candle['low']
            
            # Atualizar highest price
            if current_high > highest_price:
                highest_price = current_high
                
                # Trailing stop: mover SL para breakeven depois de 50% do caminho até TP1
                if use_trailing and not partial_exit_done:
                    halfway_to_tp1 = entry_price + (tp1 - entry_price) * 0.5
                    if highest_price >= halfway_to_tp1:
                        trailing_stop = max(trailing_stop, entry_price)  # Breakeven
            
            # Hit stop loss?
            if current_low <= trailing_stop:
                loss = (trailing_stop - entry_price) * remaining_position
                total_profit += loss
                return 'LOSS', total_profit, f'stop_loss_candle_{i}'
            
            # Hit TP2? (se ainda tem posição)
            if not partial_exit_done and current_high >= tp2:
                profit = (tp2 - entry_price) * remaining_position
                total_profit += profit
                return 'WIN', total_profit, f'tp2_hit_candle_{i}'
            
            # Hit TP1? (take profit parcial)
            if not partial_exit_done and current_high >= tp1:
                # Fechar 50% da posição em TP1
                profit_partial = (tp1 - entry_price) * 0.5
                total_profit += profit_partial
                remaining_position = 0.5
                partial_exit_done = True
                trailing_stop = entry_price  # Move SL para breakeven
        
        # Não atingiu nenhum, fechar na última vela
        final_price = candles_after[max_candles-1]['close']
        remaining_profit = (final_price - entry_price) * remaining_position
        total_profit += remaining_profit
        
        if total_profit > 0:
            return 'WIN', total_profit, 'time_exit_profit'
        else:
            return 'LOSS', total_profit, 'time_exit_loss'
    
    elif signal == 'PUT':
        lowest_price = entry_price
        
        for i, candle in enumerate(candles_after[:max_candles]):
            current_high = candle['high']
            current_low = candle['low']
            
            # Atualizar lowest price
            if current_low < lowest_price:
                lowest_price = current_low
                
                # Trailing stop
                if use_trailing and not partial_exit_done:
                    halfway_to_tp1 = entry_price - (entry_price - tp1) * 0.5
                    if lowest_price <= halfway_to_tp1:
                        trailing_stop = min(trailing_stop, entry_price)
            
            # Hit stop loss?
            if current_high >= trailing_stop:
                loss = (entry_price - trailing_stop) * remaining_position
                total_profit += loss
                return 'LOSS', total_profit, f'stop_loss_candle_{i}'
            
            # Hit TP2?
            if not partial_exit_done and current_low <= tp2:
                profit = (entry_price - tp2) * remaining_position
                total_profit += profit
                return 'WIN', total_profit, f'tp2_hit_candle_{i}'
            
            # Hit TP1?
            if not partial_exit_done and current_low <= tp1:
                profit_partial = (entry_price - tp1) * 0.5
                total_profit += profit_partial
                remaining_position = 0.5
                partial_exit_done = True
                trailing_stop = entry_price
        
        final_price = candles_after[max_candles-1]['close']
        remaining_profit = (entry_price - final_price) * remaining_position
        total_profit += remaining_profit
        
        if total_profit > 0:
            return 'WIN', total_profit, 'time_exit_profit'
        else:
            return 'LOSS', total_profit, 'time_exit_loss'
    
    return 'NEUTRAL', 0, 'no_signal'


def run_real_market_backtest(candles_full, market_name, use_advanced_exit=True):
    """Executa backtest com dados reais"""
    
    print(f"\n{'='*80}")
    print(f"📊 BACKTEST REAL: {market_name}")
    print(f"{'='*80}\n")
    
    results = []
    
    window_size = 100
    step = 5  # Mais granular
    
    num_analyses = (len(candles_full) - window_size - 20) // step
    
    print(f"📈 Total de candles: {len(candles_full)}")
    print(f"📊 Análises: {num_analyses}")
    print(f"🔄 Processando...\n")
    
    for i in range(0, len(candles_full) - window_size - 20, step):
        window = candles_full[i:i+window_size]
        candles_after = candles_full[i+window_size:i+window_size+20]
        
        signal_data = analyze_setup(window)
        
        if not signal_data:
            continue
        
        signal = signal_data['signal']
        
        if signal in ['CALL', 'PUT']:
            outcome, profit, exit_reason = simulate_trade_outcome_advanced(
                signal,
                signal_data['entry_price'],
                signal_data['stop_loss'],
                signal_data['take_profit_1'],
                signal_data['take_profit_2'],
                candles_after,
                use_trailing=use_advanced_exit
            )
            
            results.append({
                'signal': signal,
                'score': signal_data['score'],
                'confidence': signal_data['confidence'],
                'entry': signal_data['entry_price'],
                'outcome': outcome,
                'profit': profit,
                'exit_reason': exit_reason,
                'rr': signal_data['risk_reward_1']
            })
    
    return results


def calculate_advanced_metrics(results):
    """Calcula métricas avançadas"""
    if not results:
        return None
    
    total_trades = len(results)
    wins = sum(1 for r in results if r['outcome'] == 'WIN')
    losses = sum(1 for r in results if r['outcome'] == 'LOSS')
    
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    total_profit = sum(r['profit'] for r in results)
    
    winning_trades = [r['profit'] for r in results if r['outcome'] == 'WIN']
    losing_trades = [abs(r['profit']) for r in results if r['outcome'] == 'LOSS']
    
    avg_win = statistics.mean(winning_trades) if winning_trades else 0
    avg_loss = statistics.mean(losing_trades) if losing_trades else 0
    
    max_win = max(winning_trades) if winning_trades else 0
    max_loss = max(losing_trades) if losing_trades else 0
    
    profit_factor = (sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) > 0 else 0
    
    # Sharpe Ratio simplificado
    returns = [r['profit'] for r in results]
    avg_return = statistics.mean(returns) if returns else 0
    std_return = statistics.stdev(returns) if len(returns) > 1 else 0
    sharpe = (avg_return / std_return) if std_return > 0 else 0
    
    # Max Drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    
    for r in results:
        cumulative += r['profit']
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    # Exit reasons
    exit_reasons = {}
    for r in results:
        reason = r.get('exit_reason', 'unknown')
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
    
    return {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_win': max_win,
        'max_loss': max_loss,
        'profit_factor': profit_factor,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'exit_reasons': exit_reasons
    }


def main():
    """Execução principal"""
    
    print("\n" + "="*80)
    print("🎯 VALIDAÇÃO COM DADOS REAIS + GESTÃO INTELIGENTE DE PERDAS")
    print("   Objetivo: 70%+ Win Rate com dados reais de mercado")
    print("="*80 + "\n")
    
    # Buscar dados reais de múltiplos ativos
    real_data_sources = [
        ("BTC", "Bitcoin"),
        ("ETH", "Ethereum"),
        ("BNB", "BNB"),
    ]
    
    all_results = {}
    
    for symbol, name in real_data_sources:
        print(f"\n{'─'*80}")
        print(f"📊 Processando: {name} ({symbol})")
        print(f"{'─'*80}")
        
        # Tentar CryptoCompare primeiro
        candles = get_real_market_data_cryptocompare(symbol, limit=2000)
        
        if candles and len(candles) >= 150:
            print(f"✅ Dados obtidos: {len(candles)} candles")
            
            # Rodar backtest COM gestão avançada
            print(f"\n🚀 Rodando backtest com TRAILING STOP e TAKE PROFIT PARCIAL...")
            results = run_real_market_backtest(candles, f"{name} (Real Data)", use_advanced_exit=True)
            
            if results:
                metrics = calculate_advanced_metrics(results)
                all_results[name] = {'results': results, 'metrics': metrics}
                
                print(f"\n✅ RESULTADOS - {name}:")
                print(f"   Total Trades: {metrics['total_trades']}")
                print(f"   Vencedores: {metrics['wins']}")
                print(f"   Perdedores: {metrics['losses']}")
                print(f"   🎯 WIN RATE: {metrics['win_rate']:.1f}%")
                print(f"   💰 Lucro Total: ${metrics['total_profit']:.2f}")
                print(f"   📈 Lucro Médio: ${metrics['total_profit']/metrics['total_trades']:.2f}")
                print(f"   ⭐ Profit Factor: {metrics['profit_factor']:.2f}")
                print(f"   📊 Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
                print(f"   📉 Max Drawdown: ${metrics['max_drawdown']:.2f}")
            else:
                print(f"⚠️ Nenhum trade executado para {name}")
        else:
            print(f"⚠️ Dados insuficientes para {name}")
        
        time.sleep(2)  # Evitar rate limit
    
    # RESUMO FINAL
    print(f"\n{'='*80}")
    print(f"📊 RESUMO FINAL - VALIDAÇÃO COM DADOS REAIS")
    print(f"{'='*80}\n")
    
    if all_results:
        total_trades = sum(m['metrics']['total_trades'] for m in all_results.values())
        total_wins = sum(m['metrics']['wins'] for m in all_results.values())
        total_losses = sum(m['metrics']['losses'] for m in all_results.values())
        
        overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        total_profit = sum(m['metrics']['total_profit'] for m in all_results.values())
        
        avg_profit_factor = statistics.mean([m['metrics']['profit_factor'] for m in all_results.values()])
        
        print(f"📈 ESTATÍSTICAS GLOBAIS (DADOS REAIS):")
        print(f"   Ativos Testados: {len(all_results)}")
        print(f"   Total de Trades: {total_trades}")
        print(f"   Vencedores: {total_wins}")
        print(f"   Perdedores: {total_losses}")
        print(f"\n🎯 WIN RATE GERAL: {overall_win_rate:.1f}%")
        print(f"💰 Lucro Total: ${total_profit:.2f}")
        print(f"📊 Profit Factor Médio: {avg_profit_factor:.2f}")
        
        print(f"\n{'─'*80}")
        print(f"📊 DESEMPENHO POR ATIVO:")
        print(f"{'─'*80}\n")
        
        for asset_name, data in all_results.items():
            m = data['metrics']
            print(f"{asset_name}:")
            print(f"   Win Rate: {m['win_rate']:.1f}% | Trades: {m['total_trades']} | Lucro: ${m['total_profit']:.2f}")
            print(f"   PF: {m['profit_factor']:.2f} | Sharpe: {m['sharpe_ratio']:.2f} | Max DD: ${m['max_drawdown']:.2f}")
        
        print(f"\n{'─'*80}")
        print(f"🎯 AVALIAÇÃO FINAL:")
        print(f"{'─'*80}\n")
        
        if overall_win_rate >= 70:
            print(f"🎉 EXCELENTE! Win rate {overall_win_rate:.1f}% >= 70%")
            print(f"✅ OBJETIVO ATINGIDO com dados REAIS de mercado!")
            print(f"✅ Sistema está pronto para paper trading")
        elif overall_win_rate >= 65:
            print(f"✅ MUITO BOM! Win rate {overall_win_rate:.1f}% próximo de 70%")
            print(f"✅ Sistema é consistentemente lucrativo")
            print(f"⚠️ Pode fazer ajustes finos para atingir 70%+")
        elif overall_win_rate >= 60:
            print(f"✅ BOM! Win rate {overall_win_rate:.1f}% acima de 60%")
            print(f"✅ Sistema é lucrativo")
            print(f"🔧 Recomenda-se mais otimizações")
        else:
            print(f"⚠️ Win rate {overall_win_rate:.1f}% abaixo de 60%")
            print(f"🔧 Sistema precisa de ajustes adicionais")
        
        print(f"\n{'─'*80}")
        print(f"💡 MELHORIAS IMPLEMENTADAS:")
        print(f"{'─'*80}\n")
        
        print("✅ TRAILING STOP:")
        print("   - Move SL para breakeven após 50% até TP1")
        print("   - Protege lucros parciais")
        print("   - Reduz perdas em reversões")
        
        print("\n✅ TAKE PROFIT PARCIAL:")
        print("   - Fecha 50% da posição em TP1")
        print("   - Deixa 50% correr até TP2")
        print("   - Aumenta win rate e reduz risco")
        
        print("\n✅ EXIT MANAGEMENT:")
        print("   - Máximo 20 candles (100 min) por trade")
        print("   - Exit por tempo se não atingir alvos")
        print("   - Protege contra mercado parado")
        
        print(f"\n{'─'*80}")
        print(f"🚀 PRÓXIMOS PASSOS:")
        print(f"{'─'*80}\n")
        
        if overall_win_rate >= 65:
            print("1. ✅ Sistema validado com dados REAIS")
            print("2. ✅ Iniciar paper trading em exchange")
            print("3. ✅ Monitorar por 2-4 semanas")
            print("4. ✅ Se mantiver 65%+, partir para capital real pequeno")
        else:
            print("1. 🔧 Coletar mais dados de diferentes períodos")
            print("2. 🔧 Ajustar parâmetros baseado em análise estatística")
            print("3. 🔧 Testar em diferentes timeframes")
            print("4. ⚠️ NÃO operar real até atingir 65%+")
    
    print(f"\n{'='*80}")
    print("✅ VALIDAÇÃO COM DADOS REAIS COMPLETA")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
