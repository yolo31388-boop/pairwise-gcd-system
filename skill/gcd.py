"""技能公共CD与GCD系统"""
from dataclasses import dataclass, field

# GCD时长按技能类型区分（秒）
GCD_BY_TYPE = {
    "spell": 1.5,      # 读条法术
    "physical": 1.0,   # 物理技能
    "instant": 0.5,    # 瞬发技能
}

DEFAULT_QUEUE_LIMIT = 3
INTERRUPT_CD_FRACTION = 0.5    # 打断后CD转一半
INTERRUPT_MANA_COST = 0.3      # 打断耗蓝30%
HIGH_LATENCY_THRESHOLD = 150.0 # 高延迟阈值(ms)，触发预输入机制
PRE_INPUT_WINDOW = 0.2         # 高延迟预输入窗口(秒)


@dataclass
class Skill:
    sid: str
    name: str
    gcd: float = 1.0
    cast_time: float = 0
    is_instant: bool = False

    @property
    def skill_type(self) -> str:
        if self.is_instant:
            return "instant"
        if self.cast_time > 0:
            return "spell"
        return "physical"


class GCDSystem:
    def __init__(self, queue_limit: int = DEFAULT_QUEUE_LIMIT):
        self.skills: dict[str, Skill] = {}
        self.queue: list[str] = []
        self.queue_limit = queue_limit
        self.current_gcd_end: float = 0
        self.latency: float = 50
        # 技能优先级规则：类别 -> 权重，数值大者优先
        self.priority_rules: dict[str, int] = {
            "ultimate": 10,
            "interrupt": 9,
            "heal": 7,
            "normal": 5,
        }

    def get_gcd(self, skill_id: str) -> float:
        """GCD按技能类型区分：法术1.5s、物理1.0s、瞬发0.5s。"""
        skill = self.skills.get(skill_id)
        if skill is None:
            return GCD_BY_TYPE["physical"]
        return GCD_BY_TYPE[skill.skill_type]

    def get_queue_limit(self) -> int:
        """技能队列容量上限，默认3个。"""
        return self.queue_limit

    def enqueue(self, skill_id: str) -> bool:
        """入队预排技能，队列满则拒绝。"""
        if len(self.queue) >= self.queue_limit:
            return False
        self.queue.append(skill_id)
        return True

    def interrupt_skill(self, skill_id: str) -> dict:
        """打断惩罚：CD转一半、耗蓝30%（只退70%）。"""
        return {
            "cd_reset": False,
            "cd_fraction": INTERRUPT_CD_FRACTION,
            "mana_refund": 1.0 - INTERRUPT_MANA_COST,
        }

    def get_latency_compensation(self, network_ms: float) -> float:
        """按网络状况动态补偿；高延迟时附加预输入窗口。"""
        compensation = max(0.0, network_ms) * 0.5
        if network_ms >= HIGH_LATENCY_THRESHOLD:
            compensation += PRE_INPUT_WINDOW * 1000.0
        return compensation

    def is_instant_triggers_gcd(self) -> bool:
        """瞬发技能不触发完整GCD。"""
        return False

    def _priority_of(self, skill_id: str) -> int:
        """确定性的技能优先级：先匹配规则，再按施法状态/类型排序。"""
        for category, weight in self.priority_rules.items():
            if category.startswith(skill_id) or skill_id.startswith(category):
                return weight
        skill = self.skills.get(skill_id)
        if skill is None:
            return 0
        if skill.cast_time > 0:
            return 3  # 读条中的技能优先保读条
        if skill.is_instant:
            return 2
        return 1

    def get_skill_priority(self, s1: str, s2: str) -> str:
        """按优先级规则确定性排序，平局时按技能id字典序保证稳定。"""
        p1, p2 = self._priority_of(s1), self._priority_of(s2)
        if p1 != p2:
            return s1 if p1 > p2 else s2
        return min(s1, s2)

    def auto_cast_on_gcd_end(self) -> str | None:
        """GCD结束时自动释放队列头部技能。"""
        if not self.queue:
            return None
        return self.queue.pop(0)
