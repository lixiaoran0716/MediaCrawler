import asyncio
import httpx
import json

async def test_qqnews_api():
    """测试QQNews API接口"""
    # API服务器地址
    base_url = "http://127.0.0.1:8000"
    
    # 测试数据
    crawl_request = {
        "platform": "qqnews",
        "type": "search",
        "keywords": None,
        "start_page": 1,
        "get_comment": False,
        "get_sub_comment": False,
        "save_data_option": "db",
        "login_type": "qrcode"
    }
    
    print("开始测试QQNews API接口...")
    
    try:
        # 发送POST请求到/api/crawl
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/crawl",
                json=crawl_request,
                timeout=30.0
            )
            
            print(f"请求状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"任务创建成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 获取任务ID
                task_id = result.get("task_id")
                if task_id:
                    print(f"\n开始轮询任务状态，任务ID: {task_id}")
                    
                    # 轮询任务状态
                    for i in range(10):  # 最多轮询10次
                        await asyncio.sleep(5)  # 每5秒查询一次
                        
                        status_response = await client.get(f"{base_url}/api/tasks/{task_id}")
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            print(f"任务状态: {json.dumps(status_result, indent=2, ensure_ascii=False)}")
                            
                            if status_result.get("status") in ["completed", "failed"]:
                                break
                        else:
                            print(f"获取任务状态失败: {status_response.status_code}")
                            break
            else:
                print(f"请求失败: {response.status_code}")
                
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_qqnews_api())