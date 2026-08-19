"""
Feature #5: Response Fusion Engine
Combines the best parts of multiple LLM responses into a superior answer
"""

from typing import Dict, List
import re

class ResponseFusionEngine:
    """Fuses multiple LLM responses to create an optimized answer"""

    def __init__(self):
        self.llm_strengths = {
            'gpt': ['explanation', 'clarity', 'examples'],
            'claude': ['reasoning', 'structure', 'depth'],
            'gemini': ['examples', 'visualization', 'creativity'],
            'deepseek': ['technical', 'mathematical', 'code'],
            'llama': ['practical', 'application', 'concise']
        }

    def extract_sections(self, response: str) -> Dict[str, str]:
        """
        Extract different sections from a response

        Returns:
            Dict with section types as keys
        """
        sections = {
            'introduction': '',
            'explanation': '',
            'examples': '',
            'code': '',
            'conclusion': ''
        }

        # Extract code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', response)
        if code_blocks:
            sections['code'] = '\n\n'.join(code_blocks)
            # Remove code from main text for further processing
            response_without_code = re.sub(r'```[\s\S]*?```', '', response)
        else:
            response_without_code = response

        # Split into paragraphs
        paragraphs = [p.strip() for p in response_without_code.split('\n\n') if p.strip()]

        if not paragraphs:
            return sections

        # First paragraph is often introduction
        if len(paragraphs) > 0:
            sections['introduction'] = paragraphs[0]

        # Look for example indicators
        example_patterns = r'(for example|for instance|e\.g\.|such as|consider|let\'s say)'
        examples = []
        explanations = []

        for para in paragraphs[1:]:
            if re.search(example_patterns, para, re.I):
                examples.append(para)
            else:
                explanations.append(para)

        sections['explanation'] = '\n\n'.join(explanations)
        sections['examples'] = '\n\n'.join(examples)

        # Last paragraph might be conclusion
        if len(paragraphs) > 2:
            last_para = paragraphs[-1]
            conclusion_markers = ['in conclusion', 'to summarize', 'in summary', 'therefore', 'thus']
            if any(marker in last_para.lower() for marker in conclusion_markers):
                sections['conclusion'] = last_para

        return sections

    def score_section_quality(self, section: str, section_type: str) -> float:
        """
        Score the quality of a specific section

        Returns:
            Quality score 0.0 to 1.0
        """
        if not section or len(section) < 20:
            return 0.0

        score = 0.5  # Base score

        # Length appropriateness
        if section_type == 'introduction':
            if 50 < len(section) < 300:
                score += 0.2
        elif section_type == 'explanation':
            if len(section) > 100:
                score += 0.2
        elif section_type == 'examples':
            if len(section) > 50:
                score += 0.2
        elif section_type == 'code':
            if '```' in section:
                score += 0.3

        # Check for clarity markers
        clarity_markers = ['first', 'second', 'then', 'next', 'finally', 'step']
        if any(marker in section.lower() for marker in clarity_markers):
            score += 0.1

        # Check for technical depth
        if section_type == 'explanation':
            technical_markers = ['because', 'therefore', 'due to', 'as a result']
            if any(marker in section.lower() for marker in technical_markers):
                score += 0.2

        return min(1.0, score)

    def select_best_sections(
        self,
        responses: Dict[str, str],
        scores: Dict[str, Dict] = None
    ) -> Dict[str, Tuple[str, str]]:
        """
        Select the best section from each LLM for each section type

        Args:
            responses: Dict mapping llm_name to response_text
            scores: Optional scoring data from ResponseScorer

        Returns:
            Dict mapping section_type to (best_llm, section_text)
        """
        # Extract sections from all responses
        all_sections = {}
        for llm_name, response in responses.items():
            all_sections[llm_name] = self.extract_sections(response)

        # For each section type, find the best one
        best_sections = {}
        section_types = ['introduction', 'explanation', 'examples', 'code', 'conclusion']

        for section_type in section_types:
            best_score = 0
            best_llm = None
            best_content = ""

            for llm_name in responses.keys():
                section_content = all_sections[llm_name].get(section_type, '')

                if not section_content:
                    continue

                # Score this section
                quality_score = self.score_section_quality(section_content, section_type)

                # Bonus points if this LLM is known to be strong in this area
                if section_type in self.llm_strengths.get(llm_name, []):
                    quality_score += 0.1

                # Bonus from overall response quality
                if scores and llm_name in scores:
                    overall_score = scores[llm_name].get('overall_score', 0)
                    quality_score += overall_score * 0.1

                if quality_score > best_score:
                    best_score = quality_score
                    best_llm = llm_name
                    best_content = section_content

            if best_llm:
                best_sections[section_type] = (best_llm, best_content)

        return best_sections

    def fuse_responses(
        self,
        responses: Dict[str, str],
        scores: Dict[str, Dict] = None,
        strategy: str = 'best_of_each'
    ) -> Dict[str, any]:
        """
        Main fusion method

        Args:
            responses: Dict mapping llm_name to response_text
            scores: Optional scoring data
            strategy: Fusion strategy ('best_of_each', 'consensus', 'weighted')

        Returns:
            Dict with fused response and metadata
        """
        if strategy == 'best_of_each':
            return self._fuse_best_of_each(responses, scores)
        elif strategy == 'consensus':
            return self._fuse_consensus(responses, scores)
        else:
            return self._fuse_best_of_each(responses, scores)

    def _fuse_best_of_each(
        self,
        responses: Dict[str, str],
        scores: Dict[str, Dict] = None
    ) -> Dict[str, any]:
        """
        Fusion strategy: Take the best section from each LLM
        """
        best_sections = self.select_best_sections(responses, scores)

        # Build the fused response
        fused_parts = []
        attribution = {}

        for section_type in ['introduction', 'explanation', 'examples', 'code', 'conclusion']:
            if section_type in best_sections:
                llm_name, content = best_sections[section_type]
                fused_parts.append(content)
                attribution[section_type] = llm_name

        fused_response = '\n\n'.join(fused_parts)

        return {
            'fused_response': fused_response,
            'strategy': 'best_of_each',
            'attribution': attribution,
            'sections_used': list(best_sections.keys()),
            'llms_contributed': list(set(attribution.values())),
            'metadata': {
                'introduction_from': attribution.get('introduction'),
                'explanation_from': attribution.get('explanation'),
                'examples_from': attribution.get('examples'),
                'code_from': attribution.get('code'),
                'conclusion_from': attribution.get('conclusion')
            }
        }

    def _fuse_consensus(
        self,
        responses: Dict[str, str],
        scores: Dict[str, Dict] = None
    ) -> Dict[str, any]:
        """
        Fusion strategy: Focus on areas of consensus
        """
        # Extract common themes/facts that appear in multiple responses
        # This is simplified - in production, use NLP for semantic similarity

        all_sentences = {}
        for llm_name, response in responses.items():
            sentences = [s.strip() for s in re.split(r'[.!?]+', response) if len(s.strip()) > 20]
            all_sentences[llm_name] = sentences

        # Find sentences that appear in multiple responses (or are very similar)
        consensus_content = []
        used_sentences = set()

        llm_names = list(responses.keys())
        for i, llm1 in enumerate(llm_names):
            for sent1 in all_sentences[llm1]:
                if sent1 in used_sentences:
                    continue

                # Count how many other LLMs have similar sentences
                agreement_count = 1  # Starts at 1 for the source LLM
                for llm2 in llm_names[i + 1:]:
                    for sent2 in all_sentences[llm2]:
                        # Simple similarity check
                        if self._simple_similarity(sent1, sent2) > 0.6:
                            agreement_count += 1
                            break

                # If multiple LLMs agree, include in consensus
                if agreement_count >= len(llm_names) / 2:
                    consensus_content.append(sent1)
                    used_sentences.add(sent1)

        fused_response = '. '.join(consensus_content) + '.'

        return {
            'fused_response': fused_response,
            'strategy': 'consensus',
            'consensus_level': len(consensus_content) / max(sum(len(s) for s in all_sentences.values()), 1),
            'llms_contributed': llm_names,
            'metadata': {
                'total_consensus_items': len(consensus_content),
                'agreement_threshold': 0.5
            }
        }

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word-based similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def generate_attribution_note(self, attribution: Dict[str, str]) -> str:
        """Generate a nice attribution note for the fused response"""
        notes = []

        section_names = {
            'introduction': 'Introduction',
            'explanation': 'Explanation',
            'examples': 'Examples',
            'code': 'Code',
            'conclusion': 'Conclusion'
        }

        for section_type, llm_name in attribution.items():
            section_name = section_names.get(section_type, section_type)
            notes.append(f"{section_name} from {llm_name.upper()}")

        return "**Fused Response Attribution:**\n- " + "\n- ".join(notes)
