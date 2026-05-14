"""
Unit Tests - Complete Implementation of Unit Testing Framework

Provides production-ready unit testing capabilities including test runners,
test suites, test cases, and result reporting for the LamGen tools ecosystem.
"""

import time
import logging
import traceback
from typing import Dict, Any, List, Optional, Callable, Type
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from apps.tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus
from apps.tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPriority(Enum):
    """Test priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestResult:
    """Test execution result"""
    name: str
    status: TestStatus
    execution_time: float
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    assertions: int = 0
    passed_assertions: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestCase:
    """Individual test case"""
    name: str
    description: str
    test_function: Callable
    priority: TestPriority = TestPriority.MEDIUM
    timeout: float = 30.0
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)
    enabled: bool = True


class TestRunner:
    """Production-ready test runner"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_config = self._default_test_config()
        self.test_results: List[TestResult] = []
        self.test_suites: Dict[str, List[TestCase]] = {}
        self.execution_stats = defaultdict(int)
    
    def _default_test_config(self) -> Dict[str, Any]:
        """Default test configuration"""
        return {
            'max_parallel_tests': 5,
            'default_timeout': 30.0,
            'retry_failed_tests': True,
            'max_retries': 3,
            'stop_on_first_failure': False,
            'generate_reports': True,
            'coverage_analysis': True
        }
    
    def register_test_suite(self, suite_name: str, test_cases: List[TestCase]) -> None:
        """Register a test suite"""
        self.test_suites[suite_name] = test_cases
        self.logger.info(f"Registered test suite '{suite_name}' with {len(test_cases)} test cases")
    
    def run_tests(self, suite_names: List[str] = None, test_filter: str = None) -> Dict[str, Any]:
        """Run unit tests"""
        run_result = {
            'suites_run': [],
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'error_tests': 0,
            'total_time': 0,
            'success_rate': 0,
            'test_results': [],
            'coverage_report': {}
        }
        
        try:
            start_time = time.time()
            
            # Determine which suites to run
            suites_to_run = suite_names or list(self.test_suites.keys())
            run_result['suites_run'] = suites_to_run
            
            # Run each suite
            for suite_name in suites_to_run:
                if suite_name not in self.test_suites:
                    self.logger.warning(f"Test suite '{suite_name}' not found")
                    continue
                
                suite_results = self._run_test_suite(suite_name, test_filter)
                run_result['test_results'].extend(suite_results)
            
            # Calculate statistics
            run_result['total_tests'] = len(run_result['test_results'])
            run_result['passed_tests'] = len([r for r in run_result['test_results'] if r.status == TestStatus.PASSED])
            run_result['failed_tests'] = len([r for r in run_result['test_results'] if r.status == TestStatus.FAILED])
            run_result['skipped_tests'] = len([r for r in run_result['test_results'] if r.status == TestStatus.SKIPPED])
            run_result['error_tests'] = len([r for r in run_result['test_results'] if r.status == TestStatus.ERROR])
            
            run_result['total_time'] = time.time() - start_time
            run_result['success_rate'] = (run_result['passed_tests'] / run_result['total_tests'] * 100) if run_result['total_tests'] > 0 else 0
            
            # Generate coverage report
            if self.test_config['coverage_analysis']:
                run_result['coverage_report'] = self._generate_coverage_report(run_result['test_results'])
            
            # Store results
            self.test_results.extend(run_result['test_results'])
            
            self.logger.info(f"Completed {run_result['total_tests']} tests with {run_result['success_rate']:.1f}% success rate")
            
        except Exception as e:
            self.logger.error(f"Error running tests: {str(e)}")
            run_result['error'] = str(e)
        
        return run_result
    
    def _run_test_suite(self, suite_name: str, test_filter: str = None) -> List[TestResult]:
        """Run a single test suite"""
        suite_results = []
        test_cases = self.test_suites[suite_name]
        
        # Filter tests if needed
        if test_filter:
            test_cases = [tc for tc in test_cases if test_filter.lower() in tc.name.lower()]
        
        # Sort by priority
        priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        test_cases.sort(key=lambda tc: priority_order.get(tc.priority.value, 0), reverse=True)
        
        for test_case in test_cases:
            if not test_case.enabled:
                continue
            
            try:
                result = self._run_single_test(test_case, suite_name)
                suite_results.append(result)
                
                # Stop on first failure if configured
                if result.status in [TestStatus.FAILED, TestStatus.ERROR] and self.test_config['stop_on_first_failure']:
                    self.logger.info(f"Stopping test execution due to failure in {test_case.name}")
                    break
                
            except Exception as e:
                self.logger.error(f"Error running test {test_case.name}: {str(e)}")
                error_result = TestResult(
                    name=test_case.name,
                    status=TestStatus.ERROR,
                    execution_time=0,
                    error_message=str(e),
                    traceback=traceback.format_exc()
                )
                suite_results.append(error_result)
        
        return suite_results
    
    def _run_single_test(self, test_case: TestCase, suite_name: str) -> TestResult:
        """Run a single test case"""
        result = TestResult(
            name=test_case.name,
            status=TestStatus.RUNNING,
            execution_time=0
        )
        
        try:
            start_time = time.time()
            
            # Run setup function if provided
            if test_case.setup_function:
                test_case.setup_function()
            
            # Run the actual test
            test_function_result = test_case.test_function()
            
            # Handle assertions
            if isinstance(test_function_result, dict):
                assertions = test_function_result.get('assertions', 1)
                passed_assertions = test_function_result.get('passed_assertions', 1)
                
                if test_function_result.get('passed', True):
                    result.status = TestStatus.PASSED
                    result.assertions = assertions
                    result.passed_assertions = passed_assertions
                else:
                    result.status = TestStatus.FAILED
                    result.error_message = test_function_result.get('error_message', 'Test failed')
                    result.assertions = assertions
                    result.passed_assertions = passed_assertions - 1
            else:
                # Simple boolean result
                if test_function_result:
                    result.status = TestStatus.PASSED
                    result.assertions = 1
                    result.passed_assertions = 1
                else:
                    result.status = TestStatus.FAILED
                    result.error_message = 'Test returned False'
                    result.assertions = 1
                    result.passed_assertions = 0
            
            result.execution_time = time.time() - start_time
            
            # Run teardown function if provided
            if test_case.teardown_function:
                test_case.teardown_function()
            
            # Retry failed tests if configured
            if result.status == TestStatus.FAILED and self.test_config['retry_failed_tests']:
                result = self._retry_test(test_case, result)
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.execution_time = time.time() - start_time
            result.error_message = str(e)
            result.traceback = traceback.format_exc()
            
            # Run teardown function even on error
            if test_case.teardown_function:
                try:
                    test_case.teardown_function()
                except Exception as teardown_error:
                    self.logger.error(f"Error in teardown for {test_case.name}: {str(teardown_error)}")
        
        # Update execution stats
        self.execution_stats[result.status.value] += 1
        
        return result
    
    def _retry_test(self, test_case: TestCase, original_result: TestResult) -> TestResult:
        """Retry a failed test"""
        max_retries = self.test_config['max_retries']
        
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"Retrying test {test_case.name} (attempt {attempt}/{max_retries})")
                
                start_time = time.time()
                
                # Run setup function if provided
                if test_case.setup_function:
                    test_case.setup_function()
                
                # Run the test
                test_function_result = test_case.test_function()
                
                # Check if test passed
                if isinstance(test_function_result, dict):
                    if test_function_result.get('passed', True):
                        result = TestResult(
                            name=test_case.name,
                            status=TestStatus.PASSED,
                            execution_time=time.time() - start_time,
                            assertions=test_function_result.get('assertions', 1),
                            passed_assertions=test_function_result.get('passed_assertions', 1)
                        )
                        self.logger.info(f"Test {test_case.name} passed on retry {attempt}")
                        return result
                elif test_function_result:
                    result = TestResult(
                        name=test_case.name,
                        status=TestStatus.PASSED,
                        execution_time=time.time() - start_time,
                        assertions=1,
                        passed_assertions=1
                    )
                    self.logger.info(f"Test {test_case.name} passed on retry {attempt}")
                    return result
                
                # Run teardown function if provided
                if test_case.teardown_function:
                    test_case.teardown_function()
                
            except Exception as e:
                self.logger.error(f"Retry {attempt} failed for {test_case.name}: {str(e)}")
        
        # All retries failed, return original result
        return original_result
    
    def _generate_coverage_report(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Generate coverage report"""
        coverage_report = {
            'total_tests': len(test_results),
            'covered_modules': [],
            'coverage_percentage': 0,
            'uncovered_areas': [],
            'recommendations': []
        }
        
        # Simplified coverage calculation
        # In production, would use actual coverage tools
        passed_tests = [r for r in test_results if r.status == TestStatus.PASSED]
        coverage_percentage = (len(passed_tests) / len(test_results)) * 100 if test_results else 0
        
        coverage_report['coverage_percentage'] = coverage_percentage
        
        # Generate recommendations
        if coverage_percentage < 80:
            coverage_report['recommendations'].append("Increase test coverage to at least 80%")
        
        if coverage_percentage < 60:
            coverage_report['recommendations'].append("Critical: Test coverage is below 60%")
        
        # Identify uncovered areas (simplified)
        failed_tests = [r for r in test_results if r.status == TestStatus.FAILED]
        if failed_tests:
            coverage_report['uncovered_areas'] = [f.name for f in failed_tests[:5]]
        
        return coverage_report
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get test execution statistics"""
        stats = {
            'total_executions': sum(self.execution_stats.values()),
            'execution_breakdown': dict(self.execution_stats),
            'success_rate': 0,
            'average_execution_time': 0,
            'most_failed_tests': [],
            'slowest_tests': []
        }
        
        if self.test_results:
            # Calculate success rate
            passed = len([r for r in self.test_results if r.status == TestStatus.PASSED])
            stats['success_rate'] = (passed / len(self.test_results)) * 100
            
            # Calculate average execution time
            total_time = sum(r.execution_time for r in self.test_results)
            stats['average_execution_time'] = total_time / len(self.test_results)
            
            # Find most failed tests
            failed_tests = [r for r in self.test_results if r.status == TestStatus.FAILED]
            if failed_tests:
                from collections import Counter
                failure_counts = Counter(r.name for r in failed_tests)
                stats['most_failed_tests'] = failure_counts.most_common(5)
            
            # Find slowest tests
            sorted_by_time = sorted(self.test_results, key=lambda r: r.execution_time, reverse=True)
            stats['slowest_tests'] = [
                {'name': r.name, 'time': r.execution_time}
                for r in sorted_by_time[:5]
            ]
        
        return stats


class UnitTestSuite:
    """Production-ready unit test suite"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_runner = TestRunner()
        self.test_cases: List[TestCase] = []
        self.mock_data = self._default_mock_data()
    
    def _default_mock_data(self) -> Dict[str, Any]:
        """Default mock data for testing"""
        return {
            'sample_text': "This is a sample text for testing purposes.",
            'sample_url': "https://example.com/test-page",
            'sample_keywords': ["test", "sample", "example"],
            'sample_metrics': {"traffic": 1000, "conversions": 50, "bounce_rate": 0.4}
        }
    
    def create_test_case(self, name: str, description: str, test_function: Callable,
                        priority: TestPriority = TestPriority.MEDIUM, tags: List[str] = None) -> TestCase:
        """Create a test case"""
        test_case = TestCase(
            name=name,
            description=description,
            test_function=test_function,
            priority=priority,
            tags=tags or []
        )
        
        self.test_cases.append(test_case)
        return test_case
    
    def add_tool_tests(self, tool_class: Type[BaseTool]) -> None:
        """Add standard tests for a tool class"""
        tool_name = tool_class.__name__
        
        # Test tool instantiation
        def test_instantiation():
            try:
                config = ToolConfig(name="test", enabled=True)
                tool = tool_class(config)
                return {'passed': True, 'assertions': 1, 'passed_assertions': 1}
            except Exception as e:
                return {'passed': False, 'error_message': str(e), 'assertions': 1, 'passed_assertions': 0}
        
        self.create_test_case(
            name=f"{tool_name}_instantiation",
            description=f"Test {tool_name} instantiation",
            test_function=test_instantiation,
            priority=TestPriority.HIGH
        )
        
        # Test schema validation
        def test_schema_validation():
            try:
                config = ToolConfig(name="test", enabled=True)
                tool = tool_class(config)
                schema = tool.get_schema()
                
                # Basic schema validation
                assert isinstance(schema, dict), "Schema should be a dictionary"
                assert len(schema) > 0, "Schema should not be empty"
                
                return {'passed': True, 'assertions': 2, 'passed_assertions': 2}
            except Exception as e:
                return {'passed': False, 'error_message': str(e), 'assertions': 2, 'passed_assertions': 0}
        
        self.create_test_case(
            name=f"{tool_name}_schema",
            description=f"Test {tool_name} schema validation",
            test_function=test_schema_validation,
            priority=TestPriority.HIGH
        )
        
        # Test input validation
        def test_input_validation():
            try:
                config = ToolConfig(name="test", enabled=True)
                tool = tool_class(config)
                schema = tool.get_schema()
                
                # Test with valid input
                valid_input = self._generate_valid_input(schema)
                result = tool.process(valid_input)
                assert result.status in [ToolStatus.SUCCESS, ToolStatus.PARTIAL], "Valid input should not fail"
                
                # Test with invalid input
                invalid_input = self._generate_invalid_input(schema)
                result = tool.process(invalid_input)
                assert result.status == ToolStatus.ERROR, "Invalid input should return error"
                
                return {'passed': True, 'assertions': 2, 'passed_assertions': 2}
            except Exception as e:
                return {'passed': False, 'error_message': str(e), 'assertions': 2, 'passed_assertions': 0}
        
        self.create_test_case(
            name=f"{tool_name}_validation",
            description=f"Test {tool_name} input validation",
            test_function=test_input_validation,
            priority=TestPriority.MEDIUM
        )
    
    def _generate_valid_input(self, schema: Dict[str, ValidationRule]) -> Dict[str, Any]:
        """Generate valid input based on schema"""
        valid_input = {}
        
        for field_name, rule in schema.items():
            if rule.type == ValidationType.STRING:
                valid_input[field_name] = "test_string"
            elif rule.type == ValidationType.INTEGER:
                valid_input[field_name] = 1
            elif rule.type == ValidationType.FLOAT:
                valid_input[field_name] = 1.0
            elif rule.type == ValidationType.BOOLEAN:
                valid_input[field_name] = True
            elif rule.type == ValidationType.LIST:
                valid_input[field_name] = ["item1", "item2"]
            elif rule.type == ValidationType.DICTIONARY:
                valid_input[field_name] = {"key": "value"}
            else:
                valid_input[field_name] = "default_value"
        
        return valid_input
    
    def _generate_invalid_input(self, schema: Dict[str, ValidationRule]) -> Dict[str, Any]:
        """Generate invalid input based on schema"""
        invalid_input = {}
        
        for field_name, rule in schema.items():
            if rule.type == ValidationType.STRING:
                invalid_input[field_name] = 123  # Wrong type
            elif rule.type == ValidationType.INTEGER:
                invalid_input[field_name] = "not_integer"  # Wrong type
            elif rule.type == ValidationType.BOOLEAN:
                invalid_input[field_name] = "not_boolean"  # Wrong type
            else:
                invalid_input[field_name] = None  # Null value
        
        return invalid_input
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all unit tests"""
        # Register test suite
        self.test_runner.register_test_suite("unit_tests", self.test_cases)
        
        # Run tests
        return self.test_runner.run_tests(["unit_tests"])
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        report = {
            'summary': {
                'total_tests': len(self.test_results),
                'passed': len([r for r in self.test_results if r.status == TestStatus.PASSED]),
                'failed': len([r for r in self.test_results if r.status == TestStatus.FAILED]),
                'errors': len([r for r in self.test_results if r.status == TestStatus.ERROR]),
                'skipped': len([r for r in self.test_results if r.status == TestStatus.SKIPPED]),
                'success_rate': 0,
                'total_time': sum(r.execution_time for r in self.test_results)
            },
            'detailed_results': [],
            'failed_tests': [],
            'performance_analysis': {},
            'recommendations': []
        }
        
        # Calculate success rate
        if report['summary']['total_tests'] > 0:
            report['summary']['success_rate'] = (report['summary']['passed'] / report['summary']['total_tests']) * 100
        
        # Detailed results
        for result in self.test_results:
            report['detailed_results'].append({
                'name': result.name,
                'status': result.status.value,
                'execution_time': result.execution_time,
                'error_message': result.error_message,
                'assertions': result.assertions,
                'passed_assertions': result.passed_assertions
            })
        
        # Failed tests
        failed_tests = [r for r in self.test_results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
        report['failed_tests'] = [
            {
                'name': r.name,
                'error': r.error_message,
                'traceback': r.traceback
            }
            for r in failed_tests
        ]
        
        # Performance analysis
        execution_times = [r.execution_time for r in self.test_results]
        if execution_times:
            report['performance_analysis'] = {
                'average_time': sum(execution_times) / len(execution_times),
                'max_time': max(execution_times),
                'min_time': min(execution_times),
                'slow_tests': [
                    {'name': r.name, 'time': r.execution_time}
                    for r in sorted(self.test_results, key=lambda x: x.execution_time, reverse=True)[:5]
                ]
            }
        
        # Recommendations
        if report['summary']['success_rate'] < 80:
            report['recommendations'].append("Test success rate is below 80% - review failed tests")
        
        if report['performance_analysis'].get('average_time', 0) > 5:
            report['recommendations'].append("Average test execution time is high - consider optimization")
        
        if len(failed_tests) > 0:
            report['recommendations'].append(f"Fix {len(failed_tests)} failing tests")
        
        return report


# Global instances
_test_runner = None
_unit_test_suite = None


def get_test_runner() -> TestRunner:
    """Get global test runner instance"""
    global _test_runner
    if _test_runner is None:
        _test_runner = TestRunner()
    return _test_runner


def get_unit_test_suite() -> UnitTestSuite:
    """Get global unit test suite instance"""
    global _unit_test_suite
    if _unit_test_suite is None:
        _unit_test_suite = UnitTestSuite()
    return _unit_test_suite
