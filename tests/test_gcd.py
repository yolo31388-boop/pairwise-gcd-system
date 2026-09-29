"""技能公共CD与GCD系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from skill.gcd import GCDSystem, Skill

class TestGCDByType:
    def test_spell_has_longer_gcd(self):
        gs = GCDSystem()
        gs.skills["fireball"] = Skill("fireball", "fireball", cast_time=2.0)
        gs.skills["slash"] = Skill("slash", "slash", is_instant=True)
        g1 = gs.get_gcd("fireball")
        g2 = gs.get_gcd("slash")
        assert g1 > g2

class TestQueueLimit:
    def test_queue_has_capacity_limit(self):
        gs = GCDSystem()
        assert gs.get_queue_limit() <= 5

class TestInterruptPenalty:
    def test_interrupt_has_penalty(self):
        gs = GCDSystem()
        result = gs.interrupt_skill("fireball")
        assert result["cd_reset"] == False or result["mana_refund"] < 1.0

class TestLatencyCompensation:
    def test_high_latency_gets_more_compensation(self):
        gs = GCDSystem()
        c1 = gs.get_latency_compensation(20)
        c2 = gs.get_latency_compensation(200)
        assert c2 > c1

class TestInstantGCD:
    def test_instant_skill_no_gcd_or_shorter(self):
        gs = GCDSystem()
        assert gs.is_instant_triggers_gcd() == False

class TestSkillPriority:
    def test_priority_not_random(self):
        gs = GCDSystem()
        # 应该有确定的优先级规则
        assert hasattr(gs, "priority_rules")
        gs.priority_rules = {"ultimate": 10, "normal": 5}
        gs.skills["ult"] = Skill("ult", "ult")
        gs.skills["norm"] = Skill("norm", "norm")
        result = gs.get_skill_priority("ult", "norm")
        assert result == "ult"

class TestAutoCast:
    def test_auto_cast_on_gcd_end(self):
        gs = GCDSystem()
        gs.queue = ["fireball"]
        gs.current_gcd_end = 0
        result = gs.auto_cast_on_gcd_end()
        assert result == "fireball"
