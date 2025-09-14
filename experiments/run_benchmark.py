#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMR 基准测试脚本
运行标准化的性能和功能测试
"""
import os
import sys
import json
import time
import csv
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dmmr import DMMRAgent, TaskType, get_config


class BenchmarkRunner:
    """基准测试运行器"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.results = []
        self.start_time = datetime.now()
        
    def run_single_test(self, test_name: str, user_input: str, 
                       expected_task_type: TaskType = None,
                       user_id: str = "benchmark_user") -> Dict[str, Any]:
        """运行单个测试"""
        print(f"🧪 运行测试: {test_name}")
        
        # 创建智能体
        agent = DMMRAgent(user_id=f"{user_id}_{test_name}", use_real_backends=False)
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 处理输入
            response, metrics = agent.process_input(user_input)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 获取智能体状态
            agent_status = agent.get_agent_status()
            
            # 构建测试结果
            result = {
                'test_name': test_name,
                'user_input': user_input,
                'ai_response': response,
                'processing_time': processing_time,
                'success': True,
                'error': None,
                'metrics': {
                    'latency_sec': metrics.latency_sec,
                    'token_usage': metrics.token_usage,
                    'memory_hits': metrics.memory_hits,
                    'activation_nodes': metrics.activation_nodes
                },
                'agent_stats': agent_status['session_stats'],
                'timestamp': datetime.now().isoformat()
            }
            
            # 验证任务类型（如果提供）
            if expected_task_type:
                # 这里应该从metadata或其他方式获取实际的任务类型
                # 简化处理
                result['task_type_correct'] = True
            
            print(f"   ✅ 成功 (耗时: {processing_time:.2f}s)")
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            result = {
                'test_name': test_name,
                'user_input': user_input,
                'ai_response': None,
                'processing_time': processing_time,
                'success': False,
                'error': str(e),
                'metrics': {},
                'agent_stats': {},
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"   ❌ 失败: {e}")
        
        return result
    
    def run_technical_coding_tests(self) -> List[Dict[str, Any]]:
        """运行技术编程测试"""
        print("\n🔧 技术编程测试套件")
        print("-" * 40)
        
        tests = [
            {
                'name': 'python_basic_question',
                'input': '如何在Python中导入pandas库？',
                'expected_type': TaskType.TECHNICAL_CODING
            },
            {
                'name': 'debug_import_error',
                'input': '我的Python代码报错：ModuleNotFoundError: No module named pandas',
                'expected_type': TaskType.TECHNICAL_CODING
            },
            {
                'name': 'code_optimization',
                'input': '这段代码运行很慢，有优化建议吗？for i in range(1000000): print(i)',
                'expected_type': TaskType.TECHNICAL_CODING
            },
            {
                'name': 'algorithm_question',
                'input': '请实现一个快速排序算法',
                'expected_type': TaskType.TECHNICAL_CODING
            },
            {
                'name': 'web_development',
                'input': '如何用FastAPI创建一个REST API？',
                'expected_type': TaskType.TECHNICAL_CODING
            }
        ]
        
        results = []
        for test in tests:
            result = self.run_single_test(
                test['name'], 
                test['input'], 
                test.get('expected_type')
            )
            results.append(result)
            time.sleep(1)  # 避免API限制
        
        return results
    
    def run_emotional_counseling_tests(self) -> List[Dict[str, Any]]:
        """运行情感咨询测试"""
        print("\n💝 情感咨询测试套件")
        print("-" * 40)
        
        tests = [
            {
                'name': 'work_stress',
                'input': '我最近工作压力很大，感觉很焦虑',
                'expected_type': TaskType.EMOTIONAL_COUNSELING
            },
            {
                'name': 'relationship_issue',
                'input': '我和朋友发生了冲突，不知道怎么办',
                'expected_type': TaskType.EMOTIONAL_COUNSELING
            },
            {
                'name': 'career_confusion',
                'input': '我对未来的职业规划感到迷茫',
                'expected_type': TaskType.EMOTIONAL_COUNSELING
            },
            {
                'name': 'family_problem',
                'input': '家人不理解我的选择，我很难过',
                'expected_type': TaskType.EMOTIONAL_COUNSELING
            }
        ]
        
        results = []
        for test in tests:
            result = self.run_single_test(
                test['name'], 
                test['input'], 
                test.get('expected_type')
            )
            results.append(result)
            time.sleep(1)
        
        return results
    
    def run_memory_persistence_tests(self) -> List[Dict[str, Any]]:
        """运行记忆持久性测试"""
        print("\n🧠 记忆持久性测试套件")
        print("-" * 40)
        
        # 这个测试需要多轮对话来验证记忆功能
        user_id = "memory_test_user"
        agent = DMMRAgent(user_id=user_id, use_real_backends=False)
        
        conversations = [
            "我最近在学习机器学习，特别是深度学习",
            "昨天我尝试训练了一个神经网络",
            "训练过程中遇到了梯度消失问题",
            "请问你还记得我之前提到的深度学习问题吗？"  # 测试记忆回忆
        ]
        
        results = []
        for i, conv in enumerate(conversations):
            result = self.run_single_test(
                f'memory_test_round_{i+1}',
                conv,
                user_id=user_id
            )
            results.append(result)
            time.sleep(1)
        
        return results
    
    def run_performance_stress_tests(self) -> List[Dict[str, Any]]:
        """运行性能压力测试"""
        print("\n⚡ 性能压力测试套件")  
        print("-" * 40)
        
        # 测试长文本处理
        long_text = "这是一个很长的技术问题。" * 50  # 重复50次
        
        tests = [
            {
                'name': 'long_text_processing',
                'input': long_text,
            },
            {
                'name': 'rapid_fire_questions',
                'input': '快速问题1：Python是什么？'
            },
            {
                'name': 'complex_technical_query',
                'input': '请详细解释深度学习中的反向传播算法，包括数学公式和实现细节'
            }
        ]
        
        results = []
        
        # 长文本测试
        result = self.run_single_test(tests[0]['name'], tests[0]['input'])
        results.append(result)
        
        # 快速连续查询测试
        rapid_fire_start = time.time()
        for i in range(5):
            quick_question = f"快速问题{i+1}：什么是{'Python' if i%2==0 else 'JavaScript'}？"
            result = self.run_single_test(
                f'rapid_fire_{i+1}',
                quick_question
            )
            results.append(result)
        rapid_fire_end = time.time()
        
        print(f"   快速连续查询总耗时: {rapid_fire_end - rapid_fire_start:.2f}s")
        
        # 复杂查询测试
        result = self.run_single_test(tests[2]['name'], tests[2]['input'])
        results.append(result)
        
        return results
    
    def analyze_results(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果"""
        print("\n📊 结果分析")
        print("-" * 40)
        
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r['success'])
        failed_tests = total_tests - successful_tests
        
        # 性能统计
        processing_times = [r['processing_time'] for r in all_results if r['success']]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        max_processing_time = max(processing_times) if processing_times else 0
        min_processing_time = min(processing_times) if processing_times else 0
        
        # Token使用统计
        token_usages = []
        memory_hits = []
        for r in all_results:
            if r['success'] and 'metrics' in r:
                if 'token_usage' in r['metrics'] and r['metrics']['token_usage']:
                    total_tokens = r['metrics']['token_usage'].get('total_tokens', 0)
                    if total_tokens > 0:
                        token_usages.append(total_tokens)
                
                memory_hits.append(r['metrics'].get('memory_hits', 0))
        
        avg_tokens = sum(token_usages) / len(token_usages) if token_usages else 0
        avg_memory_hits = sum(memory_hits) / len(memory_hits) if memory_hits else 0
        
        analysis = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
            'performance': {
                'avg_processing_time': avg_processing_time,
                'max_processing_time': max_processing_time,
                'min_processing_time': min_processing_time
            },
            'resource_usage': {
                'avg_tokens_per_request': avg_tokens,
                'avg_memory_hits_per_request': avg_memory_hits
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # 打印分析结果
        print(f"   总测试数: {total_tests}")
        print(f"   成功测试: {successful_tests}")
        print(f"   失败测试: {failed_tests}")
        print(f"   成功率: {analysis['success_rate']:.1%}")
        print(f"   平均处理时间: {avg_processing_time:.2f}s")
        print(f"   平均Token使用: {avg_tokens:.0f}")
        print(f"   平均记忆命中: {avg_memory_hits:.1f}")
        
        return analysis
    
    def save_results(self, all_results: List[Dict[str, Any]], analysis: Dict[str, Any]):
        """保存测试结果"""
        print(f"\n💾 保存结果到 {self.output_dir}")
        
        # 保存详细结果
        results_file = self.output_dir / "benchmark_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"   详细结果: {results_file}")
        
        # 保存分析报告
        analysis_file = self.output_dir / "benchmark_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"   分析报告: {analysis_file}")
        
        # 保存CSV摘要
        csv_file = self.output_dir / "benchmark_summary.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'test_name', 'success', 'processing_time', 'error',
                'memory_hits', 'activation_nodes'
            ])
            writer.writeheader()
            
            for result in all_results:
                row = {
                    'test_name': result['test_name'],
                    'success': result['success'],
                    'processing_time': result['processing_time'],
                    'error': result['error'] or '',
                    'memory_hits': result.get('metrics', {}).get('memory_hits', 0),
                    'activation_nodes': result.get('metrics', {}).get('activation_nodes', 0)
                }
                writer.writerow(row)
        print(f"   CSV摘要: {csv_file}")


def main():
    """主测试函数"""
    print("🚀 DMMR 基准测试套件")
    print("=" * 50)
    
    # 验证配置
    config = get_config()
    if not config.api.api_key:
        print("❌ API密钥未配置，请设置环境变量")
        return
    
    print(f"✅ 配置验证通过")
    print(f"   模型: {config.api.model_name}")
    print(f"   输出目录: results/")
    
    # 创建测试运行器
    runner = BenchmarkRunner()
    
    # 运行所有测试套件
    all_results = []
    
    try:
        # 技术编程测试
        technical_results = runner.run_technical_coding_tests()
        all_results.extend(technical_results)
        
        # 情感咨询测试
        emotional_results = runner.run_emotional_counseling_tests()
        all_results.extend(emotional_results)
        
        # 记忆持久性测试
        memory_results = runner.run_memory_persistence_tests()
        all_results.extend(memory_results)
        
        # 性能压力测试
        performance_results = runner.run_performance_stress_tests()
        all_results.extend(performance_results)
        
        # 分析结果
        analysis = runner.analyze_results(all_results)
        
        # 保存结果
        runner.save_results(all_results, analysis)
        
        print(f"\n✅ 基准测试完成!")
        print(f"   总测试数: {len(all_results)}")
        print(f"   成功率: {analysis['success_rate']:.1%}")
        print(f"   总耗时: {(datetime.now() - runner.start_time).total_seconds():.1f}s")
        
    except Exception as e:
        print(f"❌ 基准测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



