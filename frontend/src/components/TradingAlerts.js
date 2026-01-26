import { useState, useEffect, useCallback } from "react";
import { X, TrendingUp, TrendingDown, Clock, Target, AlertTriangle, Volume2, VolumeX } from "lucide-react";

// Trading Alert Component
export default function TradingAlerts({ messages, enabled = true }) {
  const [alerts, setAlerts] = useState([]);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [lastProcessedId, setLastProcessedId] = useState(null);

  // Extract trading signals from AI response
  const extractSignals = useCallback((content) => {
    const signals = {
      action: null,
      confidence: null,
      asset: null,
      stopLoss: null,
      takeProfit: null,
      trend: null,
      isStrong: false
    };

    const text = content.toUpperCase();

    // Detect action
    if (text.includes('COMPRA') || text.includes('CALL') || text.includes('BUY')) {
      signals.action = 'CALL';
    } else if (text.includes('VENDA') || text.includes('PUT') || text.includes('SELL')) {
      signals.action = 'PUT';
    }

    // Only continue if we have an action
    if (!signals.action) return null;

    // Extract confidence
    const confidenceMatch = text.match(/(\d+)\s*%.*(?:CONFIANÇA|CONFIDENCE|PROBABILIDADE)/);
    const confidenceMatch2 = text.match(/(?:CONFIANÇA|CONFIDENCE|PROBABILIDADE).*?(\d+)\s*%/);
    if (confidenceMatch) {
      signals.confidence = parseInt(confidenceMatch[1]);
    } else if (confidenceMatch2) {
      signals.confidence = parseInt(confidenceMatch2[1]);
    }

    // Check if it's a strong signal
    signals.isStrong = signals.confidence >= 70 || 
      text.includes('FORTE') || 
      text.includes('STRONG') ||
      text.includes('RECOMENDADO') ||
      text.includes('ALTA PROBABILIDADE');

    // Extract asset
    const assetPatterns = [
      /EUR\/USD/i, /GBP\/USD/i, /USD\/JPY/i, /BTC\/USD/i, /ETH\/USD/i,
      /EURUSD/i, /GBPUSD/i, /USDJPY/i, /BTCUSD/i, /ETHUSD/i,
      /OTC[A-Z]+/i
    ];
    for (const pattern of assetPatterns) {
      const match = content.match(pattern);
      if (match) {
        signals.asset = match[0].toUpperCase();
        break;
      }
    }

    // Extract stop loss
    const slMatch = content.match(/STOP.*?LOSS.*?(\d+[.,]\d+)/i);
    if (slMatch) {
      signals.stopLoss = slMatch[1].replace(',', '.');
    }

    // Extract take profit
    const tpMatch = content.match(/TAKE.*?PROFIT.*?(\d+[.,]\d+)/i);
    const alvoMatch = content.match(/ALVO.*?(\d+[.,]\d+)/i);
    if (tpMatch) {
      signals.takeProfit = tpMatch[1].replace(',', '.');
    } else if (alvoMatch) {
      signals.takeProfit = alvoMatch[1].replace(',', '.');
    }

    // Extract trend
    if (text.includes('TENDÊNCIA DE ALTA') || text.includes('UPTREND')) {
      signals.trend = 'ALTA';
    } else if (text.includes('TENDÊNCIA DE BAIXA') || text.includes('DOWNTREND')) {
      signals.trend = 'BAIXA';
    }

    return signals;
  }, []);

  // Play alert sound
  const playAlertSound = useCallback((isStrong) => {
    if (!soundEnabled) return;
    
    try {
      // Create audio context for alert sound
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      // Different sounds for strong vs normal alerts
      if (isStrong) {
        oscillator.frequency.setValueAtTime(880, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(1100, audioContext.currentTime + 0.1);
        oscillator.frequency.setValueAtTime(880, audioContext.currentTime + 0.2);
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.4);
      } else {
        oscillator.frequency.setValueAtTime(660, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
      }
    } catch (e) {
      console.log('Audio not supported');
    }
  }, [soundEnabled]);

  // Process new messages for trading signals
  useEffect(() => {
    if (!enabled || messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];
    
    // Only process assistant messages we haven't seen
    if (lastMessage.role !== 'assistant' || lastMessage.id === lastProcessedId) return;
    
    setLastProcessedId(lastMessage.id);

    const signals = extractSignals(lastMessage.content);
    
    if (signals && signals.action) {
      const newAlert = {
        id: Date.now(),
        ...signals,
        timestamp: new Date(),
        content: lastMessage.content.substring(0, 200) + '...'
      };

      setAlerts(prev => [newAlert, ...prev].slice(0, 5)); // Keep max 5 alerts
      playAlertSound(signals.isStrong);
    }
  }, [messages, enabled, lastProcessedId, extractSignals, playAlertSound]);

  // Remove alert
  const removeAlert = (alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  };

  // Auto-remove alerts after 30 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now();
      setAlerts(prev => prev.filter(a => now - a.id < 30000));
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  if (!enabled) return null;

  const formatTime = (date) => {
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const getConfidenceLevel = (confidence) => {
    if (!confidence) return 'medium';
    if (confidence >= 70) return 'high';
    if (confidence >= 50) return 'medium';
    return 'low';
  };

  return (
    <>
      {/* Alert Container */}
      <div className="trading-alert-container" data-testid="trading-alerts">
        {alerts.map((alert) => (
          <div 
            key={alert.id}
            className={`trading-alert alert-${alert.action.toLowerCase()} ${alert.isStrong ? 'alert-strong' : ''}`}
            data-testid={`alert-${alert.action.toLowerCase()}`}
          >
            <div className="alert-header">
              <span className={`alert-badge badge-${alert.action.toLowerCase()}`}>
                {alert.action === 'CALL' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                {alert.action}
                {alert.isStrong && ' 🔥'}
              </span>
              <button 
                className="alert-close"
                onClick={() => removeAlert(alert.id)}
                data-testid="close-alert-btn"
              >
                <X size={18} />
              </button>
            </div>

            <div className="alert-content">
              <div className="alert-title">
                {alert.isStrong && <AlertTriangle size={18} className="text-yellow-400" />}
                {alert.asset ? `Sinal ${alert.action} - ${alert.asset}` : `Sinal de ${alert.action} Detectado!`}
              </div>

              <div className="alert-details">
                {alert.trend && (
                  <div className="alert-detail-item">
                    <span>📈 Tendência:</span>
                    <strong>{alert.trend}</strong>
                  </div>
                )}
                {alert.stopLoss && (
                  <div className="alert-detail-item">
                    <Target size={14} />
                    <span>SL:</span>
                    <strong>{alert.stopLoss}</strong>
                  </div>
                )}
                {alert.takeProfit && (
                  <div className="alert-detail-item">
                    <Target size={14} />
                    <span>TP:</span>
                    <strong>{alert.takeProfit}</strong>
                  </div>
                )}
              </div>

              {alert.confidence && (
                <div className="alert-confidence">
                  <div className="alert-detail-item">
                    <span>Confiança: <strong>{alert.confidence}%</strong></span>
                  </div>
                  <div className="confidence-bar">
                    <div 
                      className={`confidence-fill ${getConfidenceLevel(alert.confidence)}`}
                      style={{ width: `${alert.confidence}%` }}
                    />
                  </div>
                </div>
              )}

              <div className="alert-timestamp">
                <Clock size={12} />
                {formatTime(alert.timestamp)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Sound Toggle */}
      <button
        className={`alert-sound-indicator ${!soundEnabled ? 'muted' : ''}`}
        onClick={() => setSoundEnabled(!soundEnabled)}
        title={soundEnabled ? 'Desativar som de alertas' : 'Ativar som de alertas'}
        data-testid="sound-toggle"
      >
        {soundEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
        <span>{soundEnabled ? 'Alertas: ON' : 'Alertas: OFF'}</span>
      </button>
    </>
  );
}
