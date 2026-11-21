"""Action Item Synthesizer for Groww Weekly Feedback Pulse.

Generates exactly 3 concrete, pragmatic, engineering/product-actionable
next steps grounded directly in the prioritized Top 3 themes.
"""

from typing import List
from src.agent.models import ClusteredTheme, ActionItem


DOMAIN_ACTION_TEMPLATES = {
    "trading_execution": {
        "title": "Harden F&O Order Exit & Websocket Reconnection Resiliency",
        "recommendation": "Implement client-side websocket heartbeat auto-reconnect and fallback order-polling to prevent 'adapter disconnected' errors and stop-loss execution drops during peak volatility.",
    },
    "portfolio_mf": {
        "title": "Automate CAMS Mutual Fund Ingestion Reconciliation",
        "recommendation": "Deploy automated daily CAMS/KFintech statement reconciliation with discrepancy alerts to prevent incorrect XIRR calculations and portfolio allocation mismatches.",
    },
    "chart_stability": {
        "title": "Resolve Chart Loading Timeouts & Android Feature Parity",
        "recommendation": "Cache symbol candlestick data locally to eliminate 'failed to load' timeouts and ship live percentage preview line parity on Android matching the iOS experience.",
    },
    "charges_support": {
        "title": "Introduce Upfront Brokerage & Fee Transparency Breakdown",
        "recommendation": "Display an itemized pre-trade charge estimator (brokerage, STT, exchange fees) on the order ticket to eliminate surprise fee disputes in F&O trades.",
    },
    "onboarding_ipo": {
        "title": "Streamline IPO Bidding & Multi-VPA Management",
        "recommendation": "Allow inline editing of linked UPI VPAs for IPO mandates without requiring application cancellation, and clarify exchange-allotment status messaging.",
    },
}


class ActionSynthesizer:
    """Generates concrete next steps directly addressing prioritized friction themes."""

    @classmethod
    def synthesize_actions(cls, top_themes: List[ClusteredTheme]) -> List[ActionItem]:
        """Generate exactly 3 actionable engineering/product recommendations."""
        actions: List[ActionItem] = []

        for idx, theme in enumerate(top_themes[:3], start=1):
            theme_id = theme.theme_id
            template = DOMAIN_ACTION_TEMPLATES.get(
                theme_id,
                {
                    "title": f"Address Core Friction in {theme.name}",
                    "recommendation": f"Prioritize engineering investigation and UI telemetry to eliminate user-reported issues in {theme.name}.",
                }
            )

            actions.append(
                ActionItem(
                    item_id=idx,
                    title=template["title"],
                    recommendation=template["recommendation"],
                    target_theme=theme.name,
                )
            )

        return actions

