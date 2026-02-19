"""Docker-based sandbox for safe code execution."""
import os
import docker
import tempfile
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
import time


class DockerSandbox:
    """Manage Docker containers for safe code execution."""
    
    def __init__(
        self,
        image: str = "python:3.11-slim",
        timeout: int = None,
        memory_limit: str = None,
        cpu_limit: float = None,
        network_disabled: bool = True
    ):
        """Initialize Docker sandbox.
        
        Args:
            image: Docker image to use
            timeout: Execution timeout in seconds
            memory_limit: Memory limit (e.g., "512m", "1g")
            cpu_limit: CPU limit (e.g., 1.0 = 1 CPU)
            network_disabled: Disable network access
        """
        self.image = image
        self.timeout = timeout or int(os.getenv("SANDBOX_TIMEOUT", "30"))
        self.memory_limit = memory_limit or os.getenv("SANDBOX_MEMORY_LIMIT", "512m")
        self.cpu_limit = cpu_limit or float(os.getenv("SANDBOX_CPU_LIMIT", "1.0"))
        self.network_disabled = network_disabled
        
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
        except Exception as e:
            print(f"Warning: Docker not available: {e}")
            print("Sandbox features will be disabled. Install Docker to enable.")
            self.client = None
    
    def execute_python(
        self,
        code: str,
        files: Optional[Dict[str, str]] = None,
        packages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute Python code in isolated container.
        
        Args:
            code: Python code to execute
            files: Optional dict of filename -> content to create
            packages: Optional list of pip packages to install
            
        Returns:
            Dict with stdout, stderr, exit_code, execution_time
        """
        if not self.client:
            return {
                "success": False,
                "error": "Docker not available",
                "stdout": "",
                "stderr": "Docker daemon not running. Install and start Docker.",
                "exit_code": -1,
                "execution_time": 0
            }
        
        container = None
        start_time = time.time()
        
        try:
            # Create temporary directory for code
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code to file
                code_file = Path(tmpdir) / "script.py"
                code_file.write_text(code)
                
                # Write additional files if provided
                if files:
                    for filename, content in files.items():
                        file_path = Path(tmpdir) / filename
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(content)
                
                # Build command
                command = []
                
                # Install packages if needed
                if packages:
                    pip_install = f"pip install --quiet {' '.join(packages)} && "
                    command.append(f"sh -c '{pip_install}python /workspace/script.py'")
                else:
                    command = ["python", "/workspace/script.py"]
                
                # Container configuration
                container_config = {
                    "image": self.image,
                    "command": command,
                    "volumes": {tmpdir: {"bind": "/workspace", "mode": "ro"}},
                    "working_dir": "/workspace",
                    "detach": True,
                    # "remove": False,  # We'll remove manually after getting logs
                    "mem_limit": self.memory_limit,
                    "nano_cpus": int(self.cpu_limit * 1e9),
                    "network_disabled": self.network_disabled,
                    "read_only": False,  # Need write for pip install
                }
                
                # Pull image if not exists
                try:
                    self.client.images.get(self.image)
                except docker.errors.ImageNotFound:
                    print(f"Pulling image {self.image}...")
                    self.client.images.pull(self.image)
                
                # Create and start container
                container = self.client.containers.create(**container_config)
                container.start()
                
                # Wait for completion with timeout
                try:
                    result = container.wait(timeout=self.timeout)
                    exit_code = result["StatusCode"]
                except Exception as e:
                    # Timeout or other error
                    container.kill()
                    execution_time = time.time() - start_time
                    return {
                        "success": False,
                        "error": f"Execution timeout after {self.timeout}s",
                        "stdout": "",
                        "stderr": str(e),
                        "exit_code": -1,
                        "execution_time": execution_time
                    }
                
                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
                
                execution_time = time.time() - start_time
                
                return {
                    "success": exit_code == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "execution_time": execution_time
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": execution_time
            }
        
        finally:
            # Cleanup container
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
    
    def execute_shell(
        self,
        command: str,
        working_dir: str = "/workspace"
    ) -> Dict[str, Any]:
        """Execute shell command in isolated container.
        
        Args:
            command: Shell command to execute
            working_dir: Working directory
            
        Returns:
            Dict with stdout, stderr, exit_code, execution_time
        """
        if not self.client:
            return {
                "success": False,
                "error": "Docker not available",
                "stdout": "",
                "stderr": "Docker daemon not running",
                "exit_code": -1,
                "execution_time": 0
            }
        
        container = None
        start_time = time.time()
        
        try:
            # Container configuration
            container_config = {
                "image": self.image,
                "command": ["sh", "-c", command],
                "working_dir": working_dir,
                "detach": True,
                # "remove": False,
                "mem_limit": self.memory_limit,
                "nano_cpus": int(self.cpu_limit * 1e9),
                "network_disabled": self.network_disabled,
            }
            
            # Create and start container
            container = self.client.containers.create(**container_config)
            container.start()
            
            # Wait for completion
            try:
                result = container.wait(timeout=self.timeout)
                exit_code = result["StatusCode"]
            except Exception as e:
                container.kill()
                execution_time = time.time() - start_time
                return {
                    "success": False,
                    "error": f"Timeout after {self.timeout}s",
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "execution_time": execution_time
                }
            
            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            
            execution_time = time.time() - start_time
            
            return {
                "success": exit_code == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": execution_time
            }
        
        finally:
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
    
    def execute_javascript(
        self,
        code: str,
        files: Optional[Dict[str, str]] = None,
        packages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute JavaScript code in isolated Node.js container.
        
        Args:
            code: JavaScript code to execute
            files: Optional dict of filename -> content to create
            packages: Optional list of npm packages to install
            
        Returns:
            Dict with stdout, stderr, exit_code, execution_time
        """
        if not self.client:
            return {
                "success": False,
                "error": "Docker not available",
                "stdout": "",
                "stderr": "Docker daemon not running. Install and start Docker.",
                "exit_code": -1,
                "execution_time": 0
            }
        
        container = None
        start_time = time.time()
        
        try:
            # Create temporary directory for code
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code to file
                code_file = Path(tmpdir) / "script.js"
                code_file.write_text(code)
                
                # Write additional files if provided
                if files:
                    for filename, content in files.items():
                        file_path = Path(tmpdir) / filename
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(content)
                
                # Build command
                command = []
                
                # Install packages if needed
                if packages:
                    npm_install = f"npm install --silent {' '.join(packages)} && "
                    command.append(f"sh -c '{npm_install}node /workspace/script.js'")
                else:
                    command = ["node", "/workspace/script.js"]
                
                # Container configuration
                container_config = {
                    "image": "node:18-slim",
                    "command": command,
                    "volumes": {tmpdir: {"bind": "/workspace", "mode": "ro"}},
                    "working_dir": "/workspace",
                    "detach": True,
                    # "remove": False,
                    "mem_limit": self.memory_limit,
                    "nano_cpus": int(self.cpu_limit * 1e9),
                    "network_disabled": self.network_disabled,
                    "read_only": False,
                }
                
                # Pull image if not exists
                try:
                    self.client.images.get("node:18-slim")
                except docker.errors.ImageNotFound:
                    print("Pulling image node:18-slim...")
                    self.client.images.pull("node:18-slim")
                
                # Create and start container
                container = self.client.containers.create(**container_config)
                container.start()
                
                # Wait for completion with timeout
                try:
                    result = container.wait(timeout=self.timeout)
                    exit_code = result["StatusCode"]
                except Exception as e:
                    container.kill()
                    execution_time = time.time() - start_time
                    return {
                        "success": False,
                        "error": f"Execution timeout after {self.timeout}s",
                        "stdout": "",
                        "stderr": str(e),
                        "exit_code": -1,
                        "execution_time": execution_time
                    }
                
                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
                
                execution_time = time.time() - start_time
                
                return {
                    "success": exit_code == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "execution_time": execution_time
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": execution_time
            }
        
        finally:
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
    
    def execute_java(
        self,
        code: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute Java code in isolated container.
        
        Args:
            code: Java code to execute (must contain a Main class with main method)
            filename: Optional filename (defaults to Main.java)
            
        Returns:
            Dict with stdout, stderr, exit_code, execution_time
        """
        if not self.client:
            return {
                "success": False,
                "error": "Docker not available",
                "stdout": "",
                "stderr": "Docker daemon not running. Install and start Docker.",
                "exit_code": -1,
                "execution_time": 0
            }
        
        container = None
        start_time = time.time()
        
        try:
            # Create temporary directory for code
            with tempfile.TemporaryDirectory() as tmpdir:
                # Determine class name from code
                import re
                class_match = re.search(r'public\s+class\s+(\w+)', code)
                class_name = class_match.group(1) if class_match else "Main"
                
                # Write code to file
                java_filename = filename or f"{class_name}.java"
                code_file = Path(tmpdir) / java_filename
                code_file.write_text(code)
                
                # Build command: compile and run
                command = f"javac /workspace/{java_filename} && java -cp /workspace {class_name}"
                
                # Container configuration
                container_config = {
                    "image": "eclipse-temurin:17-jdk-alpine",
                    "command": ["sh", "-c", command],
                    "volumes": {tmpdir: {"bind": "/workspace", "mode": "rw"}},
                    "working_dir": "/workspace",
                    "detach": True,
                    # "remove": False,
                    "mem_limit": self.memory_limit,
                    "nano_cpus": int(self.cpu_limit * 1e9),
                    "network_disabled": self.network_disabled,
                }
                
                # Pull image if not exists
                try:
                    self.client.images.get("eclipse-temurin:17-jdk-alpine")
                except docker.errors.ImageNotFound:
                    print("Pulling image eclipse-temurin:17-jdk-alpine...")
                    self.client.images.pull("eclipse-temurin:17-jdk-alpine")
                
                # Create and start container
                container = self.client.containers.create(**container_config)
                container.start()
                
                # Wait for completion with timeout
                try:
                    result = container.wait(timeout=self.timeout)
                    exit_code = result["StatusCode"]
                except Exception as e:
                    container.kill()
                    execution_time = time.time() - start_time
                    return {
                        "success": False,
                        "error": f"Execution timeout after {self.timeout}s",
                        "stdout": "",
                        "stderr": str(e),
                        "exit_code": -1,
                        "execution_time": execution_time
                    }
                
                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
                
                execution_time = time.time() - start_time
                
                return {
                    "success": exit_code == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "execution_time": execution_time
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": execution_time
            }
        
        finally:
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
    
    def is_available(self) -> bool:
        """Check if Docker is available."""
        return self.client is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Docker stats."""
        if not self.client:
            return {"available": False}
        
        try:
            info = self.client.info()
            return {
                "available": True,
                "containers": info.get("Containers", 0),
                "containers_running": info.get("ContainersRunning", 0),
                "images": info.get("Images", 0),
                "memory_total": info.get("MemTotal", 0),
                "cpus": info.get("NCPU", 0)
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }


# Export singleton instance
sandbox = DockerSandbox()
