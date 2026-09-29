"""技能公共CD与GCD系统 - 含7个bug"""
from dataclasses import dataclass, field

@dataclass
class Skill:
    sid: str
    name: str
    gcd: float = 1.0  # bug1: 固定GCD
    cast_time: float = 0
    is_instant: bool = False

class GCDSystem:
    def __init__(self):
        self.skills: dict[str, Skill] = {}
        self.queue: list[str] = []  # bug2: 无容量限制
        self.current_gcd_end: float = 0
        self.latency: float = 50  # bug4: 固定延迟

    def get_gcd(self, skill_id: str) -> float:
        # bug1: 固定1秒不区分类型
        return 1.0

    def get_queue_limit(self) -> int:
        # bug2: 无限制
        return 999

    def interrupt_skill(self, skill_id: str) -> dict:
        # bug3: 打断无惩罚
        return {"cd_reset": True, "mana_refund": 1.0}

    def get_latency_compensation(self, network_ms: float) -> float:
        # bug4: 固定延迟
        return 50.0

    def is_instant_triggers_gcd(self) -> bool:
        # bug5: 瞬发也触发GCD
        return True

    def get_skill_priority(self, s1: str, s2: str) -> str:
        # bug6: 随机优先级
        import random
        return random.choice([s1, s2])

    def auto_cast_on_gcd_end(self) -> str | None:
        # bug7: 不自动释放
        return None
