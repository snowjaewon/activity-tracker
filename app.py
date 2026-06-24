# -*- coding: utf-8 -*-
"""
공모전 / 대외활동 트래커
- 공모전, 대외활동, 과제, 실험, 기타 활동의 마감일과 진행 상태를 한눈에 관리
- D-day 카드 대시보드 + 상태/카테고리 필터 + 추가/수정/삭제
"""

import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------------------------
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "activities.csv")

CATEGORIES = ["공모전", "대외활동", "과제/레포트", "실험/프로젝트", "시험", "기타"]
STATUSES = ["아이디어", "준비중", "진행중", "제출완료", "결과대기", "종료"]
PRIORITIES = ["높음", "보통", "낮음"]

# 상태별 색 (배지용)
STATUS_COLOR = {
    "아이디어": "#9e9e9e",
    "준비중": "#ff9800",
    "진행중": "#2196f3",
    "제출완료": "#4caf50",
    "결과대기": "#9c27b0",
    "종료": "#607d8b",
}

# 진행이 끝난(=마감 카운트다운에서 빼는) 상태
DONE_STATUSES = {"제출완료", "결과대기", "종료"}

COLUMNS = ["이름", "카테고리", "마감일", "상태", "중요도", "링크", "메모"]

WORKSHEET = "activities"


# ---------------------------------------------------------------------------
# 백엔드 선택: secrets에 구글시트 설정이 있으면 시트, 없으면 로컬 CSV
# ---------------------------------------------------------------------------
def _gsheets_conn():
    """구글시트 connection을 반환. 설정이 없으면 None."""
    try:
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            from streamlit_gsheets import GSheetsConnection
            return st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        pass
    return None


USE_GSHEETS = _gsheets_conn() is not None


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼 보정 + 문자열화 + 완전 빈 행 제거."""
    df = df.copy()
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS].fillna("").astype(str)
    df = df.replace("nan", "")
    # 이름이 빈 행 제거
    df = df[df["이름"].str.strip() != ""]
    return df.reset_index(drop=True)


def load_data() -> pd.DataFrame:
    conn = _gsheets_conn()
    if conn is not None:
        try:
            df = conn.read(worksheet=WORKSHEET, ttl=0)
            return _normalize(df)
        except Exception as e:
            st.warning(f"구글시트 읽기 실패, 빈 목록으로 시작합니다: {e}")
            return pd.DataFrame(columns=COLUMNS)
    # 로컬 CSV
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str).fillna("")
        return _normalize(df)
    return pd.DataFrame(columns=COLUMNS)


def save_data(df: pd.DataFrame) -> None:
    df = _normalize(df)
    conn = _gsheets_conn()
    if conn is not None:
        conn.update(worksheet=WORKSHEET, data=df)
    else:
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def parse_deadline(value: str):
    """문자열 마감일을 date로. 실패하면 None."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def dday_text(deadline: date, status: str):
    """(표시문자열, 남은일수 or None) 반환."""
    if status in DONE_STATUSES:
        return status, None
    if deadline is None:
        return "마감일 미정", None
    diff = (deadline - date.today()).days
    if diff > 0:
        return f"D-{diff}", diff
    if diff == 0:
        return "D-DAY", 0
    return f"D+{abs(diff)} (지남)", diff


def urgency_color(diff):
    """남은 일수 기준 카드 강조색."""
    if diff is None:
        return "#607d8b"   # 완료/미정 - 회색
    if diff < 0:
        return "#b71c1c"   # 마감 지남 - 진한 빨강
    if diff <= 3:
        return "#e53935"   # 임박 - 빨강
    if diff <= 7:
        return "#fb8c00"   # 주의 - 주황
    if diff <= 14:
        return "#fdd835"   # 여유 약간 - 노랑
    return "#43a047"       # 여유 - 초록


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="활동 트래커", page_icon="🗂️", layout="wide")
st.title("🗂️ 공모전 / 대외활동 트래커")

df = load_data()

# ----- 사이드바: 활동 추가 / 수정 -----
with st.sidebar:
    st.header("➕ 활동 추가 / 수정")

    # 수정 대상 선택
    edit_options = ["(새 활동 추가)"] + df["이름"].tolist()
    edit_target = st.selectbox("수정할 활동", edit_options)

    is_edit = edit_target != "(새 활동 추가)"
    row = df[df["이름"] == edit_target].iloc[0] if is_edit else None

    with st.form("activity_form", clear_on_submit=not is_edit):
        name = st.text_input("이름", value=row["이름"] if is_edit else "")
        category = st.selectbox(
            "카테고리", CATEGORIES,
            index=CATEGORIES.index(row["카테고리"]) if is_edit and row["카테고리"] in CATEGORIES else 0,
        )

        default_deadline = parse_deadline(row["마감일"]) if is_edit else None
        no_deadline = st.checkbox("마감일 미정", value=(is_edit and default_deadline is None))
        deadline_input = st.date_input(
            "마감일", value=default_deadline or date.today(), disabled=no_deadline
        )

        status = st.selectbox(
            "상태", STATUSES,
            index=STATUSES.index(row["상태"]) if is_edit and row["상태"] in STATUSES else 0,
        )
        priority = st.selectbox(
            "중요도", PRIORITIES,
            index=PRIORITIES.index(row["중요도"]) if is_edit and row["중요도"] in PRIORITIES else 1,
        )
        link = st.text_input("링크", value=row["링크"] if is_edit else "")
        memo = st.text_area("메모", value=row["메모"] if is_edit else "")

        col_save, col_del = st.columns(2)
        submitted = col_save.form_submit_button("💾 저장", use_container_width=True)
        deleted = col_del.form_submit_button(
            "🗑️ 삭제", use_container_width=True, disabled=not is_edit
        )

    if submitted:
        if not name.strip():
            st.error("이름을 입력해 주세요.")
        else:
            new_record = {
                "이름": name.strip(),
                "카테고리": category,
                "마감일": "" if no_deadline else deadline_input.strftime("%Y-%m-%d"),
                "상태": status,
                "중요도": priority,
                "링크": link.strip(),
                "메모": memo.strip(),
            }
            # 같은 이름이면 수정, 아니면 추가
            if name.strip() in df["이름"].values:
                df.loc[df["이름"] == name.strip(), COLUMNS] = list(new_record.values())
            else:
                df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            save_data(df)
            st.success(f"저장됨: {name.strip()}")
            st.rerun()

    if deleted and is_edit:
        df = df[df["이름"] != edit_target]
        save_data(df)
        st.success(f"삭제됨: {edit_target}")
        st.rerun()


# ----- 상단 요약 메트릭 -----
df_view = df.copy()
df_view["_deadline"] = df_view["마감일"].apply(parse_deadline)
df_view["_dday_text"], df_view["_diff"] = zip(
    *df_view.apply(lambda r: dday_text(r["_deadline"], r["상태"]), axis=1)
) if len(df_view) else ([], [])

active = df_view[~df_view["상태"].isin(DONE_STATUSES)]
imminent = active[active["_diff"].apply(lambda d: d is not None and 0 <= d <= 7)]
overdue = active[active["_diff"].apply(lambda d: d is not None and d < 0)]

m1, m2, m3, m4 = st.columns(4)
m1.metric("전체 활동", len(df_view))
m2.metric("진행 중", len(active))
m3.metric("임박 (D-7)", len(imminent))
m4.metric("마감 지남", len(overdue), delta_color="inverse")

st.divider()

# ----- 필터 -----
fc1, fc2, fc3 = st.columns([2, 2, 1])
cat_filter = fc1.multiselect("카테고리 필터", CATEGORIES, default=[])
status_filter = fc2.multiselect("상태 필터", STATUSES, default=[])
hide_done = fc3.checkbox("완료 숨기기", value=True)

filtered = df_view.copy()
if cat_filter:
    filtered = filtered[filtered["카테고리"].isin(cat_filter)]
if status_filter:
    filtered = filtered[filtered["상태"].isin(status_filter)]
if hide_done:
    filtered = filtered[~filtered["상태"].isin(DONE_STATUSES)]


# ----- 정렬: 마감 임박 우선, 미정/완료는 뒤로 -----
def sort_key(diff):
    return diff if diff is not None else 10**6


filtered = filtered.assign(_sort=filtered["_diff"].apply(sort_key)).sort_values("_sort")

# ----- 카드 대시보드 -----
if filtered.empty:
    st.info("표시할 활동이 없어요. 왼쪽 사이드바에서 활동을 추가해 보세요 👈")
else:
    cols = st.columns(3)
    for i, (_, r) in enumerate(filtered.iterrows()):
        color = urgency_color(r["_diff"])
        badge = STATUS_COLOR.get(r["상태"], "#607d8b")
        link_html = (
            f'<a href="{r["링크"]}" target="_blank" style="color:#90caf9;font-size:0.8rem;">🔗 링크</a>'
            if r["링크"] else ""
        )
        memo_html = (
            f'<div style="font-size:0.8rem;color:#cfcfcf;margin-top:6px;">{r["메모"]}</div>'
            if r["메모"] else ""
        )
        star = {"높음": "⭐", "보통": "", "낮음": ""}.get(r["중요도"], "")
        with cols[i % 3]:
            st.markdown(
                f"""
                <div style="border-left:6px solid {color};background:#1e1e1e;
                            border-radius:8px;padding:12px 14px;margin-bottom:12px;">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:1.05rem;font-weight:700;color:#fff;">{star}{r["이름"]}</span>
                    <span style="font-size:1.1rem;font-weight:800;color:{color};">{r["_dday_text"]}</span>
                  </div>
                  <div style="margin-top:6px;">
                    <span style="font-size:0.75rem;color:#bbb;">{r["카테고리"]}</span>
                    <span style="background:{badge};color:#fff;font-size:0.72rem;
                                 padding:2px 8px;border-radius:10px;margin-left:6px;">{r["상태"]}</span>
                  </div>
                  <div style="font-size:0.78rem;color:#999;margin-top:4px;">
                    {('마감 ' + r["마감일"]) if r["마감일"] else '마감일 미정'}
                  </div>
                  {memo_html}
                  <div style="margin-top:6px;">{link_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ----- 전체 표 (접기) -----
with st.expander("📋 전체 목록 (표)"):
    show = df_view[COLUMNS].copy()
    show.insert(0, "D-day", df_view["_dday_text"].values)
    st.dataframe(show, use_container_width=True, hide_index=True)
