import subprocess
import tempfile
import os
import json
import asyncio
import signal
import sys
import platform
from typing import Dict, Any
from pathlib import Path
import logging
from config.settings import settings

# Platform-specific imports
IS_WINDOWS = platform.system() == "Windows"

if not IS_WINDOWS:
    try:
        import resource
        HAS_RESOURCE = True
    except ImportError:
        HAS_RESOURCE = False
        resource = None
else:
    HAS_RESOURCE = False
    resource = None

logger = logging.getLogger(__name__)

class SecureSandbox:
    """
    Secure sandbox for executing generated scraper code
    Cross-platform compatible (Windows/Linux)
    """
    
    def __init__(self, timeout: int = None, memory_limit: int = None):
        self.timeout = timeout or settings.SANDBOX_TIMEOUT
        self.memory_limit = memory_limit or settings.SANDBOX_MEMORY_LIMIT
        self.is_windows = IS_WINDOWS
        self.allowed_modules = [
            'requests', 'bs4', 'beautifulsoup4', 'json', 'time', 'urllib',
            'datetime', 're', 'math', 'string', 'html', 'xml', 'collections',
            'itertools', 'functools', 'operator', 'typing'
        ]
    
    async def execute_scraper(self, code: str, url: str) -> Dict[str, Any]:
        """Execute scraper code in sandboxed environment"""
        logger.info(f"Executing scraper in sandbox for URL: {url} (Platform: {platform.system()})")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            wrapped_code = self._wrap_code(code)
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            # Execute with restrictions
            result = await self._run_with_limits(temp_file, url)
            logger.info(f"Sandbox execution completed with success: {result.get('success', False)}")
            return result
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return {"error": f"Sandbox execution failed: {str(e)}", "success": False}
        finally:
            # Cleanup
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
    
    def _wrap_code(self, code: str) -> str:
        """Wrap user code with safety checks and timeout"""
        # Platform-specific timeout handling
        if self.is_windows:
            timeout_setup = f'''
import threading
import time

# Windows timeout implementation using threading
def timeout_handler():
    time.sleep({self.timeout})
    import os
    os._exit(1)

timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
timeout_thread.start()
'''
        else:
            timeout_setup = f'''
import signal

# Unix timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout exceeded")

# Set up signal handler for timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.timeout})
'''

        wrapper = f'''
import sys
import json
import time
import traceback
{timeout_setup}

# Import restrictions
if isinstance(__builtins__, dict):
    original_import = __builtins__['__import__']
else:
    original_import = __builtins__.__import__

def restricted_import(name, *args, **kwargs):
    allowed = {self.allowed_modules}
    base_module = name.split('.')[0]
    if base_module not in allowed:
        raise ImportError(f"Module {{name}} not allowed in sandbox")
    return original_import(name, *args, **kwargs)

if isinstance(__builtins__, dict):
    __builtins__['__import__'] = restricted_import
else:
    __builtins__.__import__ = restricted_import

# Start execution timer
start_time = time.time()

try:
    # User code injection
{self._indent_code(code)}
    
    # Execute main function
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = scrape_data(url)
        
        # Add execution metadata
        execution_time = int((time.time() - start_time) * 1000)
        if isinstance(result, dict):
            if 'metadata' not in result:
                result['metadata'] = {{}}
            result['metadata']['execution_time_ms'] = execution_time
            result['success'] = True
        
        print(json.dumps(result, default=str))
    else:
        print(json.dumps({{"error": "No URL provided", "success": False}}))
    
except TimeoutError:
    print(json.dumps({{"error": "Execution timeout exceeded", "success": False}}))
except ImportError as e:
    print(json.dumps({{"error": f"Import not allowed: {{str(e)}}", "success": False}}))
except Exception as e:
    error_result = {{
        "error": str(e),
        "error_type": type(e).__name__,
        "traceback": traceback.format_exc(),
        "success": False
    }}
    print(json.dumps(error_result))
finally:
    # Platform-specific cleanup
    if not {self.is_windows}:
        try:
            signal.alarm(0)  # Cancel the alarm on Unix
        except:
            pass
'''
        return wrapper
    
    def _indent_code(self, code: str) -> str:
        """Indent user code for proper wrapping"""
        lines = code.split('\n')
        indented_lines = ['    ' + line for line in lines]
        return '\n'.join(indented_lines)
    
    async def _run_with_limits(self, script_path: str, url: str) -> Dict[str, Any]:
        """Run script with resource limits"""
        try:
            # Platform-specific process creation
            if self.is_windows:
                # Windows: Use synchronous subprocess due to asyncio limitations
                logger.debug("Using synchronous subprocess on Windows")
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._run_sync_process, script_path, url
                )
                return result
            else:
                # Unix: Create process with resource limits
                process = await asyncio.create_subprocess_exec(
                    sys.executable, script_path, url,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    preexec_fn=self._set_limits,
                    cwd=tempfile.gettempdir()
                )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout + 5  # Give extra 5 seconds for cleanup
                )
            except asyncio.TimeoutError:
                logger.warning("Process timeout, killing process")
                try:
                    if self.is_windows:
                        process.terminate()
                    else:
                        process.kill()
                    await process.wait()
                except:
                    pass
                return {"error": "Execution timeout", "success": False}
            
            # Parse result
            if process.returncode == 0:
                try:
                    stdout_str = stdout.decode('utf-8', errors='replace')
                    result = json.loads(stdout_str)
                    
                    # Validate result structure
                    if isinstance(result, dict):
                        if 'success' not in result:
                            result['success'] = 'error' not in result
                        return result
                    else:
                        return {
                            "error": f"Invalid result format: expected dict, got {type(result).__name__}",
                            "success": False
                        }
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON output: {e}")
                    stdout_preview = stdout.decode('utf-8', errors='replace')[:500]
                    stderr_preview = stderr.decode('utf-8', errors='replace')[:500]
                    logger.error(f"STDOUT: {stdout_preview}")
                    logger.error(f"STDERR: {stderr_preview}")
                    return {
                        "error": f"Invalid JSON output: {str(e)}",
                        "stdout_preview": stdout_preview,
                        "stderr_preview": stderr_preview,
                        "success": False
                    }
            else:
                stderr_str = stderr.decode('utf-8', errors='replace')[:500]
                stdout_str = stdout.decode('utf-8', errors='replace')[:500]
                logger.error(f"Script execution failed (exit code {process.returncode})")
                logger.error(f"STDERR: {stderr_str}")
                logger.error(f"STDOUT: {stdout_str}")
                return {
                    "error": f"Script execution failed (exit code {process.returncode})",
                    "stderr": stderr_str,
                    "stdout": stdout_str,
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Failed to execute script: {e}")
            logger.exception("Full sandbox exception details:")
            return {"error": f"Sandbox execution failed: {str(e)}", "success": False}
    
    def _run_sync_process(self, script_path: str, url: str) -> Dict[str, Any]:
        """Run process synchronously (Windows fallback)"""
        try:
            process = subprocess.run(
                [sys.executable, script_path, url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                cwd=tempfile.gettempdir(),
                text=False
            )
            
            stdout = process.stdout
            stderr = process.stderr
            
            if process.returncode == 0:
                try:
                    output_text = stdout.decode('utf-8', errors='replace')
                    result = json.loads(output_text)
                    
                    # Validate result structure
                    if isinstance(result, dict):
                        if 'success' not in result:
                            result['success'] = 'error' not in result
                        return result
                    else:
                        return {
                            "error": f"Invalid result format: expected dict, got {type(result).__name__}",
                            "success": False
                        }
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON output: {e}")
                    stdout_preview = stdout.decode('utf-8', errors='replace')[:500]
                    return {
                        "error": f"Invalid JSON output: {str(e)}",
                        "stdout_preview": stdout_preview,
                        "success": False
                    }
            else:
                stderr_str = stderr.decode('utf-8', errors='replace')[:500]
                stdout_str = stdout.decode('utf-8', errors='replace')[:500]
                logger.error(f"Script execution failed (exit code {process.returncode})")
                logger.error(f"STDERR: {stderr_str}")
                logger.error(f"STDOUT: {stdout_str}")
                return {
                    "error": f"Script execution failed (exit code {process.returncode})",
                    "stderr": stderr_str,
                    "stdout": stdout_str,
                    "success": False
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"Script execution timed out after {self.timeout} seconds")
            return {
                "error": f"Script execution timed out after {self.timeout} seconds",
                "success": False
            }
        except Exception as e:
            logger.error(f"Sync process execution failed: {e}")
            return {
                "error": f"Process execution failed: {str(e)}",
                "success": False
            }
    
    def _set_limits(self):
        """Set resource limits for subprocess (Unix only)"""
        if self.is_windows or not HAS_RESOURCE:
            logger.warning("Resource limits not available on this platform")
            return
            
        try:
            # Set memory limit (in bytes)
            memory_limit_bytes = self.memory_limit * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
            
            # Set CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
            
            # Prevent core dumps
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            
            # Limit number of processes
            resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
            
            logger.debug("Resource limits set successfully")
            
        except Exception as e:
            # Resource limits might not be available on all systems
            logger.warning(f"Failed to set resource limits: {e}")
            pass
