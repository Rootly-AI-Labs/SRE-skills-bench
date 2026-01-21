"""Benchmarking tool for testing LLM-generated Terraform code."""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from terraform_generation_bench.runner import TaskRunner, log_info, log_error
from terraform_generation_bench.terraform_generator import TerraformGenerator
from terraform_generation_bench.llm_client import LLMClientFactory


class BenchmarkRunner:
    """Runs benchmarks across multiple LLMs and tasks."""
    
    def __init__(self, generated_dir: Optional[Path] = None, 
                 results_dir: Optional[Path] = None):
        """Initialize benchmark runner.
        
        Args:
            generated_dir: Directory for generated terraform files (default: ./generated)
            results_dir: Directory for benchmark results (default: ./results)
        """
        # Use absolute paths from current working directory
        base_dir = Path.cwd()
        self.generated_dir = generated_dir or (base_dir / "generated")
        self.results_dir = results_dir or (base_dir / "results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def run_single_benchmark(self, provider: str, model: str, task_id: str, 
                            run_id: Optional[str] = None) -> Dict[str, Any]:
        """Run a single benchmark for one model and task.
        
        Args:
            provider: LLM provider ("openai", "anthropic")
            model: Model name
            task_id: Task identifier
            run_id: Optional run identifier (auto-generated if not provided)
            
        Returns:
            Benchmark result dictionary
        """
        if run_id is None:
            run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Replace both - and / with _ for valid directory names
        model_name = f"{provider}_{model.replace('-', '_').replace('/', '_')}"
        
        log_info(f"Running benchmark: {model_name} on {task_id}")
        
        result = {
            "provider": provider,
            "model": model,
            "model_name": model_name,
            "task_id": task_id,
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # Step 1: Load prompt from tasks directory
            prompt_file = Path("tasks") / task_id / "prompt.txt"
            if not prompt_file.exists():
                # Try absolute path from current working directory
                prompt_file = Path.cwd() / "tasks" / task_id / "prompt.txt"
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt file not found: tasks/{task_id}/prompt.txt")
            
            log_info(f"Loading prompt from: {prompt_file}")
            with open(prompt_file, 'r') as f:
                prompt = f.read()
            
            # Step 2: Generate Terraform code using the prompt text
            log_info(f"Step 1: Generating Terraform code with {model_name} using prompt.txt...")
            step_start = time.time()
            
            llm_client = LLMClientFactory.create_client(provider, model)
            generator = TerraformGenerator(llm_client)
            files = generator.generate(prompt, task_id, save_raw_response=True)
            
            result["steps"]["generation"] = {
                "success": True,
                "time": time.time() - step_start,
                "files_generated": list(files.keys()),
                "prompt_file": str(prompt_file)
            }
            
            # Step 3: Save generated files to new directory
            work_dir = self.generated_dir / model_name / task_id / run_id
            work_dir.mkdir(parents=True, exist_ok=True)
            generator.save_files(files, work_dir)
            log_info(f"Generated files saved to: {work_dir}")
            
            # Step 4: Run terraform pipeline
            log_info(f"Step 2: Running Terraform pipeline...")
            runner = TaskRunner(
                model_name=model_name,
                task_id=task_id,
                run_id=run_id,
                generated_dir=self.generated_dir,
                results_dir=self.results_dir
            )
            
            terraform_result = runner.run()
            
            # Merge results
            result["steps"]["terraform"] = {
                "success": terraform_result["pass"],
                "failure_category": terraform_result.get("failure_category"),
                "timings": terraform_result.get("timings", {}),
                "tool_exit_codes": terraform_result.get("tool_exit_codes", {})
            }
            
            # Step 5: Get check results if available
            check_file = runner.result_dir / "check.json"
            if check_file.exists():
                with open(check_file, 'r') as f:
                    check_result = json.load(f)
                result["steps"]["checks"] = check_result
            
            # Overall result
            result["overall_pass"] = terraform_result["pass"]
            result["total_time"] = (
                result["steps"].get("generation", {}).get("time", 0) +
                result["steps"].get("terraform", {}).get("timings", {}).get("total", 0)
            )
            
        except Exception as e:
            log_error(f"Benchmark failed: {e}")
            result["overall_pass"] = False
            result["error"] = str(e)
            result["steps"]["generation"] = {
                "success": False,
                "error": str(e)
            }
        
        # Save result
        result_file = self.results_dir / model_name / task_id / run_id / "benchmark_result.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    def run_benchmark_suite(self, models: List[Dict[str, str]], 
                           task_ids: List[str],
                           max_workers: Optional[int] = None) -> Dict[str, Any]:
        """Run benchmark suite across multiple models and tasks.
        
        Args:
            models: List of model configs [{"provider": "openai", "model": "gpt-4"}, ...]
            task_ids: List of task IDs to test
            max_workers: Maximum number of parallel workers (default: CPU count)
            
        Returns:
            Suite results dictionary
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import multiprocessing
        
        suite_start = time.time()
        suite_results = {
            "timestamp": datetime.now().isoformat(),
            "models": models,
            "tasks": task_ids,
            "results": []
        }
        
        # Determine number of workers
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), 4)  # Cap at 4 to avoid API rate limits
        
        # Create list of all benchmark jobs
        jobs = []
        for model_config in models:
            provider = model_config["provider"]
            model = model_config["model"]
            for task_id in task_ids:
                jobs.append((provider, model, task_id))
        
        log_info(f"Running {len(jobs)} benchmarks with {max_workers} parallel workers...")
        
        # Run benchmarks in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_job = {
                executor.submit(self.run_single_benchmark, provider, model, task_id): (provider, model, task_id)
                for provider, model, task_id in jobs
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_job):
                provider, model, task_id = future_to_job[future]
                completed += 1
                try:
                    result = future.result()
                    suite_results["results"].append(result)
                    status = "PASS" if result.get("overall_pass", False) else "FAIL"
                    log_info(f"[{completed}/{len(jobs)}] {provider}/{model} on {task_id}: {status}")
                except Exception as e:
                    log_error(f"Failed to run benchmark for {provider}/{model} on {task_id}: {e}")
                    suite_results["results"].append({
                        "provider": provider,
                        "model": model,
                        "task_id": task_id,
                        "overall_pass": False,
                        "error": str(e)
                    })
        
        suite_results["total_time"] = time.time() - suite_start
        
        # Save suite results
        suite_file = self.results_dir / f"benchmark_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(suite_file, 'w') as f:
            json.dump(suite_results, f, indent=2)
        
        return suite_results

