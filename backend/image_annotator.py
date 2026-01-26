"""
Professional Trading Chart Annotator
Creates institutional-grade, cinematographic trading annotations
Style: ICT, SMC, Price Action Institutional
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import base64
from typing import Dict, List, Tuple, Optional
import re
import numpy as np
import logging
import math

logger = logging.getLogger(__name__)


class ChartAnnotator:
    """
    Creates professional institutional-style trading chart annotations
    Similar to ICT, SMC, Price Action educational materials
    """
    
    def __init__(self):
        # Professional color palette
        self.colors = {
            # Zone colors (semi-transparent)
            'zone_blue': (59, 130, 246),        # Primary zone color
            'zone_blue_alpha': 45,               # Transparency for zones
            
            # CALL (Buy) colors
            'call_green': (34, 197, 94),         # Bright green for CALL
            'call_arrow': (74, 222, 128),        # Light green arrow
            
            # PUT (Sell) colors
            'put_red': (239, 68, 68),            # Bright red for PUT
            'put_arrow': (248, 113, 113),        # Light red arrow
            
            # Text colors
            'white': (255, 255, 255),
            'white_soft': (240, 240, 245),
            'gray_light': (200, 200, 210),
            'gray_medium': (148, 163, 184),
            
            # Accent colors
            'price_tag_bg': (37, 99, 235),       # Blue background for price tags
            'glow_blue': (59, 130, 246, 100),
            
            # Background overlay
            'dark_overlay': (8, 8, 12),
            'vignette': (0, 0, 0),
        }
        
        # Load fonts
        self.fonts = self._load_fonts()
    
    def _load_fonts(self) -> Dict:
        """Load professional fonts with fallbacks"""
        fonts = {}
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        try:
            # Professional typography sizes
            fonts['hero'] = ImageFont.truetype(font_paths[0], 42)      # Main labels
            fonts['title'] = ImageFont.truetype(font_paths[0], 32)    # Section titles
            fonts['label'] = ImageFont.truetype(font_paths[0], 26)    # Entry/Exit labels
            fonts['sublabel'] = ImageFont.truetype(font_paths[1], 20) # Sub-labels
            fonts['price'] = ImageFont.truetype(font_paths[0], 18)    # Price tags
            fonts['small'] = ImageFont.truetype(font_paths[1], 16)    # Small text
        except:
            default = ImageFont.load_default()
            fonts = {k: default for k in ['hero', 'title', 'label', 'sublabel', 'price', 'small']}
        
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
            'confidence': None,
            'asset': None,
            'pattern': None,
            'strategy': None,
            'trend': None,
            'timeframe': None,
        }
        
        text_upper = analysis_text.upper()
        
        # Detect action (CALL/PUT)
        call_keywords = ['COMPRA', 'CALL', 'BUY', 'BULLISH', 'LONG', 'ALTA']
        put_keywords = ['VENDA', 'PUT', 'SELL', 'BEARISH', 'SHORT', 'BAIXA']
        
        call_count = sum(1 for kw in call_keywords if kw in text_upper)
        put_count = sum(1 for kw in put_keywords if kw in text_upper)
        
        if call_count > put_count:
            signals['action'] = 'CALL'
        elif put_count > call_count:
            signals['action'] = 'PUT'
        
        # Extract asset
        asset_patterns = [
            r'(EUR/USD|GBP/USD|USD/JPY|BTC/USD|ETH/USD)',
            r'(EURUSD|GBPUSD|USDJPY|BTCUSD|ETHUSD)',
            r'([A-Z]{3}/[A-Z]{3})',
        ]
        for pattern in asset_patterns:
            match = re.search(pattern, text_upper)
            if match:
                signals['asset'] = match.group(1)
                break
        
        # Extract prices
        sl_match = re.search(r'STOP\s*LOSS[:\s]*(\d+[.,]\d+)', text_upper)
        if sl_match:
            signals['stop_loss'] = float(sl_match.group(1).replace(',', '.'))
        
        tp_match = re.search(r'TAKE\s*PROFIT[:\s]*(\d+[.,]\d+)', text_upper)
        if tp_match:
            signals['take_profit'] = float(tp_match.group(1).replace(',', '.'))
        
        # Extract confidence
        conf_match = re.search(r'(\d+)\s*%', text_upper)
        if conf_match:
            signals['confidence'] = int(conf_match.group(1))
        
        # Extract pattern/strategy
        patterns = ['REJEIÇÃO', 'REJECTION', 'BREAKOUT', 'PULLBACK', 'REVERSÃO', 
                   'REVERSAL', 'ENGULFING', 'DOJI', 'HAMMER', 'PIN BAR']
        for p in patterns:
            if p in text_upper:
                signals['pattern'] = p
                break
        
        strategies = ['COUNTER-TREND', 'TREND-FOLLOWING', 'SCALPING', 'SWING']
        for s in strategies:
            if s in text_upper:
                signals['strategy'] = s
                break
        
        return signals
    
    def _apply_cinematic_overlay(self, image: Image.Image) -> Image.Image:
        """Apply dark cinematic overlay to image"""
        # Convert to RGBA
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        width, height = image.size
        
        # Create dark overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Add subtle vignette effect (darker edges)
        for i in range(50):
            alpha = int(25 * (i / 50))
            margin = int(width * 0.02 * (50 - i) / 50)
            draw.rectangle(
                [margin, margin, width - margin, height - margin],
                outline=(0, 0, 0, alpha)
            )
        
        # Composite
        result = Image.alpha_composite(image, overlay)
        
        # Slightly increase contrast
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(1.1)
        
        return result
    
    def _draw_glow_rectangle(self, draw: ImageDraw.Draw, coords: List[int], 
                            color: Tuple[int, int, int], alpha: int = 45) -> None:
        """Draw a glowing semi-transparent rectangle zone"""
        x1, y1, x2, y2 = coords
        
        # Draw the main semi-transparent zone
        fill_color = color + (alpha,)
        draw.rectangle(coords, fill=fill_color)
        
        # Draw subtle glow border
        for i in range(3):
            glow_alpha = int((alpha * 0.7) * (3 - i) / 3)
            glow_color = color + (glow_alpha,)
            draw.rectangle(
                [x1 - i, y1 - i, x2 + i, y2 + i],
                outline=glow_color,
                width=1
            )
    
    def _draw_professional_arrow(self, draw: ImageDraw.Draw, 
                                  start: Tuple[int, int], 
                                  end: Tuple[int, int],
                                  color: Tuple[int, int, int],
                                  arrow_size: int = 15,
                                  line_width: int = 3) -> None:
        """Draw a professional arrow with clean styling"""
        # Calculate arrow head points
        ex, ey = end
        sx, sy = start
        
        # Calculate angle
        angle = math.atan2(ey - sy, ex - sx)
        
        # Draw the line
        draw.line([start, end], fill=color + (255,), width=line_width)
        
        # Draw arrowhead
        arrow_points = [
            end,
            (int(ex - arrow_size * math.cos(angle - math.pi/6)),
             int(ey - arrow_size * math.sin(angle - math.pi/6))),
            (int(ex - arrow_size * math.cos(angle + math.pi/6)),
             int(ey - arrow_size * math.sin(angle + math.pi/6)))
        ]
        draw.polygon(arrow_points, fill=color + (255,))
    
    def _draw_label_box(self, draw: ImageDraw.Draw, 
                        text: str, 
                        position: Tuple[int, int],
                        font: ImageFont.FreeTypeFont,
                        text_color: Tuple[int, int, int] = (255, 255, 255),
                        bg_color: Optional[Tuple[int, int, int]] = None,
                        padding: int = 12) -> Tuple[int, int]:
        """Draw a label with optional background box"""
        x, y = position
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw background if specified
        if bg_color:
            bg_coords = [
                x - padding,
                y - padding // 2,
                x + text_width + padding,
                y + text_height + padding // 2
            ]
            # Rounded-ish rectangle with semi-transparency
            draw.rectangle(bg_coords, fill=bg_color + (220,))
        
        # Draw text with slight shadow for depth
        shadow_offset = 2
        draw.text((x + shadow_offset, y + shadow_offset), text, 
                 font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=text_color + (255,))
        
        return text_width, text_height
    
    def _draw_price_tag(self, draw: ImageDraw.Draw,
                        price: float,
                        y_position: int,
                        x_end: int,
                        font: ImageFont.FreeTypeFont) -> None:
        """Draw a professional price tag with blue background"""
        price_text = f"{price:.4f}" if price < 100 else f"{price:.2f}"
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), price_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        padding = 8
        tag_width = text_width + padding * 2
        tag_height = text_height + padding
        
        # Position tag at right side
        tag_x = x_end - tag_width - 10
        tag_y = y_position - tag_height // 2
        
        # Draw tag background
        draw.rectangle(
            [tag_x, tag_y, tag_x + tag_width, tag_y + tag_height],
            fill=self.colors['price_tag_bg'] + (230,)
        )
        
        # Draw text
        draw.text(
            (tag_x + padding, tag_y + padding // 2),
            price_text,
            font=font,
            fill=self.colors['white'] + (255,)
        )
        
        # Draw horizontal line extending to the left
        draw.line(
            [(tag_x - 5, y_position), (50, y_position)],
            fill=self.colors['white'] + (180,),
            width=1
        )
    
    def create_professional_annotation(self, 
                                       image_bytes: bytes, 
                                       signals: Dict,
                                       operation_type: str = 'CALL') -> bytes:
        """
        Create a professional, institutional-grade trading chart annotation
        Style: ICT/SMC/Price Action Educational Materials
        """
        # Load original image
        original = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGBA
        if original.mode != 'RGBA':
            original = original.convert('RGBA')
        
        width, height = original.size
        
        # Apply cinematic overlay to original
        base_image = self._apply_cinematic_overlay(original)
        
        # Create overlay for annotations
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Calculate chart area (typically 70-85% of image)
        chart_left = int(width * 0.06)
        chart_right = int(width * 0.92)
        chart_top = int(height * 0.08)
        chart_bottom = int(height * 0.88)
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        # Determine colors based on operation type
        if operation_type == 'CALL':
            entry_color = self.colors['call_green']
            arrow_color = self.colors['call_arrow']
            entry_text = "CALL Entry"
            arrow_direction = 'up'
        else:
            entry_color = self.colors['put_red']
            arrow_color = self.colors['put_arrow']
            entry_text = "PUT Entry"
            arrow_direction = 'down'
        
        # === DRAW REJECTION ZONE (Blue Rectangle) ===
        if operation_type == 'CALL':
            # For CALL: zone in lower area (support zone)
            zone_x1 = chart_left + int(chart_width * 0.30)
            zone_y1 = chart_top + int(chart_height * 0.50)
            zone_x2 = chart_left + int(chart_width * 0.70)
            zone_y2 = chart_top + int(chart_height * 0.72)
        else:
            # For PUT: zone in upper area (resistance zone)
            zone_x1 = chart_left + int(chart_width * 0.30)
            zone_y1 = chart_top + int(chart_height * 0.22)
            zone_x2 = chart_left + int(chart_width * 0.70)
            zone_y2 = chart_top + int(chart_height * 0.45)
        
        # Draw the glowing zone
        self._draw_glow_rectangle(
            draw,
            [zone_x1, zone_y1, zone_x2, zone_y2],
            self.colors['zone_blue'],
            alpha=50
        )
        
        # === DRAW "Strong Rejection" LABEL ===
        rejection_text = signals.get('pattern', 'Strong Rejection') or 'Strong Rejection'
        rejection_x = zone_x1 - 30
        rejection_y = zone_y1 + (zone_y2 - zone_y1) // 2 - 40
        
        # Draw rejection label with underline style
        self._draw_label_box(
            draw, rejection_text,
            (rejection_x, rejection_y),
            self.fonts['label'],
            text_color=self.colors['white']
        )
        
        # Draw "Counter-Trend Trade" or strategy sublabel
        strategy_text = signals.get('strategy', 'Counter-Trend Trade') or 'Counter-Trend Trade'
        self._draw_label_box(
            draw, strategy_text,
            (rejection_x, rejection_y + 35),
            self.fonts['sublabel'],
            text_color=self.colors['gray_medium']
        )
        
        # Draw arrow from "Strong Rejection" to zone
        arrow_start = (rejection_x + 180, rejection_y + 15)
        arrow_end = (zone_x1 + 30, zone_y1 + 30 if operation_type == 'PUT' else zone_y2 - 30)
        self._draw_professional_arrow(
            draw, arrow_start, arrow_end,
            self.colors['white'],
            arrow_size=12,
            line_width=2
        )
        
        # === DRAW ENTRY LABEL AND ARROW ===
        if operation_type == 'CALL':
            entry_label_x = zone_x2 - 80
            entry_label_y = zone_y2 + 20
            entry_arrow_start = (entry_label_x + 60, entry_label_y - 5)
            entry_arrow_end = (zone_x2 - 40, zone_y1 + 20)
        else:
            entry_label_x = zone_x2 - 80
            entry_label_y = zone_y1 - 50
            entry_arrow_start = (entry_label_x + 60, entry_label_y + 35)
            entry_arrow_end = (zone_x2 - 40, zone_y2 - 20)
        
        # Draw entry label
        self._draw_label_box(
            draw, entry_text,
            (entry_label_x, entry_label_y),
            self.fonts['label'],
            text_color=entry_color
        )
        
        # Draw entry arrow
        self._draw_professional_arrow(
            draw, entry_arrow_start, entry_arrow_end,
            arrow_color,
            arrow_size=14,
            line_width=3
        )
        
        # === DRAW EXIT LABEL ===
        if operation_type == 'CALL':
            exit_x = zone_x2 + 30
            exit_y = zone_y1 - 60
        else:
            exit_x = zone_x2 + 30
            exit_y = zone_y2 + 30
        
        self._draw_label_box(
            draw, "Exit (1-2 candles)",
            (exit_x, exit_y),
            self.fonts['sublabel'],
            text_color=self.colors['white_soft']
        )
        
        # === DRAW PRICE LEVEL LINE ===
        price = signals.get('stop_loss') or signals.get('entry_price') or 1.0850
        price_y = zone_y2 + 10 if operation_type == 'CALL' else zone_y1 - 10
        
        self._draw_price_tag(
            draw, price, price_y,
            chart_right, self.fonts['price']
        )
        
        # === DRAW TITLE BANNER (Top) ===
        asset = signals.get('asset', 'Chart')
        confidence = signals.get('confidence', '')
        
        title_text = f"{operation_type} Setup"
        if asset:
            title_text = f"{operation_type} Setup - {asset}"
        
        # Draw title at top center
        bbox = draw.textbbox((0, 0), title_text, font=self.fonts['title'])
        title_width = bbox[2] - bbox[0]
        title_x = (width - title_width) // 2
        title_y = 15
        
        # Title background
        draw.rectangle(
            [title_x - 20, title_y - 5, title_x + title_width + 20, title_y + 40],
            fill=(10, 10, 15, 200)
        )
        
        # Title text
        draw.text(
            (title_x, title_y),
            title_text,
            font=self.fonts['title'],
            fill=entry_color + (255,)
        )
        
        # === DRAW INFO BOX (Bottom Left) ===
        self._draw_info_box(draw, width, height, signals, operation_type)
        
        # === COMPOSITE FINAL IMAGE ===
        result = Image.alpha_composite(base_image, overlay)
        result = result.convert('RGB')
        
        # Save to bytes
        output = io.BytesIO()
        result.save(output, format='PNG', quality=95)
        return output.getvalue()
    
    def _draw_info_box(self, draw: ImageDraw.Draw, 
                      width: int, height: int,
                      signals: Dict, 
                      operation_type: str) -> None:
        """Draw professional info box with trade details"""
        x = 25
        y = height - 150
        padding = 15
        line_height = 26
        
        # Prepare info lines
        lines = []
        
        if operation_type == 'CALL':
            lines.append(("Direção:", "Compra (CALL)", self.colors['call_green']))
        else:
            lines.append(("Direção:", "Venda (PUT)", self.colors['put_red']))
        
        if signals.get('stop_loss'):
            lines.append(("Stop Loss:", f"{signals['stop_loss']}", self.colors['put_red']))
        
        if signals.get('take_profit'):
            lines.append(("Take Profit:", f"{signals['take_profit']}", self.colors['call_green']))
        
        if signals.get('confidence'):
            lines.append(("Confiança:", f"{signals['confidence']}%", self.colors['white']))
        
        # Calculate box size
        max_width = 0
        for label, value, _ in lines:
            text = f"{label} {value}"
            bbox = draw.textbbox((0, 0), text, font=self.fonts['small'])
            max_width = max(max_width, bbox[2] - bbox[0])
        
        box_width = max_width + padding * 2 + 20
        box_height = len(lines) * line_height + padding * 2
        
        # Draw background with blur effect simulation
        draw.rectangle(
            [x, y, x + box_width, y + box_height],
            fill=(10, 10, 15, 220)
        )
        draw.rectangle(
            [x, y, x + box_width, y + box_height],
            outline=(59, 130, 246, 100),
            width=1
        )
        
        # Draw lines
        current_y = y + padding
        for label, value, color in lines:
            draw.text(
                (x + padding, current_y),
                label,
                font=self.fonts['small'],
                fill=self.colors['gray_medium'] + (255,)
            )
            
            # Get label width to position value
            bbox = draw.textbbox((0, 0), label, font=self.fonts['small'])
            label_width = bbox[2] - bbox[0]
            
            draw.text(
                (x + padding + label_width + 8, current_y),
                value,
                font=self.fonts['small'],
                fill=color + (255,)
            )
            current_y += line_height
    
    def annotate_chart(self, image_bytes: bytes, analysis_text: str, 
                      signals: Optional[Dict] = None) -> bytes:
        """Main method to annotate a chart based on AI analysis"""
        if signals is None:
            signals = self.extract_trading_signals(analysis_text)
        
        action = signals.get('action', 'CALL')
        return self.create_professional_annotation(image_bytes, signals, action)
    
    def generate_both_scenarios(self, image_bytes: bytes, 
                               analysis_text: str) -> Tuple[bytes, bytes]:
        """Generate both CALL and PUT scenario images"""
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
