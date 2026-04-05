import os
from typing import Dict, List, Union, Optional
import json
from loguru import logger
# IMPORTS REMOVED: agno.agent, get_model
# Internal LLM logic has been removed to delegate analysis to the calling Agent.
from .database_manager import DatabaseManager

# 从环境变量读取默认情绪分析模式
DEFAULT_SENTIMENT_MODE = os.getenv("SENTIMENT_MODE", "auto")  # auto, bert, llm

# Crypto pair aliases: maps canonical symbol to a list of search keywords
CRYPTO_SYMBOL_ALIASES: Dict[str, List[str]] = {
    "TRYUSDT": ["TRYUSDT", "TRY/USDT", "TRY-USDT", "Turkish Lira USDT", "土耳其里拉 USDT"],
    "TRYUSDC": ["TRYUSDC", "TRY/USDC", "TRY-USDC", "Turkish Lira USDC", "土耳其里拉 USDC"],
}

class SentimentTools:
    """
    情绪分析工具 - 支持 LLM 和 BERT 两种模式
    
    模式说明:
    - "auto": 自动选择，优先使用 BERT（速度快），不可用时回退到 LLM
    - "bert": 强制使用 BERT 模型（需要 transformers 库）
    - "llm": 强制使用 LLM（更准确但较慢）
    
    可通过环境变量 SENTIMENT_MODE 设置默认模式。
    """
    
    def __init__(self, db: DatabaseManager, mode: Optional[str] = None):
        """
        初始化情绪分析工具。
        
        Args:
            db: 数据库管理器实例
            mode: 分析模式，可选 "auto", "bert", "llm"。None 则使用环境变量默认值。
            model_provider: LLM 提供商，如 "openai", "ust", "deepseek"
            model_id: 模型标识符
        """
        self.db = db
        self.mode = mode or DEFAULT_SENTIMENT_MODE
        self.bert_pipeline = None
        
        # LLM initialization removed. Agent should perform analysis if needed.

        # Initialize BERT if needed
        if self.mode in ["bert", "auto"]:
            try:
                from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
                from transformers.utils import logging as transformers_logging
                transformers_logging.set_verbosity_error() # 减少冗余日志
                
                bert_model = os.getenv("BERT_SENTIMENT_MODEL", "uer/roberta-base-finetuned-chinanews-chinese")
                
                # 优先使用本地缓存
                try:
                    tokenizer = AutoTokenizer.from_pretrained(bert_model, local_files_only=True)
                    model = AutoModelForSequenceClassification.from_pretrained(bert_model, local_files_only=True)
                    
                    self.bert_pipeline = pipeline(
                        "sentiment-analysis", 
                        model=model,
                        tokenizer=tokenizer,
                        device=-1
                    )
                    logger.info(f"✅ BERT pipeline loaded from local cache: {bert_model}")
                except (OSError, ValueError, ImportError):
                    # 本地没有，则从网络下载
                    logger.info(f"📡 Downloading BERT model: {bert_model}...")
                    tokenizer = AutoTokenizer.from_pretrained(bert_model)
                    model = AutoModelForSequenceClassification.from_pretrained(bert_model)
                    
                    self.bert_pipeline = pipeline(
                        "sentiment-analysis", 
                        model=model,
                        tokenizer=tokenizer,
                        device=-1
                    )
                    logger.info(f"✅ BERT Sentiment pipeline ({bert_model}) initialized.")
            except ImportError:
                logger.warning("Transformers library not installed. BERT sentiment analysis disabled.")
            except Exception as e:
                if self.mode == "bert":
                    logger.error(f"BERT mode requested but failed: {e}")
                else:
                    logger.warning(f"BERT unavailable, using LLM only. Error: {e}")
                self.bert_pipeline = None


    def analyze_sentiment(self, text: str) -> Dict[str, Union[float, str]]:
        """
        分析文本的情绪极性。仅支持 BERT 模式。
        如需 LLM 分析，请 Agent 按照 SKILL.md 中的 Prompt 自行执行。
        
        Args:
            text: 需要分析的文本内容。
        
        Returns:
            BERT 分析结果，或错误信息。
        """
        if self.bert_pipeline:
            results = self.analyze_sentiment_bert([text])
            return results[0] if results else {"score": 0.0, "label": "error"}
        else:
            return {
                "score": 0.0, 
                "label": "error", 
                "reason": "BERT pipeline not initialized. For LLM analysis, please manually execute the prompt in SKILL.md."
            }

    def update_single_news_sentiment(self, news_id: Union[str, int], score: float, reason: str = "") -> bool:
        """
        允许 Agent 将手动分析的结果保存到数据库。
        
        Args:
            news_id: 新闻 ID
            score: -1.0 到 1.0
            reason: 分析理由
            
        Returns:
            Success bool
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE daily_news 
                SET sentiment_score = ?, meta_data = json_set(COALESCE(meta_data, '{}'), '$.sentiment_reason', ?)
                WHERE id = ?
            """, (score, reason, news_id))
            self.db.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update sentiment for {news_id}: {e}")
            return False

    def analyze_sentiment_bert(self, texts: List[str]) -> List[Dict]:
        """
        使用 BERT 进行批量高速情绪分析。
        
        Args:
            texts: 需要分析的文本列表。
        
        Returns:
            与输入列表等长的分析结果列表。
        """
        if not self.bert_pipeline:
            return [{"score": 0.0, "label": "error", "reason": "BERT not available"}] * len(texts)
        
        try:
            results = self.bert_pipeline(texts, truncation=True, max_length=512)
            processed = []
            for r in results:
                label = r['label'].lower()
                score = r['score']
                
                # 标准化不同模型的标签格式
                if 'negative' in label or 'neg' in label:
                    score = -score
                elif 'neutral' in label or 'neu' in label:
                    score = 0.0
                
                processed.append({
                    "score": float(round(score, 3)),
                    "label": "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral"),
                    "reason": "BERT automated analysis"
                })
            return processed
        except Exception as e:
            logger.error(f"BERT analysis failed: {e}")
            return [{"score": 0.0, "label": "error", "reason": str(e)}] * len(texts)

    def get_symbol_sentiment(self, symbol: str, days: int = 7, limit: int = 50) -> Dict:
        """
        Aggregate sentiment from DB news related to a specific symbol or crypto pair.

        Supports canonical crypto symbols (e.g. "TRYUSDT", "TRYUSDC") using
        CRYPTO_SYMBOL_ALIASES for broader keyword matching.

        Args:
            symbol: Ticker or crypto pair (e.g. "TRYUSDT", "TRYUSDC", "BTC").
            days:   How many days back to search (passed through to news query).
            limit:  Max news items to consider.

        Returns:
            Dict with keys:
              - symbol (str)
              - count (int): total matched news items
              - scored_count (int): items that have a sentiment_score
              - avg_score (float | None): average sentiment score
              - label (str): "positive" | "negative" | "neutral" | "unknown"
              - label_distribution (dict): counts per label
              - items (list): raw matched news dicts
        """
        keywords = CRYPTO_SYMBOL_ALIASES.get(symbol.upper(), [symbol])

        matched: List[Dict] = []
        seen_ids = set()
        for kw in keywords:
            results = self.db.search_local_news(kw, limit=limit)
            for item in results:
                item_id = item.get("id")
                if item_id not in seen_ids:
                    seen_ids.add(item_id)
                    matched.append(item)

        scored = [m for m in matched if m.get("sentiment_score") is not None]
        scores = [m["sentiment_score"] for m in scored]

        avg_score: Optional[float] = round(sum(scores) / len(scores), 4) if scores else None

        dist: Dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0}
        for s in scores:
            if s > 0.1:
                dist["positive"] += 1
            elif s < -0.1:
                dist["negative"] += 1
            else:
                dist["neutral"] += 1

        if avg_score is None:
            label = "unknown"
        elif avg_score > 0.1:
            label = "positive"
        elif avg_score < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return {
            "symbol": symbol.upper(),
            "count": len(matched),
            "scored_count": len(scored),
            "avg_score": avg_score,
            "label": label,
            "label_distribution": dist,
            "items": matched,
        }

    def batch_update_news_sentiment(self, source: Optional[str] = None, limit: int = 50, use_bert: Optional[bool] = None):
        """
        批量更新数据库中新闻的情绪分数。
        
        Args:
            source: 筛选特定新闻源，如 "wallstreetcn"。None 则处理所有来源。
            limit: 最多处理的新闻数量。
            use_bert: 是否使用 BERT。None 则根据初始化模式自动决定。
        
        Returns:
            成功更新的新闻数量。
        """
        news_items = self.db.get_daily_news(source=source, limit=limit)
        to_analyze = [item for item in news_items if not item.get('sentiment_score')]
        
        if not to_analyze:
            return 0

        updated_count = 0
        cursor = self.db.conn.cursor()

        # 决定使用哪种方法
        if self.bert_pipeline:
            logger.info(f"🚀 Using BERT for batch analysis of {len(to_analyze)} items...")
            titles = [item['title'] for item in to_analyze]
            results = self.analyze_sentiment_bert(titles)
            
            for item, analysis in zip(to_analyze, results):
                cursor.execute("""
                    UPDATE daily_news 
                    SET sentiment_score = ?, meta_data = json_set(COALESCE(meta_data, '{}'), '$.sentiment_reason', ?)
                    WHERE id = ?
                """, (analysis['score'], analysis['reason'], item['id']))
                updated_count += 1
        else:
            logger.warning("BERT pipeline not available. Batch update skipped. Please use Agentic analysis for high-quality results.")
        
        self.db.conn.commit()
        return updated_count

