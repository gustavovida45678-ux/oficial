"""
🎯 FOREX ENGINE V3 - OTIMIZADO PARA 35-40% WIN RATE
Implementa TODAS as melhorias para aumentar win rate em 10%
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
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"

class TradingSession(Enum):
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    OVERLAP = "OVERLAP"
    ASIA = "ASIA"
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
    entry_price: float
    stop_loss: float
    stop_loss_pips: float
    take_profit_1: float
    take_profit_1_pips: float
    take_profit_2: float
    take_profit_2_pips: float
    market_structure: MarketStructure
    session: TradingSession
    trend_confirmed: bool
    ema_50: float
    ema_200: float
    atr_value: float
    risk_reward: float
    reasons: List[str]
    warnings: List[str]


class ForexIndicators:
    """Indicadores para FOREX"""
    
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
        """Detecta estrutura com mais precisão"""
        if len(candles) < 30:
            return MarketStructure.RANGING
        
        # Usar últimos 30 candles para estrutura mais clara
        highs = [c.high for c in candles[-30:]]
        lows = [c.low for c in candles[-30:]]
        
        # Dividir em 3 partes para melhor análise
        part1_high = max(highs[:10])
        part2_high = max(highs[10:20])
        part3_high = max(highs[20:])
        
        part1_low = min(lows[:10])
        part2_low = min(lows[10:20])
        part3_low = min(lows[20:])
        
        # Higher Highs + Higher Lows = BULLISH
        if part3_high > part2_high > part1_high and part3_low > part2_low > part1_low:
            return MarketStructure.BULLISH
        
        # Lower Highs + Lower Lows = BEARISH
        if part3_high < part2_high < part1_high and part3_low < part2_low < part1_low:
            return MarketStructure.BEARISH
        
        return MarketStructure.RANGING
    
    @staticmethod
    def get_trading_session(timestamp: int) -> TradingSession:
        dt = datetime.utcfromtimestamp(timestamp)
        hour = dt.hour
        
        if 13 <= hour < 17:
            return TradingSession.OVERLAP
        if 8 <= hour < 17:
            return TradingSession.LONDON
        if 13 <= hour < 22:
            return TradingSession.NEW_YORK
        if 0 <= hour < 9:
            return TradingSession.ASIA
        
        return TradingSession.OFF_HOURS
    
    @staticmethod
    def pips_from_price(price_diff: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return price_diff * 100
        else:
            return price_diff * 10000
    
    @staticmethod
    def check_candle_confirmation(candles: List[Candle], signal_type: str) -> bool:
        """
        MELHORIA #4: Confirma direção nos últimos 2 candles
        """
        if len(candles) < 2:
            return False
        
        last_2 = candles[-2:]
        
        if signal_type == "BULLISH":
            # Últimos 2 candles devem fechar acima da abertura
            bullish_candles = sum(1 for c in last_2 if c.close > c.open)
            return bullish_candles >= 2
        
        else:  # BEARISH
            # Últimos 2 candles devem fechar abaixo da abertura
            bearish_candles = sum(1 for c in last_2 if c.close < c.open)
            return bearish_candles >= 2


class OptimizedForexEngine:
    """
    Motor FOREX V3 - OTIMIZADO
    Target: 35-40% win rate com dados reais
    """
    
    def __init__(self, pair: str = "EUR/USD"):
        self.pair = pair
        self.indicators = ForexIndicators()
    
    def analyze(self, candles: List[Candle]) -> ForexSignal:
        """Análise OTIMIZADA com todos os filtros"""
        
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
            return self._wait_signal("Mercado em RANGING")
        
        # FILTRO 2: MELHORIA #2 - Evitar sessão ASIA
        if session == TradingSession.ASIA:
            return self._wait_signal("Sessão ASIA - evitada para melhor win rate")
        
        # FILTRO 3: Não operar fora das sessões
        if session == TradingSession.OFF_HOURS:
            return self._wait_signal("Fora de horário")
        
        # FILTRO 4: MELHORIA #3 - ATR mínimo aumentado
        atr_pips = self.indicators.pips_from_price(atr, self.pair)
        if atr_pips < 15:  # Aumentado de 10 para 15
            return self._wait_signal(f"ATR muito baixo ({atr_pips:.1f} pips) - necessário >= 15")
        
        # FILTRO 5: Tendência confirmada
        trend_confirmed = False
        if current_price > ema_50 > ema_200:
            trend_confirmed = True
            trend_direction = "BULLISH"
        elif current_price < ema_50 < ema_200:
            trend_confirmed = True
            trend_direction = "BEARISH"
        else:
            return self._wait_signal("Tendência não confirmada")
        
        # FILTRO 6: Estrutura alinhada
        if trend_direction == "BULLISH" and market_structure != MarketStructure.BULLISH:
            return self._wait_signal("Estrutura não alinha")
        
        if trend_direction == "BEARISH" and market_structure != MarketStructure.BEARISH:
            return self._wait_signal("Estrutura não alinha")
        
        # FILTRO 7: MELHORIA #4 - Confirmação de candles
        if not self.indicators.check_candle_confirmation(candles, trend_direction):
            return self._wait_signal("Aguardando confirmação de candles")
        
        # Análise de entrada
        score = 0
        reasons = []
        warnings = []
        signal_type = SignalType.WAIT
        
        if trend_direction == "BULLISH":
            signal_type, score, reasons = self._analyze_bullish_entry(
                current_price, ema_50, ema_200, market_structure, session, atr_pips
            )
        else:
            signal_type, score, reasons = self._analyze_bearish_entry(
                current_price, ema_50, ema_200, market_structure, session, atr_pips
            )
        
        # FILTRO 8: MELHORIA #1 - Score mínimo aumentado de 70 para 80
        if score < 80:  # Aumentado de 70 para 80
            return self._wait_signal(f"Score insuficiente ({score}/80) - mais seletivo")
        
        # Calcular níveis
        sl_pips = max(10, min(15, atr_pips * 1.5))
        tp1_pips = sl_pips * 2.5
        tp2_pips = sl_pips * 4.0
        
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
        """Análise CALL com critérios mais rígidos"""
        score = 0
        reasons = []
        
        # 1. Pullback perfeito (35 pts - mais importante)
        distance_to_ema50 = ((price - ema_50) / ema_50) * 100
        
        if -0.05 <= distance_to_ema50 <= 0.2:  # Range mais estreito
            score += 35
            reasons.append(f"✅ Pullback PERFEITO ({distance_to_ema50:.2f}%)")
        elif 0.2 < distance_to_ema50 <= 0.4:
            score += 25
            reasons.append("✅ Pullback bom")
        else:
            reasons.append(f"⚠️ Pullback fora do ideal ({distance_to_ema50:.2f}%)")
        
        # 2. Estrutura bullish (25 pts)
        if structure == MarketStructure.BULLISH:
            score += 25
            reasons.append("✅ Estrutura HH+HL")
        
        # 3. Sessão premium (25 pts - mais pontos para OVERLAP)
        if session == TradingSession.OVERLAP:
            score += 25
            reasons.append("✅ Sessão OVERLAP (melhor)")
        elif session == TradingSession.LONDON:
            score += 20
            reasons.append("✅ Sessão Londres")
        elif session == TradingSession.NEW_YORK:
            score += 15
            reasons.append("✅ Sessão NY")
        
        # 4. ATR forte (15 pts)
        if 18 <= atr_pips <= 35:
            score += 15
            reasons.append(f"✅ ATR ideal ({atr_pips:.1f} pips)")
        elif 15 <= atr_pips < 18:
            score += 10
            reasons.append(f"✅ ATR aceitável ({atr_pips:.1f} pips)")
        
        if score >= 80:
            return SignalType.CALL, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _analyze_bearish_entry(self, price, ema_50, ema_200, structure, session, atr_pips):
        """Análise PUT com critérios mais rígidos"""
        score = 0
        reasons = []
        
        # 1. Pullback perfeito (35 pts)
        distance_to_ema50 = ((ema_50 - price) / ema_50) * 100
        
        if -0.05 <= distance_to_ema50 <= 0.2:
            score += 35
            reasons.append(f"✅ Pullback PERFEITO ({distance_to_ema50:.2f}%)")
        elif 0.2 < distance_to_ema50 <= 0.4:
            score += 25
            reasons.append("✅ Pullback bom")
        else:
            reasons.append(f"⚠️ Pullback fora do ideal ({distance_to_ema50:.2f}%)")
        
        # 2. Estrutura bearish (25 pts)
        if structure == MarketStructure.BEARISH:
            score += 25
            reasons.append("✅ Estrutura LL+LH")
        
        # 3. Sessão premium (25 pts)
        if session == TradingSession.OVERLAP:
            score += 25
            reasons.append("✅ Sessão OVERLAP (melhor)")
        elif session == TradingSession.LONDON:
            score += 20
            reasons.append("✅ Sessão Londres")
        elif session == TradingSession.NEW_YORK:
            score += 15
            reasons.append("✅ Sessão NY")
        
        # 4. ATR forte (15 pts)
        if 18 <= atr_pips <= 35:
            score += 15
            reasons.append(f"✅ ATR ideal ({atr_pips:.1f} pips)")
        elif 15 <= atr_pips < 18:
            score += 10
            reasons.append(f"✅ ATR aceitável ({atr_pips:.1f} pips)")
        
        if score >= 80:
            return SignalType.PUT, score, reasons
        else:
            return SignalType.WAIT, score, reasons
    
    def _wait_signal(self, reason: str) -> ForexSignal:
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
