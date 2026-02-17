import discord
from discord.ext import commands
from analysis import f_score_analyzer, fs_score_analyzer, ncav_analyzer, economic_indicator

intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 권한 활성화

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"봇 로그인 완료: {bot.user}")

    # 슬래시 명령어를 서버에 동기화
    await bot.tree.sync()

@bot.tree.command(name="tickercheck", description="티커 정보를 확인합니다")
async def tickercheck(interaction: discord.Interaction,ticker: str):
    try:
        await interaction.response.defer()

        # F-Score와 FS-Score 계산
        tickerdict = f_score_analyzer.calculate_f_score(ticker)
        fs_dict = fs_score_analyzer.calculate_fs_score(ticker, f_score_result=tickerdict)
        breakdown = tickerdict['breakdown']

        # NCAV 분석 결과 가져오기
        ncav_result = ncav_analyzer.calculate_ncav_ratio(ticker)
        ncav_pct = f"{ncav_result['ncav_ratio_pct']:.2f}"
        ncav_status = ncav_result['status']
        ncav_interpretation = ncav_result['interpretation']

        ticker = ticker.upper()
        #답변 쿼리 작성
        await interaction.followup.send(f"""
안녕하세요! 
{ticker} 티커 정보를 알려드리겠습니다 😊

F-Score와 FS-Score입니다. 
F-Score는 기업의 재무 건전성을 0~9점으로 평가하는 지표입니다.
FS-Score는 F-Score에 추가적으로 기업의 성장성까지 고려한 더 엄격한 점수입니다.
티커 {ticker}의 F-Score 분석 결과: {tickerdict['f_score']}
{tickerdict['status']}
티커 {ticker}의 FS-Score 분석 결과: {fs_dict['fs_score']}
{fs_dict['status']}

📈 카테고리별 점수(f-score):
  • 수익성 (Profitability): {breakdown['profitability'][0]}/{breakdown['profitability'][1]}
  • 재무구조 (Leverage): {breakdown['leverage'][0]}/{breakdown['leverage'][1]}
  • 운영 효율성 (Operating Efficiency): {breakdown['efficiency'][0]}/{breakdown['efficiency'][1]}

NCAV 분석 결과입니다.
기업의 유동자산이 시가총액보다 큰 경우(NCAV 비율 양수), Graham의 NCAV 전략에 따르면 저평가된 주식으로 간주됩니다.
    • NCAV/시가총액 비율: {ncav_pct}%
    • 상태: {ncav_status}
    • 해석: {ncav_interpretation}
""")

        
    except Exception as e:
        await interaction.followup.send(f"티커 {ticker} 분석 중 오류 발생: {e}")

@bot.tree.command(name="macrocheck", description="매크로 경제 지표를 확인합니다")
async def macrocheck(interaction: discord.Interaction):
    
    await interaction.response.send_message("매크로 경제 지표 확인 기능은 현재 준비 중입니다.")



@bot.command()
async def 안녕(ctx):
    await ctx.send("안녕하세요! 라즈베리 파이에서 실행 중이에요 😊")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "라즈베리" in message.content:
        await message.channel.send("라즈베리 파이와 연결되어 있어요!")
    await bot.process_commands(message)


from secret import DISCORD_APP_TOKEN as DISCORD_APP_TOKEN
bot.run(DISCORD_APP_TOKEN)