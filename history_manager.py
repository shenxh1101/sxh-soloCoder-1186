import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from icon_generator import HistoryRecord

class HistoryManager:
    def __init__(self, history_file: str, max_records: int = 50):
        self.history_file = history_file
        self.max_records = max_records
        self.records: List[HistoryRecord] = []
        self._load()
    
    def _load(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.records = [HistoryRecord(**r) for r in data]
            except:
                self.records = []
        else:
            self.records = []
    
    def _save(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        data = [r.__dict__ for r in self.records]
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_record(self, record: HistoryRecord):
        existing_idx = None
        for i, r in enumerate(self.records):
            if r.cache_key == record.cache_key:
                existing_idx = i
                break
        
        if existing_idx is not None:
            self.records.pop(existing_idx)
        
        self.records.insert(0, record)
        
        if len(self.records) > self.max_records:
            self.records = self.records[:self.max_records]
        
        self._save()
    
    def get_all(self) -> List[HistoryRecord]:
        return self.records.copy()
    
    def get_by_id(self, record_id: str) -> Optional[HistoryRecord]:
        for r in self.records:
            if r.id == record_id:
                return r
        return None
    
    def get_by_cache_key(self, cache_key: str) -> Optional[HistoryRecord]:
        for r in self.records:
            if r.cache_key == cache_key:
                return r
        return None
    
    def delete_record(self, record_id: str) -> bool:
        for i, r in enumerate(self.records):
            if r.id == record_id:
                self.records.pop(i)
                self._save()
                return True
        return False
    
    def clear_all(self):
        self.records = []
        self._save()
    
    def count(self) -> int:
        return len(self.records)

def create_history_record(
    record_id: str,
    original_name: str,
    file_hash: str,
    cache_key: str,
    options: Dict[str, Any],
    cached: bool = False,
    file_count: int = 0
) -> HistoryRecord:
    return HistoryRecord(
        id=record_id,
        original_name=original_name,
        file_hash=file_hash,
        cache_key=cache_key,
        options=options,
        created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        cached=cached,
        file_count=file_count
    )
