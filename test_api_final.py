import asyncio
import httpx
import json
import time

async def test_api_final():
    """最终测试API服务器功能"""
    # 创建一个持久的客户端会话
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 发送POST请求启动爬虫任务
            response = await client.post(
                "http://localhost:8000/api/crawl",
                json={
                    "platform": "qqnews",
                    "lt": "qrcode",
                    "type": "search"  # 修改为允许的值
                }
            )
            
            # 检查响应状态
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                print(f"成功启动任务，任务ID: {task_id}")
                
                # 循环检查任务状态
                for i in range(12):  # 最多检查12次，每次间隔10秒
                    status_response = await client.get(f"http://localhost:8000/api/status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get("status")
                        progress = status_data.get("progress", {})
                        
                        print(f"第{i+1}次检查 - 任务状态: {status}")
                        if progress:
                            print(f"  进度: {progress.get('percentage', 'N/A')}% - {progress.get('current_step', 'N/A')}")
                        
                        # 如果任务完成或失败，则退出循环
                        if status in ["completed", "failed"]:
                            # 获取最终结果
                            result_response = await client.get(f"http://localhost:8000/api/result/{task_id}")
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                news_count = len(result_data.get("news_list", []))
                                print(f"\n任务已完成，共获取到 {news_count} 条新闻")
                                
                                # 显示前几条新闻作为示例
                                news_list = result_data.get("news_list", [])
                                for idx, news in enumerate(news_list[:3]):
                                    print(f"{idx+1}. {news.get('title', 'N/A')}")
                                    print(f"   链接: {news.get('url', 'N/A')}\n")
                            break
                    else:
                        print(f"获取任务状态失败，状态码: {status_response.status_code}")
                    
                    # 等待10秒后再次检查
                    await asyncio.sleep(10)
            else:
                print(f"启动任务失败，状态码: {response.status_code}")
                print(response.text)
                
        except httpx.RequestError as e:
            print(f"请求发生错误: {e}")
        except Exception as e:
            print(f"测试过程中发生未知错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_final())