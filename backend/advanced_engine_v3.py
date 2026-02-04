"""
🎯 ADVANCED TRADING ENGINE V3 - Sistema Adaptativo com Filtros
Estratégia robusta com perdas calculadas e filtros de mercado
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import statistics

class SignalType(Enum):
    CALL = "CALL"
    PUT = "PUT"
    WAIT = "WAIT"

class MarketCondition(Enum):
    CRASH = "CRASH"  # Queda >5% em 24h
    PANIC = "PANIC"  # Queda >3% em 6h
    NORMAL = "NORMAL"
    RECOVERY = "RECOVERY"  # Subida após queda

@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class AdvancedSignal:
    signal: SignalType
    score: int
    confidence: float
    
    # Níveis
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    
    # Contexto
    market_condition: MarketCondition
    volatility: float
    trend_strength: float
    
    # Indicadores
    ema_fast: float
    ema_mid: float
    ema_slow: float
    rsi: float
    
    reasons: List[str]
    warnings: List[str]


class MarketAnalyzer:
    """Analisa condições de mercado para evitar crashes"""
    
    @staticmethod
    def detect_market_condition(candles: List[Candle]) -> MarketCondition:
        """Detecta se mercado está em crash/panic"""
        if len(candles) < 50:
            return MarketCondition.NORMAL
        
        closes = [c.close for c in candles]
        
        # Mudança nas últimas 24h (24 candles em 1H)
        if len(candles) >= 24:
            change_24h = ((closes[-1] - closes[-24]) / closes[-24]) * 100
            
            if change_24h < -5:
                return MarketCondition.CRASH
        
        # Mudança nas últimas 6h (6 candles em 1H)
        if len(candles) >= 6:
            change_6h = ((closes[-1] - closes[-6]) / closes[-6]) * 100
            
            if change_6h < -3:
                return MarketCondition.PANIC
            
            # Recovery: subindo após queda
            if change_24h < -2 and change_6h > 1:
                return MarketCondition.RECOVERY
        
        return MarketCondition.NORMAL
    
    @staticmethod
    def calculate_volatility(candles: List[Candle], period: int = 20) -> float:
        """Calcula volatilidade normalizada"""
        if len(candles) < period:
            return 0.0
        
        closes = [c.close for c in candles[-period:]]
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        volatility = np.std(returns) * 100  # Em %
        return volatility
    
    @staticmethod
    def calculate_trend_strength(closes: List[float], ema_fast: float, 
                                 ema_mid: float, ema_slow: float) -> float:
        """Calcula força da tendência (0-100)"""
        if len(closes) < 10:
            return 0
        
        # 1. Alinhamento de EMAs
        if ema_fast > ema_mid > ema_slow:
            alignment_score = 40
        elif ema_fast < ema_mid < ema_slow:
            alignment_score = 40
        else:
            alignment_score = 10
        
        # 2. Distância entre EMAs
        spread = abs((ema_fast - ema_slow) / ema_slow) * 100
        spread_score = min(spread * 10, 30)
        
        # 3. Consistência de movimento
        last_10 = closes[-10:]
        up_moves = sum(1 for i in range(1, 10) if last_10[i] > last_10[i-1])
        consistency = (abs(up_moves - 5) / 5) * 30
        
        total = alignment_score + spread_score + consistency
        return min(total, 100)


class AdvancedIndicators:
    """Indicadores técnicos avançados"""
    
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
    def calculate_atr(candles: List[Candle], period: int = 14) -> float:
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
    def calculate_volume_profile(candles: List[Candle], period: int = 20) -> float:
        """Analisa perfil de volume"""
        if len(candles) < period:
            return 1.0
        
        volumes = [c.volume for c in candles[-period:]]
        avg_volume = np.mean(volumes[:-1])
        current_volume = candles[-1].volume
        
        if avg_volume == 0:
            return 1.0
        
        return current_volume / avg_volume


class AdaptiveRiskManager:
    """Gerenciador de risco adaptativo"""
    
    @staticmethod
    def calculate_position_size(capital: float, market_condition: MarketCondition,
                               volatility: float) -> float:
        """Ajusta tamanho da posição baseado em condições"""
        
        base_risk = 0.01  # 1% base
        
        # Reduzir risco em condições adversas
        if market_condition == MarketCondition.CRASH:
            risk = base_risk * 0.3  # 30% do normal
        elif market_condition == MarketCondition.PANIC:
            risk = base_risk * 0.5  # 50% do normal
        elif market_condition == MarketCondition.RECOVERY:
            risk = base_risk * 0.7  # 70% do normal
        else:
            risk = base_risk
        
        # Ajustar por volatilidade
        if volatility > 3.0:  # Alta volatilidade
            risk *= 0.7
        elif volatility > 2.0:
            risk *= 0.85
        
        return capital * risk
    
    @staticmethod
    def calculate_stop_multiplier(market_condition: MarketCondition,
                                  volatility: float) -> float:
        """Calcula multiplicador de stop loss"""
        
        base_multiplier = 2.0
        
        # Aumentar stops em condições adversas
        if market_condition == MarketCondition.CRASH:
            multiplier = base_multiplier * 2.0  # Stops mais largos
        elif market_condition == MarketCondition.PANIC:
            multiplier = base_multiplier * 1.5
        else:
            multiplier = base_multiplier
        
        # Ajustar por volatilidade
        if volatility > 3.0:
            multiplier *= 1.3
        elif volatility > 2.0:
            multiplier *= 1.15
        
        return multiplier


class AdvancedTradingEngine:
    """Motor de trading adaptativo com filtros inteligentes"""
    
    def __init__(self):
        self.indicators = AdvancedIndicators()
        self.market_analyzer = MarketAnalyzer()
        self.risk_manager = AdaptiveRiskManager()
    
    def analyze(self, candles: List[Candle], capital: float = 10000.0) -> AdvancedSignal:
        """Análise completa com filtros adaptativos"""
        
        if len(candles) < 100:
            return self._wait_signal("Dados insuficientes")
        
        closes = [c.close for c in candles]
        current_price = candles[-1].close
        
        # FILTRO 1: Detectar condição de mercado
        market_condition = self.market_analyzer.detect_market_condition(candles)
        
        # FILTRO 2: NÃO OPERAR EM CRASH OU PANIC
        if market_condition in [MarketCondition.CRASH, MarketCondition.PANIC]:
            return self._wait_signal(f"Mercado em {market_condition.value} - aguardando estabilização")
        
        # Calcular indicadores
        ema_fast = self.indicators.calculate_ema(closes, 12)
        ema_mid = self.indicators.calculate_ema(closes, 26)
        ema_slow = self.indicators.calculate_ema(closes, 50)
        rsi = self.indicators.calculate_rsi(closes, 14)
        atr = self.indicators.calculate_atr(candles, 14)
        
        # Métricas de mercado
        volatility = self.market_analyzer.calculate_volatility(candles)
        trend_strength = self.market_analyzer.calculate_trend_strength(
            closes, ema_fast, ema_mid, ema_slow
        )
        volume_ratio = self.indicators.calculate_volume_profile(candles)
        
        # FILTRO 3: Volatilidade extrema
        if volatility > 4.0:
            return self._wait_signal(f"Volatilidade extrema ({volatility:.2f}%) - aguardando")
        
        # FILTRO 4: Tendência fraca
        if trend_strength < 40:
            return self._wait_signal(f"Tendência fraca ({trend_strength:.1f}) - aguardando")
        
        # FILTRO 5: Volume baixo
        if volume_ratio < 0.7:
            return self._wait_signal(f"Volume baixo ({volume_ratio:.2f}x) - aguardando")
        
        # Inicializar
        score = 0
        reasons = []
        warnings = []
        signal_type = SignalType.WAIT
        
        # === ANÁLISE DE SETUP ===
        
        # Detectar direção da tendência
        if ema_fast > ema_mid > ema_slow:
            signal_type, score, reasons = self._analyze_bullish_setup(
                current_price, ema_fast, ema_mid, ema_slow, rsi, 
                trend_strength, volume_ratio, market_condition
            )
        elif ema_fast < ema_mid < ema_slow:
            signal_type, score, reasons = self._analyze_bearish_setup(
                current_price, ema_fast, ema_mid, ema_slow, rsi,
                trend_strength, volume_ratio, market_condition
            )
        
        # FILTRO 6: Score mínimo adaptativo
        min_score = 70 if market_condition == MarketCondition.NORMAL else 80
        
        if score < min_score:
            return self._wait_signal(f"Score insuficiente ({score}/{min_score})")
        
        # Calcular níveis com risk management adaptativo
        stop_multiplier = self.risk_manager.calculate_stop_multiplier(
            market_condition, volatility
        )
        
        stop_loss, tp1, tp2 = self._calculate_adaptive_levels(
            current_price, atr, signal_type, stop_multiplier
        )
        
        # Validar Risk/Reward
        if signal_type == SignalType.CALL:
            risk = current_price - stop_loss
            reward = tp1 - current_price
        elif signal_type == SignalType.PUT:
            risk = stop_loss - current_price
            reward = current_price - tp1
        else:
            risk = atr * 2
            reward = risk * 2
        
        rr = reward / risk if risk > 0 else 0
        
        # FILTRO 7: RR mínimo
        min_rr = 1.8 if market_condition == MarketCondition.NORMAL else 2.2
        
        if signal_type != SignalType.WAIT and rr < min_rr:
            return self._wait_signal(f"Risk/Reward insuficiente ({rr:.2f} < {min_rr})")
        
        confidence = min(score / 100.0, 1.0)
        
        return AdvancedSignal(
            signal=signal_type,
            score=score,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            market_condition=market_condition,
            volatility=volatility,
            trend_strength=trend_strength,
            ema_fast=ema_fast,
            ema_mid=ema_mid,
            ema_slow=ema_slow,
            rsi=rsi,
            reasons=reasons,
            warnings=warnings
        )
    
    def _analyze_bullish_setup(self, price, ema_fast, ema_mid, ema_slow, rsi,
                               trend_strength, volume_ratio, market_condition) -> Tuple[SignalType, int, List[str]]:
        """Análise de setup CALL"""
        score = 0
        reasons = []
        
        # 1. Preço vs EMAs (30 pts)
        if price > ema_fast:
            distance = ((price - ema_fast) / ema_fast) * 100
            
            if 0.1 <= distance <= 0.8:
                score += 30
                reasons.append(f"✅ Preço ideal acima EMA rápida ({distance:.2f}%)")
            elif 0 <= distance < 0.1:
                score += 25
                reasons.append("✅ Preço tocando EMA (pullback)")
            elif 0.8 < distance <= 1.5:
                score += 20
                reasons.append("⚠️ Preço distante mas aceitável")
        
        # 2. Força da tendência (25 pts)
        if trend_strength >= 70:
            score += 25
            reasons.append(f"✅ Tendência FORTE ({trend_strength:.1f})")
        elif trend_strength >= 50:
            score += 20
            reasons.append(f"✅ Tendência boa ({trend_strength:.1f})")
        elif trend_strength >= 40:
            score += 15
            reasons.append(f"⚠️ Tendência moderada ({trend_strength:.1f})")
        
        # 3. RSI (20 pts)
        if 45 <= rsi <= 65:
            score += 20
            reasons.append(f"✅ RSI ideal ({rsi:.1f})")
        elif 40 <= rsi < 45 or 65 < rsi <= 70:
            score += 15
            reasons.append(f"✅ RSI aceitável ({rsi:.1f})")
        
        # 4. Volume (15 pts)
        if volume_ratio >= 1.3:
            score += 15
            reasons.append(f"✅ Volume forte ({volume_ratio:.2f}x)")
        elif volume_ratio >= 1.0:
            score += 10
            reasons.append(f"✅ Volume normal ({volume_ratio:.2f}x)")
        
        # 5. Condição de mercado (10 pts)
        if market_condition == MarketCondition.RECOVERY:
            score += 10
            reasons.append("✅ Mercado em recuperação")
        elif market_condition == MarketCondition.NORMAL:
            score += 5
            reasons.append("✅ Mercado normal")
        
        if score >= 70:
            return SignalType.CALL, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _analyze_bearish_setup(self, price, ema_fast, ema_mid, ema_slow, rsi,
                               trend_strength, volume_ratio, market_condition) -> Tuple[SignalType, int, List[str]]:
        """Análise de setup PUT"""
        score = 0
        reasons = []
        
        # Similar lógica mas invertida
        if price < ema_fast:
            distance = ((ema_fast - price) / ema_fast) * 100
            
            if 0.1 <= distance <= 0.8:
                score += 30
                reasons.append(f"✅ Preço ideal abaixo EMA rápida ({distance:.2f}%)")
            elif 0 <= distance < 0.1:
                score += 25
                reasons.append("✅ Preço tocando EMA (pullback)")
            elif 0.8 < distance <= 1.5:
                score += 20
                reasons.append("⚠️ Preço distante mas aceitável")
        
        if trend_strength >= 70:
            score += 25
            reasons.append(f"✅ Tendência FORTE ({trend_strength:.1f})")
        elif trend_strength >= 50:
            score += 20
            reasons.append(f"✅ Tendência boa ({trend_strength:.1f})")
        elif trend_strength >= 40:
            score += 15
            reasons.append(f"⚠️ Tendência moderada ({trend_strength:.1f})")
        
        if 35 <= rsi <= 55:
            score += 20
            reasons.append(f"✅ RSI ideal ({rsi:.1f})")
        elif 30 <= rsi < 35 or 55 < rsi <= 60:
            score += 15
            reasons.append(f"✅ RSI aceitável ({rsi:.1f})")
        
        if volume_ratio >= 1.3:
            score += 15
            reasons.append(f"✅ Volume forte ({volume_ratio:.2f}x)")
        elif volume_ratio >= 1.0:
            score += 10
            reasons.append(f"✅ Volume normal ({volume_ratio:.2f}x)")
        
        if market_condition == MarketCondition.RECOVERY:
            score += 5  # Menos pontos para PUT em recovery
            reasons.append("⚠️ Mercado em recuperação (PUT arriscado)")
        elif market_condition == MarketCondition.NORMAL:
            score += 10
            reasons.append("✅ Mercado normal")
        
        if score >= 70:
            return SignalType.PUT, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _calculate_adaptive_levels(self, entry: float, atr: float,
                                   signal: SignalType, stop_multiplier: float) -> Tuple[float, float, float]:
        """Calcula níveis com stops adaptativos"""
        
        sl_distance = atr * stop_multiplier
        tp1_distance = sl_distance * 2.0
        tp2_distance = sl_distance * 3.0
        
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
    
    def _wait_signal(self, reason: str) -> AdvancedSignal:
        """Retorna sinal de WAIT"""
        return AdvancedSignal(
            signal=SignalType.WAIT,
            score=0,
            confidence=0.0,
            entry_price=0.0,
            stop_loss=0.0,
            take_profit_1=0.0,
            take_profit_2=0.0,
            market_condition=MarketCondition.NORMAL,
            volatility=0.0,
            trend_strength=0.0,
            ema_fast=0.0,
            ema_mid=0.0,
            ema_slow=0.0,
            rsi=50.0,
            reasons=[],
            warnings=[f"⚠️ {reason}"]
        )
