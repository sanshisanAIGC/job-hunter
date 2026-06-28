#!/usr/bin/env python3
"""定时调度器 — 每2小时搜岗投递，每30分钟查消息"""
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

import schedule
from config import (
    FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_NOTIFY_OPEN_ID,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    JOB_KEYWORDS, JOB_CITY, JOB_WELFARE,
    MATCH_THRESHOLD, MAX_DAILY_APPLY,
    GREET_INTERVAL_MIN, GREET_INTERVAL_MAX,
)
from src.pipeline import JobPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("job-hunter")


class JobScheduler:
    def __init__(self):
        self.pipeline = JobPipeline(
            deepseek_api_key=DEEPSEEK_API_KEY,
            deepseek_base_url=DEEPSEEK_BASE_URL,
            deepseek_model=DEEPSEEK_MODEL,
            feishu_app_id=FEISHU_APP_ID,
            feishu_app_secret=FEISHU_APP_SECRET,
            feishu_open_id=FEISHU_NOTIFY_OPEN_ID,
            data_dir=Path("data"),
            match_threshold=MATCH_THRESHOLD,
            max_daily=MAX_DAILY_APPLY,
            delay_min=GREET_INTERVAL_MIN,
            delay_max=GREET_INTERVAL_MAX,
            job_keywords=JOB_KEYWORDS,
            job_city=JOB_CITY,
            job_welfare=JOB_WELFARE,
        )

    def search_and_apply(self):
        """搜岗投递任务"""
        logger.info("=" * 50)
        logger.info("开始搜索投递...")
        try:
            self.pipeline.load_resume("")
            stats = self.pipeline.search_and_apply()
            logger.info(f"搜索投递完成: 搜索{stats['searched']} | 投递{stats['applied']} | 跳过{stats['skipped']}")
        except Exception as e:
            logger.error(f"搜索投递失败: {e}")

    def check_messages(self):
        """检查消息任务"""
        logger.info("检查新消息...")
        try:
            self.pipeline.load_resume("")
            stats = self.pipeline.check_and_reply()
            logger.info(f"消息检查完成: 新消息{stats['new_messages']} | 已回复{stats['replied']}")
        except Exception as e:
            logger.error(f"消息检查失败: {e}")

    def daily_report(self):
        """每日报告"""
        logger.info("发送每日报告...")
        try:
            self.pipeline.load_resume("")
            self.pipeline.run_daily_report()
        except Exception as e:
            logger.error(f"每日报告失败: {e}")


def run_scheduler():
    sched = JobScheduler()

    # 每 2 小时搜岗投递（工作时间：9:00-18:00）
    for hour in ["09:00", "11:00", "14:00", "16:00"]:
        schedule.every().day.at(hour).do(sched.search_and_apply)

    # 每 30 分钟查消息
    schedule.every(30).minutes.do(sched.check_messages)

    # 每天 18:00 发送日报
    schedule.every().day.at("18:00").do(sched.daily_report)

    logger.info("求职调度器已启动")
    logger.info(f"  搜岗投递: 09:00, 11:00, 14:00, 16:00")
    logger.info(f"  消息检查: 每30分钟")
    logger.info(f"  每日报告: 18:00")
    logger.info(f"  关键词: {JOB_KEYWORDS}")
    logger.info(f"  城市: {JOB_CITY}")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("调度器已停止")


if __name__ == "__main__":
    run_scheduler()
