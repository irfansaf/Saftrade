import json
import logging
import requests
from typing import Dict, Any, Optional
from config.settings import DEEPSEEK_API_KEY

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = "https://api.deepseek.com/v1/chat/completions" # Standard OpenAI-compatible endpoint for DeepSeek usually

    def analyze_signal(self, ticker: str, technical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send technical data to DeepSeek AI for validation and trade planning.
        """
        if not self.api_key:
            logger.warning("DeepSeek API Key missing. Skipping AI validation.")
            return {"valid": True, "reason": "AI Skipped (No Key)", "plan": {}}

        prompt = self._construct_prompt(ticker, technical_data)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a Senior Hedge Fund Analyst. You are skeptical, risk-averse, and only approve high-probability setups."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"} # Ensure JSON output if supported, else rely on prompt
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse JSON from content
            try:
                ai_analysis = json.loads(content)
                return ai_analysis
            except json.JSONDecodeError:
                logger.error("Failed to parse AI response as JSON")
                return {"valid": False, "reason": "AI JSON Parse Error", "raw": content}

        except Exception as e:
            logger.error(f"AI Request Failed: {e}")
            return {"valid": False, "reason": f"AI Error: {e}"}

    def _construct_prompt(self, ticker: str, data: Dict[str, Any]) -> str:
        return f"""
        Analyze this trading setup for {ticker} (Indonesian Stock).
        
        Signal Type: {data.get('signal_type', 'Standard Swing')}
        
        Technical Data:
        - Close: {data['close']}
        - EMA200: {data['indicators']['ema_200']} (Trend: {'Up' if data['signals']['uptrend'] else 'Down'})
        - RSI(14): {data['indicators']['rsi']}
        - ATR: {data['indicators']['atr']}
        - Volume Ratio: {data['indicators']['volume_ratio']}x vs Avg (Breakout: {data['signals']['vol_breakout']})
        - Price Change: {data['indicators'].get('price_change', 0) * 100:.2f}%
        
        Task:
        1. Validate the setup. 
           - If "Volatility Breakout": 
             * ACCEPT the trade even if it looks risky/overbought, UNLESS it is essentially a guaranteed loss (e.g. falling knife).
             * If risky, set Valid=True but include "WARNING: High Risk" in the analysis.
             * Focus on managing the risk via Stop Loss rather than rejecting the trade.
           - If "Trend Swing": Is the trend healthy?
        2. If Valid == true, provide a Trade Plan.
           - Entry: Current Close
           - Stop Loss: 
             * For Breakouts: TIGHT SL (e.g., Low of Day or -3% from entry).
             * For Swing: ATR-based (2x ATR).
           - Take Profit: 1:2 Risk-Reward minimum.
        
        Output JSON Format ONLY:
        {{
            "valid": boolean,
            "analysis": "Short concise reasoning (max 2 sentences). Start with 'WARNING:' if high risk.",
            "trade_plan": {{
                "entry": float,
                "stop_loss": float,
                "take_profit": float,
                "risk_reward": string
            }}
        }}
        """
