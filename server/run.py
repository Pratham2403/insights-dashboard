#!/usr/bin/env python3
"""
Sprinklr Listening Dashboard - Terminal Runner

This script provides an easy way to run and test the Sprinklr Listening Dashboard
from the terminal with various modes and options.

Usage:
    python run.py                              # Interactive mode
    python run.py --query "your query here"    # Single query mode
    python run.py --demo                       # Run demo with sample queries
    python run.py --test                       # Run system tests
    python run.py --web                        # Start web server
    python run.py --help                       # Show help
"""

import argparse
import asyncio
import sys
import os
import logging
from typing import List, Dict, Any

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('sprinklr_dashboard.log')
        ]
    )

class SprinklrDashboardRunner:
    """Main runner class for the Sprinklr Dashboard"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        setup_logging(verbose)
        self.logger = logging.getLogger(__name__)
    
    async def run_interactive_mode(self):
        """Run the interactive CLI mode"""
        try:
            from main import main
            print("🚀 Starting Sprinklr Dashboard in Interactive Mode...")
            await main()
        except ImportError as e:
            print(f"❌ Error importing main module: {e}")
            print("Make sure you're running from the server directory.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error in interactive mode: {e}")
            sys.exit(1)
    
    async def run_single_query(self, query: str):
        """Run a single query"""
        try:
            from main import run_single_query
            print(f"🔍 Processing query: '{query}'")
            print("This may take a few moments...\n")
            result = run_single_query(query)
            return result
        except ImportError as e:
            print(f"❌ Error importing main module: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            sys.exit(1)
    
    async def run_demo_mode(self):
        """Run demo mode with sample queries"""
        print("🎯 Sprinklr Dashboard - Demo Mode")
        print("=" * 50)
        print("Running sample queries to demonstrate functionality...\n")
        
        demo_queries = [
            "Show me Samsung smartphone mentions on Twitter",
            "Analyze Apple brand sentiment in the last week",
            "Tesla customer feedback and complaints",
            "Nike product reviews on social media",
            "Microsoft customer service issues"
        ]
        
        results = []
        for i, query in enumerate(demo_queries, 1):
            print(f"\n{'='*20} DEMO {i}/{len(demo_queries)} {'='*20}")
            print(f"Query: {query}")
            print("-" * 50)
            
            try:
                result = await self.run_single_query(query)
                results.append({"query": query, "result": result, "success": True})
            except Exception as e:
                print(f"❌ Demo query failed: {e}")
                results.append({"query": query, "error": str(e), "success": False})
                continue
        
        # Summary
        print(f"\n{'='*50}")
        print("📊 DEMO SUMMARY")
        print(f"{'='*50}")
        successful = sum(1 for r in results if r["success"])
        print(f"✅ Successful queries: {successful}/{len(demo_queries)}")
        print(f"❌ Failed queries: {len(demo_queries) - successful}/{len(demo_queries)}")
        
        if successful > 0:
            print("\n🎉 Demo completed successfully!")
        else:
            print("\n⚠️  All demo queries failed. Please check the system configuration.")
    
    async def run_system_tests(self):
        """Run basic system tests"""
        print("🧪 Running System Tests...")
        print("=" * 40)
        
        tests = [
            ("Import Test", self._test_imports),
            ("Workflow Test", self._test_workflow),
            ("Agent Test", self._test_agents),
            ("Basic Query Test", self._test_basic_query)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            print(f"\n🔧 {test_name}...")
            try:
                await test_func()
                print(f"✅ {test_name} PASSED")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name} FAILED: {e}")
        
        print(f"\n{'='*40}")
        print(f"📊 Test Results: {passed}/{len(tests)} passed")
        
        if passed == len(tests):
            print("🎉 All tests passed! System is ready.")
        else:
            print("⚠️  Some tests failed. Please check the configuration.")
            sys.exit(1)
    
    async def _test_imports(self):
        """Test that all required modules can be imported"""
        import importlib.util
        
        def import_module_from_file(filepath, module_name):
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        
        # Test workflow import
        workflow_path = os.path.join(os.path.dirname(__file__), 'src', 'workflow.py')
        workflow_module = import_module_from_file(workflow_path, 'workflow')
        
        # Test main module import
        from main import SprinklrDashboardCLI
    
    async def _test_workflow(self):
        """Test workflow initialization"""
        import importlib.util
        
        def import_module_from_file(filepath, module_name):
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        
        workflow_path = os.path.join(os.path.dirname(__file__), 'src', 'workflow.py')
        workflow_module = import_module_from_file(workflow_path, 'workflow')
        workflow = workflow_module.get_workflow()
        assert workflow is not None
    
    async def _test_agents(self):
        """Test that agents can be initialized"""
        import importlib.util
        
        def import_module_from_file(filepath, module_name):
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        
        agents_dir = os.path.join(os.path.dirname(__file__), 'src', 'agents')
        agent_files = [
            'query-refiner.agent.py',
            'hitl-verification.agent.py',
            'query-generator.agent.py',
            'data-collector.agent.py',
            'data-analyzer.agent.py'
        ]
        
        for agent_file in agent_files:
            agent_path = os.path.join(agents_dir, agent_file)
            if os.path.exists(agent_path):
                module_name = agent_file.replace('.py', '').replace('-', '_')
                import_module_from_file(agent_path, module_name)
    
    async def _test_basic_query(self):
        """Test a basic query"""
        from main import SprinklrDashboardCLI
        cli = SprinklrDashboardCLI()
        result = await cli.process_query("test query for system validation")
        assert result is not None
        assert isinstance(result, dict)
    
    def run_web_server(self, host: str = "localhost", port: int = 5000):
        """Run the web server"""
        try:
            print(f"🌐 Starting Sprinklr Dashboard Web Server on {host}:{port}")
            print("Press Ctrl+C to stop the server\n")
            
            from app import app
            app.run(host=host, port=port, debug=self.verbose)
        except ImportError as e:
            print(f"❌ Error importing Flask app: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error starting web server: {e}")
            sys.exit(1)
    
    def show_status(self):
        """Show system status"""
        print("⚙️  Sprinklr Dashboard - System Status")
        print("=" * 50)
        
        # Check Python version
        print(f"🐍 Python Version: {sys.version}")
        
        # Check directory structure
        server_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"📁 Server Directory: {server_dir}")
        
        required_files = [
            'src/main.py',
            'src/workflow.py',
            'app.py',
            'requirements.txt'
        ]
        
        print("\n📋 File Check:")
        for file in required_files:
            file_path = os.path.join(server_dir, file)
            status = "✅" if os.path.exists(file_path) else "❌"
            print(f"  {status} {file}")
        
        # Check agents
        agents_dir = os.path.join(server_dir, 'src', 'agents')
        if os.path.exists(agents_dir):
            agent_files = [f for f in os.listdir(agents_dir) if f.endswith('.agent.py')]
            print(f"\n🤖 Agents Found: {len(agent_files)}")
            for agent in agent_files:
                print(f"  ✅ {agent}")
        
        print("\n🎯 Ready to run! Use --help for available commands.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sprinklr Listening Dashboard Terminal Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                              # Interactive mode
  python run.py --query "Samsung mentions"   # Single query
  python run.py --demo                       # Demo mode
  python run.py --test                       # System tests
  python run.py --web                        # Web server
  python run.py --status                     # System status
        """
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Run a single query'
    )
    
    parser.add_argument(
        '--demo', '-d',
        action='store_true',
        help='Run demo mode with sample queries'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run system tests'
    )
    
    parser.add_argument(
        '--web', '-w',
        action='store_true',
        help='Start web server'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show system status'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host for web server (default: localhost)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Port for web server (default: 5000)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = SprinklrDashboardRunner(verbose=args.verbose)
    
    try:
        # Handle different modes
        if args.status:
            runner.show_status()
        elif args.test:
            asyncio.run(runner.run_system_tests())
        elif args.demo:
            asyncio.run(runner.run_demo_mode())
        elif args.query:
            asyncio.run(runner.run_single_query(args.query))
        elif args.web:
            runner.run_web_server(host=args.host, port=args.port)
        else:
            # Default to interactive mode
            asyncio.run(runner.run_interactive_mode())
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
