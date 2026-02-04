"""
🎯 VALIDAÇÃO COMPLETA - Taxa de Acerto Real do Trading Engine
Faz múltiplas simulações e calcula métricas reais de performance
"""

import requests
import json
import numpy as np
from datetime import datetime, timedelta
import statistics

BACKEND_URL = "http://localhost:8001/api"

class MarketSimulator:
    """Simula dados de mercado realistas baseados em padrões reais"""
    
    def __init__(self, seed=None):
        if seed:
            np.random.seed(seed)
    
    def generate_trending_market(self, direction="up", num_candles=150, 
                                base_price=45000, volatility=0.02):
        """
        Gera mercado com tendência definida
        direction: 'up' ou 'down'
        volatility: 0.01 = 1%, 0.02 = 2%
        """
        candles = []
        price = base_price
        timestamp = int((datetime.now() - timedelta(hours=12)).timestamp())
        
        trend_strength = 0.0003 if direction == "up" else -0.0003  # 0.03% por candle
        
        for i in range(num_candles):
            # Tendência + ruído + correções ocasionais
            noise = np.random.normal(0, price * volatility * 0.5)
            trend = price * trend_strength
            
            # Correções periódicas (a cada 20-30 candles)
            correction = 0
            if i > 20 and i % np.random.randint(20, 30) == 0:
                correction = -trend * np.random.uniform(3, 8)  # Correção de 3-8x a tendência
            
            price_change = trend + noise + correction
            price = max(price + price_change, base_price * 0.5)  # Não deixa cair muito
            
            # Construir candle realista
            open_price = price
            close_price = price + np.random.uniform(-price * 0.001, price * 0.001)
            
            if direction == "up":
                high_price = max(open_price, close_price) + abs(np.random.uniform(0, price * 0.002))
                low_price = min(open_price, close_price) - abs(np.random.uniform(0, price * 0.001))
            else:
                high_price = max(open_price, close_price) + abs(np.random.uniform(0, price * 0.001))
                low_price = min(open_price, close_price) - abs(np.random.uniform(0, price * 0.002))
            
            volume = np.random.uniform(800, 1500) + (100 * abs(price_change) / price)
            
            candles.append({
                "timestamp": timestamp + (i * 300),  # 5 min
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": round(volume, 2)
            })
        
        return candles
    
    def generate_ranging_market(self, num_candles=150, base_price=45000, 
                                range_size=0.02):
        """Gera mercado lateral/ranging"""
        candles = []
        price = base_price
        timestamp = int((datetime.now() - timedelta(hours=12)).timestamp())
        
        range_top = base_price * (1 + range_size)
        range_bottom = base_price * (1 - range_size)
        
        for i in range(num_candles):
            # Movimento aleatório dentro do range
            if price >= range_top:
                price_change = -abs(np.random.uniform(50, 200))
            elif price <= range_bottom:
                price_change = abs(np.random.uniform(50, 200))
            else:
                price_change = np.random.uniform(-150, 150)
            
            price = max(min(price + price_change, range_top), range_bottom)
            
            open_price = price
            close_price = price + np.random.uniform(-100, 100)
            high_price = max(open_price, close_price) + abs(np.random.uniform(0, 150))
            low_price = min(open_price, close_price) - abs(np.random.uniform(0, 150))
            volume = np.random.uniform(800, 1200)
            
            candles.append({
                "timestamp": timestamp + (i * 300),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": round(volume, 2)
            })
        
        return candles
    
    def generate_volatile_market(self, num_candles=150, base_price=45000):
        """Gera mercado altamente volátil sem direção clara"""
        candles = []
        price = base_price
        timestamp = int((datetime.now() - timedelta(hours=12)).timestamp())
        
        for i in range(num_candles):
            # Movimentos grandes e aleatórios
            price_change = np.random.choice([-400, -300, -200, -100, 100, 200, 300, 400])
            price = max(price + price_change, base_price * 0.7)
            
            open_price = price
            close_price = price + np.random.uniform(-200, 200)
            high_price = max(open_price, close_price) + abs(np.random.uniform(100, 300))
            low_price = min(open_price, close_price) - abs(np.random.uniform(100, 300))
            volume = np.random.uniform(1200, 2000)
            
            candles.append({
                "timestamp": timestamp + (i * 300),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": round(volume, 2)
            })
        
        return candles


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
            print(f"❌ Erro: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None


def simulate_trade_outcome(signal, entry_price, stop_loss, tp1, candles_after):
    """
    Simula o resultado de um trade baseado nos próximos candles
    Returns: 'WIN', 'LOSS', ou 'NEUTRAL'
    """
    if not candles_after or len(candles_after) < 5:
        return 'NEUTRAL', 0
    
    if signal == 'CALL':
        # Para CALL, queremos que preço suba
        for candle in candles_after[:10]:  # Próximos 10 candles (50min)
            # Hit stop loss?
            if candle['low'] <= stop_loss:
                return 'LOSS', stop_loss - entry_price
            # Hit TP1?
            if candle['high'] >= tp1:
                return 'WIN', tp1 - entry_price
        
        # Não atingiu nenhum, ver onde fechou
        final_price = candles_after[9]['close']
        if final_price > entry_price:
            return 'WIN', final_price - entry_price
        else:
            return 'LOSS', final_price - entry_price
    
    elif signal == 'PUT':
        # Para PUT, queremos que preço caia
        for candle in candles_after[:10]:
            # Hit stop loss?
            if candle['high'] >= stop_loss:
                return 'LOSS', entry_price - stop_loss
            # Hit TP1?
            if candle['low'] <= tp1:
                return 'WIN', entry_price - tp1
        
        final_price = candles_after[9]['close']
        if final_price < entry_price:
            return 'WIN', entry_price - final_price
        else:
            return 'LOSS', entry_price - final_price
    
    return 'NEUTRAL', 0


def run_simulation_scenario(scenario_name, candles_full):
    """Executa uma simulação completa em um cenário"""
    
    print(f"\n{'='*80}")
    print(f"📊 SIMULAÇÃO: {scenario_name}")
    print(f"{'='*80}\n")
    
    results = []
    
    # Usar janela deslizante para múltiplas análises
    window_size = 100
    step = 10  # Avançar 10 candles por vez
    
    num_analyses = (len(candles_full) - window_size - 10) // step
    
    print(f"📈 Total de candles: {len(candles_full)}")
    print(f"📊 Análises a serem feitas: {num_analyses}")
    print(f"🔄 Processando...\n")
    
    for i in range(0, len(candles_full) - window_size - 10, step):
        # Pegar janela de análise
        window = candles_full[i:i+window_size]
        candles_after = candles_full[i+window_size:i+window_size+10]
        
        # Analisar setup
        signal_data = analyze_setup(window)
        
        if not signal_data:
            continue
        
        signal = signal_data['signal']
        
        # Só contar trades executados (não WAIT)
        if signal in ['CALL', 'PUT']:
            outcome, profit = simulate_trade_outcome(
                signal,
                signal_data['entry_price'],
                signal_data['stop_loss'],
                signal_data['take_profit_1'],
                candles_after
            )
            
            results.append({
                'signal': signal,
                'score': signal_data['score'],
                'confidence': signal_data['confidence'],
                'entry': signal_data['entry_price'],
                'outcome': outcome,
                'profit': profit,
                'rr': signal_data['risk_reward_1']
            })
    
    return results


def calculate_metrics(results):
    """Calcula métricas de performance"""
    if not results:
        return None
    
    total_trades = len(results)
    wins = sum(1 for r in results if r['outcome'] == 'WIN')
    losses = sum(1 for r in results if r['outcome'] == 'LOSS')
    
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    total_profit = sum(r['profit'] for r in results)
    avg_profit = total_profit / total_trades if total_trades > 0 else 0
    
    winning_trades = [r['profit'] for r in results if r['outcome'] == 'WIN']
    losing_trades = [abs(r['profit']) for r in results if r['outcome'] == 'LOSS']
    
    avg_win = statistics.mean(winning_trades) if winning_trades else 0
    avg_loss = statistics.mean(losing_trades) if losing_trades else 0
    
    profit_factor = (avg_win * wins) / (avg_loss * losses) if losses > 0 and avg_loss > 0 else 0
    
    avg_score = statistics.mean([r['score'] for r in results])
    
    return {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'avg_profit': avg_profit,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'avg_score': avg_score
    }


def main():
    """Execução principal da validação"""
    
    print("\n" + "="*80)
    print("🎯 VALIDAÇÃO COMPLETA - Taxa de Acerto Real do Trading Engine")
    print("="*80 + "\n")
    
    simulator = MarketSimulator(seed=42)
    
    # Gerar diferentes cenários de mercado
    scenarios = {
        "Tendência de Alta Forte": simulator.generate_trending_market("up", 200, 45000, 0.015),
        "Tendência de Baixa Forte": simulator.generate_trending_market("down", 200, 45000, 0.015),
        "Mercado Lateral": simulator.generate_ranging_market(200, 45000, 0.02),
        "Alta Volatilidade": simulator.generate_volatile_market(200, 45000),
        "Tendência de Alta Moderada": simulator.generate_trending_market("up", 200, 50000, 0.01),
        "Tendência de Baixa Moderada": simulator.generate_trending_market("down", 200, 50000, 0.01),
    }
    
    all_results = {}
    
    # Executar simulações
    for scenario_name, candles in scenarios.items():
        results = run_simulation_scenario(scenario_name, candles)
        
        if results:
            metrics = calculate_metrics(results)
            all_results[scenario_name] = {'results': results, 'metrics': metrics}
            
            # Exibir resultados
            print(f"✅ Resultados:")
            print(f"   Total de Trades: {metrics['total_trades']}")
            print(f"   Vencedores: {metrics['wins']}")
            print(f"   Perdedores: {metrics['losses']}")
            print(f"   📊 WIN RATE: {metrics['win_rate']:.1f}%")
            print(f"   💰 Lucro Total: ${metrics['total_profit']:.2f}")
            print(f"   📈 Lucro Médio por Trade: ${metrics['avg_profit']:.2f}")
            print(f"   ⭐ Score Médio: {metrics['avg_score']:.1f}/100")
            print(f"   🎯 Profit Factor: {metrics['profit_factor']:.2f}")
    
    # RESUMO FINAL
    print(f"\n{'='*80}")
    print(f"📊 RESUMO FINAL - TODOS OS CENÁRIOS")
    print(f"{'='*80}\n")
    
    if all_results:
        total_trades_all = sum(m['metrics']['total_trades'] for m in all_results.values())
        total_wins_all = sum(m['metrics']['wins'] for m in all_results.values())
        total_losses_all = sum(m['metrics']['losses'] for m in all_results.values())
        
        overall_win_rate = (total_wins_all / total_trades_all * 100) if total_trades_all > 0 else 0
        
        win_rates = [m['metrics']['win_rate'] for m in all_results.values()]
        avg_win_rate = statistics.mean(win_rates)
        
        total_profit_all = sum(m['metrics']['total_profit'] for m in all_results.values())
        
        print(f"📈 ESTATÍSTICAS GERAIS:")
        print(f"   Cenários Testados: {len(scenarios)}")
        print(f"   Total de Trades Executados: {total_trades_all}")
        print(f"   Total Vencedores: {total_wins_all}")
        print(f"   Total Perdedores: {total_losses_all}")
        print(f"\n🎯 WIN RATE GERAL: {overall_win_rate:.1f}%")
        print(f"📊 Win Rate Médio por Cenário: {avg_win_rate:.1f}%")
        print(f"💰 Lucro Total Combinado: ${total_profit_all:.2f}")
        
        print(f"\n{'─'*80}")
        print(f"📊 DESEMPENHO POR CENÁRIO:")
        print(f"{'─'*80}\n")
        
        for scenario_name, data in all_results.items():
            m = data['metrics']
            print(f"{scenario_name}:")
            print(f"   Win Rate: {m['win_rate']:.1f}% | Trades: {m['total_trades']} | Profit: ${m['total_profit']:.2f}")
        
        print(f"\n{'─'*80}")
        print(f"🎯 ANÁLISE DE EFICÁCIA:")
        print(f"{'─'*80}\n")
        
        if overall_win_rate >= 70:
            print(f"✅ EXCELENTE! Win rate {overall_win_rate:.1f}% >= 70%")
            print(f"   Sistema atinge o objetivo de 70%+ de assertividade!")
        elif overall_win_rate >= 60:
            print(f"✅ BOM! Win rate {overall_win_rate:.1f}% está entre 60-70%")
            print(f"   Sistema é lucrativo, pode ser otimizado para >70%")
        elif overall_win_rate >= 50:
            print(f"⚠️ MÉDIO. Win rate {overall_win_rate:.1f}% está entre 50-60%")
            print(f"   Sistema precisa de ajustes nos parâmetros")
        else:
            print(f"❌ BAIXO. Win rate {overall_win_rate:.1f}% < 50%")
            print(f"   Sistema precisa de revisão significativa")
        
        print(f"\n{'─'*80}")
        print(f"💡 INSIGHTS:")
        print(f"{'─'*80}\n")
        
        # Análise por tipo de mercado
        trend_scenarios = [k for k in all_results.keys() if 'Tendência' in k]
        range_scenarios = [k for k in all_results.keys() if 'Lateral' in k]
        volatile_scenarios = [k for k in all_results.keys() if 'Volatilidade' in k]
        
        if trend_scenarios:
            trend_wr = statistics.mean([all_results[k]['metrics']['win_rate'] for k in trend_scenarios])
            print(f"📈 Mercados com Tendência: {trend_wr:.1f}% win rate")
        
        if range_scenarios:
            range_wr = statistics.mean([all_results[k]['metrics']['win_rate'] for k in range_scenarios])
            print(f"📊 Mercados Laterais: {range_wr:.1f}% win rate")
        
        if volatile_scenarios:
            vol_wr = statistics.mean([all_results[k]['metrics']['win_rate'] for k in volatile_scenarios])
            print(f"💥 Mercados Voláteis: {vol_wr:.1f}% win rate")
        
        print(f"\n{'─'*80}")
        print(f"🚀 RECOMENDAÇÕES:")
        print(f"{'─'*80}\n")
        
        if overall_win_rate >= 70:
            print("1. ✅ Sistema está pronto para paper trading")
            print("2. ✅ Conectar com dados reais de exchange")
            print("3. ✅ Fazer 2-4 semanas de validação em demo")
            print("4. ✅ Depois pode partir para conta real com capital pequeno")
        else:
            print("1. 🔧 Ajustar parâmetros do motor:")
            print("   - Aumentar min_score para filtrar mais")
            print("   - Ajustar períodos de EMA")
            print("   - Calibrar níveis de RSI")
            print("2. 📊 Fazer mais backtests com dados históricos reais")
            print("3. ⚠️  NÃO operar com dinheiro real ainda")
    
    print(f"\n{'='*80}")
    print("✅ VALIDAÇÃO COMPLETA FINALIZADA")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
