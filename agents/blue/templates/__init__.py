"""
Document Structure Templates

Templates define the section structure and generation guidance for each document type.
"""

from .capability_statement import CapabilityStatementTemplate
from .competitive_analysis import CompetitiveAnalysisTemplate
from .swot import SWOTAnalysisTemplate
from .bd_pipeline import BDPipelineTemplate
from .proposal_strategy import ProposalStrategyTemplate
from .go_to_market import GoToMarketTemplate
from .teaming_strategy import TeamingStrategyTemplate
from .base import DocumentTemplate, get_template_for_document_type

__all__ = [
    "DocumentTemplate",
    "CapabilityStatementTemplate",
    "CompetitiveAnalysisTemplate",
    "SWOTAnalysisTemplate",
    "BDPipelineTemplate",
    "ProposalStrategyTemplate",
    "GoToMarketTemplate",
    "TeamingStrategyTemplate",
    "get_template_for_document_type",
]
