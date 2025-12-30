"""
Red Team Agents

Adversarial agents that challenge blue team outputs to strengthen
final document quality through rigorous critique and testing.
"""

from .devils_advocate import (
    DevilsAdvocateAgent,
    DevilsAdvocateResult,
    AssumptionAnalysis,
    Counterargument,
    LogicalIssue,
    ResponseEvaluation,
)

from .competitor_simulator import (
    CompetitorSimulatorAgent,
    CompetitorSimulatorResult,
    CompetitorAnalysis,
    CompetitorPerspective,
    CompetitiveVulnerability,
    CompetitorChallengeType,
)

from .evaluator_simulator import (
    EvaluatorSimulatorAgent,
    EvaluatorSimulatorResult,
    EvaluatorFinding,
    EvaluatorStrength,
    FactorEvaluation,
)

from .risk_assessor import (
    RiskAssessorAgent,
    RiskAssessorResult,
    StressTestResult,
    MitigationEvaluation,
    ResponseEvaluation as RiskResponseEvaluation,
)

from .risk_taxonomy import (
    Risk,
    RiskCategory,
    Probability,
    Impact,
    MitigationStatus,
    WorstCaseScenario,
    RiskRegister,
    identify_risk_category,
    RISK_INDICATORS,
)

__all__ = [
    # Agents
    "DevilsAdvocateAgent",
    "CompetitorSimulatorAgent",
    "EvaluatorSimulatorAgent",
    "RiskAssessorAgent",
    # Devil's Advocate result types
    "DevilsAdvocateResult",
    "AssumptionAnalysis",
    "Counterargument",
    "LogicalIssue",
    "ResponseEvaluation",
    # Competitor Simulator result types
    "CompetitorSimulatorResult",
    "CompetitorAnalysis",
    "CompetitorPerspective",
    "CompetitiveVulnerability",
    "CompetitorChallengeType",
    # Evaluator Simulator result types
    "EvaluatorSimulatorResult",
    "EvaluatorFinding",
    "EvaluatorStrength",
    "FactorEvaluation",
    # Risk Assessor result types
    "RiskAssessorAgent",
    "RiskAssessorResult",
    "StressTestResult",
    "MitigationEvaluation",
    "RiskResponseEvaluation",
    # Risk taxonomy types
    "Risk",
    "RiskCategory",
    "Probability",
    "Impact",
    "MitigationStatus",
    "WorstCaseScenario",
    "RiskRegister",
    "identify_risk_category",
    "RISK_INDICATORS",
]
