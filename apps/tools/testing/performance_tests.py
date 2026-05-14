"""
Performance Tests - Complete Implementation of Performance Testing Framework

Provides production-ready performance testing capabilities including benchmarks,
load testing, stress testing, and scalability testing for the LamGen tools ecosystem.
"""

import time
import threading
import concurrent.futures
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from apps.tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus


class TestType(Enum):
    """Performance test types"""
    BENCHMARK = "benchmark"
    LOAD = "load"
    STRESS = "stress"
    SCALABILITY = "scalability"
    ENDURANCE = "endurance"


class MetricType(Enum):
    """Performance metric types"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    ERROR_RATE = "error_rate"
    CONCURRENCY = "concurrency"


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    name: str
    type: MetricType
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Benchmark test result"""
    test_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    throughput: float
    success_rate: float
    iterations: int
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceBenchmarker:
    """Production-ready performance benchmarker"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.benchmark_config = self._default_benchmark_config()
        self.benchmark_results: List[BenchmarkResult] = []
        self.performance_metrics: List[PerformanceMetric] = []
        self.system_monitor = SystemMonitor()
    
    def _default_benchmark_config(self) -> Dict[str, Any]:
        """Default benchmark configuration"""
        return {
            'warmup_iterations': 3,
            'benchmark_iterations': 10,
            'timeout_seconds': 30,
            'memory_threshold_mb': 500,
            'cpu_threshold_percent': 80,
            'collect_system_metrics': True,
            'statistical_analysis': True
        }
    
    def benchmark_tool(self, tool_class: type, test_data: Dict[str, Any], 
                      iterations: int = None) -> BenchmarkResult:
        """Benchmark a tool's performance"""
        iterations = iterations or self.benchmark_config['benchmark_iterations']
        
        result = BenchmarkResult(
            test_name=tool_class.__name__,
            execution_time=0,
            memory_usage=0,
            cpu_usage=0,
            throughput=0,
            success_rate=0,
            iterations=iterations
        )
        
        try:
            # Start system monitoring
            if self.benchmark_config['collect_system_metrics']:
                self.system_monitor.start_monitoring()
            
            # Warmup phase
            self._warmup_tool(tool_class, test_data)
            
            # Benchmark phase
            execution_times = []
            memory_usages = []
            cpu_usages = []
            successful_runs = 0
            
            for i in range(iterations):
                try:
                    # Measure before execution
                    start_time = time.time()
                    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                    start_cpu = psutil.cpu_percent()
                    
                    # Execute tool
                    config = ToolConfig(name="benchmark_test", enabled=True)
                    tool = tool_class(config)
                    tool_result = tool.process(test_data)
                    
                    # Measure after execution
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                    end_cpu = psutil.cpu_percent()
                    
                    execution_time = end_time - start_time
                    memory_usage = end_memory - start_memory
                    cpu_usage = end_cpu - start_cpu
                    
                    execution_times.append(execution_time)
                    memory_usages.append(memory_usage)
                    cpu_usages.append(cpu_usage)
                    
                    if tool_result.status == ToolStatus.SUCCESS:
                        successful_runs += 1
                    
                except Exception as e:
                    self.logger.error(f"Benchmark iteration {i} failed: {str(e)}")
                    continue
            
            # Calculate metrics
            if execution_times:
                result.execution_time = sum(execution_times) / len(execution_times)
                result.memory_usage = sum(memory_usages) / len(memory_usages)
                result.cpu_usage = sum(cpu_usages) / len(cpu_usages)
                result.throughput = iterations / sum(execution_times) if sum(execution_times) > 0 else 0
                result.success_rate = (successful_runs / iterations) * 100
            
            # Store system metrics
            if self.benchmark_config['collect_system_metrics']:
                system_metrics = self.system_monitor.stop_monitoring()
                self.performance_metrics.extend(system_metrics)
            
            # Store benchmark result
            self.benchmark_results.append(result)
            
            self.logger.info(f"Benchmark completed for {tool_class.__name__}: {result.execution_time:.3f}s avg")
            
        except Exception as e:
            self.logger.error(f"Error benchmarking {tool_class.__name__}: {str(e)}")
            result.error = str(e)
        
        return result
    
    def _warmup_tool(self, tool_class: type, test_data: Dict[str, Any]) -> None:
        """Warm up tool before benchmarking"""
        for i in range(self.benchmark_config['warmup_iterations']):
            try:
                config = ToolConfig(name="warmup_test", enabled=True)
                tool = tool_class(config)
                tool.process(test_data)
            except Exception as e:
                self.logger.warning(f"Warmup iteration {i} failed: {str(e)}")
    
    def run_comparative_benchmark(self, tools: List[type], test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comparative benchmark across multiple tools"""
        comparative_result = {
            'tools_tested': len(tools),
            'test_data': test_data,
            'results': {},
            'rankings': {},
            'performance_comparison': {},
            'recommendations': []
        }
        
        try:
            # Benchmark each tool
            for tool_class in tools:
                result = self.benchmark_tool(tool_class, test_data)
                comparative_result['results'][tool_class.__name__] = result
            
            # Generate rankings
            rankings = self._generate_performance_rankings(comparative_result['results'])
            comparative_result['rankings'] = rankings
            
            # Performance comparison
            comparison = self._compare_performance(comparative_result['results'])
            comparative_result['performance_comparison'] = comparison
            
            # Generate recommendations
            recommendations = self._generate_performance_recommendations(comparative_result['results'])
            comparative_result['recommendations'] = recommendations
            
        except Exception as e:
            self.logger.error(f"Error in comparative benchmark: {str(e)}")
            comparative_result['error'] = str(e)
        
        return comparative_result
    
    def _generate_performance_rankings(self, results: Dict[str, BenchmarkResult]) -> Dict[str, List[str]]:
        """Generate performance rankings"""
        rankings = {
            'fastest': [],
            'most_efficient': [],
            'highest_throughput': [],
            'most_reliable': []
        }
        
        # Sort by execution time (fastest first)
        sorted_by_time = sorted(results.items(), key=lambda x: x[1].execution_time)
        rankings['fastest'] = [name for name, _ in sorted_by_time]
        
        # Sort by memory usage (most efficient first)
        sorted_by_memory = sorted(results.items(), key=lambda x: x[1].memory_usage)
        rankings['most_efficient'] = [name for name, _ in sorted_by_memory]
        
        # Sort by throughput (highest first)
        sorted_by_throughput = sorted(results.items(), key=lambda x: x[1].throughput, reverse=True)
        rankings['highest_throughput'] = [name for name, _ in sorted_by_throughput]
        
        # Sort by success rate (most reliable first)
        sorted_by_success = sorted(results.items(), key=lambda x: x[1].success_rate, reverse=True)
        rankings['most_reliable'] = [name for name, _ in sorted_by_success]
        
        return rankings
    
    def _compare_performance(self, results: Dict[str, BenchmarkResult]) -> Dict[str, Any]:
        """Compare performance across tools"""
        comparison = {
            'execution_time_stats': {},
            'memory_usage_stats': {},
            'throughput_stats': {},
            'success_rate_stats': {}
        }
        
        if not results:
            return comparison
        
        # Calculate statistics for each metric
        execution_times = [r.execution_time for r in results.values()]
        memory_usages = [r.memory_usage for r in results.values()]
        throughputs = [r.throughput for r in results.values()]
        success_rates = [r.success_rate for r in results.values()]
        
        comparison['execution_time_stats'] = self._calculate_statistics(execution_times)
        comparison['memory_usage_stats'] = self._calculate_statistics(memory_usages)
        comparison['throughput_stats'] = self._calculate_statistics(throughputs)
        comparison['success_rate_stats'] = self._calculate_statistics(success_rates)
        
        return comparison
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistical measures"""
        if not values:
            return {}
        
        return {
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'median': sorted(values)[len(values) // 2],
            'std_dev': (sum((x - sum(values) / len(values)) ** 2 for x in values) / len(values)) ** 0.5
        }
    
    def _generate_performance_recommendations(self, results: Dict[str, BenchmarkResult]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        if not results:
            return recommendations
        
        # Check for performance issues
        avg_execution_time = sum(r.execution_time for r in results.values()) / len(results)
        if avg_execution_time > 5.0:
            recommendations.append("Average execution time is high - consider optimization")
        
        avg_memory_usage = sum(r.memory_usage for r in results.values()) / len(results)
        if avg_memory_usage > 100:  # 100MB
            recommendations.append("High memory usage detected - review memory management")
        
        avg_success_rate = sum(r.success_rate for r in results.values()) / len(results)
        if avg_success_rate < 95:
            recommendations.append("Success rate is below 95% - improve error handling")
        
        # Identify best performing tools
        best_tool = min(results.items(), key=lambda x: x[1].execution_time)
        recommendations.append(f"Best performing tool: {best_tool[0]} ({best_tool[1].execution_time:.3f}s)")
        
        return recommendations
    
    def get_benchmark_summary(self) -> Dict[str, Any]:
        """Get benchmark summary statistics"""
        summary = {
            'total_benchmarks': len(self.benchmark_results),
            'average_execution_time': 0,
            'average_memory_usage': 0,
            'average_throughput': 0,
            'average_success_rate': 0,
            'performance_trends': {},
            'tool_performance': {}
        }
        
        if not self.benchmark_results:
            return summary
        
        # Calculate averages
        summary['average_execution_time'] = sum(r.execution_time for r in self.benchmark_results) / len(self.benchmark_results)
        summary['average_memory_usage'] = sum(r.memory_usage for r in self.benchmark_results) / len(self.benchmark_results)
        summary['average_throughput'] = sum(r.throughput for r in self.benchmark_results) / len(self.benchmark_results)
        summary['average_success_rate'] = sum(r.success_rate for r in self.benchmark_results) / len(self.benchmark_results)
        
        # Group by tool
        tool_performance = defaultdict(list)
        for result in self.benchmark_results:
            tool_performance[result.test_name].append(result)
        
        # Calculate tool-specific stats
        for tool_name, results in tool_performance.items():
            summary['tool_performance'][tool_name] = {
                'benchmarks': len(results),
                'avg_execution_time': sum(r.execution_time for r in results) / len(results),
                'avg_memory_usage': sum(r.memory_usage for r in results) / len(results),
                'avg_throughput': sum(r.throughput for r in results) / len(results),
                'avg_success_rate': sum(r.success_rate for r in results) / len(results)
            }
        
        return summary


class LoadTester:
    """Production-ready load tester"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.load_config = self._default_load_config()
        self.load_results: List[Dict[str, Any]] = []
    
    def _default_load_config(self) -> Dict[str, Any]:
        """Default load testing configuration"""
        return {
            'concurrent_users': 10,
            'ramp_up_time': 30,  # seconds
            'test_duration': 300,  # 5 minutes
            'max_response_time': 5.0,  # seconds
            'max_error_rate': 0.05,  # 5%
            'collect_detailed_metrics': True
        }
    
    def run_load_test(self, target_function: Callable, test_data: Dict[str, Any], 
                     concurrent_users: int = None) -> Dict[str, Any]:
        """Run load test"""
        concurrent_users = concurrent_users or self.load_config['concurrent_users']
        
        load_result = {
            'target_function': target_function.__name__,
            'concurrent_users': concurrent_users,
            'test_duration': self.load_config['test_duration'],
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0,
            'max_response_time': 0,
            'min_response_time': 0,
            'throughput': 0,
            'error_rate': 0,
            'response_times': [],
            'errors': []
        }
        
        try:
            self.logger.info(f"Starting load test with {concurrent_users} concurrent users")
            
            # Start load test
            start_time = time.time()
            response_times = []
            errors = []
            
            # Use ThreadPoolExecutor for concurrent execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                # Submit tasks
                futures = []
                for i in range(concurrent_users):
                    future = executor.submit(self._execute_load_test_user, target_function, test_data, start_time)
                    futures.append(future)
                
                # Collect results
                for future in concurrent.futures.as_completed(futures, timeout=self.load_config['test_duration']):
                    try:
                        user_result = future.result()
                        response_times.extend(user_result['response_times'])
                        errors.extend(user_result['errors'])
                        load_result['successful_requests'] += user_result['successful_requests']
                        load_result['failed_requests'] += user_result['failed_requests']
                    except Exception as e:
                        self.logger.error(f"Load test user failed: {str(e)}")
                        errors.append(str(e))
                        load_result['failed_requests'] += 1
            
            # Calculate metrics
            load_result['total_requests'] = load_result['successful_requests'] + load_result['failed_requests']
            load_result['response_times'] = response_times
            load_result['errors'] = errors
            
            if response_times:
                load_result['average_response_time'] = sum(response_times) / len(response_times)
                load_result['max_response_time'] = max(response_times)
                load_result['min_response_time'] = min(response_times)
            
            if load_result['total_requests'] > 0:
                load_result['error_rate'] = load_result['failed_requests'] / load_result['total_requests']
                load_result['throughput'] = load_result['total_requests'] / (time.time() - start_time)
            
            # Store result
            self.load_results.append(load_result)
            
            self.logger.info(f"Load test completed: {load_result['throughput']:.2f} req/s, {load_result['error_rate']:.2%} error rate")
            
        except Exception as e:
            self.logger.error(f"Error in load test: {str(e)}")
            load_result['error'] = str(e)
        
        return load_result
    
    def _execute_load_test_user(self, target_function: Callable, test_data: Dict[str, Any], 
                              start_time: float) -> Dict[str, Any]:
        """Execute load test for a single user"""
        user_result = {
            'response_times': [],
            'errors': [],
            'successful_requests': 0,
            'failed_requests': 0
        }
        
        # Simulate user behavior for test duration
        end_time = start_time + self.load_config['test_duration']
        
        while time.time() < end_time:
            try:
                request_start = time.time()
                
                # Execute target function
                result = target_function(test_data)
                
                request_time = time.time() - request_start
                user_result['response_times'].append(request_time)
                user_result['successful_requests'] += 1
                
                # Small delay between requests
                time.sleep(0.1)
                
            except Exception as e:
                user_result['errors'].append(str(e))
                user_result['failed_requests'] += 1
        
        return user_result
    
    def analyze_load_test_results(self, load_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze load test results"""
        analysis = {
            'performance_grade': 'A',
            'bottlenecks': [],
            'recommendations': [],
            'scalability_assessment': {},
            'capacity_planning': {}
        }
        
        try:
            # Grade performance
            grade = self._calculate_performance_grade(load_result)
            analysis['performance_grade'] = grade
            
            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(load_result)
            analysis['bottlenecks'] = bottlenecks
            
            # Generate recommendations
            recommendations = self._generate_load_test_recommendations(load_result, bottlenecks)
            analysis['recommendations'] = recommendations
            
            # Assess scalability
            scalability = self._assess_scalability(load_result)
            analysis['scalability_assessment'] = scalability
            
            # Capacity planning
            capacity = self._estimate_capacity(load_result)
            analysis['capacity_planning'] = capacity
            
        except Exception as e:
            self.logger.error(f"Error analyzing load test results: {str(e)}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _calculate_performance_grade(self, load_result: Dict[str, Any]) -> str:
        """Calculate performance grade"""
        avg_response_time = load_result.get('average_response_time', 0)
        error_rate = load_result.get('error_rate', 0)
        throughput = load_result.get('throughput', 0)
        
        # Grade based on multiple factors
        if avg_response_time < 1.0 and error_rate < 0.01 and throughput > 100:
            return 'A'
        elif avg_response_time < 2.0 and error_rate < 0.02 and throughput > 50:
            return 'B'
        elif avg_response_time < 5.0 and error_rate < 0.05 and throughput > 20:
            return 'C'
        else:
            return 'D'
    
    def _identify_bottlenecks(self, load_result: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        avg_response_time = load_result.get('average_response_time', 0)
        max_response_time = load_result.get('max_response_time', 0)
        error_rate = load_result.get('error_rate', 0)
        
        if avg_response_time > 3.0:
            bottlenecks.append("High average response time")
        
        if max_response_time > 10.0:
            bottlenecks.append("Very high maximum response time")
        
        if error_rate > 0.05:
            bottlenecks.append("High error rate")
        
        # Check response time distribution
        response_times = load_result.get('response_times', [])
        if response_times:
            percentile_95 = sorted(response_times)[int(len(response_times) * 0.95)]
            if percentile_95 > 5.0:
                bottlenecks.append("95th percentile response time too high")
        
        return bottlenecks
    
    def _generate_load_test_recommendations(self, load_result: Dict[str, Any], 
                                           bottlenecks: List[str]) -> List[str]:
        """Generate load test recommendations"""
        recommendations = []
        
        if "High average response time" in bottlenecks:
            recommendations.append("Optimize code for better performance")
            recommendations.append("Consider caching frequently accessed data")
        
        if "High error rate" in bottlenecks:
            recommendations.append("Improve error handling and retry mechanisms")
            recommendations.append("Review resource allocation and limits")
        
        if "95th percentile response time too high" in bottlenecks:
            recommendations.append("Investigate performance outliers")
            recommendations.append("Implement request queuing and throttling")
        
        # General recommendations
        throughput = load_result.get('throughput', 0)
        if throughput < 50:
            recommendations.append("Consider horizontal scaling for better throughput")
        
        return recommendations
    
    def _assess_scalability(self, load_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess system scalability"""
        assessment = {
            'current_capacity': load_result.get('throughput', 0),
            'scalability_factor': 1.0,
            'recommended_max_users': 0,
            'scaling_strategy': 'vertical'
        }
        
        # Estimate scalability based on performance
        concurrent_users = load_result.get('concurrent_users', 1)
        throughput = load_result.get('throughput', 0)
        
        if throughput > 0:
            # Estimate linear scalability
            assessment['scalability_factor'] = throughput / concurrent_users
            assessment['recommended_max_users'] = int(1000 / assessment['scalability_factor'])  # Target 1000 req/s
            
            # Recommend scaling strategy
            if assessment['scalability_factor'] < 5:
                assessment['scaling_strategy'] = 'vertical'
            else:
                assessment['scaling_strategy'] = 'horizontal'
        
        return assessment
    
    def _estimate_capacity(self, load_result: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate system capacity"""
        capacity = {
            'max_concurrent_users': 0,
            'max_throughput': 0,
            'resource_requirements': {},
            'scaling_recommendations': []
        }
        
        # Estimate based on current performance
        current_users = load_result.get('concurrent_users', 1)
        current_throughput = load_result.get('throughput', 0)
        error_rate = load_result.get('error_rate', 0)
        
        if error_rate < 0.05:  # If error rate is acceptable
            # Estimate maximum users (when error rate reaches 5%)
            capacity['max_concurrent_users'] = int(current_users * (0.05 / max(error_rate, 0.01)))
            capacity['max_throughput'] = int(current_throughput * (capacity['max_concurrent_users'] / current_users))
        
        # Resource requirements (simplified)
        capacity['resource_requirements'] = {
            'cpu_cores': max(2, current_users // 10),
            'memory_gb': max(4, current_users // 5),
            'network_bandwidth_mbps': max(100, current_users * 2)
        }
        
        return capacity


class StressTester:
    """Production-ready stress tester"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stress_config = self._default_stress_config()
        self.stress_results: List[Dict[str, Any]] = []
    
    def _default_stress_config(self) -> Dict[str, Any]:
        """Default stress testing configuration"""
        return {
            'max_concurrent_users': 100,
            'step_duration': 60,  # seconds
            'user_increment': 10,
            'max_test_duration': 1800,  # 30 minutes
            'failure_threshold': 0.1,  # 10% failure rate
            'response_time_threshold': 10.0  # seconds
        }
    
    def run_stress_test(self, target_function: Callable, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run stress test"""
        stress_result = {
            'test_name': 'stress_test',
            'max_users_reached': 0,
            'breaking_point': 0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'peak_throughput': 0,
            'average_response_time': 0,
            'stress_curve': [],
            'system_limits': {},
            'recommendations': []
        }
        
        try:
            self.logger.info("Starting stress test")
            
            current_users = self.stress_config['user_increment']
            max_users = self.stress_config['max_concurrent_users']
            step_duration = self.stress_config['step_duration']
            
            breaking_point = 0
            peak_throughput = 0
            
            while current_users <= max_users:
                step_start = time.time()
                
                # Run load test with current users
                load_tester = LoadTester()
                load_tester.load_config['concurrent_users'] = current_users
                load_tester.load_config['test_duration'] = step_duration
                
                step_result = load_tester.run_load_test(target_function, test_data)
                
                # Record stress curve point
                curve_point = {
                    'users': current_users,
                    'throughput': step_result.get('throughput', 0),
                    'response_time': step_result.get('average_response_time', 0),
                    'error_rate': step_result.get('error_rate', 0)
                }
                stress_result['stress_curve'].append(curve_point)
                
                # Update peak throughput
                if step_result.get('throughput', 0) > peak_throughput:
                    peak_throughput = step_result['throughput']
                
                # Check for breaking point
                error_rate = step_result.get('error_rate', 0)
                response_time = step_result.get('average_response_time', 0)
                
                if (error_rate > self.stress_config['failure_threshold'] or 
                    response_time > self.stress_config['response_time_threshold']):
                    breaking_point = current_users
                    break
                
                # Update totals
                stress_result['total_requests'] += step_result.get('total_requests', 0)
                stress_result['successful_requests'] += step_result.get('successful_requests', 0)
                stress_result['failed_requests'] += step_result.get('failed_requests', 0)
                
                current_users += self.stress_config['user_increment']
                stress_result['max_users_reached'] = current_users - self.stress_config['user_increment']
                
                # Check time limit
                if time.time() - step_start > self.stress_config['max_test_duration']:
                    break
            
            stress_result['breaking_point'] = breaking_point or current_users
            stress_result['peak_throughput'] = peak_throughput
            
            # Calculate average response time across all steps
            if stress_result['stress_curve']:
                stress_result['average_response_time'] = sum(
                    point['response_time'] for point in stress_result['stress_curve']
                ) / len(stress_result['stress_curve'])
            
            # Identify system limits
            stress_result['system_limits'] = self._identify_system_limits(stress_result['stress_curve'])
            
            # Generate recommendations
            stress_result['recommendations'] = self._generate_stress_test_recommendations(stress_result)
            
            # Store result
            self.stress_results.append(stress_result)
            
            self.logger.info(f"Stress test completed. Breaking point: {stress_result['breaking_point']} users")
            
        except Exception as e:
            self.logger.error(f"Error in stress test: {str(e)}")
            stress_result['error'] = str(e)
        
        return stress_result
    
    def _identify_system_limits(self, stress_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify system limits from stress curve"""
        limits = {
            'max_sustainable_users': 0,
            'throughput_limit': 0,
            'response_time_limit': 0,
            'bottleneck_type': 'unknown'
        }
        
        if not stress_curve:
            return limits
        
        # Find maximum sustainable throughput
        max_throughput = 0
        max_sustainable_users = 0
        
        for point in stress_curve:
            if point['error_rate'] < 0.05 and point['response_time'] < 5.0:
                if point['throughput'] > max_throughput:
                    max_throughput = point['throughput']
                    max_sustainable_users = point['users']
        
        limits['max_sustainable_users'] = max_sustainable_users
        limits['throughput_limit'] = max_throughput
        
        # Identify bottleneck type
        if stress_curve:
            last_point = stress_curve[-1]
            if last_point['error_rate'] > 0.1:
                limits['bottleneck_type'] = 'resource_exhaustion'
            elif last_point['response_time'] > 10.0:
                limits['bottleneck_type'] = 'performance_degradation'
            else:
                limits['bottleneck_type'] = 'none_detected'
        
        return limits
    
    def _generate_stress_test_recommendations(self, stress_result: Dict[str, Any]) -> List[str]:
        """Generate stress test recommendations"""
        recommendations = []
        
        breaking_point = stress_result.get('breaking_point', 0)
        max_users = stress_result.get('max_users_reached', 0)
        system_limits = stress_result.get('system_limits', {})
        
        if breaking_point < max_users:
            recommendations.append(f"System breaks at {breaking_point} users - consider scaling")
        
        bottleneck_type = system_limits.get('bottleneck_type', 'unknown')
        if bottleneck_type == 'resource_exhaustion':
            recommendations.append("Resource exhaustion detected - increase system resources")
        elif bottleneck_type == 'performance_degradation':
            recommendations.append("Performance degradation under load - optimize code")
        
        max_sustainable = system_limits.get('max_sustainable_users', 0)
        if max_sustainable > 0:
            recommendations.append(f"System can sustain {max_sustainable} concurrent users")
        
        peak_throughput = stress_result.get('peak_throughput', 0)
        if peak_throughput < 100:
            recommendations.append("Low throughput detected - consider performance optimization")
        
        return recommendations


class SystemMonitor:
    """System resource monitor"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.monitoring_thread = None
        self.metrics: List[PerformanceMetric] = []
    
    def start_monitoring(self) -> None:
        """Start system monitoring"""
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_system)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_monitoring(self) -> List[PerformanceMetric]:
        """Stop system monitoring and return metrics"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        metrics = self.metrics.copy()
        self.metrics.clear()
        return metrics
    
    def _monitor_system(self) -> None:
        """Monitor system resources"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent()
                cpu_metric = PerformanceMetric(
                    name="cpu_usage",
                    type=MetricType.CPU_USAGE,
                    value=cpu_percent,
                    unit="percent"
                )
                self.metrics.append(cpu_metric)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_metric = PerformanceMetric(
                    name="memory_usage",
                    type=MetricType.MEMORY_USAGE,
                    value=memory.percent,
                    unit="percent"
                )
                self.metrics.append(memory_metric)
                
                # Sleep for monitoring interval
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error monitoring system: {str(e)}")
                break


# Global instances
_performance_benchmarker = None
_load_tester = None
_stress_tester = None


def get_performance_benchmarker() -> PerformanceBenchmarker:
    """Get global performance benchmarker instance"""
    global _performance_benchmarker
    if _performance_benchmarker is None:
        _performance_benchmarker = PerformanceBenchmarker()
    return _performance_benchmarker


def get_load_tester() -> LoadTester:
    """Get global load tester instance"""
    global _load_tester
    if _load_tester is None:
        _load_tester = LoadTester()
    return _load_tester


def get_stress_tester() -> StressTester:
    """Get global stress tester instance"""
    global _stress_tester
    if _stress_tester is None:
        _stress_tester = StressTester()
    return _stress_tester
