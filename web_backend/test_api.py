#!/usr/bin/env python3
"""Mock 测试脚本 - 验证后端 API 接口"""

import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8002"


async def test_api():
    """测试所有 API 接口"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        tests = []

        # 1. 测试根路径
        print("1. 测试根路径 GET /")
        try:
            resp = await client.get(f"{BASE_URL}/")
            print(f"   ✓ 状态码: {resp.status_code}")
            print(f"   ✓ 响应: {resp.json()}")
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            tests.append(False)
        else:
            tests.append(resp.status_code == 200)

        # 2. 测试统计接口
        print("\n2. 测试统计接口 GET /api/stats")
        try:
            resp = await client.get(f"{BASE_URL}/api/stats")
            print(f"   ✓ 状态码: {resp.status_code}")
            data = resp.json()
            print(f"   ✓ 简历数: {data.get('total_resumes', 0)}")
            print(f"   ✓ 岗位数: {data.get('total_jobs', 0)}")
            print(f"   ✓ 匹配数: {data.get('total_matches', 0)}")
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            tests.append(False)
        else:
            tests.append(resp.status_code == 200)

        # 3. 测试岗位列表
        print("\n3. 测试岗位列表 GET /api/jobs")
        try:
            resp = await client.get(f"{BASE_URL}/api/jobs?page=1&page_size=5")
            print(f"   ✓ 状态码: {resp.status_code}")
            data = resp.json()
            print(f"   ✓ 总数: {data.get('total', 0)}")
            print(f"   ✓ 返回: {len(data.get('jobs', []))} 条")
            if data.get('jobs'):
                print(f"   ✓ 第一条: {data['jobs'][0].get('job_id', 'N/A')} - {data['jobs'][0].get('job_title', 'N/A')}")
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            tests.append(False)
        else:
            tests.append(resp.status_code == 200)

        # 4. 测试简历列表
        print("\n4. 测试简历列表 GET /api/resumes")
        try:
            resp = await client.get(f"{BASE_URL}/api/resumes?page=1&page_size=5")
            print(f"   ✓ 状态码: {resp.status_code}")
            data = resp.json()
            print(f"   ✓ 总数: {data.get('total', 0)}")
            print(f"   ✓ 返回: {len(data.get('resumes', []))} 条")
            if data.get('resumes'):
                print(f"   ✓ 第一条: {data['resumes'][0].get('resume_id', 'N/A')} - {data['resumes'][0].get('name', 'N/A')}")
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            tests.append(False)
        else:
            tests.append(resp.status_code == 200)

        # 5. 测试岗位匹配（需要先获取一个 job_id）
        print("\n5. 测试岗位匹配 GET /api/jobs/{job_id}/matches")
        try:
            jobs_resp = await client.get(f"{BASE_URL}/api/jobs?page=1&page_size=1")
            jobs_data = jobs_resp.json()
            if jobs_data.get('jobs'):
                job_id = jobs_data['jobs'][0]['job_id']
                resp = await client.get(f"{BASE_URL}/api/jobs/{job_id}/matches?limit=5")
                print(f"   ✓ 状态码: {resp.status_code}")
                data = resp.json()
                print(f"   ✓ 岗位: {data.get('job_title', 'N/A')}")
                print(f"   ✓ 匹配数: {data.get('total_matches', 0)}")
                print(f"   ✓ 返回: {len(data.get('matches', []))} 条")
                tests.append(resp.status_code == 200)
            else:
                print(f"   ⊘ 跳过（无岗位数据）")
                tests.append(True)
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            tests.append(False)

        # 6. 测试简历推荐（需要先获取一个 resume_id）
        print("\n6. 测试简历推荐 GET /api/resumes/{resume_id}/recommendations")
        try:
            resumes_resp = await client.get(f"{BASE_URL}/api/resumes?page=1&page_size=1")
            resumes_data = resumes_resp.json()
            if resumes_data.get('resumes'):
                resume_id = resumes_data['resumes'][0]['resume_id']
                resp = await client.get(f"{BASE_URL}/api/resumes/{resume_id}/recommendations?limit=5")
                print(f"   ✓ 状态码: {resp.status_code}")
                data = resp.json()
                print(f"   ✓ 简历: {data.get('resume_name', 'N/A')}")
                print(f"   ✓ 推荐数: {data.get('total_matches', 0)}")
                print(f"   ✓ 返回: {len(data.get('matches', []))} 条")
                tests.append(resp.status_code == 200)
            else:
                print(f"   ⊘ 跳过（无简历数据）")
                tests.append(True)
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            tests.append(False)

        # 7. 测试匹配详情
        print("\n7. 测试匹配详情 GET /api/matches/{resume_id}/{job_id}")
        try:
            jobs_resp = await client.get(f"{BASE_URL}/api/jobs?page=1&page_size=1")
            resumes_resp = await client.get(f"{BASE_URL}/api/resumes?page=1&page_size=1")
            jobs_data = jobs_resp.json()
            resumes_data = resumes_resp.json()

            if jobs_data.get('jobs') and resumes_data.get('resumes'):
                job_id = jobs_data['jobs'][0]['job_id']
                resume_id = resumes_data['resumes'][0]['resume_id']
                resp = await client.get(f"{BASE_URL}/api/matches/{resume_id}/{job_id}")

                if resp.status_code == 404:
                    print(f"   ⊘ 跳过（该简历和岗位无匹配记录）")
                    tests.append(True)
                else:
                    print(f"   ✓ 状态码: {resp.status_code}")
                    data = resp.json()
                    print(f"   ✓ 总分: {data.get('scores', {}).get('total_score', 0)}")
                    print(f"   ✓ 匹配技能数: {len(data.get('matched_skills', []))}")
                    print(f"   ✓ 缺失技能数: {len(data.get('missing_skills', []))}")
                    tests.append(resp.status_code == 200)
            else:
                print(f"   ⊘ 跳过（无数据）")
                tests.append(True)
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            tests.append(False)

        # 8. 测试生成器状态接口
        print("\n8. 测试生成器状态 GET /api/generator/status")
        try:
            resp = await client.get(f"{BASE_URL}/api/generator/status")
            print(f"   ✓ 状态码: {resp.status_code}")
            tests.append(resp.status_code in (200, 503))
        except Exception as e:
            print(f"   ✗ 错误: {e}")
            tests.append(False)

        # 汇总
        print("\n" + "="*60)
        passed = sum(tests)
        total = len(tests)
        print(f"测试结果: {passed}/{total} 通过")

        if passed == total:
            print("✓ 所有测试通过")
            return 0
        else:
            print("✗ 部分测试失败")
            return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_api()))
