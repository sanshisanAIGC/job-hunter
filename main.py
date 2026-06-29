#!/usr/bin/env python3
"""AI 求职助手 - CLI 入口"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_NOTIFY_OPEN_ID,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    JOB_KEYWORDS, JOB_CITY, JOB_WELFARE,
    MATCH_THRESHOLD, MAX_DAILY_APPLY,
    GREET_INTERVAL_MIN, GREET_INTERVAL_MAX,
    validate_config,
)
from src.pipeline import JobPipeline


def create_pipeline() -> JobPipeline:
    return JobPipeline(
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


def cmd_setup(args):
    """初始化：解析简历"""
    pipeline = create_pipeline()
    resume = pipeline.load_resume(args.resume)
    print(f"\n简历解析完成！")
    print(f"姓名: {resume.get('name', '未知')}")
    print(f"技能: {', '.join(resume.get('skills', [])[:10])}")
    print(f"工作经验: {len(resume.get('work_experience', []))} 段")
    print(f"已保存到 data/resume.json")


def cmd_run(args):
    """运行一轮搜索+投递"""
    pipeline = create_pipeline()
    pipeline.load_resume("")  # 从 data/resume.json 加载

    stats = pipeline.search_and_apply()
    print(f"\n完成！搜索 {stats['searched']} | 投递 {stats['applied']} | 跳过 {stats['skipped']}")


def cmd_optimize(args):
    """AI 优化简历"""
    pipeline = create_pipeline()
    pipeline.load_resume("")
    pipeline.optimize_resume(
        target_direction=args.direction or JOB_KEYWORDS,
    )
    print("\n简历已优化！打开 data/resume_optimized.md 查看和编辑")


def cmd_check(args):
    """检查消息并回复"""
    pipeline = create_pipeline()
    pipeline.load_resume("")

    stats = pipeline.check_and_reply()
    print(f"\n完成！新消息 {stats['new_messages']} | 已回复 {stats['replied']} | 面试 {stats['interviews']}")


def cmd_schedule(args):
    """启动定时调度器"""
    from scheduler import run_scheduler
    run_scheduler()


def cmd_status(args):
    """查看状态"""
    pipeline = create_pipeline()
    print(f"求职关键词: {JOB_KEYWORDS}")
    print(f"目标城市: {JOB_CITY}")
    print(f"匹配阈值: {MATCH_THRESHOLD}分")
    print(f"每日上限: {MAX_DAILY_APPLY}个")

    try:
        pipeline.load_resume("")
        print(f"\n简历: {pipeline.resume.get('name', '?')}")
        print(f"技能: {', '.join(pipeline.resume.get('skills', [])[:8])}")
    except Exception:
        print("简历未配置，请运行: python main.py setup --resume <文本>")

    applied = pipeline.boss.get_applied_ids()
    print(f"\n已投递: {len(applied)} 个岗位")
    today = pipeline.boss.get_applied_count_today()
    print(f"今日已投: {today} 个")


def cmd_login(args):
    """登录 Boss"""
    from src.boss.cli import BossCLI
    boss = BossCLI()
    result = boss.login()
    print(result)


def main():
    parser = argparse.ArgumentParser(description="AI 求职助手 - Boss直聘自动投递")
    sub = parser.add_subparsers(dest="command")

    p_setup = sub.add_parser("setup", help="解析简历")
    p_setup.add_argument("--resume", required=True, help="简历文本或PDF路径")

    sub.add_parser("run", help="运行一轮搜索+投递")
    p_opt = sub.add_parser("optimize", help="AI优化简历")
    p_opt.add_argument("--direction", help="目标方向，如 'AI视频,Python AI'")
    sub.add_parser("check", help="检查HR消息并回复")
    sub.add_parser("schedule", help="启动定时调度器")
    sub.add_parser("status", help="查看状态")
    sub.add_parser("login", help="登录Boss直聘")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    missing = validate_config()
    if missing:
        print(f"警告：缺少配置: {missing}")

    cmds = {
        "setup": cmd_setup, "run": cmd_run, "optimize": cmd_optimize,
        "check": cmd_check, "schedule": cmd_schedule, "status": cmd_status, "login": cmd_login,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
