"""
투자자 에이전트 모듈
다양한 유형의 투자자 행동을 시뮬레이션하여 군중 심리 반영
"""
import random
from typing import Dict, List
from enum import Enum


class AgentType(Enum):
    """투자자 에이전트 유형"""
    INFORMED = "informed"        # 정보형: 많은 기사를 종합적으로 분석
    BIASED = "biased"           # 편향형: 특정 섹터만 집중
    IMPULSIVE = "impulsive"     # 충동형: 헤드라인 몇 개만 보고 반응


class InvestorAgent:
    """개별 투자자 에이전트"""

    def __init__(
        self,
        agent_id: int,
        agent_type: AgentType,
        sample_size: int,
        bias_sectors: List[str] = None,
        amplification_factor: float = 1.0
    ):
        """
        Args:
            agent_id: 에이전트 고유 ID
            agent_type: 에이전트 유형 (INFORMED, BIASED, IMPULSIVE)
            sample_size: 읽을 기사 수
            bias_sectors: 관심 섹터 리스트 (BIASED 타입용)
            amplification_factor: 점수 증폭 계수 (충동형은 과잉반응)
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.sample_size = sample_size
        self.bias_sectors = bias_sectors or []
        self.amplification_factor = amplification_factor

    def select_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        에이전트 유형에 따라 읽을 기사 선택

        Args:
            articles: 전체 기사 리스트

        Returns:
            선택된 기사 리스트
        """
        if not articles:
            return []

        available_articles = articles.copy()

        # BIASED 타입: 관심 섹터 키워드가 포함된 기사 우선
        if self.agent_type == AgentType.BIASED and self.bias_sectors:
            biased_articles = []
            for article in available_articles:
                article_text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
                for sector in self.bias_sectors:
                    if sector.lower() in article_text:
                        biased_articles.append(article)
                        break

            # 편향 기사가 충분하면 그것만, 아니면 일반 기사도 포함
            if len(biased_articles) >= self.sample_size:
                available_articles = biased_articles
            else:
                # 편향 기사 우선, 나머지는 랜덤
                remaining_needed = self.sample_size - len(biased_articles)
                other_articles = [a for a in available_articles if a not in biased_articles]
                if other_articles and remaining_needed > 0:
                    biased_articles.extend(random.sample(other_articles, min(remaining_needed, len(other_articles))))
                return biased_articles[:self.sample_size]

        # 샘플 크기만큼 랜덤 선택
        actual_sample_size = min(self.sample_size, len(available_articles))
        return random.sample(available_articles, actual_sample_size)

    def apply_bias_to_scores(self, scores: Dict[str, int]) -> Dict[str, int]:
        """
        에이전트 특성에 따라 점수에 편향 적용

        Args:
            scores: 원본 섹터별 점수

        Returns:
            편향이 적용된 점수
        """
        modified_scores = scores.copy()

        # BIASED: 관심 섹터 점수 증폭
        if self.agent_type == AgentType.BIASED and self.bias_sectors:
            for sector in self.bias_sectors:
                if sector in modified_scores:
                    modified_scores[sector] = int(modified_scores[sector] * 1.5)

        # IMPULSIVE: 모든 점수 증폭 (과잉반응)
        if self.agent_type == AgentType.IMPULSIVE:
            for sector in modified_scores:
                modified_scores[sector] = int(modified_scores[sector] * self.amplification_factor)

        return modified_scores


class AgentPopulation:
    """투자자 에이전트 집단 관리"""

    # 섹터 리스트 (편향형 에이전트용)
    ALL_SECTORS = [
        "Technology", "Semiconductors", "Financials", "Healthcare",
        "Energy", "Airlines", "Consumer Discretionary", "Consumer Staples",
        "Commodities", "Utilities", "Real Estate"
    ]

    def __init__(
        self,
        num_agents: int = 100,
        informed_ratio: float = 0.20,
        biased_ratio: float = 0.50,
        impulsive_ratio: float = 0.30,
        informed_sample_size: int = 10,
        biased_sample_size: int = 5,
        impulsive_sample_size: int = 2
    ):
        """
        Args:
            num_agents: 총 에이전트 수
            informed_ratio: 정보형 에이전트 비율 (0.0 ~ 1.0)
            biased_ratio: 편향형 에이전트 비율
            impulsive_ratio: 충동형 에이전트 비율
            informed_sample_size: 정보형이 읽는 기사 수
            biased_sample_size: 편향형이 읽는 기사 수
            impulsive_sample_size: 충동형이 읽는 기사 수
        """
        self.num_agents = num_agents
        self.agents: List[InvestorAgent] = []

        # 비율 정규화
        total_ratio = informed_ratio + biased_ratio + impulsive_ratio
        informed_ratio /= total_ratio
        biased_ratio /= total_ratio
        impulsive_ratio /= total_ratio

        # 각 유형별 에이전트 수 계산
        num_informed = int(num_agents * informed_ratio)
        num_biased = int(num_agents * biased_ratio)
        num_impulsive = num_agents - num_informed - num_biased

        agent_id = 0

        # 정보형 에이전트 생성
        for _ in range(num_informed):
            self.agents.append(InvestorAgent(
                agent_id=agent_id,
                agent_type=AgentType.INFORMED,
                sample_size=informed_sample_size,
                amplification_factor=1.0
            ))
            agent_id += 1

        # 편향형 에이전트 생성 (각자 1-3개 섹터에 관심)
        for _ in range(num_biased):
            num_bias_sectors = random.randint(1, 3)
            bias_sectors = random.sample(self.ALL_SECTORS, num_bias_sectors)
            self.agents.append(InvestorAgent(
                agent_id=agent_id,
                agent_type=AgentType.BIASED,
                sample_size=biased_sample_size,
                bias_sectors=bias_sectors,
                amplification_factor=1.0
            ))
            agent_id += 1

        # 충동형 에이전트 생성 (과잉반응 계수 1.2 ~ 2.0)
        for _ in range(num_impulsive):
            amplification = random.uniform(1.2, 2.0)
            self.agents.append(InvestorAgent(
                agent_id=agent_id,
                agent_type=AgentType.IMPULSIVE,
                sample_size=impulsive_sample_size,
                amplification_factor=amplification
            ))
            agent_id += 1

        print(f"✅ 에이전트 생성 완료: 총 {num_agents}명")
        print(f"   - 정보형: {num_informed}명 (기사 {informed_sample_size}개)")
        print(f"   - 편향형: {num_biased}명 (기사 {biased_sample_size}개)")
        print(f"   - 충동형: {num_impulsive}명 (기사 {impulsive_sample_size}개)")

    def get_agents(self) -> List[InvestorAgent]:
        """모든 에이전트 반환"""
        return self.agents

    def get_population_stats(self) -> Dict:
        """에이전트 집단 통계"""
        type_counts = {
            AgentType.INFORMED: 0,
            AgentType.BIASED: 0,
            AgentType.IMPULSIVE: 0
        }

        for agent in self.agents:
            type_counts[agent.agent_type] += 1

        return {
            'total': len(self.agents),
            'informed': type_counts[AgentType.INFORMED],
            'biased': type_counts[AgentType.BIASED],
            'impulsive': type_counts[AgentType.IMPULSIVE]
        }
