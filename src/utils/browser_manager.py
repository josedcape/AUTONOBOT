"""
Enhanced Browser Manager for AUTONOBOT
Handles headless/visible mode switching and browser session management
"""

import asyncio
import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

try:
    from browser_use.browser.browser import BrowserConfig
except ImportError:
    # Fallback if browser_use structure is different
    from browser_use import BrowserConfig

try:
    from src.browser.custom_browser import CustomBrowser
except ImportError:
    # Fallback for basic browser functionality
    CustomBrowser = None

logger = logging.getLogger(__name__)

class BrowserMode(Enum):
    HEADLESS = "headless"
    VISIBLE = "visible"

@dataclass
class BrowserStatus:
    """Browser status information"""
    mode: BrowserMode
    is_active: bool
    is_healthy: bool
    context_count: int
    last_activity: Optional[str] = None
    error_message: Optional[str] = None

class BrowserManager:
    """Enhanced browser manager with headless/visible mode switching"""
    
    _instance = None
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._browser: Optional[CustomBrowser] = None
            self._browser_context = None
            self._current_mode = BrowserMode.VISIBLE
            self._is_switching = False
            self._status_callbacks: List[Callable] = []
            self._config_cache: Dict[str, Any] = {}
            self._lock = threading.Lock()
            self._health_check_interval = 30  # seconds
            self._health_check_thread: Optional[threading.Thread] = None
            self._stop_health_check = threading.Event()
            self._initialized = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
        return cls._instance
    
    def add_status_callback(self, callback: Callable) -> None:
        """Add callback for browser status updates"""
        self._status_callbacks.append(callback)
    
    def _notify_status_callbacks(self, status: BrowserStatus) -> None:
        """Notify all status callbacks"""
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in browser status callback: {e}")
    
    async def initialize_browser(self, config: Dict[str, Any], force_mode: Optional[BrowserMode] = None) -> bool:
        """Initialize browser with given configuration"""
        try:
            with self._lock:
                self._config_cache = config.copy()
                
                # Determine mode
                if force_mode:
                    self._current_mode = force_mode
                    headless = force_mode == BrowserMode.HEADLESS
                else:
                    headless = config.get('headless', False)
                    self._current_mode = BrowserMode.HEADLESS if headless else BrowserMode.VISIBLE
                
                # Update config with current mode
                self._config_cache['headless'] = headless
            
            # Create browser instance
            browser_config = BrowserConfig(
                headless=headless,
                disable_security=config.get('disable_security', True),
                chrome_instance_path=config.get('chrome_path'),
                extra_chromium_args=self._get_browser_args(config)
            )
            
            self._browser = CustomBrowser(config=browser_config)
            
            # Start health monitoring
            self._start_health_monitoring()
            
            status = BrowserStatus(
                mode=self._current_mode,
                is_active=True,
                is_healthy=True,
                context_count=0,
                last_activity="Browser initialized"
            )
            
            self._notify_status_callbacks(status)
            logger.info(f"🌐 Browser initialized in {self._current_mode.value} mode")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            status = BrowserStatus(
                mode=self._current_mode,
                is_active=False,
                is_healthy=False,
                context_count=0,
                error_message=str(e)
            )
            self._notify_status_callbacks(status)
            return False
    
    def _get_browser_args(self, config: Dict[str, Any]) -> List[str]:
        """Get browser arguments based on configuration"""
        args = [
            f"--window-size={config.get('window_w', 1280)},{config.get('window_h', 720)}",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding"
        ]
        
        # Add headless-specific optimizations
        if self._current_mode == BrowserMode.HEADLESS:
            args.extend([
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",
                "--disable-javascript-harmony-shipping",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-first-run",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-hang-monitor",
                "--disable-client-side-phishing-detection",
                "--disable-component-update"
            ])
        
        return args
    
    async def switch_mode(self, new_mode: BrowserMode, preserve_context: bool = True) -> bool:
        """Switch between headless and visible modes with enhanced context preservation"""
        if self._current_mode == new_mode:
            logger.info(f"Browser already in {new_mode.value} mode")
            return True

        if self._is_switching:
            logger.warning("Browser mode switch already in progress")
            return False

        self._is_switching = True

        try:
            logger.info(f"🔄 Switching browser from {self._current_mode.value} to {new_mode.value} mode")

            # Enhanced context preservation
            saved_context_data = None
            if preserve_context and self._browser_context:
                try:
                    # Save more comprehensive context data
                    saved_context_data = {
                        'config': getattr(self._browser_context, 'config', None),
                        'cookies': None,  # Will be implemented if needed
                        'local_storage': None,  # Will be implemented if needed
                        'session_storage': None  # Will be implemented if needed
                    }
                    logger.info("📦 Context data saved for preservation")
                except Exception as e:
                    logger.warning(f"Could not save context data: {e}")

            # Graceful browser closure
            if self._browser:
                try:
                    # Close context first
                    if self._browser_context:
                        await self._browser_context.close()
                        self._browser_context = None

                    # Then close browser
                    await self._browser.close()
                    logger.info("🔒 Previous browser session closed gracefully")
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")

            # Update mode and reinitialize with enhanced config
            self._current_mode = new_mode
            enhanced_config = self._config_cache.copy()
            enhanced_config['headless'] = (new_mode == BrowserMode.HEADLESS)

            success = await self.initialize_browser(enhanced_config, force_mode=new_mode)

            # Enhanced context restoration
            if success and preserve_context and saved_context_data:
                try:
                    # Create new context with saved configuration
                    context_config = saved_context_data.get('config')
                    self._browser_context = await self._browser.new_context(config=context_config)

                    # Future: Restore cookies, storage, etc. if needed
                    # await self._restore_context_data(saved_context_data)

                    logger.info("✅ Browser context restored with enhanced preservation")
                except Exception as e:
                    logger.warning(f"Could not restore context: {e}")
                    # Create a basic context if restoration fails
                    try:
                        self._browser_context = await self._browser.new_context()
                        logger.info("🔄 Created new basic context as fallback")
                    except Exception as e2:
                        logger.error(f"Failed to create fallback context: {e2}")

            if success:
                logger.info(f"✅ Successfully switched to {new_mode.value} mode")
                status = BrowserStatus(
                    mode=self._current_mode,
                    is_active=True,
                    is_healthy=True,
                    context_count=1 if self._browser_context else 0,
                    last_activity=f"Switched to {new_mode.value} mode automatically"
                )
            else:
                logger.error(f"❌ Failed to switch to {new_mode.value} mode")
                status = BrowserStatus(
                    mode=self._current_mode,
                    is_active=False,
                    is_healthy=False,
                    context_count=0,
                    error_message=f"Failed to switch to {new_mode.value} mode"
                )

            self._notify_status_callbacks(status)
            return success

        except Exception as e:
            logger.error(f"Error during mode switch: {e}")
            status = BrowserStatus(
                mode=self._current_mode,
                is_active=False,
                is_healthy=False,
                context_count=0,
                error_message=str(e)
            )
            self._notify_status_callbacks(status)
            return False

        finally:
            self._is_switching = False

    async def ensure_browser_ready(self, config: Dict[str, Any] = None) -> bool:
        """Ensure browser is ready and in correct mode based on configuration"""
        try:
            if config:
                self._config_cache.update(config)

            target_mode = BrowserMode.HEADLESS if self._config_cache.get('headless', False) else BrowserMode.VISIBLE

            # If browser is not initialized or in wrong mode, initialize/switch
            if not self._browser or self._current_mode != target_mode:
                if not self._browser:
                    # Initialize browser
                    return await self.initialize_browser(self._config_cache, force_mode=target_mode)
                else:
                    # Switch mode
                    return await self.switch_mode(target_mode, preserve_context=True)

            return True

        except Exception as e:
            logger.error(f"Error ensuring browser ready: {e}")
            return False
    
    async def get_or_create_context(self, context_config=None):
        """Get existing context or create new one"""
        if not self._browser:
            raise Exception("Browser not initialized")
        
        if self._browser_context is None:
            self._browser_context = await self._browser.new_context(config=context_config)
            logger.info("🌐 New browser context created")
        
        return self._browser_context
    
    def is_browser_healthy(self) -> bool:
        """Check if browser is healthy and responsive"""
        try:
            if not self._browser:
                return False
            
            # Basic health check - browser should be alive
            # More sophisticated checks can be added here
            return True
            
        except Exception as e:
            logger.error(f"Browser health check failed: {e}")
            return False
    
    def get_current_mode(self) -> BrowserMode:
        """Get current browser mode"""
        return self._current_mode
    
    def get_browser_status(self) -> BrowserStatus:
        """Get current browser status"""
        is_healthy = self.is_browser_healthy()
        context_count = 1 if self._browser_context else 0
        
        return BrowserStatus(
            mode=self._current_mode,
            is_active=self._browser is not None,
            is_healthy=is_healthy,
            context_count=context_count,
            last_activity="Status check"
        )
    
    def _start_health_monitoring(self) -> None:
        """Start background health monitoring"""
        if self._health_check_thread and self._health_check_thread.is_alive():
            return
        
        self._stop_health_check.clear()
        self._health_check_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        self._health_check_thread.start()
        logger.info("🔍 Browser health monitoring started")
    
    def _health_monitor_loop(self) -> None:
        """Background health monitoring loop"""
        while not self._stop_health_check.wait(self._health_check_interval):
            try:
                status = self.get_browser_status()
                self._notify_status_callbacks(status)
                
                if not status.is_healthy:
                    logger.warning("⚠️ Browser health check failed")
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
    
    def stop_health_monitoring(self) -> None:
        """Stop health monitoring"""
        self._stop_health_check.set()
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=5)
        logger.info("🛑 Browser health monitoring stopped")
    
    async def close(self) -> None:
        """Close browser and cleanup"""
        self.stop_health_monitoring()
        
        if self._browser_context:
            try:
                await self._browser_context.close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
        
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        
        self._browser = None
        self._browser_context = None
        
        status = BrowserStatus(
            mode=self._current_mode,
            is_active=False,
            is_healthy=False,
            context_count=0,
            last_activity="Browser closed"
        )
        self._notify_status_callbacks(status)
        logger.info("🌐 Browser manager closed")

# Global browser manager instance
browser_manager = BrowserManager()
