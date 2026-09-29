"""技能公共CD与GCD系统"""
import time
from dataclasses import dataclass, field

# fix1: GCD按技能类型区分
GCD_SPELL = 1.5    # 法术(读条)
GCD_PHYSICAL = 1.0  # 物理
GCD_INSTANT = 0.5   # 瞬发

# fix2: 队列容量上限
DEFAULT_QUEUE_LIMIT = 3

# fix3: 打断惩罚
INTERRUPT_CD_PROGRESS = 0.5   # CD转一半
INTERRUPT_MANA_REFUND = 0.7   # 耗蓝30%

# fix4: 动态延迟补偿
BASE_COMPENSATION_MS = 20.0
COMPENSATION_RATIO = 0.5       # 按网络延迟比例补偿
HIGH_LATENCY_THRESHOLD_MS = 100.0
PRE_INPUT_WINDOW_MS = 150.0    # 高延迟预输入窗口

@dataclass
class Skill:
    sid: str
    name: str
    gcd: float = 0
    cast_time: float = 0
    is_instant: bool = False
    skill_type: str = ""  # "spell" / "physical" / "instant"，空则自动推断

    def resolved_type(self) -> str:
        if self.skill_type:
            return self.skill_type
        if self.is_instant:
            return "instant"
        if self.cast_time > 0:
            return "spell"
        return "physical"

class GCDSystem:
    def __init__(self):
        self.skills: dict[str, Skill] = {}
        self.queue: list[str] = []
        self.queue_limit: int = DEFAULT_QUEUE_LIMIT
        self.current_gcd_end: float = 0
        self.latency: float = 50
        # fix6: 确定的优先级规则，数值越大优先级越高
        self.priority_rules: dict[str, float] = {
            "ultimate": 10,
            "spell": 6,
            "normal": 5,
            "physical": 4,
            "instant": 3,
        }

    def get_gcd(self, skill_id: str) -> float:
        # fix1: 按技能类型区分GCD
        skill = self.skills.get(skill_id)
        if skill is None:
            return GCD_PHYSICAL
        if skill.gcd > 0:
            return skill.gcd
        return {
            "spell": GCD_SPELL,
            "physical": GCD_PHYSICAL,
            "instant": GCD_INSTANT,
        }[skill.resolved_type()]

    def get_queue_limit(self) -> int:
        # fix2: 队列容量上限，默认3
        return self.queue_limit

    def enqueue(self, skill_id: str) -> bool:
        # fix2: 满了拒绝新技能
        if len(self.queue) >= self.get_queue_limit():
            return False
        self.queue.append(skill_id)
        return True

    def interrupt_skill(self, skill_id: str) -> dict:
        # fix3: 打断惩罚 - CD转一半、耗蓝30%
        return {
            "cd_reset": False,
            "cd_progress": INTERRUPT_CD_PROGRESS,
            "mana_refund": INTERRUPT_MANA_REFUND,
        }

    def get_latency_compensation(self, network_ms: float) -> float:
        # fix4: 按网络状况动态补偿，高延迟附带预输入窗口
        compensation = BASE_COMPENSATION_MS + network_ms * COMPENSATION_RATIO
        if network_ms >= HIGH_LATENCY_THRESHOLD_MS:
            compensation += PRE_INPUT_WINDOW_MS
        return compensation

    def is_instant_triggers_gcd(self) -> bool:
        # fix5: 瞬发技能不触发GCD
        return False

    def _priority_of(self, skill_id: str) -> float:
        # fix6: 按技能类型与施法状态确定优先级
        skill = self.skills.get(skill_id)
        best = None
        for key, value in self.priority_rules.items():
            if key == skill_id or key.startswith(skill_id) or skill_id.startswith(key):
                if best is None or value > best:
                    best = value
        if best is not None:
            return best
        if skill is not None:
            if skill.cast_time > 0 and not skill.is_instant:
                # 读条中的技能优先，避免被打断浪费
                return self.priority_rules.get("spell", 6)
            return self.priority_rules.get(skill.resolved_type(), 0)
        return 0

    def get_skill_priority(self, s1: str, s2: str) -> str:
        # fix6: 确定性优先级，平局时按skill id字典序保证稳定
        p1, p2 = self._priority_of(s1), self._priority_of(s2)
        if p1 != p2:
            return s1 if p1 > p2 else s2
        return min(s1, s2)

    def auto_cast_on_gcd_end(self) -> str | None:
        # fix7: GCD结束自动释放队列头部技能
        if not self.queue:
            return None
        if time.time() < self.current_gcd_end:
            return None
        return self.queue.pop(0)
