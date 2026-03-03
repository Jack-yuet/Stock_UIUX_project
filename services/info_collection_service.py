import yfinance as yf
from stock_mapping import add_stock_suffix
from utils.stock_mapping import stock_mapping
import requests
import json
import re

# Ollama API Endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"
# Model Name (can be configured)
OLLAMA_MODEL = "qwen2.5:7b" # Or qwen:14b, qwen:7b etc.

def get_stock_info_links(stock_code):
    """
    Generate authoritative information source links for a stock
    """
    try:
        # Get stock info
        full_code = add_stock_suffix(stock_code)
        stock_name = stock_mapping.get_stock_name(stock_code)
        
        # Base code (remove suffix)
        base_code = stock_code.split('.')[0] if '.' in stock_code else stock_code
        
        # Determine market type
        market = 'unknown'
        if full_code.endswith('.SS'):
            market = 'sh' # Shanghai
        elif full_code.endswith('.SZ'):
            market = 'sz' # Shenzhen
        elif full_code.endswith('.BJ'):
            market = 'bj' # Beijing
        elif full_code.endswith('.HK'):
            market = 'hk' # Hong Kong
        else:
            market = 'us' # US
        
        links = {
            "top_tier": [], # Top Authority: Regulators & Exchanges
            "high_tier": [], # High Authority: Official Media & Self-regulation
            "pro_tier": [], # Professional Authority: Research Platforms
            "media_tier": [], # Industry Authority: Financial Media
            "community_tier": [] # Social Media & Communities
        }
        
        # 1. Top Authority: Regulators & Exchanges
        if market in ['sh', 'sz', 'bj']:
            # CSRC
            links["top_tier"].append({
                "name": "CSRC (China Securities Regulatory Commission)",
                "desc": "Policies, regulations, supervision, penalties",
                "url": "http://www.csrc.gov.cn/pub/newsite/"
            })
            # CNINFO
            links["top_tier"].append({
                "name": "CNINFO (Official Disclosure)",
                "desc": "Designated disclosure platform, market-wide announcements",
                "url": f"http://www.cninfo.com.cn/new/fulltextSearch?notautosubmit=&keyWord={base_code}"
            })
            
            if market == 'sh':
                links["top_tier"].append({
                    "name": "SSE Official Website",
                    "desc": "Real-time announcements, inquiries, regulatory measures",
                    "url": f"http://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?companyCode={base_code}"
                })
                # SSE E-Interactive
                links["community_tier"].append({
                    "name": "SSE E-Interactive",
                    "desc": "Direct Q&A between executives and investors",
                    "url": f"http://sns.sseinfo.com/company.do?stockcode={base_code}"
                })
            elif market == 'sz':
                links["top_tier"].append({
                    "name": "SZSE Official Website",
                    "desc": "Announcements, Easy IR Q&A",
                    "url": f"http://www.szse.cn/market/listed/info/index.html?code={base_code}"
                })
                # SZSE Easy IR
                links["community_tier"].append({
                    "name": "SZSE Easy IR",
                    "desc": "Direct Q&A between executives and investors",
                    "url": f"http://irm.cninfo.com.cn/ircs/company/companyDetail?stockcode={base_code}"
                })
            elif market == 'bj':
                links["top_tier"].append({
                    "name": "BSE Official Website",
                    "desc": "BSE company disclosures",
                    "url": f"https://www.bse.cn/disclosure/announcement/index.html"
                })

        # 2. High Authority: Official Media
        links["high_tier"].extend([
            {
                "name": "Securities Times",
                "desc": "Designated disclosure media, authoritative policy interpretation",
                "url": f"https://www.stcn.com/search/index.html?search_key={stock_name}"
            },
            {
                "name": "China Securities Journal",
                "desc": "Macro policies, industry analysis, company depth",
                "url": "https://www.cs.com.cn/"
            },
            {
                "name": "Shanghai Securities News",
                "desc": "Capital market authoritative reporting",
                "url": f"https://k.cnstock.com/k/search?k={stock_name}"
            }
        ])

        # 3. Professional Authority: Research Platforms
        if market in ['sh', 'sz', 'bj']:
            links["pro_tier"].extend([
                {
                    "name": "Eastmoney Research Center",
                    "desc": "Stock reports summary, filter by rating",
                    "url": f"https://data.eastmoney.com/report/{base_code}.html"
                },
                {
                    "name": "Sina Finance Reports",
                    "desc": "Institutional ratings and deep analysis",
                    "url": f"https://stock.finance.sina.com.cn/stock/go.php/vReport_List/kind/search/index.phtml?symbol={base_code}"
                },
                {
                    "name": "Hibor Research",
                    "desc": "Professional research report aggregation",
                    "url": f"http://www.hibor.com.cn/search_1_{stock_name}_1.html"
                }
            ])

        # 4. Industry Authority: Financial Media & Data
        if market in ['sh', 'sz', 'bj']:
            links["media_tier"].extend([
                {
                    "name": "Eastmoney Stock Forum",
                    "desc": "Quotes, news, capital flow",
                    "url": f"https://guba.eastmoney.com/list,{base_code}.html"
                },
                {
                    "name": "10jqka Finance",
                    "desc": "F10 data, financial analysis",
                    "url": f"http://stockpage.10jqka.com.cn/{base_code}/"
                },
                {
                    "name": "Xueqiu (Stock Page)",
                    "desc": "Investor depth analysis, research notes",
                    "url": f"https://xueqiu.com/S/{market.upper()}{base_code}"
                },
                {
                    "name": "Sina Finance (Stock)",
                    "desc": "7x24 news, announcements, reports",
                    "url": f"https://finance.sina.com.cn/realstock/company/{market}{base_code}/nc.shtml"
                }
            ])
            
        elif market == 'us':
            links["media_tier"].extend([
                {
                    "name": "Yahoo Finance",
                    "desc": "Real-time quotes and news",
                    "url": f"https://finance.yahoo.com/quote/{base_code}"
                },
                {
                    "name": "Xueqiu (US Stock)",
                    "desc": "Chinese community for US stocks",
                    "url": f"https://xueqiu.com/S/{base_code}"
                },
                {
                    "name": "Seeking Alpha",
                    "desc": "Deep US stock investment analysis",
                    "url": f"https://seekingalpha.com/symbol/{base_code}"
                }
            ])

        # 5. Third-party Data Services (General)
        links["community_tier"].extend([
            {
                "name": "Tianyancha",
                "desc": "Corporate structure, legal risks (Login required)",
                "url": f"https://www.tianyancha.com/search?key={stock_name}"
            },
            {
                "name": "Qichacha",
                "desc": "Enterprise credit information",
                "url": f"https://www.qcc.com/web/search?key={stock_name}"
            }
        ])

        return {
            "success": True,
            "stock_code": base_code,
            "stock_name": stock_name,
            "market": market,
            "links": links
        }

    except Exception as e:
        print(f"Failed to get info links: {e}")
        return {"success": False, "message": str(e)}

def _fetch_eastmoney_news(stock_code):
    """
    Fetch Eastmoney stock news (via public API)
    """
    try:
        # Eastmoney stock news API (Unofficial but common)
        # Handle prefix: 6->1, 0/3->0
        if stock_code.startswith('6'):
            secid = f"1.{stock_code}"
        else:
            secid = f"0.{stock_code}"
            
        # Simplified logic for demo, using yfinance preferentially
        
        news_items = []
        
        # Method 1: Use yfinance
        full_code = add_stock_suffix(stock_code)
        ticker = yf.Ticker(full_code)
        yf_news = ticker.news
        if yf_news:
            for item in yf_news:
                news_items.append({
                    "title": item.get('title'),
                    "link": item.get('link'),
                    "time": str(item.get('providerPublishTime')),
                    "source": item.get('publisher')
                })
        
        return news_items
    except Exception as e:
        print(f"Failed to fetch news: {e}")
        return []

def collect_ai_research_data(stock_code, api_config=None):
    """
    Collect data and call AI API for research
    api_config: {
        'api_key': 'sk-xxx',
        'base_url': 'https://api.deepseek.com/v1', (Optional)
        'model': 'deepseek-chat' (Optional)
    }
    """
    try:
        full_code = add_stock_suffix(stock_code)
        stock_name = stock_mapping.get_stock_name(stock_code)
        ticker = yf.Ticker(full_code)
        
        # 1. Get Fundamentals
        info = ticker.info
        info_text = f"""
        Stock Name: {stock_name} ({stock_code})
        Industry: {info.get('industry', 'Unknown')}
        Market Cap: {info.get('marketCap', 'Unknown')}
        PE Ratio: {info.get('trailingPE', 'Unknown')}
        Business Summary: {info.get('longBusinessSummary', 'No description available')[:500]}...
        """
        
        # 2. Get Recent News (Prefer yfinance)
        news_items = ticker.news
        news_text = "Recent News:\n"
        if news_items:
            for i, item in enumerate(news_items[:5]):
                news_text += f"{i+1}. {item.get('title')} (Source: {item.get('publisher')})\n"
        else:
            news_text += "No recent major news sources.\n"

        # 3. Build Prompt
        prompt = f"""
        You are a professional financial analyst. Please write a short research summary report for investors based on the provided stock information and recent news.
        
        【Stock Fundamentals】
        {info_text}
        
        【Recent News/Sentiment】
        {news_text}
        
        Please output in the following format (Markdown):
        ## 1. Company Overview
        (Brief introduction of company business and industry status)
        
        ## 2. Recent Developments & Sentiment
        (Summary of recent news events and potential impact)
        
        ## 3. Risk Factors
        (Potential risks based on industry and financial data)
        
        ## 4. Summary & Recommendation
        (Neutral and objective investment recommendation)
        """
        
        # 4. Call API
        if not api_config or not api_config.get('api_key'):
             return {
                "success": False, 
                "message": "Please provide API Key to use AI analysis."
            }

        api_key = api_config.get('api_key')
        base_url = api_config.get('base_url', 'https://api.openai.com/v1') # Default OpenAI
        model = api_config.get('model', 'gpt-3.5-turbo')
        
        # Standard OpenAI format call
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful financial analyst assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        # Simple adapter for Ollama local HTTP interface check
        if "localhost" in base_url or "127.0.0.1" in base_url:
             return {"success": False, "message": "This mode supports cloud API Key only. For local Ollama please adapt self-hosted solution."}

        # Fix base_url suffix
        if not base_url.endswith('/v1') and 'openai' not in base_url and 'deepseek' not in base_url: 
             pass
             
        # Ensure url complete
        if not base_url.endswith('/chat/completions'):
            target_url = f"{base_url.rstrip('/')}/chat/completions"
        else:
            target_url = base_url

        try:
            response = requests.post(
                target_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result_json = response.json()
                try:
                    ai_report = result_json['choices'][0]['message']['content']
                    return {"success": True, "report": ai_report}
                except (KeyError, IndexError):
                    return {"success": False, "message": f"API response format error: {result_json}"}
            else:
                return {"success": False, "message": f"API request failed: {response.status_code} - {response.text}"}
                
        except Exception as req_err:
             return {"success": False, "message": f"Network error: {str(req_err)}"}
            
    except Exception as e:
        print(f"AI Research Failed: {e}")
        return {"success": False, "message": str(e)}