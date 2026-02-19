"""
에이전트 기반 군중 심리 분석 테스트
간단한 샘플 뉴스로 에이전트 시뮬레이션 검증
"""
from analysis.investor_agent import AgentPopulation, AgentType

# 샘플 뉴스 기사
sample_articles = [
    {
        'title': 'Tech Giants Report Record Earnings, AI Boom Continues',
        'summary': 'Major technology companies including Microsoft and Google reported record-breaking earnings driven by artificial intelligence demand.',
        'link': 'https://example.com/article1',
        'source': 'Tech News',
        'published': '2024-01-15'
    },
    {
        'title': 'Oil Prices Plunge on Oversupply Concerns',
        'summary': 'Crude oil prices dropped 5% as OPEC announced production increases, raising concerns about global oversupply.',
        'link': 'https://example.com/article2',
        'source': 'Energy Today',
        'published': '2024-01-15'
    },
    {
        'title': 'Semiconductor Shortage Eases, Prices Decline',
        'summary': 'Chip manufacturers report improved supply chains as semiconductor shortage finally shows signs of ending.',
        'link': 'https://example.com/article3',
        'source': 'Chip Weekly',
        'published': '2024-01-15'
    },
    {
        'title': 'Banking Sector Faces Headwinds from Rising Defaults',
        'summary': 'Major banks warn of increasing loan defaults as economic uncertainty continues.',
        'link': 'https://example.com/article4',
        'source': 'Finance Daily',
        'published': '2024-01-15'
    },
    {
        'title': 'Healthcare Stocks Surge on Drug Approval News',
        'summary': 'Pharmaceutical companies rally after FDA approves breakthrough cancer treatment.',
        'link': 'https://example.com/article5',
        'source': 'Med News',
        'published': '2024-01-15'
    }
]

print("="*60)
print("에이전트 기반 군중 심리 시뮬레이션 테스트")
print("="*60)

# 에이전트 집단 생성
print("\n1. 에이전트 집단 생성 중...")
agent_pop = AgentPopulation(
    num_agents=50,
    informed_ratio=0.20,
    biased_ratio=0.50,
    impulsive_ratio=0.30,
    informed_sample_size=5,
    biased_sample_size=3,
    impulsive_sample_size=2
)

agents = agent_pop.get_agents()
print(f"✅ 총 {len(agents)}명의 에이전트 생성 완료")

# 에이전트 유형별 통계
stats = agent_pop.get_population_stats()
print(f"\n📊 에이전트 통계:")
print(f"   - 정보형: {stats['informed']}명")
print(f"   - 편향형: {stats['biased']}명")
print(f"   - 충동형: {stats['impulsive']}명")

# 각 에이전트가 기사 선택
print(f"\n2. 각 에이전트의 기사 선택 패턴 분석 (샘플 10명)")
print(f"   총 기사 수: {len(sample_articles)}개\n")

for i, agent in enumerate(agents[:10]):  # 처음 10명만 출력
    selected = agent.select_articles(sample_articles)
    print(f"   에이전트 #{agent.agent_id} ({agent.agent_type.value}): {len(selected)}개 기사 선택")

    if agent.agent_type == AgentType.BIASED and agent.bias_sectors:
        print(f"      관심 섹터: {', '.join(agent.bias_sectors)}")

    if agent.agent_type == AgentType.IMPULSIVE:
        print(f"      증폭 계수: {agent.amplification_factor:.2f}x")

    for article in selected:
        print(f"      - {article['title'][:60]}...")

print("\n" + "="*60)
print("✅ 테스트 완료")
print("="*60)
print("\n💡 실제 파이프라인에서는:")
print("   1. RSS에서 뉴스 수집")
print("   2. 각 기사를 AI로 분석 (섹터별 점수)")
print("   3. 각 에이전트가 일부 기사만 읽고 반응")
print("   4. 모든 에이전트의 반응을 합산하여 시장 심리 계산")
print("   5. 군중의 비합리적 행동이 반영된 신호 생성")
