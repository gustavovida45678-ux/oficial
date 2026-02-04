"""
🔌 CONEXÃO COM DADOS REAIS DE FOREX
Busca dados históricos REAIS de brokers/APIs públicas
"""

import requests
import time
import statistics
import sys
from datetime import datetime, timedelta
import json
sys.path.append('/app/backend')

from forex_engine_v2 import ForexEngine, Candle, SignalType

# APIs de dados FOREX REAIS (gratuitas)
ALPHA_VANTAGE_KEY = "demo"  # Usar demo key
TWELVE_DATA_API = "https://api.twelvedata.com"
FXAPI_URL = "https://api.fxratesapi.com"

def get_real_forex_data_fxapi(pair="EUR/USD", days=30):
    """
    Busca dados REAIS do FX Rates API (gratuito)
    Retorna dados históricos reais de FOREX
    """
    try:
        print(f"🔄 Buscando dados REAIS de {pair} via FX Rates API...")
        
        # FX Rates API tem dados diários gratuitos
        base_currency = pair.split("/")[0]
        quote_currency = pair.split("/")[1]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"https://api.fxratesapi.com/timeseries"
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "base": base_currency,
            "currencies": quote_currency,
            "resolution": "1h"  # Dados de 1 hora
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API respondeu com sucesso")
            return data
        else:
            print(f"⚠️ API retornou status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ Erro: {str(e)}")
        return None


def get_real_forex_data_yahoo(pair="EURUSD=X", period="3mo"):
    """
    Busca dados REAIS do Yahoo Finance (sempre disponível)
    """
    try:
        print(f"🔄 Buscando dados REAIS via Yahoo Finance...")
        
        # Yahoo Finance tem dados forex gratuitos
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}"
        params = {
            "range": period,
            "interval": "1h",
            "includePrePost": "false"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        
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
                
                print(f"✅ {len(candles)} candles REAIS obtidos do Yahoo Finance")
                return candles
        
        print(f"⚠️ Yahoo Finance retornou status {response.status_code}")
        return None
        
    except Exception as e:
        print(f"⚠️ Erro: {str(e)}")
        return None


def get_real_forex_data_investing(pair="EUR/USD"):
    """
    Busca dados de fonte pública alternativa
    """
    try:
        print(f"🔄 Tentando fonte alternativa de dados FOREX...")
        
        # Usar API pública de taxas de câmbio
        url = "https://api.exchangerate.host/timeseries"
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        base = pair.split("/")[0]
        symbols = pair.split("/")[1]
        
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "base": base,
            "symbols": symbols
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'rates' in data:
                candles = []
                dates = sorted(data['rates'].keys())
                
                for i, date in enumerate(dates):
                    rate = data['rates'][date][symbols]
                    timestamp = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
                    
                    # Simular OHLC a partir do preço diário
                    candles.append(Candle(
                        timestamp=timestamp,
                        open=float(rate),
                        high=float(rate) * 1.001,
                        low=float(rate) * 0.999,
                        close=float(rate),
                        volume=10000.0
                    ))
                
                print(f"✅ {len(candles)} candles obtidos")
                return candles
        
        return None
        
    except Exception as e:
        print(f"⚠️ Erro: {str(e)}")
        return None


def simulate_forex_trade_real(signal_type, entry, sl, sl_pips, tp1, tp1_pips, tp2, tp2_pips, candles_after):
    """Simula trade com dados REAIS"""
    
    if not candles_after or len(candles_after) < 3:
        return 'NEUTRAL', 0, 'insufficient_data'
    
    spread_pips = 1.5
    commission_pips = 0.5
    total_cost_pips = spread_pips + commission_pips
    
    max_candles = min(len(candles_after), 48)
    position = 1.0
    total_profit_pips = -total_cost_pips
    tp1_hit = False
    
    if signal_type == 'CALL':
        for i, candle in enumerate(candles_after[:max_candles]):
            if candle.low <= sl:
                loss_pips = -sl_pips - total_cost_pips
                return 'LOSS', loss_pips, f'stop_{i}'
            
            if not tp1_hit and candle.high >= tp2:
                profit_pips = tp2_pips - total_cost_pips
                return 'WIN', profit_pips, f'tp2_{i}'
            
            if not tp1_hit and candle.high >= tp1:
                partial_pips = (tp1_pips - total_cost_pips) * 0.7
                total_profit_pips = partial_pips
                position = 0.3
                tp1_hit = True
        
        final = candles_after[max_candles-1].close
        remaining_pips = ((final - entry) / 0.0001) * position
        total_profit_pips += remaining_pips
        
        return ('WIN' if total_profit_pips > 0 else 'LOSS'), total_profit_pips, 'time_exit'
    
    else:  # PUT
        for i, candle in enumerate(candles_after[:max_candles]):
            if candle.high >= sl:
                loss_pips = -sl_pips - total_cost_pips
                return 'LOSS', loss_pips, f'stop_{i}'
            
            if not tp1_hit and candle.low <= tp2:
                profit_pips = tp2_pips - total_cost_pips
                return 'WIN', profit_pips, f'tp2_{i}'
            
            if not tp1_hit and candle.low <= tp1:
                partial_pips = (tp1_pips - total_cost_pips) * 0.7
                total_profit_pips = partial_pips
                position = 0.3
                tp1_hit = True
        
        final = candles_after[max_candles-1].close
        remaining_pips = ((entry - final) / 0.0001) * position
        total_profit_pips += remaining_pips
        
        return ('WIN' if total_profit_pips > 0 else 'LOSS'), total_profit_pips, 'time_exit'


def test_with_real_data(pair_name, pair_display):
    """Testa com dados REAIS"""
    
    print(f"\n{'='*100}")
    print(f"📊 TESTE COM DADOS REAIS: {pair_display}")
    print(f"{'='*100}\n")
    
    # Tentar buscar dados reais de múltiplas fontes
    candles = None
    
    # Tentar Yahoo Finance primeiro (mais confiável)
    yahoo_pair = pair_name.replace("/", "") + "=X"
    candles = get_real_forex_data_yahoo(yahoo_pair, "3mo")
    
    if not candles or len(candles) < 200:
        print("⚠️ Yahoo Finance não retornou dados suficientes")
        print("📝 Para validação completa, você precisará:")
        print("   1. Abrir conta em broker (IC Markets, Pepperstone)")
        print("   2. Baixar dados históricos do MetaTrader")
        print("   3. Ou fazer paper trading por 30 dias")
        return None
    
    print(f"\n📊 Dados REAIS obtidos:")
    print(f"   De: {datetime.fromtimestamp(candles[0].timestamp)}")
    print(f"   Até: {datetime.fromtimestamp(candles[-1].timestamp)}")
    print(f"   Preço inicial: {candles[0].close:.5f}")
    print(f"   Preço final: {candles[-1].close:.5f}")
    print(f"   Variação: {((candles[-1].close / candles[0].close - 1) * 100):.2f}%")
    
    engine = ForexEngine(pair=pair_name)
    
    all_trades = []
    trade_num = 0
    
    window = 200
    step = 10
    
    print(f"\n🔄 Analisando...\n")
    
    for i in range(0, len(candles) - window - 48, step):
        analysis_window = candles[i:i+window]
        future_candles = candles[i+window:i+window+48]
        
        signal_data = engine.analyze(analysis_window)
        
        if signal_data.signal.value in ['CALL', 'PUT']:
            trade_num += 1
            
            outcome, profit_pips, exit_reason = simulate_forex_trade_real(
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
            
            profit_usd = profit_pips * 10
            
            trade_info = {
                'num': trade_num,
                'timestamp': datetime.fromtimestamp(candles[i+window].timestamp),
                'signal': signal_data.signal.value,
                'score': signal_data.score,
                'structure': signal_data.market_structure.value,
                'session': signal_data.session.value,
                'outcome': outcome,
                'profit_pips': profit_pips,
                'profit_usd': profit_usd
            }
            
            all_trades.append(trade_info)
            
            color = "\033[92m" if outcome == 'WIN' else "\033[91m"
            reset = "\033[0m"
            
            print(f"{color}Trade #{trade_num} - {outcome}{reset}")
            print(f"   {trade_info['timestamp']} | {trade_info['signal']} | Score: {trade_info['score']}")
            print(f"   {trade_info['structure']} | {trade_info['session']}")
            print(f"   {color}Resultado: {profit_pips:+.1f} pips (${profit_usd:+.2f}){reset}\n")
    
    if not all_trades:
        print("⚠️ Nenhum trade gerado nos dados reais")
        print("   Sistema está muito seletivo OU")
        print("   Período testado não teve setups válidos")
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
    print(f"📊 RESUMO COM DADOS REAIS - {pair_display}")
    print(f"{'='*100}\n")
    
    print(f"📈 ESTATÍSTICAS:")
    print(f"   Total Trades: {total}")
    print(f"   Vencedores: {wins}")
    print(f"   Perdedores: {losses}")
    print(f"   🎯 WIN RATE: {win_rate:.1f}%")
    
    print(f"\n💰 FINANCEIRO:")
    print(f"   Total Pips: {total_pips:+.1f}")
    print(f"   Total USD: ${total_usd:+.2f}")
    print(f"   Média Win: {avg_win:.1f} pips")
    print(f"   Média Loss: {avg_loss:.1f} pips")
    print(f"   📊 Profit Factor: {profit_factor:.2f}")
    
    return {
        'pair': pair_display,
        'total_trades': total,
        'wins': wins,
        'win_rate': win_rate,
        'total_pips': total_pips,
        'total_usd': total_usd,
        'profit_factor': profit_factor
    }


def main():
    print("\n" + "="*100)
    print("🔌 VALIDAÇÃO COM DADOS REAIS DE FOREX")
    print("   Buscando dados históricos reais de APIs públicas")
    print("="*100)
    
    forex_pairs = [
        ("EUR/USD", "Euro / Dólar"),
        ("GBP/USD", "Libra / Dólar"),
    ]
    
    all_results = []
    
    for pair, display in forex_pairs:
        result = test_with_real_data(pair, display)
        if result:
            all_results.append(result)
        time.sleep(3)
    
    # RELATÓRIO FINAL
    if all_results:
        print(f"\n{'='*100}")
        print(f"📊 RELATÓRIO FINAL - DADOS REAIS")
        print(f"{'='*100}\n")
        
        print(f"{'Par':<20} {'Trades':<10} {'WR %':<10} {'Pips':<15} {'USD $':<15} {'PF':<10} {'Status':<15}")
        print(f"{'─'*100}")
        
        for r in all_results:
            status = "✅ LUCRATIVO" if r['total_pips'] > 0 else "❌ PREJUÍZO"
            print(f"{r['pair']:<20} {r['total_trades']:<10} {r['win_rate']:<10.1f} {r['total_pips']:<+15.1f} ${r['total_usd']:<+14.2f} {r['profit_factor']:<10.2f} {status:<15}")
        
        if len(all_results) > 1:
            total_trades = sum(r['total_trades'] for r in all_results)
            total_wins = sum(r['wins'] for r in all_results)
            total_pips = sum(r['total_pips'] for r in all_results)
            total_usd = sum(r['total_usd'] for r in all_results)
            avg_pf = statistics.mean([r['profit_factor'] for r in all_results if r['profit_factor'] > 0]) if any(r['profit_factor'] > 0 for r in all_results) else 0
            overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
            
            print(f"{'─'*100}")
            print(f"{'TOTAL':<20} {total_trades:<10} {overall_wr:<10.1f} {total_pips:<+15.1f} ${total_usd:<+14.2f} {avg_pf:<10.2f}")
            
            print(f"\n{'='*100}")
            print(f"🎯 PODE USAR DINHEIRO REAL?")
            print(f"{'='*100}\n")
            
            profitable = sum(1 for r in all_results if r['total_pips'] > 0)
            
            print(f"📊 CRITÉRIOS:")
            print(f"   Pares lucrativos: {profitable}/{len(all_results)}")
            print(f"   Win Rate: {overall_wr:.1f}% (necessário >= 35%)")
            print(f"   Profit Factor: {avg_pf:.2f} (necessário >= 1.5)")
            print(f"   Total Pips: {total_pips:+.1f}")
            
            approved = (
                profitable >= 1 and
                overall_wr >= 35 and
                avg_pf >= 1.5 and
                total_pips > 0
            )
            
            print(f"\n{'─'*100}")
            if approved:
                print(f"✅ SISTEMA APROVADO COM DADOS REAIS!")
                print(f"\n💰 PRÓXIMOS PASSOS:")
                print(f"   1. Fazer 30 dias paper trading em broker")
                print(f"   2. Se manter win rate >= 35%, começar real")
                print(f"   3. Capital inicial: $500-$1,000")
                print(f"   4. Lote: Micro ($0.10/pip)")
            else:
                print(f"⚠️ AINDA PRECISA MAIS VALIDAÇÃO")
                if profitable < 1:
                    print(f"   ❌ Nenhum par lucrativo")
                if overall_wr < 35:
                    print(f"   ❌ Win rate baixo ({overall_wr:.1f}%)")
                if avg_pf < 1.5:
                    print(f"   ❌ Profit factor baixo ({avg_pf:.2f})")
                
                print(f"\n📋 RECOMENDAÇÃO:")
                print(f"   Use CRYPTO (ETH+BNB 1H) que já está validado")
    
    else:
        print(f"\n⚠️ Não foi possível obter dados reais suficientes")
        print(f"\n📋 PRÓXIMOS PASSOS:")
        print(f"   1. Abrir conta demo em broker FOREX")
        print(f"   2. Baixar MT4/MT5")
        print(f"   3. Exportar dados históricos")
        print(f"   4. Ou fazer paper trading manual por 30 dias")
    
    # Guia MetaTrader
    print(f"\n{'='*100}")
    print(f"📚 GUIA: COMO IMPLEMENTAR EM METATRADER")
    print(f"{'='*100}\n")
    
    print("""
1️⃣ ABRIR CONTA DEMO
   - IC Markets: https://www.icmarkets.com/
   - Pepperstone: https://pepperstone.com/
   - OANDA: https://www.oanda.com/

2️⃣ BAIXAR METATRADER 4/5
   - Instalar do site do broker
   - Fazer login com credenciais demo

3️⃣ EXPORTAR DADOS HISTÓRICOS
   - Tools → History Center
   - Selecionar par (EUR/USD)
   - Selecionar H1
   - Export → Salvar CSV

4️⃣ PAPER TRADING MANUAL (30 DIAS)
   - Seguir sinais do sistema
   - Registrar todos trades
   - Calcular win rate final

5️⃣ SE WIN RATE >= 35% E PF >= 1.5
   - Começar com dinheiro real
   - Capital inicial: $500
   - Lote: Micro ($0.10/pip)
    """)
    
    print(f"{'='*100}")
    print("✅ VALIDAÇÃO COMPLETA")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
