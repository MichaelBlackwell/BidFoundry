"""
Orchestrator Agents

Contains the Arbiter agent and supporting infrastructure for
orchestrating the adversarial document generation workflow.
"""

from .arbiter import (
    ArbiterAgent,
    DocumentRequest,
    FinalOutput,
)
from .workflow import (
    DocumentWorkflow,
    WorkflowConfig,
    WorkflowState,
    WorkflowPhase,
    WorkflowStatus,
)
from .consensus import (
    ConsensusDetector,
    ConsensusResult,
    ConsensusStatus,
    ConsensusConfig,
)
from .synthesis import (
    DocumentSynthesizer,
    SynthesisConfig,
    SectionMetadata,
)

__all__ = [
    # Arbiter
    "ArbiterAgent",
    "DocumentRequest",
    "FinalOutput",
    # Workflow
    "DocumentWorkflow",
    "WorkflowConfig",
    "WorkflowState",
    "WorkflowPhase",
    "WorkflowStatus",
    # Consensus
    "ConsensusDetector",
    "ConsensusResult",
    "ConsensusStatus",
    "ConsensusConfig",
    # Synthesis
    "DocumentSynthesizer",
    "SynthesisConfig",
    "SectionMetadata",
]
