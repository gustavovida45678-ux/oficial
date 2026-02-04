"""
🎯 Motor Matemático de Trading - Análise Técnica Avançada
Objetivo: 70%+ win rate com gestão inteligente de perdas
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Tipos de sinal de trading"""
    CALL = "CALL"  # Compra
    PUT = "PUT"    # Venda
    WAIT = "WAIT"  # Aguardar


class TrendType(Enum):
    """Tipos de tendência"""
    BULLISH = "ALTA"      # Tendência de alta
    BEARISH = "BAIXA"     # Tendência de baixa
    SIDEWAYS = "LATERAL"  # Lateral/consolidação


@dataclass
class Candle:
    """Estrutura de um candle OHLCV"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class TradingSignal:
    """Sinal de trading com todos os detalhes"""
    signal: SignalType
    score: int  # 0-100
    confidence: float  # 0.0-1.0
    
    # Níveis de preço
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    
    # Análise técnica
    trend: TrendType
    rsi_value: float
    ema_20: float
    ema_50: float
    atr_value: float
    
    # Risk Management
    risk_reward_1: float  # RR para TP1
    risk_reward_2: float  # RR para TP2
    risk_amount: float    # Valor em risco
    
    # Razões para o sinal
    reasons: List[str]
    warnings: List[str]


class TechnicalIndicators:
    """Calculadora de indicadores técnicos"""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """
        Calcula EMA (Exponential Moving Average)
        Dá mais peso aos preços recentes
        """
        if len(prices) < period:
            return np.mean(prices)
        
        prices_array = np.array(prices)
        ema = prices_array[:period].mean()
        multiplier = 2 / (period + 1)
        
        for price in prices_array[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Calcula RSI (Relative Strength Index)
        Valores: 0-100
        > 70: Sobrecomprado
        < 30: Sobrevendido
        """
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_atr(candles: List[Candle], period: int = 14) -> float:
        """
        Calcula ATR (Average True Range)
        Mede a volatilidade do ativo
        """
        if len(candles) < period:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i-1].close
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return np.mean(true_ranges[-period:])
    
    @staticmethod
    def calculate_macd(prices: List[float]) -> Tuple[float, float, float]:
        """
        Calcula MACD (Moving Average Convergence Divergence)
        Returns: (macd_line, signal_line, histogram)
        """
        if len(prices) < 26:
            return 0.0, 0.0, 0.0
        
        ema_12 = TechnicalIndicators.calculate_ema(prices, 12)
        ema_26 = TechnicalIndicators.calculate_ema(prices, 26)
        macd_line = ema_12 - ema_26
        
        # Signal line (EMA 9 do MACD)
        signal_line = macd_line * 0.2  # Simplified
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def detect_candle_pattern(candles: List[Candle]) -> Tuple[str, int]:
        """
        Detecta padrões de candles
        Returns: (pattern_name, score_contribution)
        """
        if len(candles) < 3:
            return "INSUFFICIENT_DATA", 0
        
        current = candles[-1]
        prev = candles[-2]
        
        body_current = abs(current.close - current.open)
        body_prev = abs(prev.close - prev.open)
        
        # Hammer (Martelo) - bullish
        if (current.close > current.open and 
            body_current < (current.high - current.low) * 0.3 and
            (current.close - current.low) > body_current * 2):
            return "HAMMER_BULLISH", 15
        
        # Shooting Star - bearish
        if (current.close < current.open and
            body_current < (current.high - current.low) * 0.3 and
            (current.high - current.close) > body_current * 2):
            return "SHOOTING_STAR_BEARISH", 15
        
        # Engulfing Bullish
        if (current.close > current.open and 
            prev.close < prev.open and
            current.close > prev.open and
            current.open < prev.close):
            return "ENGULFING_BULLISH", 15
        
        # Engulfing Bearish
        if (current.close < current.open and
            prev.close > prev.open and
            current.close < prev.open and
            current.open > prev.close):
            return "ENGULFING_BEARISH", 15
        
        # Doji - indecisão
        if body_current < (current.high - current.low) * 0.1:
            return "DOJI_INDECISION", 5
        
        return "NO_PATTERN", 8


class TradingEngine:
    """
    Motor principal de trading
    Estratégia: Tendência + Recuo + Confirmação
    """
    
    def __init__(self, 
                 min_score: int = 70,
                 risk_reward_min: float = 2.0,
                 max_daily_loss_pct: float = 2.0,
                 max_drawdown_pct: float = 10.0):
        """
        Args:
            min_score: Score mínimo para gerar sinal (0-100)
            risk_reward_min: Risk/Reward mínimo aceito
            max_daily_loss_pct: Perda máxima diária (% do capital)
            max_drawdown_pct: Drawdown máximo permitido
        """
        self.min_score = min_score
        self.risk_reward_min = risk_reward_min
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        
        self.indicators = TechnicalIndicators()
    
    def analyze(self, candles: List[Candle], capital: float = 10000.0) -> TradingSignal:
        """
        Análise principal - gera sinal de trading
        
        Args:
            candles: Lista de candles OHLCV (mínimo 50 recomendado)
            capital: Capital disponível para trading
        
        Returns:
            TradingSignal com análise completa
        """
        if len(candles) < 50:
            logger.warning(f"Poucos candles para análise confiável: {len(candles)}")
        
        # Extrair preços de fechamento
        closes = [c.close for c in candles]
        current_price = candles[-1].close
        
        # Calcular indicadores
        ema_20 = self.indicators.calculate_ema(closes, 20)
        ema_50 = self.indicators.calculate_ema(closes, 50)
        rsi = self.indicators.calculate_rsi(closes, 14)
        atr = self.indicators.calculate_atr(candles, 14)
        macd, signal, histogram = self.indicators.calculate_macd(closes)
        
        # Detectar padrão de candle
        pattern, pattern_score = self.indicators.detect_candle_pattern(candles)
        
        # Inicializar score e razões
        score = 0
        reasons = []
        warnings = []
        
        # === ANÁLISE DE TENDÊNCIA (25 pontos) ===
        trend, trend_score = self._analyze_trend(ema_20, ema_50, current_price)
        score += trend_score
        
        if trend == TrendType.BULLISH:
            reasons.append(f"✅ Tendência de ALTA confirmada (EMA20: {ema_20:.5f} > EMA50: {ema_50:.5f})")
        elif trend == TrendType.BEARISH:
            reasons.append(f"✅ Tendência de BAIXA confirmada (EMA20: {ema_20:.5f} < EMA50: {ema_50:.5f})")
        else:
            warnings.append(f"⚠️ Mercado LATERAL - aguardar tendência clara")
        
        # === ANÁLISE DE RECUO (25 pontos) ===
        pullback_score, pullback_valid = self._analyze_pullback(
            current_price, ema_20, ema_50, trend
        )
        score += pullback_score
        
        if pullback_valid:
            reasons.append(f"✅ Recuo saudável detectado - preço próximo à EMA20")
        
        # === ANÁLISE RSI (20 pontos) ===
        rsi_score = self._analyze_rsi(rsi, trend)
        score += rsi_score
        
        if 40 <= rsi <= 60:
            reasons.append(f"✅ RSI equilibrado ({rsi:.1f}) - momentum neutro")
        elif trend == TrendType.BULLISH and 30 <= rsi < 40:
            reasons.append(f"✅ RSI em zona de compra ({rsi:.1f})")
        elif trend == TrendType.BEARISH and 60 < rsi <= 70:
            reasons.append(f"✅ RSI em zona de venda ({rsi:.1f})")
        else:
            warnings.append(f"⚠️ RSI em extremo ({rsi:.1f}) - aguardar normalização")
        
        # === ANÁLISE DE VOLUME (15 pontos) ===
        volume_score = self._analyze_volume(candles)
        score += volume_score
        
        if volume_score >= 12:
            reasons.append(f"✅ Volume forte confirmando movimento")
        
        # === PADRÃO DE CANDLE (15 pontos) ===
        score += pattern_score
        
        if pattern_score >= 12:
            reasons.append(f"✅ Padrão de candle detectado: {pattern}")
        
        # === DETERMINAR SINAL ===
        signal_type = SignalType.WAIT
        
        if score >= self.min_score:
            if trend == TrendType.BULLISH and pullback_valid:
                signal_type = SignalType.CALL
            elif trend == TrendType.BEARISH and pullback_valid:
                signal_type = SignalType.PUT
        else:
            warnings.append(f"⚠️ Score insuficiente ({score}/{self.min_score}) - aguardar setup melhor")
        
        # === CALCULAR NÍVEIS DE STOP LOSS E TAKE PROFIT ===
        stop_loss, tp1, tp2 = self._calculate_levels(
            current_price, atr, signal_type
        )
        
        # Calcular Risk/Reward
        if signal_type == SignalType.CALL:
            risk = current_price - stop_loss
            reward_1 = tp1 - current_price
            reward_2 = tp2 - current_price
        elif signal_type == SignalType.PUT:
            risk = stop_loss - current_price
            reward_1 = current_price - tp1
            reward_2 = current_price - tp2
        else:
            risk = atr * 1.5
            reward_1 = risk * 2
            reward_2 = risk * 3
        
        rr_1 = reward_1 / risk if risk > 0 else 0
        rr_2 = reward_2 / risk if risk > 0 else 0
        
        # Validar Risk/Reward
        if signal_type != SignalType.WAIT and rr_1 < self.risk_reward_min:
            warnings.append(f"⚠️ Risk/Reward baixo ({rr_1:.2f}) - aumentar TP ou ajustar SL")
            signal_type = SignalType.WAIT
        
        # Calcular risco em capital
        risk_amount = capital * 0.01  # 1% do capital por trade
        
        # Calcular confiança (0.0 - 1.0)
        confidence = min(score / 100.0, 1.0)
        
        # Criar sinal
        signal = TradingSignal(
            signal=signal_type,
            score=score,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            trend=trend,
            rsi_value=rsi,
            ema_20=ema_20,
            ema_50=ema_50,
            atr_value=atr,
            risk_reward_1=rr_1,
            risk_reward_2=rr_2,
            risk_amount=risk_amount,
            reasons=reasons,
            warnings=warnings
        )
        
        return signal
    
    def _analyze_trend(self, ema_20: float, ema_50: float, 
                       current_price: float) -> Tuple[TrendType, int]:
        """
        Analisa tendência baseado nas EMAs
        Returns: (trend_type, score_contribution)
        """
        # Spread entre EMAs (em %)
        spread = abs(ema_20 - ema_50) / ema_50 * 100
        
        if ema_20 > ema_50:
            # Tendência de alta
            if spread >= 0.5:  # Forte
                return TrendType.BULLISH, 25
            elif spread >= 0.2:  # Moderada
                return TrendType.BULLISH, 20
            else:  # Fraca
                return TrendType.BULLISH, 15
        elif ema_20 < ema_50:
            # Tendência de baixa
            if spread >= 0.5:  # Forte
                return TrendType.BEARISH, 25
            elif spread >= 0.2:  # Moderada
                return TrendType.BEARISH, 20
            else:  # Fraca
                return TrendType.BEARISH, 15
        else:
            # Lateral
            return TrendType.SIDEWAYS, 5
    
    def _analyze_pullback(self, current_price: float, ema_20: float,
                          ema_50: float, trend: TrendType) -> Tuple[int, bool]:
        """
        Analisa se há recuo válido para entrada
        Returns: (score_contribution, is_valid)
        """
        distance_to_ema20 = abs(current_price - ema_20) / ema_20 * 100
        
        if trend == TrendType.BULLISH:
            # Para CALL, queremos que o preço esteja próximo ou acima da EMA20
            if distance_to_ema20 <= 0.3:  # Muito próximo
                return 25, True
            elif distance_to_ema20 <= 0.5:
                return 20, True
            elif distance_to_ema20 <= 1.0:
                return 15, True
            else:
                return 0, False
        
        elif trend == TrendType.BEARISH:
            # Para PUT, queremos que o preço esteja próximo ou abaixo da EMA20
            if distance_to_ema20 <= 0.3:
                return 25, True
            elif distance_to_ema20 <= 0.5:
                return 20, True
            elif distance_to_ema20 <= 1.0:
                return 15, True
            else:
                return 0, False
        
        else:
            return 0, False
    
    def _analyze_rsi(self, rsi: float, trend: TrendType) -> int:
        """
        Analisa RSI considerando a tendência
        Returns: score_contribution
        """
        if trend == TrendType.BULLISH:
            # Para CALL, RSI ideal entre 30-60
            if 40 <= rsi <= 60:
                return 20
            elif 30 <= rsi < 40:
                return 18
            elif 60 < rsi <= 70:
                return 10
            else:
                return 0
        
        elif trend == TrendType.BEARISH:
            # Para PUT, RSI ideal entre 40-70
            if 40 <= rsi <= 60:
                return 20
            elif 60 < rsi <= 70:
                return 18
            elif 30 <= rsi < 40:
                return 10
            else:
                return 0
        
        else:
            # Lateral
            if 40 <= rsi <= 60:
                return 15
            else:
                return 5
    
    def _analyze_volume(self, candles: List[Candle]) -> int:
        """
        Analisa volume para confirmar movimento
        Returns: score_contribution
        """
        if len(candles) < 20:
            return 8
        
        # Volume médio dos últimos 20 candles
        avg_volume = np.mean([c.volume for c in candles[-20:]])
        current_volume = candles[-1].volume
        
        # Volume atual vs média
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio >= 1.5:  # 50% acima da média
            return 15
        elif volume_ratio >= 1.2:  # 20% acima
            return 12
        elif volume_ratio >= 1.0:  # Na média
            return 10
        else:  # Abaixo da média
            return 5
    
    def _calculate_levels(self, entry: float, atr: float, 
                         signal: SignalType) -> Tuple[float, float, float]:
        """
        Calcula Stop Loss e Take Profits
        Returns: (stop_loss, take_profit_1, take_profit_2)
        """
        # Stop Loss: 1.5x ATR
        sl_distance = atr * 1.5
        
        # Take Profit 1: 2x risco (RR 1:2)
        tp1_distance = sl_distance * 2
        
        # Take Profit 2: 3x risco (RR 1:3)
        tp2_distance = sl_distance * 3
        
        if signal == SignalType.CALL:
            stop_loss = entry - sl_distance
            tp1 = entry + tp1_distance
            tp2 = entry + tp2_distance
        elif signal == SignalType.PUT:
            stop_loss = entry + sl_distance
            tp1 = entry - tp1_distance
            tp2 = entry - tp2_distance
        else:
            # WAIT - valores neutros
            stop_loss = entry - sl_distance
            tp1 = entry + tp1_distance
            tp2 = entry + tp2_distance
        
        return stop_loss, tp1, tp2


class Backtester:
    """Sistema de backtest para validar estratégia"""
    
    def __init__(self, engine: TradingEngine):
        self.engine = engine
    
    def run(self, historical_candles: List[Candle], 
            initial_capital: float = 10000.0) -> Dict:
        """
        Executa backtest na série histórica
        
        Returns:
            Dict com métricas de performance
        """
        capital = initial_capital
        trades = []
        wins = 0
        losses = 0
        
        # Simular trading com janela deslizante
        window_size = 50
        
        for i in range(window_size, len(historical_candles) - 1):
            # Pegar janela de candles
            window = historical_candles[i-window_size:i]
            
            # Gerar sinal
            signal = self.engine.analyze(window, capital)
            
            if signal.signal == SignalType.WAIT:
                continue
            
            # Simular execução do trade
            entry_price = signal.entry_price
            stop_loss = signal.stop_loss
            tp1 = signal.take_profit_1
            
            # Ver o que aconteceu no próximo candle
            next_candle = historical_candles[i + 1]
            
            # Verificar se hit SL ou TP
            hit_sl = False
            hit_tp = False
            
            if signal.signal == SignalType.CALL:
                if next_candle.low <= stop_loss:
                    hit_sl = True
                elif next_candle.high >= tp1:
                    hit_tp = True
            else:  # PUT
                if next_candle.high >= stop_loss:
                    hit_sl = True
                elif next_candle.low <= tp1:
                    hit_tp = True
            
            # Calcular resultado
            if hit_tp:
                profit = signal.risk_amount * signal.risk_reward_1
                capital += profit
                wins += 1
                trades.append({
                    'type': signal.signal.value,
                    'entry': entry_price,
                    'exit': tp1,
                    'result': 'WIN',
                    'profit': profit
                })
            elif hit_sl:
                loss = signal.risk_amount
                capital -= loss
                losses += 1
                trades.append({
                    'type': signal.signal.value,
                    'entry': entry_price,
                    'exit': stop_loss,
                    'result': 'LOSS',
                    'profit': -loss
                })
        
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Calcular métricas
        profit_factor = 0
        if losses > 0:
            total_wins_value = sum([t['profit'] for t in trades if t['result'] == 'WIN'])
            total_losses_value = abs(sum([t['profit'] for t in trades if t['result'] == 'LOSS']))
            profit_factor = total_wins_value / total_losses_value if total_losses_value > 0 else 0
        
        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'initial_capital': initial_capital,
            'final_capital': capital,
            'profit': capital - initial_capital,
            'profit_pct': ((capital - initial_capital) / initial_capital * 100),
            'profit_factor': profit_factor,
            'trades': trades
        }
