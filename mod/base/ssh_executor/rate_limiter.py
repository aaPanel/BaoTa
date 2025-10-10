"""
Rate limiter for file transfers with clean separation of concerns.

NOTE: These rate limiters are NOT thread-safe by design.
Rate limiting operations are typically single-threaded, and removing
threading overhead improves performance.
"""

import time
from typing import Optional, Callable


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for controlling transfer speed with burst support.
    
    NOTE: This class is NOT thread-safe. Rate limiting operations are typically
    single-threaded, and removing threading overhead improves performance.
    
    The token bucket algorithm allows for:
    - Sustained rate limiting (tokens per second)
    - Burst control (bucket capacity)
    - Peak rate control
    
    Usage:
        limiter = TokenBucketRateLimiter(
            rate=1024*1024,      # 1MB/s sustained rate
            capacity=2*1024*1024  # 2MB burst capacity
        )
        for chunk in data_chunks:
            limiter.wait_if_needed(len(chunk))
            # transfer chunk
    """
    
    def __init__(self, 
                 rate: Optional[int] = None, 
                 capacity: Optional[int] = None,
                 initial_tokens: Optional[int] = None):
        """
        Initialize token bucket rate limiter.
        
        Args:
            rate: Tokens (bytes) per second. None means no rate limiting.
            capacity: Maximum bucket capacity in bytes. If None, defaults to rate.
            initial_tokens: Initial tokens in bucket. If None, defaults to capacity.
        """
        self.rate = rate
        self.capacity = capacity if capacity is not None else rate
        self.initial_tokens = initial_tokens if initial_tokens is not None else self.capacity
        
        # Current state
        self.tokens = self.initial_tokens
        self.last_update = None
        self._started = False
        
    def start(self):
        """Start timing for rate limiting."""
        if self.rate and not self._started:
            self._started = True
            self.last_update = time.time()
            self.tokens = self.initial_tokens
    
    def wait_if_needed(self, chunk_size: int):
        """
        Wait if necessary to maintain the specified transfer rate.
        
        Args:
            chunk_size: Size of the chunk just transferred in bytes.
        """
        if not self.rate or not self.last_update:
            return
            
        # Refill tokens based on elapsed time
        now = time.time()
        elapsed = now - self.last_update
        tokens_to_add = elapsed * self.rate
        
        # Add tokens up to capacity
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_update = now
        
        # Check if we have enough tokens
        if self.tokens < chunk_size:
            # Calculate wait time to get enough tokens
            tokens_needed = chunk_size - self.tokens
            wait_time = tokens_needed / self.rate
            time.sleep(wait_time)
            
            # Refill tokens after waiting
            now = time.time()
            elapsed = now - self.last_update
            tokens_to_add = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_update = now
        
        # Consume tokens
        self.tokens -= chunk_size


class LeakyBucketRateLimiter:
    """
    Leaky bucket rate limiter for strict rate limiting without burst support.
    
    NOTE: This class is NOT thread-safe. Rate limiting operations are typically
    single-threaded, and removing threading overhead improves performance.
    
    The leaky bucket algorithm provides:
    - Strict rate limiting (no burst)
    - Predictable output rate
    - Better for network protocols that can't handle bursts
    
    Usage:
        limiter = LeakyBucketRateLimiter(rate=1024*1024)  # 1MB/s strict rate
        for chunk in data_chunks:
            limiter.wait_if_needed(len(chunk))
            # transfer chunk
    """
    
    def __init__(self, rate: Optional[int] = None):
        """
        Initialize leaky bucket rate limiter.
        
        Args:
            rate: Tokens (bytes) per second. None means no rate limiting.
        """
        self.rate = rate
        self.last_update = None
        self._started = False
        
    def start(self):
        """Start timing for rate limiting."""
        if self.rate and not self._started:
            self.last_update = time.time()
    
    def wait_if_needed(self, chunk_size: int):
        """
        Wait if necessary to maintain the specified transfer rate.
        
        Args:
            chunk_size: Size of the chunk just transferred in bytes.
        """
        if not self.rate or not self.last_update:
            return
            
        now = time.time()
        elapsed = now - self.last_update
        
        # Calculate minimum time needed for this chunk
        min_time = chunk_size / self.rate
        
        if elapsed < min_time:
            wait_time = min_time - elapsed
            time.sleep(wait_time)
        
        self.last_update = time.time()


class RateLimiter:
    """
    Main rate limiter class that provides a unified interface.
    
    NOTE: This class is NOT thread-safe. Rate limiting operations are typically
    single-threaded, and removing threading overhead improves performance.
    
    This class can use different underlying algorithms:
    - TokenBucketRateLimiter: For burst-capable rate limiting
    - LeakyBucketRateLimiter: For strict rate limiting
    """
    
    def __init__(self, 
                 bytes_per_second: Optional[int] = None,
                 algorithm: str = "token_bucket",
                 burst_capacity: Optional[int] = None):
        """
        Initialize rate limiter.
        
        Args:
            bytes_per_second: Transfer rate limit in bytes per second.
            algorithm: Rate limiting algorithm ("token_bucket" or "leaky_bucket")
            burst_capacity: For token bucket, maximum burst capacity in bytes.
                          If None, defaults to bytes_per_second.
        """
        if algorithm == "token_bucket":
            self._limiter = TokenBucketRateLimiter(
                rate=bytes_per_second,
                capacity=burst_capacity
            )
        elif algorithm == "leaky_bucket":
            self._limiter = LeakyBucketRateLimiter(bytes_per_second)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}. Use 'token_bucket' or 'leaky_bucket'")
        
        self.bytes_per_second = bytes_per_second
        self.algorithm = algorithm
        
    def start(self):
        """Start timing for rate limiting."""
        self._limiter.start()
    
    def wait_if_needed(self, chunk_size: int):
        """
        Wait if necessary to maintain the specified transfer rate.
        
        Args:
            chunk_size: Size of the chunk just transferred in bytes.
        """
        self._limiter.wait_if_needed(chunk_size)


class ProgressTracker:
    """
    Simple progress tracking with configurable update frequency.
    
    NOTE: This class is NOT thread-safe. Progress tracking operations are typically
    single-threaded, and removing threading overhead improves performance.
    """
    
    def __init__(self, 
                 callback: Optional[Callable[[int, int], None]] = None,
                 update_interval: float = 0.1):
        """
        Initialize progress tracker.
        
        Args:
            callback: Function to call with (transferred, total) progress updates
            update_interval: Minimum seconds between progress updates
        """
        self.callback = callback
        self.update_interval = update_interval
        self.last_update_time = 0
        
    def start(self):
        """Start progress tracking."""
        self.last_update_time = 0
        
    def update(self, transferred: int, total: int):
        """
        Update progress if enough time has passed since last update.
        
        Args:
            transferred: Bytes transferred so far
            total: Total bytes to transfer
        """
        if not self.callback:
            return
            
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.callback(transferred, total)
            self.last_update_time = current_time
    
    def finish(self, total: int):
        """Force final progress update."""
        if self.callback:
            self.callback(total, total)
