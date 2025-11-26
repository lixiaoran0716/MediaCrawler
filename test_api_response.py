import asyncio
import httpx
import json

async def test_api_response():
    """测试API服务器的响应格式"""
    # 创建测试请求数据
    test_data = {
        "platform": "qqnews",
        "type": "search",
        "save_data_option": "json"
    }
    
    # 使用同一个客户端实例
    async with httpx.AsyncClient() as client:
        try:
            # 发送POST请求到API服务器
            response = await client.post(
                "http://127.0.0.1:8000/api/crawl",
                json=test_data,
                timeout=30.0
            )
            
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"解析后的JSON数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    # 获取任务ID并检查任务状态
                    if 'task_id' in data:
                        task_id = data['task_id']
                        print(f"\n正在检查任务状态: {task_id}")
                        
                        # 等待更长时间让任务执行完成
                        for i in range(6):  # 最多等待60秒
                            await asyncio.sleep(10)
                            
                            # 检查任务状态
                            status_response = await client.get(
                                f"http://127.0.0.1:8000/api/tasks/{task_id}"
                            )
                            
                            status_data = status_response.json()
                            print(f"任务状态响应: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
                            
                            # 如果任务已完成或失败，退出循环
                            if status_data.get('status') in ['completed', 'failed']:
                                break
                            
                except Exception as e:
                    print(f"解析响应时出错: {e}")
            else:
                print(f"API请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"请求API时出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_response())