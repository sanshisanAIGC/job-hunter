"""
boss-agent-cli 封装
通过 subprocess 调用 CLI，解析 JSON 输出
"""
import json
import subprocess
import time
import random
from pathlib import Path


class BossCLI:
    """封装 boss-agent-cli 命令，所有方法返回解析后的 dict"""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._applied_file = self.data_dir / "applied_jobs.json"
        self._load_applied()

    def _run(self, *args) -> dict:
        """执行 boss 命令并解析 JSON 输出"""
        cmd = ["boss"] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = result.stdout.strip()
            if not output:
                return {"ok": False, "error": result.stderr.strip() or "no output"}
            return json.loads(output)
        except json.JSONDecodeError:
            return {"ok": False, "error": f"JSON parse error: {result.stdout[:200]}"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "command timeout"}
        except FileNotFoundError:
            return {"ok": False, "error": "boss CLI not installed. Install: pip install boss-agent-cli"}

    # ━━━━ 认证 ━━━━

    def login(self) -> dict:
        """登录 Boss 直聘"""
        return self._run("login")

    def status(self) -> dict:
        """检查登录状态"""
        return self._run("status")

    def doctor(self) -> dict:
        """环境自检"""
        return self._run("doctor")

    # ━━━━ 搜索 ━━━━

    def search(self, keyword: str, city: str = "",
               salary: str = "", welfare: str = "",
               page: int = 1) -> dict:
        """搜索岗位"""
        args = ["search", keyword]
        if city:
            args += ["--city", city]
        if salary:
            args += ["--salary", salary]
        if welfare:
            args += ["--welfare", welfare]
        if page > 1:
            args += ["--page", str(page)]

        return self._run(*args)

    def detail(self, security_id: str) -> dict:
        """获取岗位详情"""
        return self._run("detail", security_id)

    def recommend(self) -> dict:
        """获取推荐岗位"""
        return self._run("recommend")

    # ━━━━ 投递动作 ━━━━

    def greet(self, security_id: str, job_id: str) -> dict:
        """打招呼"""
        return self._run("greet", security_id, job_id)

    def batch_greet(self, keyword: str, city: str = "", count: int = 5) -> dict:
        """批量打招呼 (最多10个)"""
        args = ["batch-greet", keyword]
        if city:
            args += ["--city", city]
        args += ["-n", str(min(count, 10))]
        return self._run(*args)

    def apply(self, security_id: str, job_id: str) -> dict:
        """投递简历"""
        return self._run("apply", security_id, job_id)

    def exchange(self, security_id: str) -> dict:
        """交换联系方式"""
        return self._run("exchange", security_id)

    # ━━━━ 沟通 ━━━━

    def chat_list(self) -> dict:
        """获取聊天列表"""
        return self._run("chat")

    def chatmsg(self, security_id: str) -> dict:
        """获取与某人的聊天消息"""
        return self._run("chatmsg", security_id)

    def chat_summary(self) -> dict:
        """获取沟通摘要"""
        return self._run("chat-summary")

    def digest(self) -> dict:
        """每日摘要"""
        return self._run("digest")

    def interviews(self) -> dict:
        """面试邀请"""
        return self._run("interviews")

    # ━━━━ AI 辅助 ━━━━

    def ai_analyze_jd(self, security_id: str) -> dict:
        """AI 分析 JD"""
        return self._run("ai", "analyze-jd", security_id)

    def ai_fit(self, security_id: str) -> dict:
        """AI 匹配评分"""
        return self._run("ai", "fit", security_id)

    # ━━━━ 本地管理 ━━━━

    def _load_applied(self):
        """加载已投递记录"""
        if self._applied_file.exists():
            self.applied = json.loads(self._applied_file.read_text("utf-8"))
        else:
            self.applied = {}

    def _save_applied(self):
        """保存已投递记录"""
        self._applied_file.write_text(json.dumps(self.applied, ensure_ascii=False, indent=2), "utf-8")

    def is_applied(self, security_id: str) -> bool:
        """检查是否已投递"""
        return security_id in self.applied

    def mark_applied(self, security_id: str, job_info: dict):
        """标记为已投递"""
        self.applied[security_id] = {
            "applied_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "job_name": job_info.get("job_name", ""),
            "company": job_info.get("company", ""),
            "score": job_info.get("match_score", 0),
        }
        self._save_applied()

    def get_applied_count_today(self) -> int:
        """获取今日已投递数量"""
        today = time.strftime("%Y-%m-%d")
        count = 0
        for v in self.applied.values():
            if v.get("applied_at", "").startswith(today):
                count += 1
        return count

    def get_applied_ids(self) -> set:
        """获取所有已投递的 security_id"""
        return set(self.applied.keys())

    # ━━━━ 工具方法 ━━━━

    @staticmethod
    def extract_jobs_from_search(result: dict) -> list[dict]:
        """从搜索结果中提取岗位列表"""
        if not result.get("ok"):
            return []
        data = result.get("data", {})
        # boss-agent-cli 的 search 返回 {ok, data: {jobs: [...], ...}}
        if isinstance(data, dict):
            return data.get("jobs", data.get("items", []))
        if isinstance(data, list):
            return data
        return []

    @staticmethod
    def extract_job_detail(result: dict) -> dict:
        """从详情结果中提取 JD 信息"""
        if not result.get("ok"):
            return {}
        return result.get("data", {})

    def random_delay(self, min_sec: int = 30, max_sec: int = 120):
        """随机延迟，避免触发风控"""
        delay = random.randint(min_sec, max_sec)
        print(f"  [Boss] 等待 {delay}s ...")
        time.sleep(delay)
