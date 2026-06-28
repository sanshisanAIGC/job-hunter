"""求职流程编排 — Search → Match → Greet → Monitor → Reply"""
import json
import time
from pathlib import Path
from src.ai.client import DeepSeekClient
from src.ai.matcher import JDMacher
from src.ai.greeter import Greeter
from src.ai.replier import Replier
from src.boss.cli import BossCLI
from src.resume.parser import ResumeParser
from src.feishu.notifier import FeishuNotifier


class JobPipeline:
    def __init__(self, deepseek_api_key: str, deepseek_base_url: str,
                 deepseek_model: str, feishu_app_id: str, feishu_app_secret: str,
                 feishu_open_id: str = "", data_dir: Path = None,
                 match_threshold: int = 70, max_daily: int = 50,
                 delay_min: int = 30, delay_max: int = 120,
                 job_keywords: str = "", job_city: str = "", job_welfare: str = ""):
        self.data_dir = data_dir or Path("data")
        self.match_threshold = match_threshold
        self.max_daily = max_daily
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.job_keywords = job_keywords
        self.job_city = job_city
        self.job_welfare = job_welfare

        # 初始化组件
        self.ai = DeepSeekClient(deepseek_api_key, deepseek_base_url, deepseek_model)
        self.boss = BossCLI(self.data_dir)
        self.parser = ResumeParser(self.ai)
        self.notifier = FeishuNotifier(feishu_app_id, feishu_app_secret, feishu_open_id)

        # 延迟初始化（需要 resume 加载后）
        self.resume = None
        self.resume_summary = ""
        self.matcher = None
        self.greeter = None
        self.replier = None

    def load_resume(self, source: str | Path) -> dict:
        """加载简历"""
        resume_file = self.data_dir / "resume.json"
        if resume_file.exists() and not source:
            self.resume = self.parser.load(resume_file)
        elif source:
            self.resume = self.parser.parse(source)
            self.parser.save(self.resume, resume_file)
        else:
            raise RuntimeError("请提供简历文本或文件路径")

        self.resume_summary = self.parser.get_summary(self.resume)
        self.matcher = JDMacher(self.ai, self.resume)
        self.greeter = Greeter(self.ai, self.resume_summary)
        self.replier = Replier(self.ai, self.resume_summary)

        print(f"[Pipeline] 简历已加载: {self.resume.get('name', '未知')}")
        print(f"[Pipeline] 技能: {', '.join(self.resume.get('skills', [])[:10])}")
        return self.resume

    def search_and_apply(self) -> dict:
        """搜索岗位并投递（单次运行）"""
        stats = {"searched": 0, "applied": 0, "skipped": 0, "errors": 0}
        applied_today = self.boss.get_applied_count_today()

        if applied_today >= self.max_daily:
            print(f"[Pipeline] 今日已达上限 ({applied_today}/{self.max_daily})")
            return stats

        # 按关键词搜索
        keywords = [k.strip() for k in self.job_keywords.split(",") if k.strip()]
        if not keywords:
            keywords = ["Python"]

        all_jobs = []
        for kw in keywords[:3]:  # 最多搜 3 个关键词
            print(f"\n[Pipeline] 搜索: {kw} @ {self.job_city}")
            result = self.boss.search(kw, self.job_city, welfare=self.job_welfare)
            jobs = self.boss.extract_jobs_from_search(result)
            print(f"  找到 {len(jobs)} 个岗位")
            all_jobs.extend(jobs)
            time.sleep(2)

        # 去重
        seen_ids = self.boss.get_applied_ids()
        new_jobs = [j for j in all_jobs if j.get("security_id") not in seen_ids]
        stats["searched"] = len(new_jobs)

        print(f"\n[Pipeline] 去重后剩余 {len(new_jobs)} 个新岗位")

        # 逐个匹配 + 投递
        for i, job in enumerate(new_jobs):
            if self.boss.get_applied_count_today() >= self.max_daily:
                print(f"[Pipeline] 达到每日上限，停止")
                break

            sid = job.get("security_id", "")
            if not sid:
                continue

            print(f"\n[{i+1}/{len(new_jobs)}] {job.get('job_name', '?')} @ {job.get('brand', job.get('company', '?'))}")

            # 获取详情
            detail = self.boss.detail(sid)
            job_detail = self.boss.extract_job_detail(detail)
            if job_detail:
                job.update(job_detail)

            # AI 匹配
            match = self.matcher.match(job)
            score = match.get("score", 0)
            print(f"  匹配分: {score}")

            if score < self.match_threshold:
                print(f"  跳过 (低于阈值 {self.match_threshold})")
                stats["skipped"] += 1
                continue

            # 生成招呼语
            greeting = self.greeter.generate(job, match)
            print(f"  招呼语: {greeting[:80]}...")

            # 投递
            job_id = job.get("job_id", job.get("encrypt_job_id", ""))
            result = self.boss.greet(sid, job_id)
            if result.get("ok"):
                job["match_score"] = score
                self.boss.mark_applied(sid, job)
                stats["applied"] += 1
                print(f"  ✅ 已投递!")

                # 通知高匹配
                if score >= 80:
                    self.notifier.notify_high_match(job, score, greeting)
            else:
                stats["errors"] += 1
                print(f"  ❌ 投递失败: {result.get('error', 'unknown')}")

            # 随机延迟
            if i < len(new_jobs) - 1:
                self.boss.random_delay(self.delay_min, self.delay_max)

        print(f"\n[Pipeline] 本轮结果: 搜索{stats['searched']} | 投递{stats['applied']} | 跳过{stats['skipped']} | 失败{stats['errors']}")
        return stats

    def check_and_reply(self) -> dict:
        """检查新消息并自动回复"""
        stats = {"new_messages": 0, "replied": 0, "interviews": 0}

        summary = self.boss.chat_summary()
        if not summary.get("ok"):
            print("[Pipeline] 获取消息摘要失败")
            return stats

        # 获取聊天列表
        chat_list = self.boss.chat_list()
        chats = chat_list.get("data", [])
        if isinstance(chats, dict):
            chats = chats.get("items", chats.get("chats", []))

        for chat in (chats or [])[:20]:
            sid = chat.get("security_id", "")
            if not sid:
                continue

            # 获取消息
            msgs = self.boss.chatmsg(sid)
            msg_data = msgs.get("data", {})
            messages = msg_data.get("messages", []) if isinstance(msg_data, dict) else []

            # 检查未读 HR 消息
            hr_msgs = [m for m in messages if m.get("from") == "hr" or m.get("sender_type") == "hr"]
            if not hr_msgs:
                continue

            latest = hr_msgs[-1]
            hr_text = latest.get("content", latest.get("text", ""))
            stats["new_messages"] += 1

            # AI 分析意图
            intent = self.replier.analyze_intent(hr_text)
            print(f"[Pipeline] HR消息: {hr_text[:80]}...")
            print(f"  意图: {intent.get('intent')}")

            if intent.get("intent") == "interview_invite":
                stats["interviews"] += 1
                job_name = chat.get("job_name", "")
                company = chat.get("brand", "")
                self.notifier.notify_interview(job_name, company, hr_text)

            if intent.get("need_reply"):
                reply = self.replier.generate_reply(hr_text)
                print(f"  AI回复: {reply[:80]}...")

                # 发送回复（注意：boss-agent-cli 低风险模式可能阻断）
                # 此处预留 send_message 接口
                stats["replied"] += 1
                self.notifier.notify_new_message(
                    chat.get("hr_name", chat.get("brand", "HR")),
                    hr_text, reply,
                )

            time.sleep(1)

        return stats

    def run_daily_report(self):
        """发送每日报告"""
        applied_today = self.boss.get_applied_count_today()
        all_applied = len(self.boss.get_applied_ids())

        stats = {
            "searched": 0,  # 需要从日志中累计
            "applied": applied_today,
            "new_messages": 0,
            "interviews": 0,
            "total_applied": all_applied,
        }
        self.notifier.notify_daily_summary(stats)
