"""LLM Client and synthesis coordinator for Phase 2 Agentic Analysis using Groq LLM.

Uses Groq Cloud API (Llama 3.3 70B Versatile) for ultra-fast thematic synthesis
and action ideation, with deterministic domain semantic fallback for offline/test environments.
"""

import os
import json
import logging
from typing import List, Optional
from src.config.settings import settings
from src.ingestion.models import ReviewRecord
from src.agent.models import ClusteredTheme, VerbatimQuote, ActionItem, ExecutivePulsePayload
from src.agent.clusterer import ThematicClusterer
from src.agent.action_synthesizer import ActionSynthesizer
from src.agent.pulse_distiller import PulseDistiller

logger = logging.getLogger(__name__)


class AgentSynthesisCoordinator:
    """Coordinates clustering, quote extraction, action ideation, and distillation using Groq."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or settings.agent.api_key
        self.model_name = model_name or settings.agent.model_name
        self.clusterer = ThematicClusterer()
        self.groq_client = None

        if self.api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.api_key)
                logger.info("Initialized Groq LLM client with model '%s'", self.model_name)
            except Exception as e:
                logger.warning("Failed to initialize Groq client: %s. Falling back to deterministic engine.", e)

    def synthesize_actions_with_groq(
        self,
        top_themes: List[ClusteredTheme],
        quotes: List[VerbatimQuote],
    ) -> List[ActionItem]:
        """Synthesize 3 concrete, high-leverage product/engineering actions using Groq Llama 3.3 70B."""
        if not self.groq_client:
            return ActionSynthesizer.synthesize_actions(top_themes)

        theme_summaries = []
        for i, t in enumerate(top_themes, 1):
            theme_summaries.append(
                f"Theme {i}: {t.name}\n"
                f"Description: {t.description}\n"
                f"Review Count: {t.review_count}\n"
                f"Negative Ratings: {t.rating_breakdown.get(1, 0) + t.rating_breakdown.get(2, 0)}"
            )

        quote_texts = [f"- \"{q.quote_text}\" ({q.theme_name})" for q in quotes]

        prompt = (
            "You are a Chief Product Officer and Lead Architect for the Groww trading platform.\n"
            "Analyze the top 3 user friction themes and verbatim review quotes below. "
            "Generate exactly 3 concrete, high-leverage, engineering-actionable recommendations "
            "(one per theme) to eliminate the root causes.\n\n"
            "TOP THEMES:\n" + "\n\n".join(theme_summaries) + "\n\n"
            "VERBATIM USER QUOTES:\n" + "\n".join(quote_texts) + "\n\n"
            "Respond strictly with a JSON object in this exact schema without markdown backticks:\n"
            "{\n"
            '  "actions": [\n'
            '    {"item_id": 1, "title": "...", "recommendation": "...", "target_theme": "..."},\n'
            '    {"item_id": 2, "title": "...", "recommendation": "...", "target_theme": "..."},\n'
            '    {"item_id": 3, "title": "...", "recommendation": "...", "target_theme": "..."}\n'
            "  ]\n"
            "}"
        )

        try:
            logger.info("Calling Groq LLM (%s) for action item synthesis...", self.model_name)
            response = self.groq_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert product and fintech engineering strategist."},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.agent.temperature,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content.strip()
            data = json.loads(raw_content)
            actions_data = data.get("actions", [])

            actions: List[ActionItem] = []
            for item in actions_data[:3]:
                actions.append(
                    ActionItem(
                        item_id=item.get("item_id", len(actions) + 1),
                        title=item.get("title", f"Action {len(actions) + 1}"),
                        recommendation=item.get("recommendation", ""),
                        target_theme=item.get("target_theme", top_themes[len(actions)].name),
                    )
                )

            if len(actions) == 3:
                logger.info("Successfully synthesized 3 actions using Groq LLM.")
                return actions
            else:
                logger.warning("Groq returned %d actions instead of 3. Using template synthesizer fallback.", len(actions))
                return ActionSynthesizer.synthesize_actions(top_themes)

        except Exception as e:
            logger.warning("Groq API call failed (%s). Falling back to deterministic synthesizer.", e)
            return ActionSynthesizer.synthesize_actions(top_themes)

    def generate_weekly_pulse(
        self,
        reviews: List[ReviewRecord],
        date_range: Optional[str] = None,
    ) -> ExecutivePulsePayload:
        """Run the complete Phase 2 agentic synthesis workflow on clean reviews.

        Steps:
            1. Cluster reviews into <= 5 themes and prioritize Top 3 based on severity score.
            2. Extract and verify 3 verbatim user quotes (one per top theme).
            3. Synthesize 3 concrete next action ideas (via Groq LLM when configured).
            4. Distill into a scannable markdown note bounded strictly to <= 250 words.
        """
        if not reviews:
            raise ValueError("Cannot generate weekly pulse from an empty review corpus.")

        if not date_range:
            sorted_dates = sorted(r.date for r in reviews)
            earliest = sorted_dates[0].strftime("%b %d, %Y")
            latest = sorted_dates[-1].strftime("%b %d, %Y")
            date_range = f"{earliest} - {latest}"

        logger.info(
            "Synthesizing weekly pulse for %d reviews across timeframe %s (LLM Provider: Groq)",
            len(reviews),
            date_range,
        )

        # 1. Cluster & extract Top 3 themes and verified quotes
        top_themes, quotes = self.clusterer.get_top_themes_and_quotes(reviews, top_n=3)

        # 2. Synthesize 3 concrete action ideas (uses Groq LLM when GROQ_API_KEY is available)
        action_ideas = self.synthesize_actions_with_groq(top_themes, quotes)

        # 3. Distill into scannable markdown note (<= 250 words)
        payload = PulseDistiller.distill_note(
            date_range=date_range,
            total_reviews=len(reviews),
            top_themes=top_themes,
            quotes=quotes,
            actions=action_ideas,
            max_words=settings.agent.max_word_count,
        )

        logger.info(
            "Weekly pulse generated successfully: %d words, 3 themes, 3 quotes, 3 actions.",
            payload.word_count,
        )
        return payload
