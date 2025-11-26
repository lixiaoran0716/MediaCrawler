import asyncio
import httpx
import json

async def test_api_complete():
    """测试API服务器的完整流程"""
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
                        completed = False
                        for i in range(12):  # 最多等待120秒
                            await asyncio.sleep(10)
                            
                            # 检查任务状态
                            status_response = await client.get(
                                f"http://127.0.0.1:8000/api/tasks/{task_id}"
                            )
                            
                            status_data = status_response.json()
                            print(f"任务状态响应: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
                            
                            # 如果任务已完成或失败，退出循环
                            if status_data.get('status') in ['completed', 'failed']:
                                completed = True
                                # 如果任务完成，获取结果数据
                                if status_data.get('status') == 'completed' and status_data.get('result'):
                                    print(f"\n=== 爬取结果 ===")
                                    result = status_data.get('result', {})
                                    news_list = result.get('news_list', [])
                                    print(f"共获取到 {len(news_list)} 条新闻:")
                                    for i, news in enumerate(news_list[:5]):  # 只显示前5条
                                        print(f"{i+1}. 标题: {news.get('title', 'N/A')}")
                                        print(f"   链接: {news.get('url', 'N/A')}")
                                        print()
                                break
                        
                        if not completed:
                            print("任务在规定时间内未完成")
                            
                except Exception as e:
                    print(f"解析响应时出错: {e}")
            else:
                print(f"API请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"请求API时出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_complete())