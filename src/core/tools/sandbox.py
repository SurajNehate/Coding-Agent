"""LangChain tools for safe code execution in Docker sandbox."""
from langchain.tools import tool
from typing import Optional
from src.infrastructure.sandbox.docker_manager import sandbox


@tool
def execute_python_code(code: str, packages: Optional[str] = None) -> str:
    """Execute Python code safely in an isolated Docker container.
    
    Args:
        code: Python code to execute
        packages: Optional comma-separated list of pip packages to install
        
    Returns:
        Execution result with stdout, stderr, and exit code
        
    Example:
        execute_python_code("print('Hello, World!')")
        execute_python_code("import requests; print(requests.get('https://api.github.com').status_code)", packages="requests")
    """
    if not sandbox.is_available():
        return "❌ Docker sandbox not available. Please install and start Docker."
    
    # Parse packages
    package_list = None
    if packages:
        package_list = [p.strip() for p in packages.split(",")]
    
    result = sandbox.execute_python(code, packages=package_list)
    
    if result["success"]:
        output = f"✅ Execution successful ({result['execution_time']:.2f}s)\n\n"
        if result["stdout"]:
            output += f"Output:\n{result['stdout']}\n"
        return output
    else:
        output = f"❌ Execution failed ({result['execution_time']:.2f}s)\n\n"
        if result.get("error"):
            output += f"Error: {result['error']}\n"
        if result["stderr"]:
            output += f"Stderr:\n{result['stderr']}\n"
        return output


@tool
def execute_shell_command(command: str) -> str:
    """Execute a shell command safely in an isolated Docker container.
    
    Args:
        command: Shell command to execute
        
    Returns:
        Command output
        
    Example:
        execute_shell_command("ls -la")
        execute_shell_command("echo 'Hello' > test.txt && cat test.txt")
    """
    if not sandbox.is_available():
        return "❌ Docker sandbox not available. Please install and start Docker."
    
    result = sandbox.execute_shell(command)
    
    if result["success"]:
        output = f"✅ Command successful ({result['execution_time']:.2f}s)\n\n"
        if result["stdout"]:
            output += result["stdout"]
        return output
    else:
        output = f"❌ Command failed ({result['execution_time']:.2f}s)\n\n"
        if result.get("error"):
            output += f"Error: {result['error']}\n"
        if result["stderr"]:
            output += result["stderr"]
        return output


@tool
def test_python_code(code: str, test_code: str, packages: Optional[str] = None) -> str:
    """Test Python code by running it with test cases in a sandbox.
    
    Args:
        code: Python code to test
        test_code: Test code (pytest or unittest)
        packages: Optional comma-separated list of pip packages
        
    Returns:
        Test results
        
    Example:
        test_python_code(
            code="def add(a, b): return a + b",
            test_code="assert add(2, 3) == 5"
        )
    """
    if not sandbox.is_available():
        return "❌ Docker sandbox not available. Please install and start Docker."
    
    # Combine code and tests
    full_code = f"{code}\n\n# Tests\n{test_code}"
    
    # Parse packages
    package_list = ["pytest"] if not packages else ["pytest"] + [p.strip() for p in packages.split(",")]
    
    result = sandbox.execute_python(full_code, packages=package_list)
    
    if result["success"]:
        return f"✅ All tests passed ({result['execution_time']:.2f}s)\n\n{result['stdout']}"
    else:
        output = f"❌ Tests failed ({result['execution_time']:.2f}s)\n\n"
        if result["stderr"]:
            output += result["stderr"]
        return output


@tool
def check_sandbox_status() -> str:
    """Check if Docker sandbox is available and get stats.
    
    Returns:
        Sandbox status and statistics
    """
    if not sandbox.is_available():
        return "❌ Docker sandbox not available. Please install and start Docker."
    
    stats = sandbox.get_stats()
    
    if stats.get("available"):
        return f"""✅ Docker sandbox is available

Stats:
- Running containers: {stats.get('containers_running', 0)}
- Total containers: {stats.get('containers', 0)}
- Images: {stats.get('images', 0)}
- CPUs: {stats.get('cpus', 0)}
- Memory: {stats.get('memory_total', 0) / (1024**3):.1f} GB
"""
    else:
        return f"❌ Docker error: {stats.get('error', 'Unknown')}"


@tool
def execute_javascript_code(code: str, packages: Optional[str] = None) -> str:
    """Execute JavaScript code safely in an isolated Node.js container.
    
    Args:
        code: JavaScript code to execute
        packages: Optional comma-separated list of npm packages to install
        
    Returns:
        Execution result with stdout, stderr, and exit code
        
    Example:
        execute_javascript_code("console.log('Hello, World!');")
    """
    if not sandbox.is_available():
        return "❌ Docker sandbox not available. Please install and start Docker."
    
    # Parse packages
    package_list = None
    if packages:
        package_list = [p.strip() for p in packages.split(",")]
    
    result = sandbox.execute_javascript(code, packages=package_list)
    
    if result["success"]:
        output = f"✅ Execution successful ({result['execution_time']:.2f}s)\n\n"
        if result["stdout"]:
            output += f"Output:\n{result['stdout']}\n"
        return output
    else:
        output = f"❌ Execution failed ({result['execution_time']:.2f}s)\n\n"
        if result.get("error"):
            output += f"Error: {result['error']}\n"
        if result["stderr"]:
            output += f"Stderr:\n{result['stderr']}\n"
        return output


@tool
def execute_java_code(code: str) -> str:
    """Execute Java code safely in an isolated container.
    
    Args:
        code: Java code to execute (must contain a Main class with main method)
        
    Returns:
        Execution result with stdout, stderr, and exit code
        
    Example:
        execute_java_code('''
        public class Main {
            public static void main(String[] args) {
                System.out.println("Hello World");
            }
        }
        ''')
    """
    if not sandbox.is_available():
        return "❌ Docker sandbox not available. Please install and start Docker."
    
    result = sandbox.execute_java(code)
    
    if result["success"]:
        output = f"✅ Execution successful ({result['execution_time']:.2f}s)\n\n"
        if result["stdout"]:
            output += f"Output:\n{result['stdout']}\n"
        return output
    else:
        output = f"❌ Execution failed ({result['execution_time']:.2f}s)\n\n"
        if result.get("error"):
            output += f"Error: {result['error']}\n"
        if result["stderr"]:
            output += f"Stderr:\n{result['stderr']}\n"
        return output


# Export all tools
__all__ = [
    "execute_python_code",
    "execute_shell_command",
    "test_python_code",
    "check_sandbox_status",
    "execute_javascript_code",
    "execute_java_code"
]
