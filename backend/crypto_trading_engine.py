"""
🎯 CRYPTO TRADING ENGINE V2 - Otimizado para Criptomoedas
Focado em 70%+ win rate com dados REAIS
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    CALL = "CALL"
    PUT = "PUT"
    WAIT = "WAIT"


class MarketContext(Enum):
    STRONG_UPTREND = "STRONG_UPTREND"
    UPTREND = "UPTREND"
    RANGING = "RANGING"
    DOWNTREND = "DOWNTREND"
    STRONG_DOWNTREND = "STRONG_DOWNTREND"


@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class CryptoTradingSignal:
    signal: SignalType
    score: int
    confidence: float
    
    # Níveis
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float  # TP adicional para crypto
    
    # Contexto
    market_context: MarketContext
    volatility_level: str  # LOW, MEDIUM, HIGH
    
    # Indicadores
    ema_20: float
    ema_50: float
    ema_200: float  # EMA longa para contexto
    rsi_value: float
    atr_value: float
    volume_ratio: float
    
    # Risk
    risk_reward_1: float
    risk_reward_2: float
    risk_amount: float
    
    reasons: List[str]
    warnings: List[str]


class CryptoIndicators:
    """Indicadores otimizados para criptomoedas"""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """EMA padrão"""
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
        """RSI padrão"""
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
        """ATR padrão"""
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
    def detect_market_context(closes: List[float], ema_20: float, 
                             ema_50: float, ema_200: float, 
                             current_price: float) -> MarketContext:
        """
        Detecta o contexto do mercado (CRÍTICO para crypto)
        """
        # Calcular slope das EMAs
        if len(closes) >= 20:
            ema20_slope = (ema_20 - CryptoIndicators.calculate_ema(closes[:-10], 20)) / ema_20
            ema50_slope = (ema_50 - CryptoIndicators.calculate_ema(closes[:-10], 50)) / ema_50
        else:
            ema20_slope = 0
            ema50_slope = 0
        
        # Posição do preço em relação às EMAs
        above_200 = current_price > ema_200
        above_50 = current_price > ema_50
        above_20 = current_price > ema_20
        
        ema_aligned_up = ema_20 > ema_50 > ema_200
        ema_aligned_down = ema_20 < ema_50 < ema_200
        
        # Detectar ranging
        ema_spread_20_50 = abs(ema_20 - ema_50) / ema_50
        ema_spread_50_200 = abs(ema_50 - ema_200) / ema_200
        
        is_ranging = ema_spread_20_50 < 0.01 and ema_spread_50_200 < 0.02
        
        if is_ranging:
            return MarketContext.RANGING
        
        # Strong trends
        if ema_aligned_up and above_200 and ema20_slope > 0.005:
            return MarketContext.STRONG_UPTREND
        elif ema_aligned_down and not above_200 and ema20_slope < -0.005:
            return MarketContext.STRONG_DOWNTREND
        
        # Regular trends
        if ema_20 > ema_50 and above_50:
            return MarketContext.UPTREND
        elif ema_20 < ema_50 and not above_50:
            return MarketContext.DOWNTREND
        
        return MarketContext.RANGING
    
    @staticmethod
    def calculate_volume_ratio(candles: List[Candle], period: int = 20) -> float:
        """Ratio do volume atual vs média"""
        if len(candles) < period:
            return 1.0
        
        avg_volume = np.mean([c.volume for c in candles[-period:-1]])
        current_volume = candles[-1].volume
        
        if avg_volume == 0:
            return 1.0
        
        return current_volume / avg_volume
    
    @staticmethod
    def detect_volatility_level(atr: float, current_price: float) -> str:
        """Detecta nível de volatilidade"""
        atr_pct = (atr / current_price) * 100
        
        if atr_pct > 3.0:
            return "HIGH"
        elif atr_pct > 1.5:
            return "MEDIUM"
        else:
            return "LOW"


class CryptoTradingEngine:
    """
    Motor de Trading OTIMIZADO para Criptomoedas
    - Múltiplas estratégias baseadas em contexto
    - Adaptação à volatilidade
    - Timeframes maiores (1H+)
    """
    
    def __init__(self):
        self.indicators = CryptoIndicators()
    
    def analyze(self, candles: List[Candle], capital: float = 10000.0) -> CryptoTradingSignal:
        """
        Análise principal adaptada para CRYPTO
        """
        if len(candles) < 200:
            logger.warning(f"Recomendado mínimo 200 candles, recebido {len(candles)}")
        
        # Extrair dados
        closes = [c.close for c in candles]
        current_price = candles[-1].close
        
        # Calcular indicadores
        ema_20 = self.indicators.calculate_ema(closes, 20)
        ema_50 = self.indicators.calculate_ema(closes, 50)
        ema_200 = self.indicators.calculate_ema(closes, 200) if len(closes) >= 200 else ema_50
        rsi = self.indicators.calculate_rsi(closes, 14)
        atr = self.indicators.calculate_atr(candles, 14)
        volume_ratio = self.indicators.calculate_volume_ratio(candles, 20)
        
        # CRÍTICO: Detectar contexto de mercado
        market_context = self.indicators.detect_market_context(
            closes, ema_20, ema_50, ema_200, current_price
        )
        
        # Detectar volatilidade
        volatility = self.indicators.detect_volatility_level(atr, current_price)
        
        # Inicializar
        score = 0
        reasons = []
        warnings = []
        signal_type = SignalType.WAIT
        
        # === ESTRATÉGIA BASEADA EM CONTEXTO ===
        
        if market_context == MarketContext.RANGING:
            # NÃO OPERAR em ranging (maior causa de perdas)
            warnings.append("⚠️ Mercado LATERAL - aguardar tendência clara")
            score = 0
        
        elif market_context in [MarketContext.STRONG_UPTREND, MarketContext.UPTREND]:
            # Estratégia de CALL apenas em uptrends
            signal_type, score, trade_reasons = self._analyze_uptrend_setup(
                current_price, ema_20, ema_50, ema_200, rsi, volume_ratio, 
                market_context, volatility
            )
            reasons.extend(trade_reasons)
        
        elif market_context in [MarketContext.STRONG_DOWNTREND, MarketContext.DOWNTREND]:
            # Estratégia de PUT apenas em downtrends
            signal_type, score, trade_reasons = self._analyze_downtrend_setup(
                current_price, ema_20, ema_50, ema_200, rsi, volume_ratio,
                market_context, volatility
            )
            reasons.extend(trade_reasons)
        
        # Filtro de volatilidade extrema
        if volatility == "HIGH":
            warnings.append("⚠️ Volatilidade ALTA - risco aumentado")
            if score < 75:  # Reduzido de 85 para 75
                signal_type = SignalType.WAIT
                warnings.append("⚠️ Score insuficiente para volatilidade alta")
        
        # Calcular níveis de stop e take profit
        stop_loss, tp1, tp2, tp3 = self._calculate_crypto_levels(
            current_price, atr, signal_type, volatility
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
            risk = atr * 2
            reward_1 = risk * 2
            reward_2 = risk * 3
        
        rr_1 = reward_1 / risk if risk > 0 else 0
        rr_2 = reward_2 / risk if risk > 0 else 0
        
        # Validar RR mínimo
        if signal_type != SignalType.WAIT and rr_1 < 2.0:
            warnings.append(f"⚠️ Risk/Reward insuficiente ({rr_1:.2f})")
            signal_type = SignalType.WAIT
        
        # Risco de capital
        risk_amount = capital * 0.01
        confidence = min(score / 100.0, 1.0)
        
        return CryptoTradingSignal(
            signal=signal_type,
            score=score,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            market_context=market_context,
            volatility_level=volatility,
            ema_20=ema_20,
            ema_50=ema_50,
            ema_200=ema_200,
            rsi_value=rsi,
            atr_value=atr,
            volume_ratio=volume_ratio,
            risk_reward_1=rr_1,
            risk_reward_2=rr_2,
            risk_amount=risk_amount,
            reasons=reasons,
            warnings=warnings
        )
    
    def _analyze_uptrend_setup(self, price: float, ema20: float, ema50: float,
                              ema200: float, rsi: float, vol_ratio: float,
                              context: MarketContext, volatility: str) -> Tuple[SignalType, int, List[str]]:
        """Analisa setup de CALL em uptrend"""
        score = 0
        reasons = []
        
        # 1. Preço deve estar ACIMA das EMAs (30 pts)
        above_20 = price > ema20
        above_50 = price > ema50
        above_200 = price > ema200
        
        if above_20 and above_50 and above_200:
            score += 30
            reasons.append("✅ Preço acima de todas EMAs (forte tendência de alta)")
        elif above_20 and above_50:
            score += 20
            reasons.append("✅ Preço acima EMA20 e EMA50")
        elif above_20:
            score += 10
            reasons.append("⚠️ Preço apenas acima EMA20")
        
        # 2. Recuo válido para EMA20 (25 pts)
        distance_to_ema20 = ((price - ema20) / ema20) * 100
        
        if 0.1 <= distance_to_ema20 <= 1.0:
            score += 25
            reasons.append(f"✅ Recuo ideal ({distance_to_ema20:.2f}% acima EMA20)")
        elif 0 <= distance_to_ema20 <= 0.1:
            score += 20
            reasons.append("✅ Preço na EMA20 (ponto de recuo)")
        elif 1.0 < distance_to_ema20 <= 2.0:
            score += 15
            reasons.append("⚠️ Preço um pouco distante da EMA20")
        
        # 3. RSI em zona ideal (20 pts)
        if 40 <= rsi <= 65:
            score += 20
            reasons.append(f"✅ RSI ideal para CALL ({rsi:.1f})")
        elif 30 <= rsi < 40:
            score += 15
            reasons.append(f"✅ RSI em zona de sobrevenda leve ({rsi:.1f})")
        elif 65 < rsi <= 75:
            score += 10
            reasons.append(f"⚠️ RSI elevado ({rsi:.1f})")
        
        # 4. Volume confirmando (15 pts)
        if vol_ratio >= 1.5:
            score += 15
            reasons.append(f"✅ Volume forte ({vol_ratio:.2f}x média)")
        elif vol_ratio >= 1.2:
            score += 10
            reasons.append(f"✅ Volume acima da média ({vol_ratio:.2f}x)")
        
        # 5. Contexto de mercado (10 pts)
        if context == MarketContext.STRONG_UPTREND:
            score += 10
            reasons.append("✅ Forte tendência de ALTA")
        elif context == MarketContext.UPTREND:
            score += 5
            reasons.append("✅ Tendência de alta")
        
        # Decidir sinal
        if score >= 60:  # Reduzido de 70 para 60 (permitir mais trades)
            return SignalType.CALL, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _analyze_downtrend_setup(self, price: float, ema20: float, ema50: float,
                                ema200: float, rsi: float, vol_ratio: float,
                                context: MarketContext, volatility: str) -> Tuple[SignalType, int, List[str]]:
        """Analisa setup de PUT em downtrend"""
        score = 0
        reasons = []
        
        # 1. Preço deve estar ABAIXO das EMAs (30 pts)
        below_20 = price < ema20
        below_50 = price < ema50
        below_200 = price < ema200
        
        if below_20 and below_50 and below_200:
            score += 30
            reasons.append("✅ Preço abaixo de todas EMAs (forte tendência de baixa)")
        elif below_20 and below_50:
            score += 20
            reasons.append("✅ Preço abaixo EMA20 e EMA50")
        elif below_20:
            score += 10
            reasons.append("⚠️ Preço apenas abaixo EMA20")
        
        # 2. Recuo válido para EMA20 (25 pts)
        distance_to_ema20 = ((ema20 - price) / ema20) * 100
        
        if 0.1 <= distance_to_ema20 <= 1.0:
            score += 25
            reasons.append(f"✅ Recuo ideal ({distance_to_ema20:.2f}% abaixo EMA20)")
        elif 0 <= distance_to_ema20 <= 0.1:
            score += 20
            reasons.append("✅ Preço na EMA20 (ponto de recuo)")
        elif 1.0 < distance_to_ema20 <= 2.0:
            score += 15
            reasons.append("⚠️ Preço um pouco distante da EMA20")
        
        # 3. RSI em zona ideal (20 pts)
        if 35 <= rsi <= 60:
            score += 20
            reasons.append(f"✅ RSI ideal para PUT ({rsi:.1f})")
        elif 60 < rsi <= 70:
            score += 15
            reasons.append(f"✅ RSI em zona de sobrecompra leve ({rsi:.1f})")
        elif 25 <= rsi < 35:
            score += 10
            reasons.append(f"⚠️ RSI baixo ({rsi:.1f})")
        
        # 4. Volume confirmando (15 pts)
        if vol_ratio >= 1.5:
            score += 15
            reasons.append(f"✅ Volume forte ({vol_ratio:.2f}x média)")
        elif vol_ratio >= 1.2:
            score += 10
            reasons.append(f"✅ Volume acima da média ({vol_ratio:.2f}x)")
        
        # 5. Contexto de mercado (10 pts)
        if context == MarketContext.STRONG_DOWNTREND:
            score += 10
            reasons.append("✅ Forte tendência de BAIXA")
        elif context == MarketContext.DOWNTREND:
            score += 5
            reasons.append("✅ Tendência de baixa")
        
        # Decidir sinal
        if score >= 60:  # Reduzido de 70 para 60
            return SignalType.PUT, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _calculate_crypto_levels(self, entry: float, atr: float, 
                                 signal: SignalType, volatility: str) -> Tuple[float, float, float, float]:
        """
        Calcula níveis adaptados para volatilidade de crypto
        """
        # Stop Loss baseado em volatilidade
        if volatility == "HIGH":
            sl_multiplier = 3.0  # Stop mais largo em alta volatilidade
        elif volatility == "MEDIUM":
            sl_multiplier = 2.5
        else:
            sl_multiplier = 2.0
        
        sl_distance = atr * sl_multiplier
        
        # Take Profits escalonados (crypto move mais)
        tp1_distance = sl_distance * 2.0  # RR 1:2
        tp2_distance = sl_distance * 3.5  # RR 1:3.5
        tp3_distance = sl_distance * 5.0  # RR 1:5 (home run)
        
        if signal == SignalType.CALL:
            stop_loss = entry - sl_distance
            tp1 = entry + tp1_distance
            tp2 = entry + tp2_distance
            tp3 = entry + tp3_distance
        elif signal == SignalType.PUT:
            stop_loss = entry + sl_distance
            tp1 = entry - tp1_distance
            tp2 = entry - tp2_distance
            tp3 = entry - tp3_distance
        else:
            stop_loss = entry - sl_distance
            tp1 = entry + tp1_distance
            tp2 = entry + tp2_distance
            tp3 = entry + tp3_distance
        
        return stop_loss, tp1, tp2, tp3
