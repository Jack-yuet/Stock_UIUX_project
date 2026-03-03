"""
股票映射模块
管理股票代码和名称的对应关系
"""

import json
import os

class StockMapping:
    """股票映射类"""
    
    def __init__(self, mapping_file='stock_mapping.json'):
        """
        Initialize stock mapping
        
        Args:
            mapping_file (str): Mapping file path
        """
        self.mapping_file = mapping_file
        self.stock_map = self._load_mapping()
    
    def _load_mapping(self):
        """Load stock mapping data"""
        try:
            # Vercel: Prefer /tmp version if exists (persisted within instance lifespan)
            if 'VERCEL' in os.environ:
                tmp_path = os.path.join('/tmp', os.path.basename(self.mapping_file))
                if os.path.exists(tmp_path):
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            # Load from source (read-only on Vercel)
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # If file doesn't exist, return default
                return self._get_default_mapping()
        except Exception as e:
            print(f"Failed to load stock mapping file: {e}")
            return self._get_default_mapping()
    
    def _get_default_mapping(self):
        """Get default stock mapping"""
        return {
            "603126": "Sinoma Energy",
            "300133": "Huace Film",
            "600598": "Beidahuang",
            "000899": "Ganneng",
            "600895": "Zhangjiang High-Tech",
            "000786": "BNBM",
            "003035": "China Southern Power",
            "000753": "Zhangzhou Development",
            "600051": "Ningbo United",
            "600030": "CITIC Securities",
            "601878": "Zheshang Securities",
            "002756": "Yongxing Materials",
            "002643": "Wanrun",
            "002640": "Global Top",
            "002865": "Junda",
            "603533": "IReader",
            "000100": "TCL Tech",
            "603260": "Hoshine Silicon"
        }
    
    def get_stock_name(self, stock_code):
        """
        根据股票代码获取股票名称
        """
        stock = self.stock_map.get(stock_code)
        if isinstance(stock, dict):
            return stock.get('name', stock_code)
        return stock or stock_code
    
    def get_stock_name_or_default(self, stock_code, default_value='未知'):
        stock = self.stock_map.get(stock_code)
        if isinstance(stock, dict):
            return stock.get('name', default_value)
        return stock or default_value
    
    def has_stock(self, stock_code):
        return stock_code in self.stock_map
    
    def get_all_stock_codes(self):
        return list(self.stock_map.keys())
    
    def get_all_stocks(self):
        result = []
        for code, value in self.stock_map.items():
            if isinstance(value, dict):
                enable_batch = value.get('enable_batch', 't')
                enable_batch_bool = (enable_batch == 't')
                result.append({
                    'code': code,
                    'name': value.get('name', code),
                    'enable_batch': enable_batch_bool
                })
            else:
                result.append({'code': code, 'name': value, 'enable_batch': True})
        return result
    
    def format_stock_display(self, stock_code):
        name = self.get_stock_name(stock_code)
        return f"{stock_code} {name}" if name != stock_code else stock_code
    
    def reload_mapping(self):
        """重新加载映射数据"""
        self.stock_map = self._load_mapping()
    
    def update_mapping(self, stock_code, stock_name):
        """
        更新股票映射
        
        Args:
            stock_code (str): 股票代码
            stock_name (str): 股票名称
        """
        self.stock_map[stock_code] = stock_name
        self._save_mapping()
    
    def _save_mapping(self):
        """Save mapping data to file"""
        try:
            save_path = self.mapping_file
            if 'VERCEL' in os.environ:
                save_path = os.path.join('/tmp', os.path.basename(self.mapping_file))
                
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.stock_map, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save stock mapping file: {e}")

# 创建全局实例
stock_mapping = StockMapping() 