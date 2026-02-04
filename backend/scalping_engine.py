"""
🎯 SCALPING ENGINE - Otimizado para 5 MINUTOS
Sistema específico para timeframes curtos com alta taxa de acerto
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class SignalType(Enum):
    CALL = "CALL"
    PUT = "PUT"
    WAIT = "WAIT"


@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class ScalpSignal:
    signal: SignalType
    score: int
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    
    # Indicadores
    ema_9: float
    ema_21: float
    rsi_value: float
    momentum: float
    volatility: str
    
    reasons: List[str]
    warnings: List[str]


class ScalpingIndicators:
    """Indicadores rápidos para scalping"""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
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
    def calculate_momentum(prices: List[float], period: int = 10) -> float:
        """Momentum = preço atual vs preço N períodos atrás"""
        if len(prices) < period + 1:
            return 0
        
        return ((prices[-1] - prices[-period-1]) / prices[-period-1]) * 100
    
    @staticmethod
    def detect_micro_trend(prices: List[float], ema_9: float, ema_21: float) -> str:
        """Detecta micro tendência dos últimos 5-10 candles"""
        if len(prices) < 10:
            return "UNCLEAR"
        
        recent_prices = prices[-10:]
        
        # Contar quantos closes estão acima/abaixo das EMAs
        above_9 = sum(1 for p in recent_prices[-5:] if p > ema_9)
        below_9 = sum(1 for p in recent_prices[-5:] if p < ema_9)
        
        # Verificar alinhamento de EMAs
        ema_aligned_up = ema_9 > ema_21
        ema_aligned_down = ema_9 < ema_21
        
        # Micro uptrend
        if above_9 >= 4 and ema_aligned_up:
            return "UP"
        # Micro downtrend
        elif below_9 >= 4 and ema_aligned_down:
            return "DOWN"
        else:
            return "RANGING"
    
    @staticmethod
    def calculate_atr_fast(candles: List[Candle], period: int = 7) -> float:
        """ATR rápido para scalping"""
        if len(candles) < period:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i-1].close
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
        
        return np.mean(true_ranges[-period:])
    
    @staticmethod
    def detect_volatility_spike(candles: List[Candle]) -> bool:
        """Detecta spike de volatilidade (evitar)"""
        if len(candles) < 20:
            return False
        
        recent_ranges = [(c.high - c.low) for c in candles[-10:]]
        avg_range = np.mean([(c.high - c.low) for c in candles[-20:-10]])
        
        current_range = candles[-1].high - candles[-1].low
        
        # Spike se atual é 2x a média
        return current_range > avg_range * 2.0
    
    @staticmethod
    def check_volume_surge(candles: List[Candle]) -> float:
        """Ratio de volume atual vs média"""
        if len(candles) < 20:
            return 1.0
        
        avg_volume = np.mean([c.volume for c in candles[-20:-1]])
        current_volume = candles[-1].volume
        
        if avg_volume == 0:
            return 1.0
        
        return current_volume / avg_volume


class ScalpingEngine:
    """
    Motor de SCALPING para 5 minutos
    Estratégia: Quick in, Quick out
    Objetivo: 60-70% win rate com RR 1:1.5
    """
    
    def __init__(self):
        self.indicators = ScalpingIndicators()
    
    def analyze(self, candles: List[Candle], capital: float = 10000.0) -> ScalpSignal:
        """Análise para scalping em 5min"""
        
        if len(candles) < 50:
            return self._wait_signal("Dados insuficientes")
        
        closes = [c.close for c in candles]
        current_price = candles[-1].close
        
        # Indicadores RÁPIDOS
        ema_9 = self.indicators.calculate_ema(closes, 9)
        ema_21 = self.indicators.calculate_ema(closes, 21)
        rsi = self.indicators.calculate_rsi(closes, 14)
        momentum = self.indicators.calculate_momentum(closes, 10)
        atr = self.indicators.calculate_atr_fast(candles, 7)
        
        # Detectores
        micro_trend = self.indicators.detect_micro_trend(closes, ema_9, ema_21)
        volatility_spike = self.indicators.detect_volatility_spike(candles)
        volume_ratio = self.indicators.check_volume_surge(candles)
        
        # FILTRO CRÍTICO 1: Não operar em volatilidade extrema
        if volatility_spike:
            return self._wait_signal("Volatilidade extrema detectada")
        
        # FILTRO CRÍTICO 2: Volume mínimo
        if volume_ratio < 0.8:
            return self._wait_signal("Volume muito baixo")
        
        # FILTRO CRÍTICO 3: Apenas em micro trends claros
        if micro_trend == "RANGING":
            return self._wait_signal("Mercado sem direção clara")
        
        # Inicializar
        score = 0
        reasons = []
        warnings = []
        signal_type = SignalType.WAIT
        
        # === ANÁLISE DE SETUP ===
        
        if micro_trend == "UP":
            signal_type, score, reasons = self._analyze_scalp_long(
                current_price, ema_9, ema_21, rsi, momentum, volume_ratio
            )
        
        elif micro_trend == "DOWN":
            signal_type, score, reasons = self._analyze_scalp_short(
                current_price, ema_9, ema_21, rsi, momentum, volume_ratio
            )
        
        # Calcular níveis (SCALPING = alvos pequenos)
        stop_loss, tp1, tp2 = self._calculate_scalp_levels(
            current_price, atr, signal_type
        )
        
        # Validar Risk/Reward mínimo
        if signal_type == SignalType.CALL:
            risk = current_price - stop_loss
            reward = tp1 - current_price
        elif signal_type == SignalType.PUT:
            risk = stop_loss - current_price
            reward = current_price - tp1
        else:
            risk = atr
            reward = atr * 1.5
        
        rr = reward / risk if risk > 0 else 0
        
        # Scalping aceita RR menor (1:1.2 mínimo)
        if signal_type != SignalType.WAIT and rr < 1.2:
            return self._wait_signal(f"Risk/Reward insuficiente ({rr:.2f})")
        
        confidence = min(score / 100.0, 1.0)
        
        volatility_level = "HIGH" if volatility_spike else "NORMAL"
        
        return ScalpSignal(
            signal=signal_type,
            score=score,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            ema_9=ema_9,
            ema_21=ema_21,
            rsi_value=rsi,
            momentum=momentum,
            volatility=volatility_level,
            reasons=reasons,
            warnings=warnings
        )
    
    def _analyze_scalp_long(self, price: float, ema9: float, ema21: float,
                           rsi: float, momentum: float, vol_ratio: float) -> Tuple[SignalType, int, List[str]]:
        """Análise de scalp LONG (CALL)"""
        score = 0
        reasons = []
        
        # 1. Preço acima de EMA9 (35 pts)
        if price > ema9:
            distance = ((price - ema9) / ema9) * 100
            
            if 0.05 <= distance <= 0.3:  # Muito próximo = ideal
                score += 35
                reasons.append(f"✅ Preço ideal acima EMA9 ({distance:.2f}%)")
            elif 0 <= distance < 0.05:
                score += 30
                reasons.append("✅ Preço tocando EMA9 (pullback perfeito)")
            elif 0.3 < distance <= 0.5:
                score += 25
                reasons.append("⚠️ Preço um pouco distante da EMA9")
        else:
            reasons.append("❌ Preço abaixo EMA9")
        
        # 2. EMA9 > EMA21 (25 pts)
        if ema9 > ema21:
            spread = ((ema9 - ema21) / ema21) * 100
            if spread >= 0.1:
                score += 25
                reasons.append("✅ EMAs alinhadas para alta")
            else:
                score += 15
                reasons.append("⚠️ EMAs muito próximas")
        
        # 3. RSI entre 45-70 (20 pts)
        if 50 <= rsi <= 65:
            score += 20
            reasons.append(f"✅ RSI ideal ({rsi:.1f})")
        elif 45 <= rsi < 50:
            score += 15
            reasons.append(f"✅ RSI bom ({rsi:.1f})")
        elif 65 < rsi <= 75:
            score += 10
            reasons.append(f"⚠️ RSI elevado ({rsi:.1f})")
        
        # 4. Momentum positivo (15 pts)
        if momentum > 0.2:
            score += 15
            reasons.append(f"✅ Momentum forte (+{momentum:.2f}%)")
        elif momentum > 0:
            score += 10
            reasons.append(f"✅ Momentum positivo (+{momentum:.2f}%)")
        
        # 5. Volume confirmando (5 pts)
        if vol_ratio >= 1.3:
            score += 5
            reasons.append(f"✅ Volume forte ({vol_ratio:.2f}x)")
        
        # Decisão (score mínimo 70 para scalping)
        if score >= 70:
            return SignalType.CALL, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _analyze_scalp_short(self, price: float, ema9: float, ema21: float,
                            rsi: float, momentum: float, vol_ratio: float) -> Tuple[SignalType, int, List[str]]:
        """Análise de scalp SHORT (PUT)"""
        score = 0
        reasons = []
        
        # 1. Preço abaixo de EMA9 (35 pts)
        if price < ema9:
            distance = ((ema9 - price) / ema9) * 100
            
            if 0.05 <= distance <= 0.3:
                score += 35
                reasons.append(f"✅ Preço ideal abaixo EMA9 ({distance:.2f}%)")
            elif 0 <= distance < 0.05:
                score += 30
                reasons.append("✅ Preço tocando EMA9 (pullback perfeito)")
            elif 0.3 < distance <= 0.5:
                score += 25
                reasons.append("⚠️ Preço um pouco distante da EMA9")
        else:
            reasons.append("❌ Preço acima EMA9")
        
        # 2. EMA9 < EMA21 (25 pts)
        if ema9 < ema21:
            spread = ((ema21 - ema9) / ema21) * 100
            if spread >= 0.1:
                score += 25
                reasons.append("✅ EMAs alinhadas para baixa")
            else:
                score += 15
                reasons.append("⚠️ EMAs muito próximas")
        
        # 3. RSI entre 30-55 (20 pts)
        if 35 <= rsi <= 50:
            score += 20
            reasons.append(f"✅ RSI ideal ({rsi:.1f})")
        elif 50 < rsi <= 55:
            score += 15
            reasons.append(f"✅ RSI bom ({rsi:.1f})")
        elif 25 <= rsi < 35:
            score += 10
            reasons.append(f"⚠️ RSI baixo ({rsi:.1f})")
        
        # 4. Momentum negativo (15 pts)
        if momentum < -0.2:
            score += 15
            reasons.append(f"✅ Momentum forte ({momentum:.2f}%)")
        elif momentum < 0:
            score += 10
            reasons.append(f"✅ Momentum negativo ({momentum:.2f}%)")
        
        # 5. Volume confirmando (5 pts)
        if vol_ratio >= 1.3:
            score += 5
            reasons.append(f"✅ Volume forte ({vol_ratio:.2f}x)")
        
        # Decisão
        if score >= 70:
            return SignalType.PUT, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _calculate_scalp_levels(self, entry: float, atr: float, 
                               signal: SignalType) -> Tuple[float, float, float]:
        """
        Níveis de scalping = alvos PEQUENOS e rápidos
        """
        # Stop loss APERTADO para scalping (1.5x ATR ou menos)
        sl_distance = atr * 1.2
        
        # Take profits pequenos (scalping)
        tp1_distance = sl_distance * 1.5  # RR 1:1.5
        tp2_distance = sl_distance * 2.0  # RR 1:2
        
        if signal == SignalType.CALL:
            stop_loss = entry - sl_distance
            tp1 = entry + tp1_distance
            tp2 = entry + tp2_distance
        elif signal == SignalType.PUT:
            stop_loss = entry + sl_distance
            tp1 = entry - tp1_distance
            tp2 = entry - tp2_distance
        else:
            stop_loss = entry - sl_distance
            tp1 = entry + tp1_distance
            tp2 = entry + tp2_distance
        
        return stop_loss, tp1, tp2
    
    def _wait_signal(self, reason: str) -> ScalpSignal:
        """Retorna sinal de WAIT"""
        return ScalpSignal(
            signal=SignalType.WAIT,
            score=0,
            confidence=0.0,
            entry_price=0.0,
            stop_loss=0.0,
            take_profit_1=0.0,
            take_profit_2=0.0,
            ema_9=0.0,
            ema_21=0.0,
            rsi_value=50.0,
            momentum=0.0,
            volatility="UNKNOWN",
            reasons=[],
            warnings=[f"⚠️ {reason}"]
        )
