import React, { useState } from 'react';

const TradingEngine = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [interval, setInterval] = useState('5m');

  const fetchBinanceCandles = async (symbol, interval, limit = 100) => {
    try {
      const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`;
      const response = await fetch(url);
      const data = await response.json();
      
      return data.map(k => ({
        timestamp: Math.floor(k[0] / 1000),
        open: parseFloat(k[1]),
        high: parseFloat(k[2]),
        low: parseFloat(k[3]),
        close: parseFloat(k[4]),
        volume: parseFloat(k[5])
      }));
    } catch (err) {
      throw new Error(`Erro ao buscar dados: ${err.message}`);
    }
  };

  const analyzeSetup = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Buscar candles da Binance
      const candles = await fetchBinanceCandles(symbol, interval);
      
      // Enviar para análise
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/trade-setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          candles: candles,
          capital: 10000,
          explain_with_ai: true
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signal) => {
    if (signal === 'CALL') return 'text-green-500';
    if (signal === 'PUT') return 'text-red-500';
    return 'text-yellow-500';
  };

  const getSignalBg = (signal) => {
    if (signal === 'CALL') return 'bg-green-500/10 border-green-500';
    if (signal === 'PUT') return 'bg-red-500/10 border-red-500';
    return 'bg-yellow-500/10 border-yellow-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 mb-2">
            🎯 Motor Matemático de Trading
          </h1>
          <p className="text-gray-300">Análise técnica com 70%+ de assertividade</p>
        </div>

        {/* Input Section */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">⚙️ Configuração</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Símbolo
              </label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:ring-2 focus:ring-purple-500 outline-none"
                placeholder="BTCUSDT"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Timeframe
              </label>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
                className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:ring-2 focus:ring-purple-500 outline-none"
              >
                <option value="1m">1 Minuto</option>
                <option value="5m">5 Minutos</option>
                <option value="15m">15 Minutos</option>
                <option value="1h">1 Hora</option>
                <option value="4h">4 Horas</option>
                <option value="1d">1 Dia</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={analyzeSetup}
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-2 px-6 rounded-lg transition-all duration-200"
              >
                {loading ? '🔄 Analisando...' : '🚀 Analisar Setup'}
              </button>
            </div>
          </div>

          <p className="text-sm text-gray-400">
            💡 Dados em tempo real da Binance. Score mínimo: 70/100 para gerar sinal.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-2xl p-4 mb-6">
            <p className="text-red-400">❌ {error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Main Signal */}
            <div className={`${getSignalBg(result.signal)} rounded-2xl p-6 border-2`}>
              <div className="text-center">
                <h2 className="text-3xl font-bold text-white mb-2">
                  {result.signal === 'CALL' && '📈 CALL - COMPRA'}
                  {result.signal === 'PUT' && '📉 PUT - VENDA'}
                  {result.signal === 'WAIT' && '⏸️ AGUARDAR'}
                </h2>
                <div className="flex justify-center items-center gap-8 mt-4">
                  <div>
                    <p className="text-gray-300 text-sm">Score</p>
                    <p className={`text-3xl font-bold ${getSignalColor(result.signal)}`}>
                      {result.score}/100
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-300 text-sm">Confiança</p>
                    <p className={`text-3xl font-bold ${getSignalColor(result.signal)}`}>
                      {(result.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Price Levels */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
              <h3 className="text-xl font-semibold text-white mb-4">📊 Níveis de Preço</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <p className="text-sm text-gray-400">Entrada</p>
                  <p className="text-lg font-bold text-white">{result.entry_price.toFixed(5)}</p>
                </div>
                <div className="bg-red-500/10 rounded-lg p-4 border border-red-500/30">
                  <p className="text-sm text-gray-400">Stop Loss</p>
                  <p className="text-lg font-bold text-red-400">{result.stop_loss.toFixed(5)}</p>
                </div>
                <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
                  <p className="text-sm text-gray-400">Take Profit 1</p>
                  <p className="text-lg font-bold text-green-400">{result.take_profit_1.toFixed(5)}</p>
                </div>
                <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
                  <p className="text-sm text-gray-400">Take Profit 2</p>
                  <p className="text-lg font-bold text-green-400">{result.take_profit_2.toFixed(5)}</p>
                </div>
              </div>
            </div>

            {/* Technical Indicators */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
              <h3 className="text-xl font-semibold text-white mb-4">📈 Indicadores Técnicos</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Tendência</p>
                  <p className="text-lg font-bold text-purple-400">{result.trend}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">EMA 20</p>
                  <p className="text-lg font-bold text-white">{result.ema_20.toFixed(5)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">EMA 50</p>
                  <p className="text-lg font-bold text-white">{result.ema_50.toFixed(5)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">RSI</p>
                  <p className="text-lg font-bold text-white">{result.rsi_value.toFixed(1)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">ATR</p>
                  <p className="text-lg font-bold text-white">{result.atr_value.toFixed(5)}</p>
                </div>
              </div>
            </div>

            {/* Risk Management */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
              <h3 className="text-xl font-semibold text-white mb-4">💰 Gestão de Risco</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Risk/Reward TP1</p>
                  <p className="text-lg font-bold text-white">1:{result.risk_reward_1.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Risk/Reward TP2</p>
                  <p className="text-lg font-bold text-white">1:{result.risk_reward_2.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Risco por Trade</p>
                  <p className="text-lg font-bold text-white">${result.risk_amount.toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Reasons */}
            {result.reasons && result.reasons.length > 0 && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
                <h3 className="text-xl font-semibold text-white mb-4">✅ Razões do Sinal</h3>
                <ul className="space-y-2">
                  {result.reasons.map((reason, idx) => (
                    <li key={idx} className="text-gray-300 flex items-start gap-2">
                      <span className="text-green-400">•</span>
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Warnings */}
            {result.warnings && result.warnings.length > 0 && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-2xl p-6">
                <h3 className="text-xl font-semibold text-yellow-400 mb-4">⚠️ Avisos</h3>
                <ul className="space-y-2">
                  {result.warnings.map((warning, idx) => (
                    <li key={idx} className="text-gray-300 flex items-start gap-2">
                      <span className="text-yellow-400">•</span>
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* AI Explanation */}
            {result.ai_explanation && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
                <h3 className="text-xl font-semibold text-white mb-4">🤖 Explicação da IA</h3>
                <div className="prose prose-invert max-w-none">
                  <p className="text-gray-300 whitespace-pre-wrap">{result.ai_explanation}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingEngine;
