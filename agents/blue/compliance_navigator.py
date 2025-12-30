"""
Compliance Navigator Agent

Regulatory and eligibility expertise agent for federal contracting.
Validates company eligibility, checks FAR/DFARS compliance, and
produces compliance checklists.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from agents.base import BlueTeamAgent, SwarmContext, AgentOutput
from agents.config import AgentConfig
from agents.types import AgentRole, AgentCategory

from .prompts.compliance_navigator_prompts import (
    COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT,
    get_eligibility_assessment_prompt,
    get_far_compliance_prompt,
    get_oci_analysis_prompt,
    get_compliance_checklist_prompt,
    get_limitations_on_subcontracting_prompt,
    get_revision_prompt,
)
from agents.utils.section_formatter import (
    format_eligibility_section,
    format_checklist_section,
    format_oci_section,
    format_subcontracting_section,
    format_compliance_comprehensive_section,
)
from .rules import (
    FARComplianceChecker,
    ComplianceCheckResult,
    SmallBusinessValidator,
    EligibilityCheckResult,
    SetAsideValidator,
    SetAsideEligibility,
    SetAsideType,
)


@dataclass
class ComplianceAnalysisResult:
    """Result of a compliance analysis operation."""

    # Eligibility
    eligibility_results: Dict[str, Any] = field(default_factory=dict)
    eligible_setasides: List[str] = field(default_factory=list)

    # FAR Compliance
    far_compliance_results: List[Dict[str, Any]] = field(default_factory=list)
    compliance_gaps: List[Dict[str, Any]] = field(default_factory=list)

    # OCI Analysis
    oci_assessment: Dict[str, Any] = field(default_factory=dict)
    oci_risk_level: str = "Unknown"

    # Checklist
    compliance_checklist: List[Dict[str, Any]] = field(default_factory=list)

    # Limitations on Subcontracting
    subcontracting_compliance: Dict[str, Any] = field(default_factory=dict)

    # Summary
    overall_compliance_status: str = "Unknown"  # Compliant, Issues Found, Non-Compliant
    critical_issues: List[str] = field(default_factory=list)
    high_priority_items: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Meta
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "eligibility_results": self.eligibility_results,
            "eligible_setasides": self.eligible_setasides,
            "far_compliance_results": self.far_compliance_results,
            "compliance_gaps": self.compliance_gaps,
            "oci_assessment": self.oci_assessment,
            "oci_risk_level": self.oci_risk_level,
            "compliance_checklist": self.compliance_checklist,
            "subcontracting_compliance": self.subcontracting_compliance,
            "overall_compliance_status": self.overall_compliance_status,
            "critical_issues": self.critical_issues,
            "high_priority_items": self.high_priority_items,
            "recommendations": self.recommendations,
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "token_usage": self.token_usage,
        }


class ComplianceNavigatorAgent(BlueTeamAgent):
    """
    The Compliance Navigator provides regulatory and eligibility expertise.

    Responsibilities:
    - Validate company eligibility for specific set-asides (8(a), HUBZone, SDVOSB, WOSB)
    - Check strategy alignment with FAR/DFARS requirements
    - Flag potential Organizational Conflict of Interest (OCI) issues
    - Produce compliance checklists for specific opportunities
    - Assess limitations on subcontracting compliance

    The Compliance Navigator works with:
    - FAR (Federal Acquisition Regulation)
    - DFARS (Defense FAR Supplement)
    - SBA regulations (13 CFR)
    - Agency-specific requirements
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Compliance Navigator agent.

        Args:
            config: Optional agent configuration. If not provided, uses defaults.
        """
        if config is None:
            from agents.config import get_default_config
            config = get_default_config(AgentRole.COMPLIANCE_NAVIGATOR)

        super().__init__(config)

        # Initialize compliance checkers
        self._far_checker = FARComplianceChecker()
        self._sb_validator = SmallBusinessValidator()
        self._setaside_validator = SetAsideValidator()

    @property
    def role(self) -> AgentRole:
        return AgentRole.COMPLIANCE_NAVIGATOR

    @property
    def category(self) -> AgentCategory:
        return AgentCategory.BLUE

    async def process(self, context: SwarmContext) -> AgentOutput:
        """
        Process the context and generate compliance analysis.

        The processing mode depends on the context:
        - Eligibility assessment
        - FAR compliance review
        - OCI analysis
        - Compliance checklist generation

        Args:
            context: SwarmContext containing company profile and opportunity

        Returns:
            AgentOutput with compliance analysis content
        """
        start_time = time.time()

        # Validate context
        validation_errors = self.validate_context(context)
        if validation_errors:
            return self._create_output(
                success=False,
                error_message="; ".join(validation_errors),
            )

        try:
            # Determine analysis type from context
            # Ensure custom_data is a dict (defensive check)
            if not isinstance(context.custom_data, dict):
                self.log_warning(f"custom_data is not a dict: {type(context.custom_data)}, using empty dict")
                context.custom_data = {}
            analysis_type = context.custom_data.get("analysis_type", "comprehensive")

            if analysis_type == "eligibility":
                result = await self._assess_eligibility(context)
            elif analysis_type == "far_compliance":
                result = await self._check_far_compliance(context)
            elif analysis_type == "oci":
                result = await self._analyze_oci(context)
            elif analysis_type == "checklist":
                result = await self._generate_checklist(context)
            elif analysis_type == "subcontracting":
                result = await self._check_subcontracting(context)
            else:
                # Comprehensive analysis
                result = await self._comprehensive_analysis(context)

            processing_time = int((time.time() - start_time) * 1000)

            # Build output content
            content = self._format_analysis_content(result, analysis_type)

            return self._create_output(
                content=content,
                success=result.success,
                error_message=result.errors[0] if result.errors else None,
                warnings=result.warnings,
                processing_time_ms=processing_time,
                token_usage=result.token_usage,
                metadata={
                    "analysis_type": analysis_type,
                    "eligible_setasides": result.eligible_setasides,
                    "overall_status": result.overall_compliance_status,
                    "critical_issues_count": len(result.critical_issues),
                    "compliance_gaps_count": len(result.compliance_gaps),
                    "oci_risk_level": result.oci_risk_level,
                },
            )

        except Exception as e:
            self.log_error(f"Error in Compliance Navigator processing: {e}")
            return self._create_output(
                success=False,
                error_message=f"Processing error: {str(e)}",
            )

    def validate_context(self, context: SwarmContext) -> List[str]:
        """
        Validate the context for Compliance Navigator processing.

        Args:
            context: The SwarmContext to validate

        Returns:
            List of validation error messages
        """
        errors = super().validate_context(context)

        # Require company profile for most compliance checks
        if not context.company_profile:
            errors.append("Company profile is required for compliance analysis")

        return errors

    async def _comprehensive_analysis(
        self,
        context: SwarmContext,
    ) -> ComplianceAnalysisResult:
        """
        Perform comprehensive compliance analysis.

        Args:
            context: SwarmContext with company and opportunity data

        Returns:
            ComplianceAnalysisResult with full analysis
        """
        result = ComplianceAnalysisResult()

        # 1. Eligibility Assessment
        eligibility_result = await self._assess_eligibility(context)
        result.eligibility_results = eligibility_result.eligibility_results
        result.eligible_setasides = eligibility_result.eligible_setasides

        # 2. FAR Compliance Check (if document content available)
        if context.current_draft or context.section_drafts:
            far_result = await self._check_far_compliance(context)
            result.far_compliance_results = far_result.far_compliance_results
            result.compliance_gaps = far_result.compliance_gaps

        # 3. OCI Analysis
        oci_result = await self._analyze_oci(context)
        result.oci_assessment = oci_result.oci_assessment
        result.oci_risk_level = oci_result.oci_risk_level

        # 4. Generate Checklist
        if context.opportunity:
            checklist_result = await self._generate_checklist(context)
            result.compliance_checklist = checklist_result.compliance_checklist

        # 5. Aggregate findings
        result.critical_issues = self._aggregate_critical_issues(result)
        result.high_priority_items = self._aggregate_high_priority_items(result)
        result.recommendations = self._generate_recommendations(result)
        result.overall_compliance_status = self._determine_overall_status(result)

        # Merge token usage
        for sub_result in [eligibility_result, oci_result]:
            for key, value in sub_result.token_usage.items():
                result.token_usage[key] = result.token_usage.get(key, 0) + value

        return result

    async def _assess_eligibility(
        self,
        context: SwarmContext,
    ) -> ComplianceAnalysisResult:
        """
        Assess company eligibility for set-asides.

        Args:
            context: SwarmContext with company profile

        Returns:
            ComplianceAnalysisResult with eligibility findings
        """
        result = ComplianceAnalysisResult()
        company_profile = context.company_profile or {}

        # Use rule-based validator for initial assessment
        setaside_results = self._setaside_validator.check_all_setasides(
            company_profile,
            context.opportunity,
        )

        # Convert to dict for storage
        for sa_type, eligibility in setaside_results.items():
            result.eligibility_results[sa_type.value] = eligibility.to_dict()
            if eligibility.is_eligible:
                result.eligible_setasides.append(sa_type.value)

        # Use LLM for enhanced analysis
        target_setaside = context.custom_data.get("target_setaside")
        prompt = get_eligibility_assessment_prompt(
            company_profile=company_profile,
            opportunity=context.opportunity,
            target_setaside=target_setaside,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            # Parse and enhance results with LLM insights
            llm_content = llm_response.get("content", "")
            self._enhance_eligibility_results(result, llm_content)
            result.token_usage = llm_response.get("usage", {})

        return result

    async def _check_far_compliance(
        self,
        context: SwarmContext,
    ) -> ComplianceAnalysisResult:
        """
        Check document content for FAR/DFARS compliance.

        Args:
            context: SwarmContext with document content

        Returns:
            ComplianceAnalysisResult with compliance findings
        """
        result = ComplianceAnalysisResult()

        # Get document content
        content = ""
        if context.current_draft:
            content = str(context.current_draft)
        elif context.section_drafts:
            content = "\n\n".join(context.section_drafts.values())

        if not content:
            result.warnings.append("No document content available for FAR compliance review")
            return result

        # Use rule-based checker for initial assessment
        applicable_rules = self._far_checker.get_applicable_rules(
            contract_type=context.opportunity.get("contract_type") if context.opportunity else None,
            set_aside=context.opportunity.get("set_aside") if context.opportunity else None,
            is_dod=self._is_dod_contract(context.opportunity) if context.opportunity else False,
            contract_value=context.opportunity.get("estimated_value") if context.opportunity else None,
        )

        rule_results = self._far_checker.check_compliance(
            content=content,
            company_profile=context.company_profile,
            opportunity=context.opportunity,
            rules=applicable_rules,
        )

        for check in rule_results:
            result.far_compliance_results.append(check.to_dict())
            if check.status.value == "Non-Compliant":
                result.compliance_gaps.append({
                    "rule_id": check.rule_id,
                    "title": check.rule_title,
                    "risk_level": check.risk_level.value,
                    "findings": check.findings,
                    "recommendations": check.recommendations,
                })

        # Use LLM for enhanced compliance review
        specific_parts = context.custom_data.get("far_parts")
        prompt = get_far_compliance_prompt(
            document_content=content,
            opportunity=context.opportunity,
            specific_far_parts=specific_parts,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            llm_content = llm_response.get("content", "")
            self._enhance_far_results(result, llm_content)
            result.token_usage = llm_response.get("usage", {})

        return result

    async def _analyze_oci(
        self,
        context: SwarmContext,
    ) -> ComplianceAnalysisResult:
        """
        Analyze potential Organizational Conflicts of Interest.

        Args:
            context: SwarmContext with company and opportunity data

        Returns:
            ComplianceAnalysisResult with OCI findings
        """
        result = ComplianceAnalysisResult()

        if not context.opportunity:
            result.warnings.append("Opportunity context required for OCI analysis")
            result.oci_risk_level = "Unknown"
            return result

        # Get current contracts from custom_data if available
        current_contracts = context.custom_data.get("current_contracts", [])

        prompt = get_oci_analysis_prompt(
            company_profile=context.company_profile or {},
            opportunity=context.opportunity,
            current_contracts=current_contracts,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            content = llm_response.get("content", "")
            result.oci_assessment = self._parse_oci_response(content)
            result.oci_risk_level = result.oci_assessment.get("risk_level", "Unknown")
            result.token_usage = llm_response.get("usage", {})
        else:
            result.oci_risk_level = "Unknown"
            result.warnings.append("OCI analysis could not be completed")

        return result

    async def _generate_checklist(
        self,
        context: SwarmContext,
    ) -> ComplianceAnalysisResult:
        """
        Generate a compliance checklist for an opportunity.

        Args:
            context: SwarmContext with opportunity data

        Returns:
            ComplianceAnalysisResult with checklist
        """
        result = ComplianceAnalysisResult()

        if not context.opportunity:
            result.warnings.append("Opportunity required for checklist generation")
            return result

        # Use rule-based checker to generate initial checklist
        rule_checklist = self._far_checker.generate_compliance_checklist(
            context.opportunity
        )
        result.compliance_checklist = rule_checklist

        # Enhance with LLM
        prompt = get_compliance_checklist_prompt(
            opportunity=context.opportunity,
            company_profile=context.company_profile,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            content = llm_response.get("content", "")
            enhanced_items = self._parse_checklist_response(content)
            # Merge with rule-based checklist
            result.compliance_checklist.extend(enhanced_items)
            result.token_usage = llm_response.get("usage", {})

        return result

    async def _check_subcontracting(
        self,
        context: SwarmContext,
    ) -> ComplianceAnalysisResult:
        """
        Check limitations on subcontracting compliance.

        Args:
            context: SwarmContext with staffing plan

        Returns:
            ComplianceAnalysisResult with subcontracting compliance
        """
        result = ComplianceAnalysisResult()

        set_aside = "Small Business Set-Aside"
        if context.opportunity:
            set_aside = context.opportunity.get("set_aside", set_aside)

        contract_type = context.custom_data.get("contract_type", "services")
        staffing_plan = context.custom_data.get("staffing_plan")

        prompt = get_limitations_on_subcontracting_prompt(
            set_aside_type=set_aside,
            staffing_plan=staffing_plan,
            contract_type=contract_type,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            content = llm_response.get("content", "")
            result.subcontracting_compliance = self._parse_subcontracting_response(content)
            result.token_usage = llm_response.get("usage", {})

        return result

    async def draft_section(
        self,
        context: SwarmContext,
        section_name: str,
    ) -> str:
        """
        Draft compliance content for a specific section.

        Args:
            context: The swarm context
            section_name: Name of the section to draft

        Returns:
            The drafted content for the section
        """
        section_lower = section_name.lower()

        if "eligibility" in section_lower:
            result = await self._assess_eligibility(context)
            return self._format_eligibility_section(result)

        elif "compliance" in section_lower and "checklist" in section_lower:
            result = await self._generate_checklist(context)
            return self._format_checklist_section(result)

        elif "oci" in section_lower or "conflict" in section_lower:
            result = await self._analyze_oci(context)
            return self._format_oci_section(result)

        elif "subcontracting" in section_lower or "limitation" in section_lower:
            result = await self._check_subcontracting(context)
            return self._format_subcontracting_section(result)

        else:
            # Default to comprehensive analysis
            result = await self._comprehensive_analysis(context)
            return self._format_analysis_content(result, "comprehensive")

    async def revise_section(
        self,
        context: SwarmContext,
        section_name: str,
        critiques: List[Dict[str, Any]],
    ) -> str:
        """
        Revise compliance section based on critiques.

        Args:
            context: The swarm context
            section_name: Name of the section to revise
            critiques: List of critiques to address

        Returns:
            The revised content for the section
        """
        original = context.section_drafts.get(section_name, "")
        if not original:
            return await self.draft_section(context, section_name)

        prompt = get_revision_prompt(
            original_content=original,
            section_name=section_name,
            critiques=critiques,
        )

        llm_response = await self._call_llm(
            system_prompt=COMPLIANCE_NAVIGATOR_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if llm_response.get("success"):
            return llm_response.get("content", original)
        return original

    def _generate_mock_content(self, prompt: str) -> str:
        """Generate mock compliance content for testing."""
        prompt_lower = prompt.lower()

        if "eligibility" in prompt_lower:
            return """## Set-Aside Eligibility Assessment

### Size Status Determination
Based on the company profile, the following size determinations apply:

**NAICS 541512 (Computer Systems Design Services)**
- Size Standard: $34.0 million average annual receipts
- Company Status: **Qualifies as Small Business**
- Margin: 35% below threshold

### Eligibility Matrix

| Set-Aside Type | Status | Confidence | Notes |
|---------------|--------|------------|-------|
| Small Business | Eligible | High | Meets size standard for primary NAICS |
| 8(a) | Eligible | High | Active certification verified |
| HUBZone | Not Eligible | High | No HUBZone certification on file |
| SDVOSB | Eligible | High | VetCert certification active |
| WOSB | Not Eligible | High | Not applicable based on ownership |

### Certification Status
- **8(a)**: Active, expires in 18 months (Year 7 of 9)
- **SDVOSB**: VetCert active, no expiration concern
- **GSA MAS**: Active schedule holder

### Risk Assessment
- No immediate eligibility concerns
- Monitor 8(a) graduation timeline for long-term opportunities
- Maintain size recertification documentation

### Recommendations
1. Continue pursuing 8(a) and SDVOSB set-asides as primary targets
2. Consider HUBZone certification if principal office relocation is feasible
3. Document mentor-protégé relationships for joint venture opportunities
4. Plan for 8(a) graduation transition strategy"""

        elif "oci" in prompt_lower or "conflict" in prompt_lower:
            return """## Organizational Conflict of Interest Analysis

### OCI Type Assessment

**1. Unequal Access to Information**
- Risk Level: **Low**
- Finding: No current contracts provide access to non-public evaluation criteria or source selection information for the target opportunity.
- Mitigation: Standard information barriers are sufficient.

**2. Biased Ground Rules**
- Risk Level: **None Identified**
- Finding: Company has not participated in developing specifications, requirements, or evaluation criteria for this procurement.

**3. Impaired Objectivity**
- Risk Level: **Medium**
- Finding: Current IT support contract at the same agency could create perception of bias if advisory services are proposed.
- Recommendation: Document organizational separation between support and advisory functions.

### Overall Risk Assessment
**Overall OCI Risk: Low to Medium**

The company can proceed with this pursuit with appropriate mitigations in place.

### Mitigation Strategies
1. Establish information firewall between current support contract team and proposal team
2. Document organizational separation in proposal
3. Prepare OCI disclosure for inclusion with proposal
4. Brief proposal team on OCI restrictions and information handling

### Disclosure Requirements
- Disclose current contract at agency in proposal
- Describe mitigation measures in place
- Certify compliance with FAR 9.5

### Recommendation
**Proceed with pursuit.** Low risk OCI concerns can be adequately mitigated through standard practices. Include OCI mitigation plan in proposal."""

        elif "checklist" in prompt_lower:
            return """## Compliance Checklist

### Eligibility Requirements
- [ ] **SAM.gov Registration** - Verify active and current (Critical)
- [ ] **Size Standard Compliance** - Document size calculation (Critical)
- [ ] **Set-Aside Certification** - Verify 8(a)/SDVOSB certification active (Critical)
- [ ] **Clearance Requirements** - Confirm facility clearance if required (High)

### FAR/DFARS Requirements
- [ ] **FAR 52.212-3** - Offeror Representations and Certifications (Critical)
- [ ] **FAR 52.219-14** - Limitations on Subcontracting compliance documented (Critical)
- [ ] **DFARS 252.204-7012** - NIST 800-171 compliance if CUI involved (High)
- [ ] **CMMC Certification** - Verify level meets requirement (High)

### Technical Compliance
- [ ] **Past Performance** - Identify 3 relevant contracts (High)
- [ ] **Key Personnel** - Confirm availability and qualifications (High)
- [ ] **Technical Approach** - Address all PWS requirements (Critical)

### Administrative Requirements
- [ ] **Proposal Format** - Comply with page limits and formatting (Medium)
- [ ] **Required Forms** - Complete all required certifications (Critical)
- [ ] **Submission Method** - Confirm electronic submission requirements (Medium)

### Pre-Submission Review
- [ ] **Compliance Matrix** - Verify all requirements addressed
- [ ] **Final Review** - Legal/contracts review complete
- [ ] **Authorized Signature** - Binding commitment obtained"""

        elif "subcontracting" in prompt_lower or "limitation" in prompt_lower:
            return """## Limitations on Subcontracting Analysis

### Applicable Requirement
Per FAR 52.219-14, for services contracts set aside for small business:
- At least **50%** of the cost of contract performance incurred for personnel must be expended for employees of the concern.

### Current Staffing Plan Analysis

| Category | Hours | Labor Cost | Percentage |
|----------|-------|------------|------------|
| Prime Labor | 12,000 | $1,440,000 | 60% |
| Subcontractor | 8,000 | $960,000 | 40% |
| **Total** | 20,000 | $2,400,000 | 100% |

### Compliance Determination
**Status: COMPLIANT**

Prime personnel costs represent 60% of total personnel costs, exceeding the 50% threshold by 10 percentage points.

### Similarly Situated Entity Analysis
- SubCo A (SDVOSB): $480,000 - Could be counted toward prime if similarly situated
- SubCo B (Large Business): $480,000 - Cannot be counted toward prime

### Risk Assessment
- **Current Margin**: 10% above threshold
- **Risk Level**: Low
- **Recommendation**: Maintain staffing ratio; monitor during performance

### Monitoring Recommendations
1. Track labor hours monthly during contract performance
2. Document any changes to staffing plan
3. Recalculate compliance if subcontracting increases
4. Maintain records for potential audit

### Adjustments if Needed
If additional subcontracting is required:
- Prioritize similarly situated small business subcontractors
- Increase prime labor hours proportionally
- Document justification for any changes"""

        else:
            # Comprehensive analysis
            return """## Compliance Navigator Analysis

### Executive Summary
Based on the analysis of company profile and opportunity requirements, the company is **generally well-positioned** for this pursuit with minor compliance items to address.

### Eligibility Status
- **Primary Set-Aside Eligibility**: 8(a), SDVOSB, Small Business
- **Certification Status**: All relevant certifications current and valid
- **Size Standard**: Meets requirements with comfortable margin

### Compliance Assessment

#### FAR Compliance
- **FAR Part 15**: Negotiated procurement requirements understood
- **FAR Part 19**: Small business provisions applicable
- **FAR 9.5 OCI**: Low risk identified, standard mitigation sufficient

#### DFARS Compliance (if applicable)
- **DFARS 7012**: Cybersecurity requirements analysis needed
- **CMMC**: Verify certification level meets solicitation requirement

### Critical Items (Action Required)
1. Verify CMMC certification level before proposal submission
2. Complete OCI disclosure documentation
3. Finalize subcontracting plan to demonstrate limitations compliance

### High Priority Items
1. Update SAM.gov registration with current information
2. Prepare past performance references
3. Document key personnel availability

### Recommendations
1. Proceed with proposal development
2. Address critical items before submission deadline
3. Conduct final compliance review 48 hours before submission
4. Maintain documentation for potential audit

### Risk Assessment
**Overall Compliance Risk: Low**

No critical compliance gaps identified. Standard proposal preparation process is appropriate."""

    def _is_dod_contract(self, opportunity: Optional[Dict[str, Any]]) -> bool:
        """Check if opportunity is a DoD contract."""
        if not opportunity:
            return False

        agency = opportunity.get("agency", {})
        if isinstance(agency, dict):
            agency_name = agency.get("name", "")
        else:
            agency_name = str(agency)

        dod_indicators = ["DoD", "Defense", "Army", "Navy", "Air Force", "Marine", "DISA", "DARPA"]
        return any(ind.lower() in agency_name.lower() for ind in dod_indicators)

    def _enhance_eligibility_results(
        self,
        result: ComplianceAnalysisResult,
        llm_content: str,
    ) -> None:
        """Enhance eligibility results with LLM insights."""
        # Parse LLM response to add recommendations and warnings
        if "not eligible" in llm_content.lower():
            result.warnings.append("Some eligibility concerns identified - review detailed analysis")

    def _enhance_far_results(
        self,
        result: ComplianceAnalysisResult,
        llm_content: str,
    ) -> None:
        """Enhance FAR compliance results with LLM insights."""
        # Extract additional compliance gaps from LLM analysis
        if "critical" in llm_content.lower():
            result.warnings.append("Critical compliance items identified - immediate attention required")

    def _parse_oci_response(self, content: str) -> Dict[str, Any]:
        """Parse OCI analysis response from LLM."""
        result = {
            "risk_level": "Unknown",
            "oci_types_identified": [],
            "mitigation_required": False,
            "recommendation": "",
        }

        content_lower = content.lower()

        # Determine risk level
        if "high risk" in content_lower or "significant conflict" in content_lower:
            result["risk_level"] = "High"
            result["mitigation_required"] = True
        elif "medium risk" in content_lower or "potential" in content_lower:
            result["risk_level"] = "Medium"
            result["mitigation_required"] = True
        elif "low risk" in content_lower or "low to medium" in content_lower:
            result["risk_level"] = "Low"
        elif "no oci" in content_lower or "none identified" in content_lower:
            result["risk_level"] = "None"

        # Extract recommendation
        if "proceed" in content_lower:
            result["recommendation"] = "Proceed with appropriate mitigations"
        elif "do not pursue" in content_lower or "avoid" in content_lower:
            result["recommendation"] = "Consider not pursuing due to OCI concerns"

        return result

    def _parse_checklist_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse checklist items from LLM response."""
        items = []
        # Simple parsing - extract checkbox items
        import re

        checkbox_pattern = r'\[\s*\]\s*\*\*([^*]+)\*\*\s*-\s*(.+?)(?:\((\w+)\))?$'
        for match in re.finditer(checkbox_pattern, content, re.MULTILINE):
            items.append({
                "title": match.group(1).strip(),
                "description": match.group(2).strip(),
                "risk_level": match.group(3) if match.group(3) else "Medium",
                "checked": False,
            })

        return items

    def _parse_subcontracting_response(self, content: str) -> Dict[str, Any]:
        """Parse subcontracting analysis response."""
        result = {
            "is_compliant": False,
            "prime_percentage": 0,
            "threshold": 50,
            "margin": 0,
            "risk_level": "Unknown",
        }

        content_lower = content.lower()

        if "compliant" in content_lower and "non-compliant" not in content_lower:
            result["is_compliant"] = True

        # Extract percentage if present
        import re
        pct_match = re.search(r'(\d+)%', content)
        if pct_match:
            result["prime_percentage"] = int(pct_match.group(1))
            result["margin"] = result["prime_percentage"] - 50

        return result

    def _aggregate_critical_issues(self, result: ComplianceAnalysisResult) -> List[str]:
        """Aggregate critical issues from all analysis results."""
        issues = []

        for gap in result.compliance_gaps:
            if gap.get("risk_level") == "critical":
                issues.append(f"{gap.get('title')}: {gap.get('findings', [''])[0]}")

        if result.oci_risk_level == "High":
            issues.append("High OCI risk identified - requires mitigation or reconsideration")

        return issues

    def _aggregate_high_priority_items(self, result: ComplianceAnalysisResult) -> List[str]:
        """Aggregate high priority items from analysis."""
        items = []

        for gap in result.compliance_gaps:
            if gap.get("risk_level") == "High":
                items.append(gap.get("title", "Unknown compliance gap"))

        return items

    def _generate_recommendations(self, result: ComplianceAnalysisResult) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        if result.critical_issues:
            recommendations.append("Address critical compliance issues before proposal submission")

        if result.oci_risk_level in ["Medium", "High"]:
            recommendations.append("Develop and document OCI mitigation plan")

        if not result.eligible_setasides:
            recommendations.append("Consider teaming arrangements to access set-aside opportunities")

        if len(result.compliance_gaps) > 3:
            recommendations.append("Conduct detailed compliance review with legal counsel")

        if not recommendations:
            recommendations.append("Continue with standard proposal preparation process")

        return recommendations

    def _determine_overall_status(self, result: ComplianceAnalysisResult) -> str:
        """Determine overall compliance status."""
        if result.critical_issues:
            return "Non-Compliant"
        elif result.high_priority_items or result.compliance_gaps:
            return "Issues Found"
        else:
            return "Compliant"

    def _format_analysis_content(
        self,
        result: ComplianceAnalysisResult,
        analysis_type: str,
    ) -> str:
        """Format analysis result as content string."""
        if analysis_type == "eligibility":
            return self._format_eligibility_section(result)
        elif analysis_type == "checklist":
            return self._format_checklist_section(result)
        elif analysis_type == "oci":
            return self._format_oci_section(result)
        elif analysis_type == "subcontracting":
            return self._format_subcontracting_section(result)
        else:
            return self._format_comprehensive_section(result)

    def _format_eligibility_section(self, result: ComplianceAnalysisResult) -> str:
        """Format eligibility analysis as a section."""
        return format_eligibility_section(result)

    def _format_checklist_section(self, result: ComplianceAnalysisResult) -> str:
        """Format compliance checklist as a section."""
        return format_checklist_section(result.compliance_checklist)

    def _format_oci_section(self, result: ComplianceAnalysisResult) -> str:
        """Format OCI analysis as a section."""
        return format_oci_section(result.oci_risk_level, result.oci_assessment)

    def _format_subcontracting_section(self, result: ComplianceAnalysisResult) -> str:
        """Format subcontracting compliance as a section."""
        return format_subcontracting_section(result.subcontracting_compliance)

    def _format_comprehensive_section(self, result: ComplianceAnalysisResult) -> str:
        """Format comprehensive analysis as a section."""
        return format_compliance_comprehensive_section(result)
