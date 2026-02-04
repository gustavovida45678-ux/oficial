"""
🎯 FOREX ENGINE V2 - Otimizado para M30/H1
Implementa TODAS as correções:
- Timeframe M30/H1
- TP/SL em pips adequados
- Estrutura de mercado
- Sessões de trading
- Filtros de tendência e volatilidade
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class SignalType(Enum):
    CALL = "CALL"
    PUT = "PUT"
    WAIT = "WAIT"

class MarketStructure(Enum):
    BULLISH = "BULLISH"  # Higher Highs + Higher Lows
    BEARISH = "BEARISH"  # Lower Lows + Lower Highs
    RANGING = "RANGING"  # Sem estrutura clara

class TradingSession(Enum):
    LONDON = "LONDON"  # 08:00-17:00 GMT
    NEW_YORK = "NEW_YORK"  # 13:00-22:00 GMT
    OVERLAP = "OVERLAP"  # 13:00-17:00 GMT (melhor)
    ASIA = "ASIA"  # 00:00-09:00 GMT
    OFF_HOURS = "OFF_HOURS"

@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class ForexSignal:
    signal: SignalType
    score: int
    confidence: float
    
    # Níveis em PIPS
    entry_price: float
    stop_loss: float
    stop_loss_pips: float
    take_profit_1: float
    take_profit_1_pips: float
    take_profit_2: float
    take_profit_2_pips: float
    
    # Contexto
    market_structure: MarketStructure
    session: TradingSession
    trend_confirmed: bool
    
    # Indicadores
    ema_50: float
    ema_200: float
    atr_value: float
    
    # Risk/Reward
    risk_reward: float
    
    reasons: List[str]
    warnings: List[str]


class ForexIndicators:
    """Indicadores específicos para FOREX"""
    
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
    def detect_market_structure(candles: List[Candle]) -> MarketStructure:
        """
        Detecta estrutura de mercado:
        - BULLISH: Higher Highs + Higher Lows
        - BEARISH: Lower Lows + Lower Highs
        - RANGING: Sem padrão claro
        """
        if len(candles) < 20:
            return MarketStructure.RANGING
        
        # Identificar swing highs e lows dos últimos 20 candles
        highs = [c.high for c in candles[-20:]]
        lows = [c.low for c in candles[-20:]]
        
        # Simplificado: comparar primeiros 10 com últimos 10
        first_half_high = max(highs[:10])
        second_half_high = max(highs[10:])
        
        first_half_low = min(lows[:10])
        second_half_low = min(lows[10:])
        
        # Higher Highs + Higher Lows = BULLISH
        if second_half_high > first_half_high and second_half_low > first_half_low:
            return MarketStructure.BULLISH
        
        # Lower Highs + Lower Lows = BEARISH
        if second_half_high < first_half_high and second_half_low < first_half_low:
            return MarketStructure.BEARISH
        
        return MarketStructure.RANGING
    
    @staticmethod
    def get_trading_session(timestamp: int) -> TradingSession:
        """Identifica sessão de trading (GMT)"""
        dt = datetime.utcfromtimestamp(timestamp)
        hour = dt.hour
        
        # Overlap Londres/NY (melhor liquidez)
        if 13 <= hour < 17:
            return TradingSession.OVERLAP
        
        # Londres
        if 8 <= hour < 17:
            return TradingSession.LONDON
        
        # New York
        if 13 <= hour < 22:
            return TradingSession.NEW_YORK
        
        # Asia
        if 0 <= hour < 9:
            return TradingSession.ASIA
        
        return TradingSession.OFF_HOURS
    
    @staticmethod
    def pips_from_price(price_diff: float, pair: str = "EUR/USD") -> float:
        """Converte diferença de preço em pips"""
        # Para pares com USD: 1 pip = 0.0001
        # Para pares com JPY: 1 pip = 0.01
        if "JPY" in pair:
            return price_diff * 100
        else:
            return price_diff * 10000


class ForexEngine:
    """
    Motor FOREX otimizado para M30/H1
    Expectativa matemática positiva com RR 1:2.5
    """
    
    def __init__(self, pair: str = "EUR/USD"):
        self.pair = pair
        self.indicators = ForexIndicators()
    
    def analyze(self, candles: List[Candle]) -> ForexSignal:
        """Análise otimizada para FOREX"""
        
        if len(candles) < 200:
            return self._wait_signal("Dados insuficientes")
        
        closes = [c.close for c in candles]
        current_price = candles[-1].close
        
        # Calcular indicadores
        ema_50 = self.indicators.calculate_ema(closes, 50)
        ema_200 = self.indicators.calculate_ema(closes, 200)
        atr = self.indicators.calculate_atr(candles, 14)
        
        # Detectar contexto
        market_structure = self.indicators.detect_market_structure(candles)
        session = self.indicators.get_trading_session(candles[-1].timestamp)
        
        # FILTRO 1: Não operar em ranging
        if market_structure == MarketStructure.RANGING:
            return self._wait_signal("Mercado em RANGING - aguardar estrutura")
        
        # FILTRO 2: Não operar fora das sessões principais
        if session == TradingSession.OFF_HOURS:
            return self._wait_signal("Fora do horário de sessão principal")
        
        # FILTRO 3: ATR mínimo (volatilidade)
        atr_pips = self.indicators.pips_from_price(atr, self.pair)
        if atr_pips < 10:  # Mínimo 10 pips de ATR
            return self._wait_signal(f"ATR muito baixo ({atr_pips:.1f} pips)")
        
        # FILTRO 4: Tendência confirmada por EMAs
        trend_confirmed = False
        if current_price > ema_50 > ema_200:
            trend_confirmed = True
            trend_direction = "BULLISH"
        elif current_price < ema_50 < ema_200:
            trend_confirmed = True
            trend_direction = "BEARISH"
        else:
            return self._wait_signal("Tendência não confirmada pelas EMAs")
        
        # FILTRO 5: Estrutura alinhada com tendência
        if trend_direction == "BULLISH" and market_structure != MarketStructure.BULLISH:
            return self._wait_signal("Estrutura não alinha com tendência")
        
        if trend_direction == "BEARISH" and market_structure != MarketStructure.BEARISH:
            return self._wait_signal("Estrutura não alinha com tendência")
        
        # Inicializar
        score = 0
        reasons = []
        warnings = []
        signal_type = SignalType.WAIT
        
        # === ANÁLISE DE ENTRADA ===
        
        if trend_direction == "BULLISH":
            signal_type, score, reasons = self._analyze_bullish_entry(
                current_price, ema_50, ema_200, market_structure, session, atr_pips
            )
        else:
            signal_type, score, reasons = self._analyze_bearish_entry(
                current_price, ema_50, ema_200, market_structure, session, atr_pips
            )
        
        # FILTRO 6: Score mínimo
        if score < 70:
            return self._wait_signal(f"Score insuficiente ({score}/100)")
        
        # === CALCULAR NÍVEIS EM PIPS ===
        
        # Stop Loss: 10-15 pips baseado em ATR
        sl_pips = max(10, min(15, atr_pips * 1.5))
        
        # Take Profit 1: RR 1:2.5
        tp1_pips = sl_pips * 2.5
        
        # Take Profit 2: RR 1:4
        tp2_pips = sl_pips * 4.0
        
        # Converter pips para preço
        if "JPY" in self.pair:
            pip_value = 0.01
        else:
            pip_value = 0.0001
        
        if signal_type == SignalType.CALL:
            stop_loss = current_price - (sl_pips * pip_value)
            tp1 = current_price + (tp1_pips * pip_value)
            tp2 = current_price + (tp2_pips * pip_value)
        elif signal_type == SignalType.PUT:
            stop_loss = current_price + (sl_pips * pip_value)
            tp1 = current_price - (tp1_pips * pip_value)
            tp2 = current_price - (tp2_pips * pip_value)
        else:
            stop_loss = current_price
            tp1 = current_price
            tp2 = current_price
        
        # Risk/Reward
        risk_reward = tp1_pips / sl_pips
        
        confidence = min(score / 100.0, 1.0)
        
        return ForexSignal(
            signal=signal_type,
            score=score,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            stop_loss_pips=sl_pips,
            take_profit_1=tp1,
            take_profit_1_pips=tp1_pips,
            take_profit_2=tp2,
            take_profit_2_pips=tp2_pips,
            market_structure=market_structure,
            session=session,
            trend_confirmed=trend_confirmed,
            ema_50=ema_50,
            ema_200=ema_200,
            atr_value=atr,
            risk_reward=risk_reward,
            reasons=reasons,
            warnings=warnings
        )
    
    def _analyze_bullish_entry(self, price, ema_50, ema_200, structure, session, atr_pips):
        """Análise de entrada CALL"""
        score = 0
        reasons = []
        
        # 1. Preço em pullback para EMA50 (30 pts)
        distance_to_ema50 = ((price - ema_50) / ema_50) * 100
        
        if -0.1 <= distance_to_ema50 <= 0.3:  # Próximo ou ligeiramente acima
            score += 30
            reasons.append(f"✅ Pullback ideal para EMA50 ({distance_to_ema50:.2f}%)")
        elif 0.3 < distance_to_ema50 <= 0.5:
            score += 20
            reasons.append("✅ Preço próximo da EMA50")
        
        # 2. Estrutura de mercado bullish (25 pts)
        if structure == MarketStructure.BULLISH:
            score += 25
            reasons.append("✅ Estrutura de alta confirmada (HH + HL)")
        
        # 3. Sessão de trading (20 pts)
        if session == TradingSession.OVERLAP:
            score += 20
            reasons.append("✅ Sessão OVERLAP (melhor liquidez)")
        elif session in [TradingSession.LONDON, TradingSession.NEW_YORK]:
            score += 15
            reasons.append(f"✅ Sessão {session.value}")
        
        # 4. ATR adequado (15 pts)
        if 15 <= atr_pips <= 40:
            score += 15
            reasons.append(f"✅ ATR ideal ({atr_pips:.1f} pips)")
        elif 10 <= atr_pips < 15:
            score += 10
            reasons.append(f"✅ ATR aceitável ({atr_pips:.1f} pips)")
        
        # 5. Distância da EMA200 (10 pts)
        distance_to_ema200 = ((price - ema_200) / ema_200) * 100
        if distance_to_ema200 > 0.5:
            score += 10
            reasons.append("✅ Bem acima da EMA200")
        elif distance_to_ema200 > 0:
            score += 5
            reasons.append("✅ Acima da EMA200")
        
        if score >= 70:
            return SignalType.CALL, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _analyze_bearish_entry(self, price, ema_50, ema_200, structure, session, atr_pips):
        """Análise de entrada PUT"""
        score = 0
        reasons = []
        
        # 1. Preço em pullback para EMA50 (30 pts)
        distance_to_ema50 = ((ema_50 - price) / ema_50) * 100
        
        if -0.1 <= distance_to_ema50 <= 0.3:
            score += 30
            reasons.append(f"✅ Pullback ideal para EMA50 ({distance_to_ema50:.2f}%)")
        elif 0.3 < distance_to_ema50 <= 0.5:
            score += 20
            reasons.append("✅ Preço próximo da EMA50")
        
        # 2. Estrutura de mercado bearish (25 pts)
        if structure == MarketStructure.BEARISH:
            score += 25
            reasons.append("✅ Estrutura de baixa confirmada (LL + LH)")
        
        # 3. Sessão de trading (20 pts)
        if session == TradingSession.OVERLAP:
            score += 20
            reasons.append("✅ Sessão OVERLAP (melhor liquidez)")
        elif session in [TradingSession.LONDON, TradingSession.NEW_YORK]:
            score += 15
            reasons.append(f"✅ Sessão {session.value}")
        
        # 4. ATR adequado (15 pts)
        if 15 <= atr_pips <= 40:
            score += 15
            reasons.append(f"✅ ATR ideal ({atr_pips:.1f} pips)")
        elif 10 <= atr_pips < 15:
            score += 10
            reasons.append(f"✅ ATR aceitável ({atr_pips:.1f} pips)")
        
        # 5. Distância da EMA200 (10 pts)
        distance_to_ema200 = ((ema_200 - price) / ema_200) * 100
        if distance_to_ema200 > 0.5:
            score += 10
            reasons.append("✅ Bem abaixo da EMA200")
        elif distance_to_ema200 > 0:
            score += 5
            reasons.append("✅ Abaixo da EMA200")
        
        if score >= 70:
            return SignalType.PUT, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _wait_signal(self, reason: str) -> ForexSignal:
        """Retorna sinal de WAIT"""
        return ForexSignal(
            signal=SignalType.WAIT,
            score=0,
            confidence=0.0,
            entry_price=0.0,
            stop_loss=0.0,
            stop_loss_pips=0.0,
            take_profit_1=0.0,
            take_profit_1_pips=0.0,
            take_profit_2=0.0,
            take_profit_2_pips=0.0,
            market_structure=MarketStructure.RANGING,
            session=TradingSession.OFF_HOURS,
            trend_confirmed=False,
            ema_50=0.0,
            ema_200=0.0,
            atr_value=0.0,
            risk_reward=0.0,
            reasons=[],
            warnings=[f"⚠️ {reason}"]
        )
