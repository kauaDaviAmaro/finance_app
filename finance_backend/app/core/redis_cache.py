"""
Módulo de cache Redis para dados do yfinance.
Usa db=1 para não misturar com o Celery (que usa db=0).
"""
import redis
import json
import pandas as pd
from typing import Optional, Any, Dict
import os

# Configuração do cliente Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB_CACHE = 1  # DB separado do Celery (que usa db=0)

# Pool de conexão e cliente
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None

def _init_redis_client():
    """Inicializa o cliente Redis para cache."""
    global redis_pool, redis_client
    
    if redis_client is not None:
        return redis_client
    
    try:
        redis_pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB_CACHE,
            decode_responses=False  # Precisamos de bytes para JSON
        )
        redis_client = redis.Redis(connection_pool=redis_pool)
        redis_client.ping()
        print(f"✅ Conectado ao Redis para CACHE (db={REDIS_DB_CACHE})")
    except Exception as e:
        print(f"⚠️  Não conectou no Redis do cache: {e}")
        print("   O app continuará funcionando, mas sem cache (requisições diretas ao yfinance)")
        redis_client = None
    
    return redis_client

def get_redis_client() -> Optional[redis.Redis]:
    """Retorna o cliente Redis, inicializando se necessário."""
    if redis_client is None:
        _init_redis_client()
    return redis_client

# TTL padrão (5 minutos)
DEFAULT_CACHE_TTL = 300  # 5 minutos em segundos

def get_cached_dataframe(cache_key: str) -> Optional[pd.DataFrame]:
    """
    Busca um DataFrame do cache Redis.
    
    Args:
        cache_key: Chave do cache
        
    Returns:
        DataFrame se encontrado, None caso contrário
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        cached_data = client.get(cache_key)
        if cached_data:
            data_json = json.loads(cached_data)
            df = pd.read_json(data_json, orient='split')
            print(f"✅ CACHE HIT: {cache_key}")
            return df
    except Exception as e:
        print(f"⚠️  Erro no REDIS GET ({cache_key}): {e}")
    
    return None

def set_cached_dataframe(cache_key: str, df: pd.DataFrame, ttl: int = DEFAULT_CACHE_TTL):
    """
    Salva um DataFrame no cache Redis.
    
    Args:
        cache_key: Chave do cache
        df: DataFrame para salvar
        ttl: Time to live em segundos (padrão: 5 minutos)
    """
    client = get_redis_client()
    if not client:
        return
    
    if df is None or df.empty:
        return
    
    try:
        data_json = df.to_json(orient='split', date_format='iso')
        client.setex(cache_key, ttl, data_json)
        print(f"💾 CACHE SET: {cache_key} (TTL: {ttl}s)")
    except Exception as e:
        print(f"⚠️  Erro no REDIS SETEX ({cache_key}): {e}")

def get_cached_dict(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Busca um dicionário do cache Redis.
    
    Args:
        cache_key: Chave do cache
        
    Returns:
        Dicionário se encontrado, None caso contrário
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        cached_data = client.get(cache_key)
        if cached_data:
            data_dict = json.loads(cached_data)
            print(f"✅ CACHE HIT: {cache_key}")
            return data_dict
    except Exception as e:
        print(f"⚠️  Erro no REDIS GET ({cache_key}): {e}")
    
    return None

def set_cached_dict(cache_key: str, data: Dict[str, Any], ttl: int = DEFAULT_CACHE_TTL):
    """
    Salva um dicionário no cache Redis.
    
    Args:
        cache_key: Chave do cache
        data: Dicionário para salvar
        ttl: Time to live em segundos (padrão: 5 minutos)
    """
    client = get_redis_client()
    if not client:
        return
    
    if not data:
        return
    
    try:
        data_json = json.dumps(data)
        client.setex(cache_key, ttl, data_json)
        print(f"💾 CACHE SET: {cache_key} (TTL: {ttl}s)")
    except Exception as e:
        print(f"⚠️  Erro no REDIS SETEX ({cache_key}): {e}")

def clear_cache_pattern(pattern: str):
    """
    Limpa todas as chaves do cache que correspondem a um padrão.
    
    Args:
        pattern: Padrão de chave (ex: "yfinance:historical:*")
    """
    client = get_redis_client()
    if not client:
        return
    
    try:
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
            print(f"🗑️  Limpou {len(keys)} chaves do cache (padrão: {pattern})")
    except Exception as e:
        print(f"⚠️  Erro ao limpar cache ({pattern}): {e}")



