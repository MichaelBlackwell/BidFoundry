"""
Agent Registration

Registers all agent implementations with the global registry.
This module must be imported at application startup to ensure
agents are available for the orchestrator.
"""

import logging

from .types import AgentRole
from .registry import get_registry, AgentRegistrationError

logger = logging.getLogger(__name__)


def register_all_agents() -> None:
    """
    Register all agent implementations with the global registry.

    This function should be called once at application startup,
    before any document generation workflows are started.
    """
    registry = get_registry()

    # Track registration results
    registered = []
    failed = []

    # Blue Team Agents
    try:
        from .blue.strategy_architect import StrategyArchitectAgent
        registry.register(AgentRole.STRATEGY_ARCHITECT, StrategyArchitectAgent, replace=True)
        registered.append(AgentRole.STRATEGY_ARCHITECT.value)
    except Exception as e:
        logger.warning(f"Failed to register Strategy Architect: {e}")
        failed.append(("Strategy Architect", str(e)))

    try:
        from .blue.market_analyst import MarketAnalystAgent
        registry.register(AgentRole.MARKET_ANALYST, MarketAnalystAgent, replace=True)
        registered.append(AgentRole.MARKET_ANALYST.value)
    except Exception as e:
        logger.warning(f"Failed to register Market Analyst: {e}")
        failed.append(("Market Analyst", str(e)))

    try:
        from .blue.compliance_navigator import ComplianceNavigatorAgent
        registry.register(AgentRole.COMPLIANCE_NAVIGATOR, ComplianceNavigatorAgent, replace=True)
        registered.append(AgentRole.COMPLIANCE_NAVIGATOR.value)
    except Exception as e:
        logger.warning(f"Failed to register Compliance Navigator: {e}")
        failed.append(("Compliance Navigator", str(e)))

    try:
        from .blue.capture_strategist import CaptureStrategistAgent
        registry.register(AgentRole.CAPTURE_STRATEGIST, CaptureStrategistAgent, replace=True)
        registered.append(AgentRole.CAPTURE_STRATEGIST.value)
    except Exception as e:
        logger.warning(f"Failed to register Capture Strategist: {e}")
        failed.append(("Capture Strategist", str(e)))

    # Red Team Agents
    try:
        from .red.devils_advocate import DevilsAdvocateAgent
        registry.register(AgentRole.DEVILS_ADVOCATE, DevilsAdvocateAgent, replace=True)
        registered.append(AgentRole.DEVILS_ADVOCATE.value)
    except Exception as e:
        logger.warning(f"Failed to register Devil's Advocate: {e}")
        failed.append(("Devil's Advocate", str(e)))

    try:
        from .red.competitor_simulator import CompetitorSimulatorAgent
        registry.register(AgentRole.COMPETITOR_SIMULATOR, CompetitorSimulatorAgent, replace=True)
        registered.append(AgentRole.COMPETITOR_SIMULATOR.value)
    except Exception as e:
        logger.warning(f"Failed to register Competitor Simulator: {e}")
        failed.append(("Competitor Simulator", str(e)))

    try:
        from .red.evaluator_simulator import EvaluatorSimulatorAgent
        registry.register(AgentRole.EVALUATOR_SIMULATOR, EvaluatorSimulatorAgent, replace=True)
        registered.append(AgentRole.EVALUATOR_SIMULATOR.value)
    except Exception as e:
        logger.warning(f"Failed to register Evaluator Simulator: {e}")
        failed.append(("Evaluator Simulator", str(e)))

    try:
        from .red.risk_assessor import RiskAssessorAgent
        registry.register(AgentRole.RISK_ASSESSOR, RiskAssessorAgent, replace=True)
        registered.append(AgentRole.RISK_ASSESSOR.value)
    except Exception as e:
        logger.warning(f"Failed to register Risk Assessor: {e}")
        failed.append(("Risk Assessor", str(e)))

    # Orchestrator Agents
    try:
        from .orchestrator.arbiter import ArbiterAgent
        registry.register(AgentRole.ARBITER, ArbiterAgent, replace=True)
        registered.append(AgentRole.ARBITER.value)
    except Exception as e:
        logger.warning(f"Failed to register Arbiter: {e}")
        failed.append(("Arbiter", str(e)))

    # Log summary
    logger.info(f"Agent registration complete: {len(registered)} registered, {len(failed)} failed")
    if registered:
        logger.debug(f"Registered agents: {', '.join(registered)}")
    if failed:
        for name, error in failed:
            logger.error(f"Failed to register {name}: {error}")


def ensure_agents_registered() -> bool:
    """
    Ensure agents are registered, registering them if needed.

    Returns:
        True if at least the core agents are registered
    """
    registry = get_registry()

    # Check if key agents are already registered
    core_agents = [
        AgentRole.STRATEGY_ARCHITECT,
        AgentRole.ARBITER,
    ]

    all_registered = all(registry.is_registered(role) for role in core_agents)

    if not all_registered:
        register_all_agents()
        all_registered = all(registry.is_registered(role) for role in core_agents)

    return all_registered
