"""실행: python -m streamlit run app.py"""
from pathlib import Path
from io import BytesIO
from html import escape
import math

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
# 각 축은 서로 반대인 성향입니다. 높고 낮음은 우열이 아닙니다.
AXES = [
    ("관계 에너지", "혼자 충전", "함께 충전"),
    ("행동 방식", "신중하게 살피기", "바로 시도하기"),
    ("감정 표현", "속에서 정리하기", "바로 표현하기"),
    ("새로움 선호", "익숙한 안정", "새로운 경험"),
    ("관계 속 역할", "도움받으며 참여", "돌보고 이끌기"),
    ("자기표현", "조용히 참여", "존재감 드러내기"),
    ("목표를 대하는 방식", "유연하게 전환", "꾸준히 이어가기"),
    ("배우는 방식", "스스로 탐색", "본보기를 따라 연습"),
]

# 문항마다 한 축만 측정합니다. 보기 순서는 고정 순환하여 응답 위치 편향을 줄입니다.
# low -> high 순으로 작성한 뒤 화면에서는 순서를 바꿉니다.
RAW_QUESTIONS = [
    (0, "친구 관계", "처음 만나는 사람이 많은 모임에 갔어요.", [
        "혼자 주변을 구경하며 분위기를 익힌다.", "익숙한 한두 사람과 편하게 대화한다.",
        "옆 사람에게 먼저 가볍게 말을 건넨다.", "여러 사람과 인사하고 함께 어울린다."]),
    (1, "새로운 도전", "처음 해보는 취미를 시작하려고 해요.", [
        "준비 방법과 후기를 충분히 살펴본다.", "기본적인 방법을 익힌 후 시작한다.",
        "간단한 설명을 보고 직접 해본다.", "일단 체험하며 나에게 맞는 방법을 찾는다."]),
    (2, "친구 관계", "친구에게 뜻밖의 선물을 받았어요.", [
        "고마운 마음을 느끼며 나중에 차분히 전한다.", "짧게 고맙다고 말하고 오래 간직한다.",
        "어떤 점이 좋은지 바로 이야기한다.", "반가움과 고마움을 표정과 말로 듬뿍 표현한다."]),
    (3, "휴식과 취향", "여유로운 오후, 어디에서 시간을 보낼까요?", [
        "늘 편안한 익숙한 장소", "가봤던 곳 중 오늘 끌리는 장소",
        "익숙한 동네에 새로 생긴 장소", "한 번도 가보지 않은 동네의 장소"]),
    (4, "친구 관계", "친구들과 함께 여행을 준비해요.", [
        "친구의 안내를 받으며 필요한 일에 참여한다.", "정해진 역할을 맡아 준비한다.",
        "필요한 일이 있는지 살피며 먼저 돕는다.", "전체 일정을 정리하고 친구들을 챙긴다."]),
    (5, "휴식과 취향", "단체 사진을 찍을 때 나는?", [
        "가장자리에서 조용히 함께한다.", "편안한 자리에서 자연스럽게 웃는다.",
        "마음에 드는 포즈를 제안한다.", "가운데에서 개성 있는 포즈를 즐긴다."]),
    (0, "휴식과 취향", "바빴던 한 주가 끝났어요. 에너지를 채우는 방법은?", [
        "혼자만의 시간을 넉넉하게 보낸다.", "혼자 쉬고 가까운 사람과 잠깐 연락한다.",
        "친한 사람을 만나 느긋하게 이야기한다.", "여럿이 만나 즐거운 시간을 보낸다."]),
    (1, "예상 밖 상황", "해보고 싶던 활동에 갑자기 빈자리가 생겼어요.", [
        "조건과 내 상황을 충분히 검토한다.", "중요한 조건을 확인하고 결정한다.",
        "큰 문제가 없으면 우선 신청한다.", "마음이 끌리면 바로 도전한다."]),
    (2, "새로운 도전", "준비한 일이 기대와 다르게 끝났어요.", [
        "먼저 내 마음을 혼자 정리한다.", "생각을 정리한 뒤 가까운 사람에게 전한다.",
        "지금 느끼는 감정을 누군가에게 이야기한다.", "표정과 말로 감정을 자연스럽게 드러낸다."]),
    (3, "예상 밖 상황", "가려던 식당이 문을 닫았어요.", [
        "실패할 걱정이 없는 단골집으로 간다.", "예전에 괜찮았던 식당을 고른다.",
        "저장해 둔 새로운 식당을 찾아본다.", "주변에서 처음 보는 메뉴에 도전한다."]),
    (4, "새로운 도전", "팀 과제에서 모두가 어려움을 느끼고 있어요.", [
        "경험 있는 사람에게 방향을 물어보고 함께한다.", "내가 맡은 부분부터 차근차근 해결한다.",
        "막힌 부분을 함께 살피고 필요한 도움을 준다.", "할 일을 나누고 전체 진행을 이끈다."]),
    (5, "예상 밖 상황", "내가 한 일로 칭찬과 관심을 받게 됐어요.", [
        "조용히 인정받는 정도가 편하다.", "가까운 사람들과 기쁨을 나누면 충분하다.",
        "내가 한 일을 사람들에게 이야기하고 싶다.", "많은 사람 앞에서도 내 성과를 즐겁게 소개한다."]),
    (6, "목표와 성장", "새로운 기술을 배우는데 생각보다 진도가 느려요.", [
        "더 잘 맞는 다른 활동을 찾아본다.", "잠시 쉬면서 목표를 유연하게 바꾼다.",
        "연습량을 조절하며 조금씩 이어간다.", "작은 일일 목표를 세우고 꾸준히 반복한다."]),
    (7, "목표와 성장", "정말 잘하고 싶은 일을 만났을 때, 배우는 방법은?", [
        "여러 방법을 직접 실험하며 내 방식을 만든다.", "혼자 해보다 필요한 자료만 참고한다.",
        "잘하는 사람의 방법을 참고해 나에게 맞춘다.", "믿는 선생님이나 선배의 기본기를 차근차근 따라 한다."]),
    (6, "목표와 성장", "오랫동안 준비하는 목표가 있을 때 내 모습은?", [
        "상황에 따라 더 끌리는 목표로 자연스럽게 바꾼다.", "여러 목표를 번갈아 하며 동기를 유지한다.",
        "정한 목표를 중심에 두되 일정은 유연하게 조절한다.", "정한 목표를 위해 규칙적인 루틴을 오래 유지한다."]),
    (7, "목표와 성장", "처음 만드는 요리에 도전해요. 나는?", [
        "감각대로 재료를 조합하며 새 방법을 실험한다.", "큰 틀만 참고하고 내 방식으로 만들어본다.",
        "추천받은 조리법을 익힌 뒤 조금씩 응용한다.", "숙련자의 레시피를 정확히 반복하며 기본을 익힌다."]),
]
QUESTIONS = []
for i, (axis, category, question, labels) in enumerate(RAW_QUESTIONS):
    order = [(j + i) % 4 for j in range(4)]
    QUESTIONS.append(dict(axis=axis, category=category, text=question,
                          options=[dict(text=labels[j], score=j) for j in order]))

# 공식 분류가 아닌 제작자의 해석에 기반한 초기 기준값입니다.
CHARACTERS = [
    dict(name="치이카와", symbol="🌷", image="chiikawa.png", vector=[20, 20, 30, 25, 25, 20, 70, 65],
         title="작은 용기를 차곡차곡 쌓는 사람",
         strength="세심하게 살피고 자신의 속도로 한 걸음씩 나아가는 힘",
         tip="완벽히 준비되지 않았더라도 작은 시도 하나면 충분해요.", color="#F4CBD6"),
    dict(name="하치와레", symbol="☁️", image="hachiware.png", vector=[85, 60, 85, 60, 65, 45, 65, 50],
         title="함께라면 해낼 수 있다고 믿는 사람",
         strength="마음을 표현하고 함께할 방법을 찾는 따뜻함",
         tip="주변 사람을 챙기는 만큼 내 마음도 살펴봐 주세요.", color="#C5E3F4"),
    dict(name="우사기", symbol="⚡", image="usagi.png", vector=[55, 95, 65, 95, 30, 85, 20, 10],
         title="새로운 재미를 발견하는 자유로운 탐험가",
         strength="낯선 경험에도 먼저 발을 내딛는 호기심과 추진력",
         tip="즐거운 아이디어 하나를 끝까지 해보는 경험도 쌓아보세요.", color="#F6E6A9"),
    dict(name="모몽가", symbol="🎀", image="momonga.png", vector=[75, 65, 90, 55, 15, 95, 25, 25],
         title="원하는 것을 솔직하게 표현하는 사람",
         strength="자신의 마음과 취향을 선명하게 드러내는 솔직함",
         tip="내 마음을 전한 뒤 상대의 마음에도 잠깐 귀를 기울여보세요.", color="#E2D5F4"),
    dict(name="쿠리만쥬", symbol="🍵", image="kurimanju.png", vector=[15, 40, 20, 20, 55, 25, 40, 35],
         title="소소한 즐거움을 깊게 누리는 사람",
         strength="자신의 리듬을 지키며 일상에서 만족을 발견하는 여유",
         tip="좋아하는 것을 가끔 누군가와 나누면 새로운 즐거움이 생겨요.", color="#DFD0BA"),
    dict(name="랏코", symbol="⭐", image="rakko.png", vector=[45, 80, 35, 50, 95, 55, 90, 35],
         title="필요할 때 든든하게 나서는 사람",
         strength="상황을 정리하고 함께하는 사람을 챙기는 책임감",
         tip="모든 일을 혼자 맡기보다 다른 사람에게 기대어도 괜찮아요.", color="#CBE7DD"),
    dict(name="시사", symbol="🌺", image="shisa.png", vector=[55, 30, 55, 25, 55, 30, 95, 95],
         title="존경하는 본보기를 따라 꾸준히 성장하는 사람",
         strength="배움에 열린 태도로 기본기를 익히고 목표를 향해 성실하게 노력하는 힘",
         tip="누군가의 좋은 점을 배우면서도 나만의 방식과 속도를 아껴주세요.", color="#D8E8AE"),
]

def calculate(answers):
    """전 문항의 유효 답변만 허용하고 축마다 가능한 범위로 환산합니다."""
    if len(answers) != len(QUESTIONS) or any(type(a) is not int or a not in range(4) for a in answers):
        raise ValueError(f"{len(QUESTIONS)}개 질문에 모두 답해주세요.")
    totals, maxima = [0] * len(AXES), [0] * len(AXES)
    for q, a in zip(QUESTIONS, answers):
        totals[q["axis"]] += q["options"][a]["score"]
        maxima[q["axis"]] += 3
    vector = [100 * value / maximum for value, maximum in zip(totals, maxima)]
    ranked = sorted(
        [(sum((v - target) ** 2 for v, target in zip(vector, c["vector"])), c)
         for c in CHARACTERS],
        key=lambda row: row[0],
    )
    ties = [c for distance, c in ranked if math.isclose(distance, ranked[0][0], abs_tol=1e-8)]
    return vector, ranked, ties

def evidence(answers, character):
    # 결과 캐릭터와 가장 가까운 답변을 서로 다른 축에서 3개 선택합니다.
    candidates = []
    for q, a in zip(QUESTIONS, answers):
        option = q["options"][a]
        gap = abs(option["score"] / 3 * 100 - character["vector"][q["axis"]])
        candidates.append((gap, q["axis"], option["text"]))
    found, used = [], set()
    for _, axis, label in sorted(candidates, key=lambda item: item[0]):
        if axis not in used:
            found.append((AXES[axis][0], label))
            used.add(axis)
        if len(found) == 3:
            break
    return found

def make_card(nickname, character, vector, ties):
    """폰트를 번들로 포함해 외부 API 없이 한글 PNG를 만듭니다."""
    canvas = Image.new("RGB", (1080, 1900), "#FFF9F3")
    draw = ImageDraw.Draw(canvas)
    font_path = ROOT / "assets" / "NanumGothic.ttf"
    def font(size):
        return ImageFont.truetype(str(font_path), size)
    def centered(text, y, size, color="#473D46"):
        draw.text((540, y), text, font=font(size), fill=color, anchor="mt")
    draw.rounded_rectangle((45, 45, 1035, 1855), radius=40, fill="white", outline=character["color"], width=5)
    centered("나의 치이카와 타입 찾기", 100, 30)
    centered(f"{nickname[:16]} 님과 닮은 캐릭터", 180, 34)
    centered(character["name"], 265, 80)
    centered(character["title"], 370, 30)
    with Image.open(ROOT / "assets" / "characters" / character["image"]) as source:
        # 첨부 원본의 글씨와 비율을 보존하며 카드 안에 배치합니다.
        portrait = ImageOps.contain(source.convert("RGBA"), (700, 630), Image.Resampling.LANCZOS)
        canvas.paste(portrait, ((1080 - portrait.width) // 2, 440 + (630 - portrait.height) // 2), portrait)
    for i, (label, low, high) in enumerate(AXES):
        y = 1120 + i * 75
        draw.text((100, y), low, font=font(23), fill="#645767")
        draw.text((980, y), high, font=font(23), fill="#645767", anchor="ra")
        draw.rounded_rectangle((100, y + 35, 980, y + 48), radius=6, fill="#F1ECEF")
        x = 100 + vector[i] / 100 * 880
        draw.ellipse((x - 11, y + 30, x + 11, y + 52), fill="#CB6685")
    if len(ties) > 1:
        centered("공동 결과: " + " · ".join(c["name"] for c in ties), 1750, 24)
    centered("비공식 팬 테스트 · 재미로 보는 성향 해석", 1800, 23, "#7D717D")
    output = BytesIO()
    canvas.save(output, format="PNG")
    return output.getvalue()

def reset():
    for key in list(st.session_state):
        del st.session_state[key]

def main():
    st.set_page_config(page_title="나의 치이카와 타입 찾기", page_icon="🌷", layout="centered")
    st.markdown("""
    <style>
    .block-container {max-width:760px;padding-top:2.5rem;}
    h1,h2,h3 {letter-spacing:-.04em;}
    div[role="radiogroup"] label {background:#fff;border:1px solid #eadde3;
      border-radius:14px;padding:15px 18px;margin-bottom:8px;min-height:55px;}
    .hero {padding:32px 24px;background:white;border:1px solid #f0dde3;
      border-radius:24px;text-align:center;margin:16px 0 24px;}
    .eyebrow {letter-spacing:.15em;font-size:12px;color:#A56C81;}
    </style>""", unsafe_allow_html=True)
    s = st.session_state
    if "page" in s and len(s.get("answers", [])) != len(QUESTIONS):
        reset()
    if "page" not in s:
        s.page, s.index, s.answers, s.nickname = "home", 0, [None] * len(QUESTIONS), ""

    st.caption("SMALL QUESTIONS, A LITTLE DISCOVERY")
    if s.page == "home":
        st.markdown('<div class="hero"><div class="eyebrow">MY CHIIKAWA TYPE</div>'
                    '<h1>나는 어떤<br>치이카와 캐릭터일까?</h1>'
                    '<p>나의 일상 속 선택에서 발견하는 작고 귀여운 닮은 점</p>'
                    '<p>🌷 ☁️ ⚡ 🎀 🍵 ⭐ 🌺</p></div>', unsafe_allow_html=True)
        st.write(f"{len(QUESTIONS)}개의 질문 · 약 3~4분 · 7가지 캐릭터")
        nickname = st.text_input("닉네임 (선택)", max_chars=16, placeholder="나를 부를 이름")
        if st.button("내 캐릭터 찾기 →", type="primary", use_container_width=True):
            s.nickname = nickname.strip() or "당신"
            s.page = "quiz"
            st.rerun()
        st.caption("답변은 현재 접속 세션에서만 사용하며 별도 데이터베이스에 저장하지 않습니다. "
                   "새로고침하거나 연결이 끊기면 초기화될 수 있어요.")
    elif s.page == "quiz":
        i = s.index
        q = QUESTIONS[i]
        st.caption(f'{q["category"]}  ·  QUESTION {i + 1:02d}')
        st.progress((i + 1) / len(QUESTIONS), text=f"{i + 1} / {len(QUESTIONS)}")
        st.subheader(q["text"])
        st.write("평소의 나와 가장 가까운 답을 골라주세요.")
        answer = st.radio("나의 선택", range(4), index=s.answers[i],
                          format_func=lambda a: q["options"][a]["text"],
                          key=f"question_{i}", label_visibility="collapsed")
        # 위젯 키는 화면을 떠나면 제거될 수 있어 별도 배열에도 보관합니다.
        s.answers[i] = answer
        left, right = st.columns(2)
        if left.button("← 이전", disabled=i == 0, use_container_width=True):
            s.index -= 1
            st.rerun()
        if right.button("결과 보기 ✨" if i == len(QUESTIONS) - 1 else "다음 →", type="primary",
                        disabled=answer is None, use_container_width=True):
            if i == len(QUESTIONS) - 1:
                s.page = "result"
            else:
                s.index += 1
            st.rerun()
        st.button("처음부터 다시", on_click=reset)
    else:
        vector, ranked, ties = calculate(s.answers)
        character = ranked[0][1]
        st.caption("YOUR LITTLE DISCOVERY")
        st.markdown(
            f'<div class="hero"><p>{escape(s.nickname)} 님과 가장 닮은 캐릭터</p>'
            f'<h1>{character["symbol"]} {character["name"]}</h1>'
            f'<h3>{character["title"]}</h3></div>', unsafe_allow_html=True)
        _, image_column, _ = st.columns([1, 3, 1])
        with image_column:
            st.image(str(ROOT / "assets" / "characters" / character["image"]),
                     caption=character["name"], use_container_width=True)
        if len(ties) > 1:
            st.info("공동 결과: " + ", ".join(c["name"] for c in ties) +
                    " — 거리 점수가 같아요. 아래 카드는 표시 순서상 첫 캐릭터예요.")
        st.subheader("이런 선택에서 닮은 점을 찾았어요")
        for axis, label in evidence(s.answers, character):
            st.write(f"• **{axis}** — “{label}”를 선택했어요.")
        st.success("나의 강점 · " + character["strength"])
        st.info("균형을 위한 한마디 · " + character["tip"])
        st.subheader("나의 여덟 가지 성향")
        for (label, low, high), value in zip(AXES, vector):
            st.caption(f"{label}  |  {low} ↔ {high}")
            st.progress(value / 100)
        st.caption("막대는 왼쪽·오른쪽 성향 사이의 위치예요. 능력이나 적합도 점수가 아닙니다.")
        second = ranked[1][1]
        st.write(f'**또 다른 닮은 모습: {second["symbol"]} {second["name"]}**')
        st.write(second["title"])
        with st.expander("두 번째 캐릭터 이미지 보기"):
            st.image(str(ROOT / "assets" / "characters" / second["image"]), width=250)
        try:
            png = make_card(s.nickname, character, vector, ties)
            st.download_button("결과 카드 저장 (PNG)", png, "my_chiikawa_type.png",
                               "image/png", use_container_width=True)
        except OSError:
            st.warning("결과 카드용 이미지나 폰트를 읽을 수 없어요. assets 폴더 전체가 있는지 확인해 주세요.")
        st.caption("결과 이미지를 저장해서 친구에게 보내보세요. 배포한 앱의 주소도 함께 공유할 수 있어요.")
        with st.expander("내 답변 확인"):
            for q, a in zip(QUESTIONS, s.answers):
                st.write("**" + q["text"] + "**")
                st.write(q["options"][a]["text"])
        left, right = st.columns(2)
        if left.button("답변 수정하기", use_container_width=True):
            s.page, s.index = "quiz", 0
            st.rerun()
        right.button("다시 테스트하기", on_click=reset, use_container_width=True)
    st.divider()
    st.caption("비공식 팬 테스트입니다. 캐릭터 성향은 제작자의 해석이며 심리검사나 공식 설정 분류가 아닙니다. "
               "첨부된 캐릭터 소개 이미지를 사용했습니다. 성향 점수는 검사 정확도나 일치 확률이 아닙니다.")

if __name__ == "__main__":
    main()
