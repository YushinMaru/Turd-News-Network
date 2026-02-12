"""
Sentiment Analysis Module - Financial sentiment scoring using FinBERT with VADER fallback
"""

from typing import Dict, List, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

from config import (
    ENABLE_FINBERT, FINBERT_MODEL, FINBERT_DEVICE,
    FINBERT_MAX_LENGTH, FINBERT_BATCH_SIZE
)

# Attempt to load FinBERT dependencies
_finbert_available = False
try:
    if ENABLE_FINBERT:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        _finbert_available = True
except ImportError:
    pass


class SentimentAnalyzer:
    """Analyzes sentiment of DD posts and Reddit comments using FinBERT (primary) or VADER (fallback)"""

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.finbert_model = None
        self.finbert_tokenizer = None
        self.use_finbert = False

        if _finbert_available and ENABLE_FINBERT:
            try:
                print("[i] Loading FinBERT model... (first run downloads ~400MB)")
                self.finbert_tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL)
                self.finbert_model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL)
                self.finbert_model.to(FINBERT_DEVICE)
                self.finbert_model.eval()
                self.use_finbert = True
                print("[i] FinBERT loaded successfully")
            except Exception as e:
                print(f"[!] FinBERT failed to load, falling back to VADER: {e}")
                self.use_finbert = False

        if not self.use_finbert:
            if ENABLE_FINBERT:
                print("[i] Using VADER sentiment (install transformers + torch for FinBERT)")
            else:
                print("[i] Using VADER sentiment (FinBERT disabled in config)")

        # Financial-specific sentiment keywords (used by both engines)
        self.bullish_keywords = [
            'moon', 'rocket', 'bull', 'calls', 'long', 'buy', 'undervalued',
            'growth', 'catalyst', 'breakout', 'squeeze', 'tendies', 'gains',
            'upside', 'opportunity', 'strong', 'bullish', 'rally', 'surge'
        ]

        self.bearish_keywords = [
            'crash', 'bear', 'puts', 'short', 'sell', 'overvalued', 'dump',
            'decline', 'drop', 'downside', 'risk', 'loss', 'bearish', 'falling',
            'bubble', 'worthless', 'bagholding', 'rug pull', 'scam'
        ]

    # ------------------------------------------------------------------
    # FinBERT internals
    # ------------------------------------------------------------------

    def _finbert_score(self, text: str) -> Dict:
        """
        Run FinBERT on a single text string.
        Returns {'positive': float, 'negative': float, 'neutral': float, 'compound': float}
        where compound is mapped to the -1..1 range for compatibility with VADER output.
        """
        text = text[:2000]  # truncate very long texts before tokenization
        inputs = self.finbert_tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=FINBERT_MAX_LENGTH,
            padding=True
        )
        inputs = {k: v.to(FINBERT_DEVICE) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.finbert_model(**inputs)

        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

        # FinBERT label order: positive, negative, neutral
        positive = probs[0].item()
        negative = probs[1].item()
        neutral = probs[2].item()

        # Map to a compound score compatible with VADER's -1..1 range
        compound = positive - negative  # ranges from -1 to 1

        return {
            'positive': round(positive, 4),
            'negative': round(negative, 4),
            'neutral': round(neutral, 4),
            'compound': round(compound, 4)
        }

    def _finbert_batch_score(self, texts: List[str]) -> List[Dict]:
        """Run FinBERT on a batch of texts."""
        results = []
        for i in range(0, len(texts), FINBERT_BATCH_SIZE):
            batch = texts[i:i + FINBERT_BATCH_SIZE]
            batch = [t[:2000] for t in batch]

            inputs = self.finbert_tokenizer(
                batch,
                return_tensors='pt',
                truncation=True,
                max_length=FINBERT_MAX_LENGTH,
                padding=True
            )
            inputs = {k: v.to(FINBERT_DEVICE) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.finbert_model(**inputs)

            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

            for j in range(len(batch)):
                positive = probs[j][0].item()
                negative = probs[j][1].item()
                neutral = probs[j][2].item()
                compound = positive - negative
                results.append({
                    'positive': round(positive, 4),
                    'negative': round(negative, 4),
                    'neutral': round(neutral, 4),
                    'compound': round(compound, 4)
                })
        return results

    # ------------------------------------------------------------------
    # Public API (same interface as before)
    # ------------------------------------------------------------------

    def analyze_post_sentiment(self, title: str, content: str) -> Dict:
        """
        Analyze sentiment of DD post.

        Returns:
            {
                'overall_score': float (-1 to 1),
                'sentiment': str (BULLISH/BEARISH/NEUTRAL),
                'confidence': float (0 to 1),
                'title_sentiment': float,
                'content_sentiment': float,
                'keyword_signals': dict,
                'engine': str ('finbert' or 'vader'),
                'breakdown': {'positive': float, 'negative': float, 'neutral': float}
            }
        """
        title_clean = self._clean_text(title)
        content_clean = self._clean_text(content)

        keyword_signals = self._analyze_keywords(title_clean + ' ' + content_clean)

        if self.use_finbert:
            return self._analyze_post_finbert(title_clean, content_clean, keyword_signals)
        else:
            return self._analyze_post_vader(title_clean, content_clean, keyword_signals)

    def _analyze_post_finbert(self, title_clean: str, content_clean: str, keyword_signals: Dict) -> Dict:
        title_fb = self._finbert_score(title_clean) if title_clean.strip() else {'compound': 0, 'positive': 0, 'negative': 0, 'neutral': 1}

        # For long content, analyze in chunks and average
        if len(content_clean) > 1500:
            chunks = self._split_into_chunks(content_clean, 1500)
            chunk_scores = [self._finbert_score(c) for c in chunks]
            content_fb = {
                'compound': sum(s['compound'] for s in chunk_scores) / len(chunk_scores),
                'positive': sum(s['positive'] for s in chunk_scores) / len(chunk_scores),
                'negative': sum(s['negative'] for s in chunk_scores) / len(chunk_scores),
                'neutral': sum(s['neutral'] for s in chunk_scores) / len(chunk_scores),
            }
        elif content_clean.strip():
            content_fb = self._finbert_score(content_clean)
        else:
            content_fb = {'compound': 0, 'positive': 0, 'negative': 0, 'neutral': 1}

        # Weighted: title 30%, content 50%, keywords 20%
        overall_score = (
            title_fb['compound'] * 0.3 +
            content_fb['compound'] * 0.5 +
            keyword_signals['score'] * 0.2
        )

        sentiment, confidence = self._classify_sentiment(overall_score, content_fb)

        return {
            'overall_score': round(overall_score, 3),
            'sentiment': sentiment,
            'confidence': round(confidence, 3),
            'title_sentiment': round(title_fb['compound'], 3),
            'content_sentiment': round(content_fb['compound'], 3),
            'keyword_signals': keyword_signals,
            'engine': 'finbert',
            'breakdown': {
                'positive': round(content_fb['positive'], 3),
                'negative': round(content_fb['negative'], 3),
                'neutral': round(content_fb['neutral'], 3)
            }
        }

    def _analyze_post_vader(self, title_clean: str, content_clean: str, keyword_signals: Dict) -> Dict:
        title_scores = self.vader.polarity_scores(title_clean)
        content_scores = self.vader.polarity_scores(content_clean)

        overall_score = (
            title_scores['compound'] * 0.3 +
            content_scores['compound'] * 0.5 +
            keyword_signals['score'] * 0.2
        )

        if overall_score >= 0.25:
            sentiment = 'BULLISH'
        elif overall_score <= -0.25:
            sentiment = 'BEARISH'
        else:
            sentiment = 'NEUTRAL'

        confidence = min(abs(overall_score), 1.0)

        return {
            'overall_score': round(overall_score, 3),
            'sentiment': sentiment,
            'confidence': round(confidence, 3),
            'title_sentiment': round(title_scores['compound'], 3),
            'content_sentiment': round(content_scores['compound'], 3),
            'keyword_signals': keyword_signals,
            'engine': 'vader',
            'breakdown': {
                'positive': round(content_scores['pos'], 3),
                'negative': round(content_scores['neg'], 3),
                'neutral': round(content_scores['neu'], 3)
            }
        }

    def analyze_comments_sentiment(self, comments: List[str], limit: int = 50) -> Dict:
        """
        Analyze sentiment of comments.

        Returns:
            {
                'avg_sentiment': float,
                'bullish_pct': float,
                'bearish_pct': float,
                'neutral_pct': float,
                'total_analyzed': int,
                'crowd_consensus': str,
                'engine': str
            }
        """
        if not comments:
            return self._empty_comment_sentiment()

        cleaned = []
        for comment in comments[:limit]:
            c = self._clean_text(comment)
            if len(c) >= 10:
                cleaned.append(c)

        if not cleaned:
            return self._empty_comment_sentiment()

        if self.use_finbert:
            return self._analyze_comments_finbert(cleaned)
        else:
            return self._analyze_comments_vader(cleaned)

    def _analyze_comments_finbert(self, cleaned_comments: List[str]) -> Dict:
        scores = self._finbert_batch_score(cleaned_comments)

        sentiments = [s['compound'] for s in scores]
        bullish_count = sum(1 for s in sentiments if s >= 0.2)
        bearish_count = sum(1 for s in sentiments if s <= -0.2)
        neutral_count = len(sentiments) - bullish_count - bearish_count

        total = len(sentiments)
        avg_sentiment = sum(sentiments) / total

        bullish_pct = (bullish_count / total) * 100
        bearish_pct = (bearish_count / total) * 100
        neutral_pct = (neutral_count / total) * 100

        consensus = self._determine_consensus(bullish_pct, bearish_pct)

        return {
            'avg_sentiment': round(avg_sentiment, 3),
            'bullish_pct': round(bullish_pct, 1),
            'bearish_pct': round(bearish_pct, 1),
            'neutral_pct': round(neutral_pct, 1),
            'total_analyzed': total,
            'crowd_consensus': consensus,
            'engine': 'finbert'
        }

    def _analyze_comments_vader(self, cleaned_comments: List[str]) -> Dict:
        sentiments = []
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        for comment in cleaned_comments:
            score = self.vader.polarity_scores(comment)['compound']
            sentiments.append(score)

            if score >= 0.2:
                bullish_count += 1
            elif score <= -0.2:
                bearish_count += 1
            else:
                neutral_count += 1

        total = len(sentiments)
        avg_sentiment = sum(sentiments) / total

        bullish_pct = (bullish_count / total) * 100
        bearish_pct = (bearish_count / total) * 100
        neutral_pct = (neutral_count / total) * 100

        consensus = self._determine_consensus(bullish_pct, bearish_pct)

        return {
            'avg_sentiment': round(avg_sentiment, 3),
            'bullish_pct': round(bullish_pct, 1),
            'bearish_pct': round(bearish_pct, 1),
            'neutral_pct': round(neutral_pct, 1),
            'total_analyzed': total,
            'crowd_consensus': consensus,
            'engine': 'vader'
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _classify_sentiment(self, overall_score: float, fb_scores: Dict) -> tuple:
        """Classify sentiment and compute confidence from FinBERT output."""
        if overall_score >= 0.20:
            sentiment = 'BULLISH'
        elif overall_score <= -0.20:
            sentiment = 'BEARISH'
        else:
            sentiment = 'NEUTRAL'

        # Confidence: use the dominant probability from FinBERT breakdown
        dominant_prob = max(fb_scores.get('positive', 0), fb_scores.get('negative', 0), fb_scores.get('neutral', 0))
        # Blend model confidence with score magnitude
        confidence = min((dominant_prob * 0.6 + abs(overall_score) * 0.4), 1.0)

        return sentiment, confidence

    def _determine_consensus(self, bullish_pct: float, bearish_pct: float) -> str:
        """Determine crowd consensus label."""
        if bullish_pct > 50:
            return 'BULLISH'
        elif bearish_pct > 50:
            return 'BEARISH'
        elif bullish_pct > bearish_pct:
            return 'CAUTIOUSLY_BULLISH'
        elif bearish_pct > bullish_pct:
            return 'CAUTIOUSLY_BEARISH'
        else:
            return 'MIXED'

    def _split_into_chunks(self, text: str, max_chars: int) -> List[str]:
        """Split text into sentence-aware chunks for FinBERT processing."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ''
        for sentence in sentences:
            if len(current) + len(sentence) + 1 > max_chars and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = current + ' ' + sentence if current else sentence
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [text[:max_chars]]

    def _analyze_keywords(self, text: str) -> Dict:
        """Analyze financial-specific keywords."""
        text_lower = text.lower()

        bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)

        total_keywords = bullish_count + bearish_count

        if total_keywords == 0:
            score = 0.0
            signal = 'NEUTRAL'
        else:
            score = (bullish_count - bearish_count) / max(total_keywords, 1)
            if score > 0.3:
                signal = 'BULLISH'
            elif score < -0.3:
                signal = 'BEARISH'
            else:
                signal = 'NEUTRAL'

        return {
            'score': score,
            'signal': signal,
            'bullish_keywords': bullish_count,
            'bearish_keywords': bearish_count
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'[^\w\s.,!?]', ' ', text)
        text = ' '.join(text.split())
        return text

    def _empty_comment_sentiment(self) -> Dict:
        """Return empty sentiment result."""
        return {
            'avg_sentiment': 0.0,
            'bullish_pct': 0.0,
            'bearish_pct': 0.0,
            'neutral_pct': 0.0,
            'total_analyzed': 0,
            'crowd_consensus': 'NO_DATA',
            'engine': 'finbert' if self.use_finbert else 'vader'
        }

    def get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment."""
        emoji_map = {
            'BULLISH': '\U0001f7e2',
            'BEARISH': '\U0001f534',
            'NEUTRAL': '\U0001f7e1',
            'CAUTIOUSLY_BULLISH': '\U0001f7e2\u26a0\ufe0f',
            'CAUTIOUSLY_BEARISH': '\U0001f534\u26a0\ufe0f',
            'MIXED': '\U0001f914',
            'NO_DATA': '\u2753'
        }
        return emoji_map.get(sentiment, '\u2753')
