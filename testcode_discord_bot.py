import discord
from discord.ext import commands
from analysis import f_score_analyzer, fs_score_analyzer

intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 권한 활성화

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"봇 로그인 완료: {bot.user}")

    # 슬래시 명령어를 서버에 동기화
    await bot.tree.sync()

@bot.tree.command(name="tickercheck", description="봇이 인사해줍니다")
async def 안녕(interaction: discord.Interaction,ticker: str):
    try:
        tickerdict = f_score_analyzer.calculate_f_score(ticker)
        fs_dict = fs_score_analyzer.calculate_fs_score(ticker, f_score_result=tickerdict)
        breakdown = tickerdict['breakdown']

        ticker = ticker.upper()
        #답변 쿼리 작성
        await interaction.response.send_message(f"""
안녕하세요! 
{ticker} 티커 정보를 알려드리겠습니다 😊

두 점수는 F-Score와 FS-Score입니다. F-Score는 기업의 재무 건전성을 0~9점으로 평가하는 지표입니다.
FS-Score는 F-Score에 추가적으로 기업의 성장성까지 고려한 더 엄격한 점수입니다.
티커 {ticker}의 F-Score 분석 결과: {tickerdict['f_score']}
티커 {ticker}의 FS-Score 분석 결과: {fs_dict['fs_score']}

📈 카테고리별 점수(f-score):
  • 수익성 (Profitability): {breakdown['profitability'][0]}/{breakdown['profitability'][1]}
  • 재무구조 (Leverage): {breakdown['leverage'][0]}/{breakdown['leverage'][1]}
  • 운영 효율성 (Operating Efficiency): {breakdown['efficiency'][0]}/{breakdown['efficiency'][1]}
""")

        
    except Exception as e:
        await interaction.response.send_message(f"티커 {ticker} 분석 중 오류 발생: {e}")



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