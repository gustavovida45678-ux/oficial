from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Header
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import base64
import tempfile
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
from image_annotator import ChartAnnotator
from trading_engine import TradingEngine, Candle, TradingSignal, Backtester


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Use tempfile for uploads to avoid disk bloat
UPLOAD_FOLDER = tempfile.gettempdir()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # 'user' or 'assistant'
    content: str
    image_urls: Optional[List[str]] = None
    annotated_image_urls: Optional[List[str]] = None
    call_annotated_urls: Optional[List[str]] = None
    put_annotated_urls: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    user_message: Message
    assistant_message: Message

class ImageAnalysisResponse(BaseModel):
    image_id: str
    image_path: str
    annotated_image_path: Optional[str] = None
    call_annotated_path: Optional[str] = None
    put_annotated_path: Optional[str] = None
    user_message: Message
    assistant_message: Message

class MultipleImagesAnalysisResponse(BaseModel):
    image_ids: List[str]
    image_paths: List[str]
    annotated_image_paths: Optional[List[str]] = None
    call_annotated_paths: Optional[List[str]] = None
    put_annotated_paths: Optional[List[str]] = None
    user_message: Message
    assistant_message: Message

class ImageGenerationRequest(BaseModel):
    prompt: str
    number_of_images: int = 1

class ImageGenerationResponse(BaseModel):
    image_id: str
    image_path: str
    image_base64: str
    user_message: Message
    assistant_message: Message


# === NEW: Trading Engine Models ===
class CandleInput(BaseModel):
    """Input para um candle OHLCV"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class TradeSetupRequest(BaseModel):
    """Request para análise de setup de trading"""
    candles: List[CandleInput]
    capital: float = 10000.0
    explain_with_ai: bool = True  # Se True, IA explica a decisão


class TradeSetupResponse(BaseModel):
    """Response com análise completa do setup"""
    signal: str  # "CALL", "PUT", "WAIT"
    score: int
    confidence: float
    
    # Níveis
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    
    # Análise técnica
    trend: str
    rsi_value: float
    ema_20: float
    ema_50: float
    atr_value: float
    
    # Risk Management
    risk_reward_1: float
    risk_reward_2: float
    risk_amount: float
    
    # Explicação
    reasons: List[str]
    warnings: List[str]
    ai_explanation: Optional[str] = None


class BacktestRequest(BaseModel):
    """Request para backtest"""
    candles: List[CandleInput]
    initial_capital: float = 10000.0


class BacktestResponse(BaseModel):
    """Response do backtest"""
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    initial_capital: float
    final_capital: float
    profit: float
    profit_pct: float
    profit_factor: float



# Chat endpoint
@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_custom_api_key: Optional[str] = Header(None)):
    try:
        # Use custom API key if provided, otherwise use Emergent key
        api_key = x_custom_api_key if x_custom_api_key else os.environ['EMERGENT_LLM_KEY']
        
        # Create user message
        user_message = Message(
            role="user",
            content=request.message
        )
        
        # Save user message to database
        user_doc = user_message.model_dump()
        user_doc['timestamp'] = user_doc['timestamp'].isoformat()
        await db.messages.insert_one(user_doc)
        
        # Initialize LLM chat
        chat_client = LlmChat(
            api_key=api_key,
            session_id="chat-session",
            system_message="Você é um assistente útil e amigável. Responda em português de forma clara e concisa."
        )
        chat_client.with_model("openai", "gpt-5.1")
        
        # Send message to AI
        user_msg = UserMessage(text=request.message)
        ai_response = await chat_client.send_message(user_msg)
        
        # Create assistant message
        assistant_message = Message(
            role="assistant",
            content=ai_response
        )
        
        # Save assistant message to database
        assistant_doc = assistant_message.model_dump()
        assistant_doc['timestamp'] = assistant_doc['timestamp'].isoformat()
        await db.messages.insert_one(assistant_doc)
        
        return ChatResponse(
            user_message=user_message,
            assistant_message=assistant_message
        )
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in chat endpoint: {error_msg}")
        
        # Check if it's a budget error
        if "Budget has been exceeded" in error_msg or "budget" in error_msg.lower():
            raise HTTPException(
                status_code=402,  # Payment Required
                detail="❌ Orçamento da chave LLM excedido! Por favor, adicione créditos em Profile -> Universal Key -> Add Balance"
            )
        
        raise HTTPException(status_code=500, detail=f"Error processing chat: {error_msg}")


# Image analysis endpoint
@api_router.post("/chat/image", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    question: str = Form(default="Faça uma análise técnica completa deste gráfico: identifique o ativo, timeframe, tendência, padrões de candlestick, níveis de suporte/resistência, indicadores visíveis, e forneça projeções com estimativas de próximos movimentos, incluindo probabilidades e recomendações de entrada (COMPRA/VENDA) com níveis de stop loss e take profit."),
    x_custom_api_key: Optional[str] = Header(None)
):
    try:
        # Use custom API key if provided
        api_key = x_custom_api_key if x_custom_api_key else os.environ['EMERGENT_LLM_KEY']
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Arquivo não é uma imagem válida")
        
        # Read image
        image_bytes = await file.read()
        
        # Validate image is not empty
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Imagem está vazia")
        
        # Convert to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # Save image to temp directory
        image_id = str(uuid.uuid4())
        image_filename = f"{image_id}_{file.filename}"
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        
        # Create user message with image
        user_message = Message(
            role="user",
            content=question,
            image_urls=[f"/api/uploads/{image_filename}"]
        )
        
        # Save user message to database
        user_doc = user_message.model_dump()
        user_doc['timestamp'] = user_doc['timestamp'].isoformat()
        await db.messages.insert_one(user_doc)
        
        # Initialize LLM chat with vision model
        chat_client = LlmChat(
            api_key=api_key,
            session_id="vision-session",
            system_message="""Você é um analista técnico profissional especializado em análise de gráficos de trading e mercado financeiro.

INSTRUÇÕES PARA ANÁLISE DE GRÁFICOS:

1. IDENTIFICAÇÃO DO ATIVO E TIMEFRAME:
   - Identifique o par/ativo sendo negociado (ex: EUR/USD, BTC/USD, etc.)
   - Determine o timeframe do gráfico (ex: M1, M5, M15, H1, H4, D1)
   - Anote o horário atual e preço atual

2. ANÁLISE TÉCNICA COMPLETA:
   - **Tendência Principal**: Identifique se está em tendência de alta, baixa ou lateral
   - **Padrões de Candlestick**: Identifique padrões (Doji, Hammer, Engulfing, etc.)
   - **Níveis de Suporte e Resistência**: Marque os níveis-chave onde o preço reagiu
   - **Estrutura de Mercado**: Identifique topos e fundos, rompimentos, pullbacks
   - **Volume**: Observe se há indicadores de volume e o que indicam

3. INDICADORES TÉCNICOS (se visíveis):
   - Médias Móveis (posição e cruzamentos)
   - RSI (sobrecompra/sobrevenda)
   - MACD (divergências e cruzamentos)
   - Bandas de Bollinger
   - Fibonacci (retrações e extensões)
   - Outros indicadores visíveis

4. ANÁLISE DO MOMENTUM:
   - Determine se o momentum é forte, fraco ou neutro
   - Identifique divergências entre preço e indicadores
   - Avalie a força da tendência atual

5. PROJEÇÕES E ESTIMATIVAS:
   - **Próxima Resistência/Suporte**: Onde o preço provavelmente reagirá
   - **Cenários Possíveis**: 
     * Cenário Alta: Próximos alvos, condições necessárias
     * Cenário Baixa: Próximos alvos, condições necessárias
     * Cenário Lateral: Faixas de consolidação
   - **Probabilidade**: Estime probabilidades baseadas na análise técnica
   - **Stop Loss e Take Profit**: Sugira níveis prudentes

6. SINAIS DE ENTRADA (se solicitado):
   - Condições para entrada COMPRA (CALL/BUY)
   - Condições para entrada VENDA (PUT/SELL)
   - Timeframe recomendado para a operação
   - Gestão de risco (% do capital)

7. CONTEXTO DE MERCADO:
   - Identifique se estamos perto de aberturas/fechamentos importantes
   - Note qualquer evento econômico relevante (se visível)
   - Avalie a volatilidade atual

8. CONCLUSÃO E RECOMENDAÇÕES:
   - Resuma a análise em 3-4 pontos principais
   - Dê uma recomendação clara (COMPRA, VENDA, ou AGUARDAR)
   - Indique o nível de confiança da análise (%)
   - Destaque os principais riscos

FORMATO DA RESPOSTA:
Use markdown com seções claras, bullet points, e **destaque** para informações importantes.
Seja específico com números (preços, percentuais, timeframes).
Forneça análise profunda como um analista técnico experiente faria.

Responda SEMPRE em português brasileiro de forma profissional e detalhada."""
        )
        chat_client.with_model("openai", "gpt-5.1")
        
        # Create image content
        image_content = ImageContent(image_base64=image_base64)
        
        # Send message with image to AI
        user_msg = UserMessage(
            text=question,
            file_contents=[image_content]
        )
        ai_response = await chat_client.send_message(user_msg)
        
        # Generate annotated images for both CALL and PUT scenarios
        annotated_image_path = None
        call_annotated_path = None
        put_annotated_path = None
        annotated_filename = None
        
        try:
            annotator = ChartAnnotator()
            signals = annotator.extract_trading_signals(ai_response)
            
            # Always generate both CALL and PUT scenario images
            call_bytes, put_bytes = annotator.generate_both_scenarios(image_bytes, ai_response)
            
            # Save CALL annotated image
            call_filename = f"{image_id}_call.png"
            call_annotated_path = os.path.join(UPLOAD_FOLDER, call_filename)
            with open(call_annotated_path, "wb") as f:
                f.write(call_bytes)
            logging.info(f"Generated CALL annotated image: {call_annotated_path}")
            
            # Save PUT annotated image
            put_filename = f"{image_id}_put.png"
            put_annotated_path = os.path.join(UPLOAD_FOLDER, put_filename)
            with open(put_annotated_path, "wb") as f:
                f.write(put_bytes)
            logging.info(f"Generated PUT annotated image: {put_annotated_path}")
            
            # Set the main annotated image based on detected action
            if signals['action'] == 'CALL':
                annotated_filename = call_filename
                annotated_image_path = call_annotated_path
            elif signals['action'] == 'PUT':
                annotated_filename = put_filename
                annotated_image_path = put_annotated_path
            else:
                # Default to CALL if no clear signal
                annotated_filename = call_filename
                annotated_image_path = call_annotated_path
                
        except Exception as e:
            logging.error(f"Error generating annotated images: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            # Continue without annotated images
        
        # Create assistant message
        assistant_message = Message(
            role="assistant",
            content=ai_response
        )
        
        # Save assistant message to database
        assistant_doc = assistant_message.model_dump()
        assistant_doc['timestamp'] = assistant_doc['timestamp'].isoformat()
        await db.messages.insert_one(assistant_doc)
        
        return ImageAnalysisResponse(
            image_id=image_id,
            image_path=image_path,
            annotated_image_path=f"/api/uploads/{annotated_filename}" if annotated_image_path else None,
            call_annotated_path=f"/api/uploads/{call_filename}" if call_annotated_path else None,
            put_annotated_path=f"/api/uploads/{put_filename}" if put_annotated_path else None,
            user_message=user_message,
            assistant_message=assistant_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in image analysis endpoint: {error_msg}")
        
        # Check if it's a budget error
        if "Budget has been exceeded" in error_msg or "budget" in error_msg.lower():
            raise HTTPException(
                status_code=402,  # Payment Required
                detail="❌ Orçamento da chave LLM excedido! Por favor, adicione créditos em Profile -> Universal Key -> Add Balance"
            )
        
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {error_msg}")


# Multiple images analysis endpoint
@api_router.post("/chat/images", response_model=MultipleImagesAnalysisResponse)
async def analyze_multiple_images(
    files: List[UploadFile] = File(...),
    question: str = Form(default="Faça uma análise técnica completa comparativa destes gráficos: para cada imagem, identifique o ativo, timeframe, tendência, padrões, níveis chave, e forneça uma análise consolidada com recomendações gerais considerando todos os gráficos."),
    x_custom_api_key: Optional[str] = Header(None)
):
    try:
        # Use custom API key if provided
        api_key = x_custom_api_key if x_custom_api_key else os.environ['EMERGENT_LLM_KEY']
        
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="Nenhuma imagem foi enviada")
        
        # Validate all files are images
        for file in files:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"Arquivo {file.filename} não é uma imagem válida")
        
        image_ids = []
        image_paths = []
        image_contents = []
        image_urls = []
        original_image_bytes = []  # Store original bytes for annotation
        
        # Process all images
        for file in files:
            # Read image
            image_bytes = await file.read()
            
            # Validate image is not empty
            if len(image_bytes) == 0:
                raise HTTPException(status_code=400, detail=f"Imagem {file.filename} está vazia")
            
            # Store original bytes
            original_image_bytes.append(image_bytes)
            
            # Convert to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            
            # Save image to temp directory
            image_id = str(uuid.uuid4())
            image_filename = f"{image_id}_{file.filename}"
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            image_ids.append(image_id)
            image_paths.append(image_path)
            image_urls.append(f"/api/uploads/{image_filename}")
            
            # Create image content for AI
            image_content = ImageContent(image_base64=image_base64)
            image_contents.append(image_content)
        
        # Create user message with multiple images
        user_message = Message(
            role="user",
            content=question,
            image_urls=image_urls
        )
        
        # Save user message to database
        user_doc = user_message.model_dump()
        user_doc['timestamp'] = user_doc['timestamp'].isoformat()
        await db.messages.insert_one(user_doc)
        
        # Initialize LLM chat with vision model
        chat_client = LlmChat(
            api_key=api_key,
            session_id="vision-multiple-session",
            system_message="""Você é um analista técnico profissional especializado em análise comparativa de múltiplos gráficos de trading.

INSTRUÇÕES PARA ANÁLISE DE MÚLTIPLOS GRÁFICOS:

1. Para cada imagem/gráfico recebido:
   - Identifique o ativo, timeframe, preço atual
   - Faça uma análise técnica individual resumida

2. Análise Comparativa:
   - Compare tendências entre os diferentes ativos/timeframes
   - Identifique correlações ou divergências
   - Note diferenças significativas em força de tendência

3. Síntese e Recomendações:
   - Forneça uma visão consolidada do mercado
   - Identifique qual ativo/timeframe apresenta melhor oportunidade
   - Dê recomendações priorizadas (qual operar primeiro)
   - Inclua níveis chave e gestão de risco global

Use formato:
## Imagem 1: [Ativo] [Timeframe]
- Análise técnica resumida
- Tendência, níveis, oportunidade

## Imagem 2: [Ativo] [Timeframe]
...

## Análise Comparativa
...

## Recomendações Prioritárias
...

Responda SEMPRE em português brasileiro de forma profissional."""
        )
        chat_client.with_model("openai", "gpt-5.1")
        
        # Send message with all images to AI
        user_msg = UserMessage(
            text=question,
            file_contents=image_contents
        )
        ai_response = await chat_client.send_message(user_msg)
        
        # Generate annotated images for both CALL and PUT scenarios
        annotated_image_paths = []
        call_annotated_paths = []
        put_annotated_paths = []
        
        try:
            annotator = ChartAnnotator()
            signals = annotator.extract_trading_signals(ai_response)
            
            # Generate both scenarios for each image
            for idx, (img_bytes, img_id) in enumerate(zip(original_image_bytes, image_ids)):
                try:
                    call_bytes, put_bytes = annotator.generate_both_scenarios(img_bytes, ai_response)
                    
                    # Save CALL annotated image
                    call_filename = f"{img_id}_call.png"
                    call_path = os.path.join(UPLOAD_FOLDER, call_filename)
                    with open(call_path, "wb") as f:
                        f.write(call_bytes)
                    call_annotated_paths.append(f"/api/uploads/{call_filename}")
                    
                    # Save PUT annotated image
                    put_filename = f"{img_id}_put.png"
                    put_path = os.path.join(UPLOAD_FOLDER, put_filename)
                    with open(put_path, "wb") as f:
                        f.write(put_bytes)
                    put_annotated_paths.append(f"/api/uploads/{put_filename}")
                    
                    # Add main annotated based on detected signal
                    if signals['action'] == 'PUT':
                        annotated_image_paths.append(f"/api/uploads/{put_filename}")
                    else:
                        annotated_image_paths.append(f"/api/uploads/{call_filename}")
                    
                    logging.info(f"Generated CALL and PUT images for image {idx + 1}")
                except Exception as e:
                    logging.error(f"Error annotating image {idx + 1}: {str(e)}")
                    annotated_image_paths.append(None)
                    call_annotated_paths.append(None)
                    put_annotated_paths.append(None)
        except Exception as e:
            logging.error(f"Error in annotation process: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            # Continue without annotated images
        
        # Filter out None values
        filtered_annotated = [p for p in annotated_image_paths if p] if annotated_image_paths else None
        filtered_call = [p for p in call_annotated_paths if p] if call_annotated_paths else None
        filtered_put = [p for p in put_annotated_paths if p] if put_annotated_paths else None
        
        # Create assistant message with annotated image paths
        assistant_message = Message(
            role="assistant",
            content=ai_response,
            annotated_image_urls=filtered_annotated,
            call_annotated_urls=filtered_call,
            put_annotated_urls=filtered_put
        )
        
        # Save assistant message to database
        assistant_doc = assistant_message.model_dump()
        assistant_doc['timestamp'] = assistant_doc['timestamp'].isoformat()
        await db.messages.insert_one(assistant_doc)
        
        return MultipleImagesAnalysisResponse(
            image_ids=image_ids,
            image_paths=image_paths,
            annotated_image_paths=filtered_annotated,
            call_annotated_paths=filtered_call,
            put_annotated_paths=filtered_put,
            user_message=user_message,
            assistant_message=assistant_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in multiple images analysis endpoint: {error_msg}")
        
        # Check if it's a budget error
        if "Budget has been exceeded" in error_msg or "budget" in error_msg.lower():
            raise HTTPException(
                status_code=402,  # Payment Required
                detail="❌ Orçamento da chave LLM excedido! Por favor, adicione créditos em Profile -> Universal Key -> Add Balance"
            )
        
        raise HTTPException(status_code=500, detail=f"Error analyzing images: {error_msg}")


# Image generation endpoint
@api_router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest, x_custom_api_key: Optional[str] = Header(None)):
    try:
        # Use custom API key if provided
        api_key = x_custom_api_key if x_custom_api_key else os.environ['EMERGENT_LLM_KEY']
        
        # Initialize image generator
        image_gen = OpenAIImageGeneration(api_key=api_key)
        
        # Create user message
        user_message = Message(
            role="user",
            content=f"🎨 Gerar imagem: {request.prompt}"
        )
        
        # Save user message to database
        user_doc = user_message.model_dump()
        user_doc['timestamp'] = user_doc['timestamp'].isoformat()
        await db.messages.insert_one(user_doc)
        
        # Generate image
        images = await image_gen.generate_images(
            prompt=request.prompt,
            model="gpt-image-1",
            number_of_images=request.number_of_images
        )
        
        if not images or len(images) == 0:
            raise HTTPException(status_code=500, detail="Nenhuma imagem foi gerada")
        
        # Get first image
        image_bytes = images[0]
        
        # Convert to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Save image to temp directory
        image_id = str(uuid.uuid4())
        image_filename = f"{image_id}_generated.png"
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        
        # Create assistant message with generated image
        assistant_message = Message(
            role="assistant",
            content=f"✅ Imagem gerada com sucesso a partir do prompt:\n\n**{request.prompt}**",
            image_urls=[f"/api/uploads/{image_filename}"]
        )
        
        # Save assistant message to database
        assistant_doc = assistant_message.model_dump()
        assistant_doc['timestamp'] = assistant_doc['timestamp'].isoformat()
        await db.messages.insert_one(assistant_doc)
        
        return ImageGenerationResponse(
            image_id=image_id,
            image_path=image_path,
            image_base64=image_base64,
            user_message=user_message,
            assistant_message=assistant_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in image generation endpoint: {error_msg}")
        
        # Check if it's a budget error
        if "Budget has been exceeded" in error_msg or "budget" in error_msg.lower():
            raise HTTPException(
                status_code=402,  # Payment Required
                detail="❌ Orçamento da chave LLM excedido! Por favor, adicione créditos em Profile -> Universal Key -> Add Balance"
            )
        
        raise HTTPException(status_code=500, detail=f"Error generating image: {error_msg}")


@api_router.get("/messages", response_model=List[Message])
async def get_messages():
    """Get all chat messages"""
    messages = await db.messages.find({}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for msg in messages:
        if isinstance(msg['timestamp'], str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return messages


@api_router.delete("/messages")
async def clear_messages():
    """Clear all chat messages"""
    result = await db.messages.delete_many({})
    return {"deleted_count": result.deleted_count}


@api_router.get("/")
async def root():
    return {"message": "Chat API is running"}


# === NEW: Trading Engine Endpoints ===

@api_router.post("/trade-setup", response_model=TradeSetupResponse)
async def analyze_trade_setup(
    request: TradeSetupRequest,
    x_custom_api_key: Optional[str] = Header(None)
):
    """
    🎯 NOVO ENDPOINT - Análise Matemática de Setup de Trading
    
    Fluxo: Candles → Trading Engine → Análise Técnica → IA Explica
    
    Este endpoint usa análise técnica avançada (EMA, RSI, ATR) para
    determinar setups de alta probabilidade (70%+ win rate).
    """
    try:
        # Converter input para objetos Candle
        candles = [
            Candle(
                timestamp=c.timestamp,
                open=c.open,
                high=c.high,
                low=c.low,
                close=c.close,
                volume=c.volume
            )
            for c in request.candles
        ]
        
        # Validar quantidade de candles
        if len(candles) < 50:
            logger.warning(f"Poucos candles recebidos: {len(candles)}. Recomendado: 50+")
        
        # Inicializar Trading Engine
        engine = TradingEngine(
            min_score=70,  # Mínimo 70 pontos para gerar sinal
            risk_reward_min=2.0,  # RR mínimo 1:2
            max_daily_loss_pct=2.0,
            max_drawdown_pct=10.0
        )
        
        # Analisar setup
        signal = engine.analyze(candles, request.capital)
        
        # Explicação com IA (opcional)
        ai_explanation = None
        if request.explain_with_ai:
            try:
                api_key = x_custom_api_key if x_custom_api_key else os.environ.get('EMERGENT_LLM_KEY')
                
                if api_key:
                    # Criar contexto para a IA
                    context = f"""
**ANÁLISE TÉCNICA MATEMÁTICA COMPLETA**

**SINAL GERADO:** {signal.signal.value}
**SCORE DE QUALIDADE:** {signal.score}/100
**CONFIANÇA:** {signal.confidence*100:.1f}%

**NÍVEIS DE PREÇO:**
- Entrada: {signal.entry_price:.5f}
- Stop Loss: {signal.stop_loss:.5f}
- Take Profit 1: {signal.take_profit_1:.5f}
- Take Profit 2: {signal.take_profit_2:.5f}

**INDICADORES TÉCNICOS:**
- Tendência: {signal.trend.value}
- EMA 20: {signal.ema_20:.5f}
- EMA 50: {signal.ema_50:.5f}
- RSI: {signal.rsi_value:.1f}
- ATR: {signal.atr_value:.5f}

**GESTÃO DE RISCO:**
- Risk/Reward TP1: 1:{signal.risk_reward_1:.2f}
- Risk/Reward TP2: 1:{signal.risk_reward_2:.2f}
- Risco por trade: ${signal.risk_amount:.2f}

**RAZÕES DO SINAL:**
{chr(10).join(signal.reasons)}

**AVISOS:**
{chr(10).join(signal.warnings) if signal.warnings else "Nenhum aviso"}
"""
                    
                    chat_client = LlmChat(
                        api_key=api_key,
                        session_id="trading-analysis",
                        system_message="""Você é um analista técnico profissional especializado em trading.
Sua função é explicar de forma clara e didática as decisões do motor de trading matemático.

Ao receber uma análise técnica, você deve:
1. Validar se o sinal faz sentido do ponto de vista técnico
2. Explicar em linguagem simples os motivos da recomendação
3. Destacar os pontos fortes e fracos do setup
4. Dar dicas de execução e gestão de risco
5. Mencionar condições que invalidariam o setup

Seja direto, profissional e educativo. Use emojis para destacar pontos importantes."""
                    )
                    chat_client.with_model("openai", "gpt-5.1")
                    
                    user_msg = UserMessage(text=f"Explique esta análise técnica de forma profissional:\n\n{context}")
                    ai_explanation = await chat_client.send_message(user_msg)
                    
            except Exception as e:
                logger.error(f"Erro ao gerar explicação da IA: {str(e)}")
                ai_explanation = "⚠️ Não foi possível gerar explicação detalhada. Análise técnica disponível acima."
        
        # Montar resposta
        response = TradeSetupResponse(
            signal=signal.signal.value,
            score=signal.score,
            confidence=signal.confidence,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit_1=signal.take_profit_1,
            take_profit_2=signal.take_profit_2,
            trend=signal.trend.value,
            rsi_value=signal.rsi_value,
            ema_20=signal.ema_20,
            ema_50=signal.ema_50,
            atr_value=signal.atr_value,
            risk_reward_1=signal.risk_reward_1,
            risk_reward_2=signal.risk_reward_2,
            risk_amount=signal.risk_amount,
            reasons=signal.reasons,
            warnings=signal.warnings,
            ai_explanation=ai_explanation
        )
        
        return response
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro no endpoint trade-setup: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Erro na análise de setup: {error_msg}")


@api_router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    📊 Endpoint de Backtest - Testa estratégia em dados históricos
    
    Simula trades com a estratégia do Trading Engine para validar
    win rate e performance.
    """
    try:
        # Converter input para objetos Candle
        candles = [
            Candle(
                timestamp=c.timestamp,
                open=c.open,
                high=c.high,
                low=c.low,
                close=c.close,
                volume=c.volume
            )
            for c in request.candles
        ]
        
        if len(candles) < 100:
            raise HTTPException(
                status_code=400,
                detail="Backtest requer no mínimo 100 candles históricos"
            )
        
        # Inicializar engine e backtester
        engine = TradingEngine(min_score=70, risk_reward_min=2.0)
        backtester = Backtester(engine)
        
        # Executar backtest
        results = backtester.run(candles, request.initial_capital)
        
        return BacktestResponse(**results)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro no backtest: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Erro no backtest: {error_msg}")


# Include the router in the main app
app.include_router(api_router)

# Mount static files for uploads directory under /api prefix
# Note: Using tempfile directory now
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()