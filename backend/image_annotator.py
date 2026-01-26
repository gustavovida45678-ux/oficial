"""
Advanced Image Annotator for Trading Chart Analysis
Generates professional chart annotations similar to trading platforms
Creates visual CALL and PUT operation zones with entry, stop loss, and take profit
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import base64
from typing import Dict, List, Tuple, Optional
import re
import numpy as np
import cv2
import logging
import math

logger = logging.getLogger(__name__)


class ChartAnnotator:
    """Advanced annotator that creates professional trading chart visualizations"""
    
    def __init__(self):
        # Professional color scheme
        self.colors = {
            # CALL (Buy) colors
            'call_zone': (0, 180, 80, 50),      # Semi-transparent green zone
            'call_entry': (34, 197, 94),         # Bright green
            'call_arrow': (74, 222, 128),        # Light green arrow
            'call_text': (74, 222, 128),         # Green text
            
            # PUT (Sell) colors
            'put_zone': (220, 50, 50, 50),       # Semi-transparent red zone
            'put_entry': (239, 68, 68),          # Bright red
            'put_arrow': (248, 113, 113),        # Light red arrow
            'put_text': (248, 113, 113),         # Red text
            
            # Entry zone (blue like reference image)
            'entry_zone': (59, 130, 246, 60),    # Semi-transparent blue
            'entry_border': (96, 165, 250),      # Light blue border
            
            # General colors
            'white': (255, 255, 255),
            'text_bg': (10, 10, 15, 230),        # Dark background for text
            'support': (59, 130, 246),           # Blue for support
            'resistance': (251, 146, 60),        # Orange for resistance
            'stop_loss': (239, 68, 68),          # Red for SL
            'take_profit': (34, 197, 94),        # Green for TP
            'price_line': (148, 163, 184),       # Gray for price lines
        }
        
        # Font setup
        self.fonts = self._load_fonts()
    
    def _load_fonts(self) -> Dict:
        """Load fonts with fallbacks"""
        fonts = {}
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        try:
            fonts['title'] = ImageFont.truetype(font_paths[0], 32)
            fonts['large'] = ImageFont.truetype(font_paths[0], 26)
            fonts['medium'] = ImageFont.truetype(font_paths[0], 20)
            fonts['small'] = ImageFont.truetype(font_paths[1], 16)
            fonts['tiny'] = ImageFont.truetype(font_paths[1], 14)
        except:
            fonts['title'] = ImageFont.load_default()
            fonts['large'] = ImageFont.load_default()
            fonts['medium'] = ImageFont.load_default()
            fonts['small'] = ImageFont.load_default()
            fonts['tiny'] = ImageFont.load_default()
        
        return fonts
    
    def extract_trading_signals(self, analysis_text: str) -> Dict:
        """Extract trading signals from AI analysis text"""
        signals = {
            'action': None,
            'entry_price': None,
            'entry_price_min': None,
            'entry_price_max': None,
            'stop_loss': None,
            'take_profit': None,
            'take_profit_2': None,
            'take_profit_3': None,
            'strategy': None,
            'confidence': None,
            'key_levels': [],
            'support_levels': [],
            'resistance_levels': [],
            'trend': None,
            'timeframe': None,
            'asset': None,
            'pattern': None,
        }
        
        text = analysis_text
        text_upper = text.upper()
        
        # Detect action (CALL/PUT)
        call_keywords = ['COMPRA', 'CALL', 'BUY', 'BULLISH', 'LONG', 'ALTA PROBABILIDADE DE ALTA']
        put_keywords = ['VENDA', 'PUT', 'SELL', 'BEARISH', 'SHORT', 'ALTA PROBABILIDADE DE BAIXA']
        
        call_count = sum(1 for kw in call_keywords if kw in text_upper)
        put_count = sum(1 for kw in put_keywords if kw in text_upper)
        
        if call_count > put_count:
            signals['action'] = 'CALL'
        elif put_count > call_count:
            signals['action'] = 'PUT'
        elif 'AGUARDAR' in text_upper or 'WAIT' in text_upper:
            signals['action'] = 'WAIT'
        
        # Extract asset/pair
        asset_patterns = [
            r'(EUR/USD|GBP/USD|USD/JPY|USD/CHF|AUD/USD|NZD/USD|USD/CAD)',
            r'(EURUSD|GBPUSD|USDJPY|USDCHF|AUDUSD|NZDUSD|USDCAD)',
            r'(BTC/USD|ETH/USD|XRP/USD|BTCUSD|ETHUSD)',
            r'(OTC[A-Z]+)',
            r'([A-Z]{3}/[A-Z]{3})',
        ]
        for pattern in asset_patterns:
            match = re.search(pattern, text_upper)
            if match:
                signals['asset'] = match.group(1)
                break
        
        # Extract timeframe
        tf_patterns = [r'(M1|M5|M15|M30|H1|H4|D1|W1)', r'(\d+\s*MINUTO)', r'(\d+\s*HORA)']
        for pattern in tf_patterns:
            match = re.search(pattern, text_upper)
            if match:
                signals['timeframe'] = match.group(1)
                break
        
        # Extract entry price range
        entry_patterns = [
            r'ENTRADA.*?(\d+[.,]\d+).*?(?:A|E|-).*?(\d+[.,]\d+)',
            r'ENTRE.*?(\d+[.,]\d+).*?E.*?(\d+[.,]\d+)',
            r'ZONA.*?ENTRADA.*?(\d+[.,]\d+)',
            r'ENTRY.*?(\d+[.,]\d+)',
        ]
        for pattern in entry_patterns:
            match = re.search(pattern, text_upper)
            if match:
                try:
                    signals['entry_price_min'] = float(match.group(1).replace(',', '.'))
                    if len(match.groups()) > 1 and match.group(2):
                        signals['entry_price_max'] = float(match.group(2).replace(',', '.'))
                    signals['entry_price'] = signals['entry_price_min']
                except:
                    pass
                break
        
        # Extract Stop Loss
        sl_patterns = [
            r'STOP\s*LOSS[:\s]*(\d+[.,]\d+)',
            r'SL[:\s]*(\d+[.,]\d+)',
            r'STOP[:\s]*(\d+[.,]\d+)',
            r'PROTEGER.*?(\d+[.,]\d+)',
        ]
        for pattern in sl_patterns:
            match = re.search(pattern, text_upper)
            if match:
                signals['stop_loss'] = float(match.group(1).replace(',', '.'))
                break
        
        # Extract Take Profit (multiple targets)
        tp_patterns = [
            r'TAKE\s*PROFIT[:\s]*(\d+[.,]\d+)',
            r'TP[:\s]*(\d+[.,]\d+)',
            r'ALVO\s*1?[:\s]*(\d+[.,]\d+)',
            r'TARGET[:\s]*(\d+[.,]\d+)',
        ]
        tp_values = []
        for pattern in tp_patterns:
            matches = re.findall(pattern, text_upper)
            for m in matches:
                try:
                    tp_values.append(float(m.replace(',', '.')))
                except:
                    pass
        
        if tp_values:
            tp_values = sorted(set(tp_values))
            signals['take_profit'] = tp_values[0] if len(tp_values) > 0 else None
            signals['take_profit_2'] = tp_values[1] if len(tp_values) > 1 else None
            signals['take_profit_3'] = tp_values[2] if len(tp_values) > 2 else None
        
        # Extract confidence
        confidence_patterns = [
            r'(\d+)\s*%.*?(?:CONFIANÇA|CONFIDENCE|PROBABILIDADE)',
            r'(?:CONFIANÇA|CONFIDENCE|PROBABILIDADE).*?(\d+)\s*%',
        ]
        for pattern in confidence_patterns:
            match = re.search(pattern, text_upper)
            if match:
                signals['confidence'] = int(match.group(1))
                break
        
        # Extract trend
        if 'TENDÊNCIA DE ALTA' in text_upper or 'UPTREND' in text_upper or 'ALTA' in text_upper:
            signals['trend'] = 'ALTA'
        elif 'TENDÊNCIA DE BAIXA' in text_upper or 'DOWNTREND' in text_upper or 'BAIXA' in text_upper:
            signals['trend'] = 'BAIXA'
        
        # Extract pattern
        patterns = [
            'DOJI', 'HAMMER', 'ENGULFING', 'SHOOTING STAR', 'MORNING STAR',
            'EVENING STAR', 'HARAMI', 'PIERCING', 'DARK CLOUD', 'MARUBOZU',
            'REJEIÇÃO', 'REJECTION', 'BREAKOUT', 'ROMPIMENTO', 'PULLBACK',
            'CONSOLIDAÇÃO', 'TRIÂNGULO', 'CUNHA', 'BANDEIRA', 'RETÂNGULO'
        ]
        for p in patterns:
            if p in text_upper:
                signals['pattern'] = p
                break
        
        # Extract strategy type
        strategies = [
            'COUNTER-TREND', 'CONTRA-TENDÊNCIA', 'TREND-FOLLOWING',
            'BREAKOUT', 'REVERSAL', 'REVERSÃO', 'PULLBACK', 'SCALPING'
        ]
        for s in strategies:
            if s in text_upper:
                signals['strategy'] = s
                break
        
        # Extract all price levels
        all_prices = re.findall(r'(\d+[.,]\d{4,5})', text)
        if all_prices:
            prices = [float(p.replace(',', '.')) for p in all_prices]
            signals['key_levels'] = sorted(set(prices))[:8]
        
        return signals
    
    def create_professional_annotation(self, 
                                       image_bytes: bytes, 
                                       signals: Dict,
                                       operation_type: str = 'CALL') -> bytes:
        """
        Create a professional trading chart annotation
        Similar to the reference image style
        """
        # Load original image
        original = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGBA
        if original.mode != 'RGBA':
            original = original.convert('RGBA')
        
        width, height = original.size
        
        # Create overlay for annotations
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Detect chart area (approximately 70-80% of image)
        chart_left = int(width * 0.08)
        chart_right = int(width * 0.88)
        chart_top = int(height * 0.08)
        chart_bottom = int(height * 0.85)
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        # Determine colors based on operation type
        if operation_type == 'CALL':
            zone_color = self.colors['call_zone']
            entry_color = self.colors['call_entry']
            arrow_color = self.colors['call_arrow']
            text_color = self.colors['call_text']
            direction = 'up'
        else:  # PUT
            zone_color = self.colors['put_zone']
            entry_color = self.colors['put_entry']
            arrow_color = self.colors['put_arrow']
            text_color = self.colors['put_text']
            direction = 'down'
        
        # === DRAW ENTRY ZONE (Blue rectangle like reference) ===
        # Position entry zone based on operation type
        if operation_type == 'CALL':
            # For CALL: entry zone in lower-middle area
            zone_x1 = chart_left + int(chart_width * 0.35)
            zone_y1 = chart_top + int(chart_height * 0.45)
            zone_x2 = chart_left + int(chart_width * 0.75)
            zone_y2 = chart_top + int(chart_height * 0.70)
        else:
            # For PUT: entry zone in upper-middle area
            zone_x1 = chart_left + int(chart_width * 0.35)
            zone_y1 = chart_top + int(chart_height * 0.25)
            zone_x2 = chart_left + int(chart_width * 0.75)
            zone_y2 = chart_top + int(chart_height * 0.50)
        
        # Draw semi-transparent entry zone
        entry_zone_color = self.colors['entry_zone']
        draw.rectangle([zone_x1, zone_y1, zone_x2, zone_y2], fill=entry_zone_color)
        
        # Draw entry zone border
        border_color = self.colors['entry_border'] + (180,)
        draw.rectangle([zone_x1, zone_y1, zone_x2, zone_y2], outline=border_color, width=2)
        
        # === DRAW ENTRY LABEL ===
        entry_text = f"{operation_type} Entry"
        self._draw_label_with_background(
            draw, 
            entry_text, 
            (zone_x1 + 20, zone_y1 - 50),
            self.fonts['large'],
            text_color,
            with_arrow=True,
            arrow_direction=direction,
            arrow_end=(zone_x1 + 80, zone_y1 + 30)
        )
        
        # === DRAW STOP LOSS LINE AND LABEL ===
        if signals.get('stop_loss'):
            sl_y = zone_y2 + 60 if operation_type == 'CALL' else zone_y1 - 60
            sl_text = f"Stop Loss: {signals['stop_loss']}"
            
            # Draw SL line
            draw.line([(chart_left, sl_y), (chart_right, sl_y)], 
                     fill=self.colors['stop_loss'] + (180,), width=2)
            
            # Draw SL label
            self._draw_label_with_background(
                draw,
                sl_text,
                (chart_right - 200, sl_y - 25),
                self.fonts['medium'],
                self.colors['stop_loss']
            )
        
        # === DRAW TAKE PROFIT LINE AND LABEL ===
        if signals.get('take_profit'):
            tp_y = zone_y1 - 80 if operation_type == 'CALL' else zone_y2 + 80
            tp_text = f"Take Profit: {signals['take_profit']}"
            
            # Draw TP line
            draw.line([(chart_left, tp_y), (chart_right, tp_y)], 
                     fill=self.colors['take_profit'] + (180,), width=2)
            
            # Draw TP label
            self._draw_label_with_background(
                draw,
                tp_text,
                (chart_right - 220, tp_y - 25),
                self.fonts['medium'],
                self.colors['take_profit']
            )
        
        # === DRAW PATTERN/SIGNAL INDICATOR ===
        pattern_text = signals.get('pattern') or signals.get('strategy') or 'Strong Signal'
        
        signal_x = chart_left + 30
        signal_y = zone_y1 + int((zone_y2 - zone_y1) / 2) - 20
        
        # Draw signal indicator with arrow
        self._draw_signal_indicator(
            draw,
            pattern_text,
            (signal_x, signal_y),
            (zone_x1 - 10, signal_y + 10),
            self.fonts['medium']
        )
        
        # === DRAW EXIT LABEL ===
        exit_x = zone_x2 - 50
        exit_y = zone_y2 + 20 if operation_type == 'CALL' else zone_y1 - 50
        self._draw_label_with_background(
            draw,
            "Exit (1-2 candles)",
            (exit_x, exit_y),
            self.fonts['small'],
            self.colors['white']
        )
        
        # === DRAW TITLE BANNER ===
        self._draw_title_banner(draw, width, operation_type, signals, text_color)
        
        # === DRAW CONFIDENCE INDICATOR ===
        if signals.get('confidence'):
            self._draw_confidence_bar(draw, width, height, signals['confidence'], text_color)
        
        # === DRAW INFO BOX ===
        self._draw_info_box(draw, width, height, signals, operation_type)
        
        # Composite
        result = Image.alpha_composite(original, overlay)
        result = result.convert('RGB')
        
        # Save to bytes
        output = io.BytesIO()
        result.save(output, format='PNG', quality=95)
        return output.getvalue()
    
    def _draw_label_with_background(self, draw, text, position, font, text_color, 
                                    with_arrow=False, arrow_direction='down', arrow_end=None):
        """Draw text label with dark background"""
        x, y = position
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        padding = 10
        
        # Draw background
        bg_coords = [
            x - padding,
            y - padding,
            x + text_width + padding,
            y + text_height + padding
        ]
        draw.rectangle(bg_coords, fill=self.colors['text_bg'])
        
        # Draw text
        if isinstance(text_color, tuple) and len(text_color) == 3:
            text_color = text_color + (255,)
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Draw arrow if requested
        if with_arrow and arrow_end:
            arrow_start = (x + text_width + padding + 5, y + text_height // 2)
            self._draw_arrow(draw, arrow_start, arrow_end, text_color[:3] + (200,), arrow_direction)
    
    def _draw_arrow(self, draw, start, end, color, direction='down'):
        """Draw an arrow from start to end"""
        # Draw line
        draw.line([start, end], fill=color, width=3)
        
        # Draw arrowhead
        ex, ey = end
        size = 12
        
        if direction == 'down':
            points = [(ex, ey + size), (ex - size//2, ey), (ex + size//2, ey)]
        elif direction == 'up':
            points = [(ex, ey - size), (ex - size//2, ey), (ex + size//2, ey)]
        elif direction == 'right':
            points = [(ex + size, ey), (ex, ey - size//2), (ex, ey + size//2)]
        else:
            points = [(ex - size, ey), (ex, ey - size//2), (ex, ey + size//2)]
        
        draw.polygon(points, fill=color)
    
    def _draw_signal_indicator(self, draw, text, text_pos, arrow_target, font):
        """Draw signal indicator with arrow pointing to chart"""
        x, y = text_pos
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        padding = 8
        
        # Draw background
        draw.rectangle([
            x - padding, y - padding,
            x + text_width + padding, y + text_height + padding + 20
        ], fill=self.colors['text_bg'])
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=self.colors['white'])
        
        # Draw sub-label
        sub_text = "Trade Signal"
        draw.text((x, y + text_height + 5), sub_text, font=self.fonts['tiny'], fill=(148, 163, 184, 255))
        
        # Draw arrow
        arrow_start = (x + text_width + padding + 10, y + text_height // 2)
        self._draw_arrow(draw, arrow_start, arrow_target, self.colors['white'] + (200,), 'right')
    
    def _draw_title_banner(self, draw, width, operation_type, signals, color):
        """Draw title banner at top of image"""
        # Determine banner text
        asset = signals.get('asset', 'Chart')
        confidence = signals.get('confidence', '')
        
        if operation_type == 'CALL':
            title = f"📈 {operation_type} - {asset}"
            if confidence:
                title += f" ({confidence}% conf.)"
        else:
            title = f"📉 {operation_type} - {asset}"
            if confidence:
                title += f" ({confidence}% conf.)"
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), title, font=self.fonts['title'])
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position at top center
        x = (width - text_width) // 2
        y = 15
        padding = 15
        
        # Draw background with gradient effect (simulated with solid)
        bg_color = self.colors['text_bg']
        border_color = color[:3] + (200,) if len(color) >= 3 else color
        
        draw.rectangle([
            x - padding - 5, y - padding,
            x + text_width + padding + 5, y + text_height + padding
        ], fill=bg_color)
        
        draw.rectangle([
            x - padding - 5, y - padding,
            x + text_width + padding + 5, y + text_height + padding
        ], outline=border_color, width=3)
        
        # Draw text
        draw.text((x, y), title, font=self.fonts['title'], fill=color)
    
    def _draw_confidence_bar(self, draw, width, height, confidence, color):
        """Draw confidence progress bar"""
        bar_width = 150
        bar_height = 10
        x = width - bar_width - 30
        y = height - 60
        
        # Draw label
        label = f"Confiança: {confidence}%"
        draw.text((x, y - 20), label, font=self.fonts['small'], fill=self.colors['white'])
        
        # Draw background bar
        draw.rectangle([x, y, x + bar_width, y + bar_height], fill=(50, 50, 60, 200))
        
        # Draw filled portion
        fill_width = int(bar_width * confidence / 100)
        if confidence >= 70:
            fill_color = self.colors['take_profit']
        elif confidence >= 50:
            fill_color = (250, 204, 21)  # Yellow
        else:
            fill_color = self.colors['stop_loss']
        
        draw.rectangle([x, y, x + fill_width, y + bar_height], fill=fill_color + (255,))
    
    def _draw_info_box(self, draw, width, height, signals, operation_type):
        """Draw info box with trade details"""
        x = 20
        y = height - 150
        padding = 15
        line_height = 22
        
        # Prepare info lines
        lines = []
        lines.append(f"Direção: {'Compra (CALL)' if operation_type == 'CALL' else 'Venda (PUT)'}")
        
        if signals.get('entry_price_min') and signals.get('entry_price_max'):
            lines.append(f"Entrada: {signals['entry_price_min']} - {signals['entry_price_max']}")
        elif signals.get('entry_price'):
            lines.append(f"Entrada: {signals['entry_price']}")
        
        if signals.get('stop_loss'):
            lines.append(f"Stop Loss: {signals['stop_loss']}")
        
        if signals.get('take_profit'):
            lines.append(f"Take Profit: {signals['take_profit']}")
        
        if signals.get('timeframe'):
            lines.append(f"Timeframe: {signals['timeframe']}")
        
        # Calculate box size
        max_width = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=self.fonts['small'])
            max_width = max(max_width, bbox[2] - bbox[0])
        
        box_width = max_width + padding * 2
        box_height = len(lines) * line_height + padding * 2
        
        # Draw background
        draw.rectangle([x, y, x + box_width, y + box_height], fill=self.colors['text_bg'])
        draw.rectangle([x, y, x + box_width, y + box_height], 
                      outline=(100, 100, 120, 200), width=1)
        
        # Draw lines
        current_y = y + padding
        for i, line in enumerate(lines):
            # Color first line based on operation type
            if i == 0:
                line_color = self.colors['call_text'] if operation_type == 'CALL' else self.colors['put_text']
            elif 'Stop' in line:
                line_color = self.colors['stop_loss']
            elif 'Take' in line:
                line_color = self.colors['take_profit']
            else:
                line_color = self.colors['white']
            
            draw.text((x + padding, current_y), line, font=self.fonts['small'], fill=line_color)
            current_y += line_height
    
    def annotate_chart(self, image_bytes: bytes, analysis_text: str, signals: Optional[Dict] = None) -> bytes:
        """
        Main method to annotate a chart based on AI analysis
        Generates annotation based on detected signals
        """
        if signals is None:
            signals = self.extract_trading_signals(analysis_text)
        
        if signals.get('action') in ['CALL', 'PUT']:
            return self.create_professional_annotation(image_bytes, signals, signals['action'])
        
        # Default to CALL if no clear signal
        return self.create_professional_annotation(image_bytes, signals, 'CALL')
    
    def generate_both_scenarios(self, image_bytes: bytes, analysis_text: str) -> Tuple[bytes, bytes]:
        """
        Generate both CALL and PUT scenario images
        Returns tuple of (call_image_bytes, put_image_bytes)
        """
        signals = self.extract_trading_signals(analysis_text)
        
        call_image = self.create_professional_annotation(image_bytes, signals, 'CALL')
        put_image = self.create_professional_annotation(image_bytes, signals, 'PUT')
        
        return call_image, put_image


def create_annotated_chart(image_bytes: bytes, analysis_text: str) -> bytes:
    """Convenience function to create annotated chart"""
    annotator = ChartAnnotator()
    return annotator.annotate_chart(image_bytes, analysis_text)


def create_both_scenarios(image_bytes: bytes, analysis_text: str) -> Tuple[bytes, bytes]:
    """Convenience function to create both CALL and PUT scenarios"""
    annotator = ChartAnnotator()
    return annotator.generate_both_scenarios(image_bytes, analysis_text)
