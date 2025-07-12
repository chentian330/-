import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import base64
import os
import glob
import warnings
from html import escape
import time
from io import BytesIO

# 忽略警告
warnings.filterwarnings('ignore')


# 智能金额格式化函数
def format_amount(value, unit="万元"):
    if pd.isna(value) or value is None:
        return "-"
    if value == int(value):
        return f"{int(value):,}{unit}"
    formatted = f"{value:,.2f}"
    if '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
    return f"{formatted}{unit}"


# 初始化会话状态
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'score_df' not in st.session_state:
    st.session_state.score_df = None
if 'sales_df' not in st.session_state:
    st.session_state.sales_df = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None


# 自定义CSS样式 - 米白色背景苹果风格
def load_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Text:wght@400;500&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=SF+Mono&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        :root {{
            --space-xxl: 4rem;
            --space-xl: 2.5rem;
            --space-lg: 1.8rem;
            --space-md: 1.2rem;
            --space-sm: 0.8rem;
            --space-xs: 0.4rem;

            --color-primary: #0A84FF;
            --color-secondary: #BF5AF2;
            --color-bg: #F5F5F7;  /* 米白色背景 */
            --color-surface: #FFFFFF;
            --color-card: rgba(255, 255, 255, 0.92);
            --color-text-primary: #1D1D1F;
            --color-text-secondary: #86868B;
            --color-text-tertiary: #8E8E93;
            --color-accent-red: #FF453A;
            --color-accent-blue: #0A84FF;
            --color-accent-purple: #BF5AF2;
            --color-accent-green: #30D158;
            --color-accent-yellow: #FFD60A;

            --glass-bg: rgba(255, 255, 255, 0.85);
            --glass-border: rgba(0, 0, 0, 0.08);
            --glass-highlight: rgba(0, 0, 0, 0.05);
        }}

        body, .stApp {{
            background: var(--color-bg);
            color: var(--color-text-primary);
            font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
            background-attachment: fixed;
            background-image: radial-gradient(circle at 15% 50%, rgba(10, 132, 255, 0.05), transparent 40%),
                              radial-gradient(circle at 85% 30%, rgba(191, 90, 242, 0.05), transparent 40%);
        }}

        .stDeployButton {{ display: none; }}
        header[data-testid="stHeader"] {{ display: none; }}
        .stMainBlockContainer {{ padding-top: var(--space-xl); }}

        /* 导航栏样式 - 磨砂玻璃效果 */
        .stNavContainer {{
            background: var(--glass-bg) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border-radius: 18px !important;
            border: 0.5px solid var(--glass-border) !important;
            box-shadow: 
                0 12px 30px rgba(0, 0, 0, 0.05),
                inset 0 0 0 1px rgba(255, 255, 255, 0.5) !important;
            padding: 12px 20px !important;
            margin: 20px auto 15px !important;
            max-width: 80% !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.1) !important;
            animation: fadeInDown 0.6s ease forwards;
        }}

        .stNavContainer:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 
                0 15px 40px rgba(0, 0, 0, 0.08),
                inset 0 0 0 1px rgba(255, 255, 255, 0.7) !important;
        }}

        /* 导航按钮样式 */
        .stNav > div > button {{
            background: transparent !important;
            border: none !important;
            color: var(--color-text-primary) !important;
            font-family: 'SF Pro Text', sans-serif !important;
            font-weight: 500 !important;
            font-size: 1.1rem !important;
            padding: 12px 25px !important;
            margin: 0 8px !important;
            border-radius: 50px !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: none !important;
        }}

        .stNav > div > button:hover {{
            background: rgba(255, 255, 255, 0.3) !important;
            transform: translateY(-2px) !important;
        }}

        .stNav > div > button:focus {{
            box-shadow: 0 0 0 2px var(--color-primary) !important;
        }}

        /* 导航按钮图标样式 */
        .nav-icon {{
            font-size: 1.4rem !important;
            margin-right: 8px !important;
            transition: transform 0.3s ease !important;
        }}

        .stNav > div > button:hover .nav-icon {{
            transform: scale(1.15) !important;
        }}

        /* 移除原来的分割线 */
        .stMainBlockContainer > hr {{
            display: none !important;
        }}

        /* 玻璃卡片 */
        .glass-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-radius: 18px;
            border: 0.5px solid var(--glass-border);
            box-shadow: 
                0 12px 30px rgba(0, 0, 0, 0.05),
                inset 0 0 0 1px rgba(255, 255, 255, 0.5);
            padding: var(--space-lg);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.1);
            position: relative;
            overflow: hidden;
        }}

        .glass-card:hover {{
            transform: translateY(-6px);
            box-shadow: 
                0 20px 40px rgba(0, 0, 0, 0.08),
                inset 0 0 0 1px rgba(255, 255, 255, 0.7);
        }}

        .glass-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--glass-highlight), transparent);
        }}

        /* 主标题 */
        .main-title {{
            text-align: center;
            font-family: 'SF Pro Display', sans-serif;
            font-weight: 700;
            font-size: 3.5rem;
            margin-bottom: var(--space-sm);
            background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
            line-height: 1.1;
        }}

        .main-subtitle {{
            text-align: center;
            font-family: 'SF Pro Text', sans-serif;
            font-size: 1.4rem;
            font-weight: 400;
            color: var(--color-text-secondary);
            max-width: 700px;
            margin: 0 auto var(--space-xl);
            line-height: 1.6;
        }}

        /* 导航按钮 */
        .nav-container {{
            display: flex;
            justify-content: center;
            gap: var(--space-sm);
            margin-bottom: var(--space-xl);
        }}

        .nav-btn {{
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 50px;
            padding: var(--space-sm) var(--space-md);
            color: var(--color-text-primary);
            font-family: 'SF Pro Text', sans-serif;
            font-size: 1.1rem;
            font-weight: 500;
            border: 0.5px solid rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        }}

        .nav-btn:hover {{
            background: rgba(255, 255, 255, 1);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.05);
            border-color: rgba(0, 0, 0, 0.1);
        }}

        /* 上传区域 */
        .upload-area {{
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(10px);
            border: 1.5px dashed rgba(0, 0, 0, 0.1);
            border-radius: 18px;
            padding: var(--space-xl);
            text-align: center;
            transition: all 0.3s ease;
            color: var(--color-text-secondary);
        }}

        .upload-area:hover {{
            border-color: var(--color-primary);
            background: rgba(255, 255, 255, 0.92);
        }}

        /* 菜单按钮 */
        .menu-btn {{
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            padding: var(--space-lg);
            color: var(--color-text-primary);
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: var(--space-md);
            font-family: 'SF Pro Text', sans-serif;
            font-size: 1.2rem;
            font-weight: 500;
            border: 0.5px solid rgba(0, 0, 0, 0.05);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.03);
        }}

        .menu-btn:hover:not(.disabled) {{
            background: rgba(255, 255, 255, 1);
            transform: translateY(-5px);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.05);
            border-color: rgba(0, 0, 0, 0.1);
        }}

        .menu-btn.disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        /* 标题样式 */
        .section-title {{
            font-family: 'SF Pro Display', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            margin: var(--space-xl) 0 var(--space-md);
            color: var(--color-text-primary);
            position: relative;
            padding-left: var(--space-md);
            letter-spacing: -0.5px;
        }}

        .section-title:before {{
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            height: 70%;
            width: 4px;
            background: linear-gradient(to bottom, var(--color-primary), var(--color-secondary));
            border-radius: 4px;
        }}

        .red-title:before {{
            background: linear-gradient(to bottom, var(--color-accent-red), #FF375F);
        }}

        .black-title:before {{
            background: linear-gradient(to bottom, #8E8E93, #636366);
        }}

        /* 按钮样式 */
        .stButton>button {{
            background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
            color: white;
            border: none;
            border-radius: 12px;
            padding: {st.session_state.get('button_padding', '12px 25px')};
            font-family: 'SF Pro Text', sans-serif;
            font-weight: 500;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(10, 132, 255, 0.2);
        }}

        .stButton>button:hover {{
            transform: scale(1.03);
            box-shadow: 0 8px 20px rgba(191, 90, 242, 0.25);
        }}

        /* 页脚 */
        .footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.9);
            color: var(--color-text-secondary);
            padding: var(--space-sm) 0;
            text-align: center;
            font-size: 0.9rem;
            z-index: 100;
            backdrop-filter: blur(10px);
            border-top: 0.5px solid rgba(0, 0, 0, 0.05);
            font-family: 'SF Pro Text', sans-serif;
        }}

        /* 员工卡片 */
        .employee-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border-radius: 18px;
            padding: var(--space-lg);
            margin-bottom: var(--space-lg);
            border: 0.5px solid var(--glass-border);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.05);
        }}

        .employee-name {{
            font-family: 'SF Pro Display', sans-serif;
            font-weight: 700;
            font-size: 1.5rem;
            margin-bottom: var(--space-xs);
            color: var(--color-text-primary);
        }}

        .employee-group {{
            font-family: 'SF Pro Text', sans-serif;
            font-size: 1rem;
            color: var(--color-text-secondary);
            margin-bottom: var(--space-md);
        }}

        /* 徽章系统 */
        .badge-container {{
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            padding: var(--space-md);
            border-radius: 16px;
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border: 0.5px solid var(--glass-border);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
        }}

        .badge-container:hover {{
            transform: translateY(-6px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
        }}

        .badge-icon {{
            font-size: 3.5rem;
            margin-bottom: var(--space-sm);
            transition: all 0.3s;
        }}

        .badge-title {{
            font-family: 'SF Pro Display', sans-serif;
            font-weight: 700;
            font-size: 1.3rem;
            margin-bottom: var(--space-xs);
            color: var(--color-text-primary);
        }}

        .badge-recipient {{
            font-family: 'SF Pro Text', sans-serif;
            font-size: 1rem;
            color: var(--color-text-secondary);
        }}

        /* 分割线 */
        .divider {{
            height: 0.5px;
            width: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.08), transparent);
            margin: var(--space-md) 0;
        }}

        /* 表格样式 */
        .stDataFrame {{
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            border: 0.5px solid rgba(0, 0, 0, 0.05);
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
        }}

        /* 图表容器 */
        .plot-container {{
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            border: 0.5px solid rgba(0, 0, 0, 0.05);
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
        }}

        /* 上传按钮 */
        .stFileUploader > div > div {{
            background: var(--glass-bg) !important;
            border-radius: 18px !important;
            border: 0.5px solid rgba(0, 0, 0, 0.05) !important;
            padding: var(--space-md) !important;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.03) !important;
            backdrop-filter: blur(10px) !important;
        }}

        /* 进度条 */
        .stProgress > div > div > div {{
            background: linear-gradient(90deg, var(--color-primary), var(--color-secondary)) !important;
        }}

        /* 选择框 */
        .stSelectbox:not(div) {{
            background: var(--glass-bg) !important;
            border-radius: 12px !important;
            border: 0.5px solid rgba(0, 0, 0, 0.05) !important;
        }}

        /* 文本输入 */
        .stTextInput input {{
            background: var(--glass-bg) !important;
            border-radius: 12px !important;
            border: 0.5px solid rgba(0, 0, 0, 0.05) !important;
            color: var(--color-text-primary) !important;
        }}

        /* 动画效果 */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .fade-in {{
            animation: fadeIn 0.6s ease forwards;
        }}
    </style>

    <script>
        // 动态光照效果
        document.addEventListener('DOMContentLoaded', function() {{
            const cards = document.querySelectorAll('.glass-card');

            cards.forEach(card => {{
                card.addEventListener('mousemove', function(e) {{
                    const rect = this.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;

                    this.style.setProperty('--x', x + 'px');
                    this.style.setProperty('--y', y + 'px');
                }});
            }});
        }});
    </script>
    """, unsafe_allow_html=True)


# 自动检测Excel文件
def auto_detect_excel_file():
    try:
        pattern = "员工销售回款统计_*.xlsx"
        files = glob.glob(pattern)
        if files:
            latest_file = max(files, key=os.path.getctime)
            return latest_file
        return None
    except Exception as e:
        st.error(f"文件检测出错: {e}")
        return None


# 加载Excel数据
def load_excel_data(file_path):
    try:
        score_df = pd.read_excel(file_path, sheet_name='员工积分数据', engine='openpyxl')
        if '队名' not in score_df.columns:
            return None, None, "数据文件中缺少'队名'列"

        sales_df = None
        try:
            sales_df = pd.read_excel(file_path, sheet_name='销售回款数据统计', engine='openpyxl')
        except:
            try:
                sales_df = pd.read_excel(file_path, sheet_name='销售回款数据', engine='openpyxl')
            except:
                pass

        return score_df, sales_df, None
    except Exception as e:
        return None, None, f"读取文件时出错: {str(e)}"


# 导航栏
def show_navigation():
    # 创建导航栏
    nav_items = {
        "nav_home": {"label": "首页", "icon": "🏠"},
        "nav_back": {"label": "返回", "icon": "⬅️"},
        "nav_undo": {"label": "撤销", "icon": "↩️"}
    }

    # 使用columns创建居中布局
    cols = st.columns([1, 2, 2, 2, 1])

    with cols[1]:
        if st.button(
                f"{nav_items['nav_home']['icon']} {nav_items['nav_home']['label']}",
                help="返回主页",
                key="nav_home",
                use_container_width=True
        ):
            st.session_state.current_page = 'home'
            st.rerun()

    with cols[2]:
        if st.button(
                f"{nav_items['nav_back']['icon']} {nav_items['nav_back']['label']}",
                help="返回上级菜单",
                key="nav_back",
                use_container_width=True
        ):
            if st.session_state.current_page != 'home':
                st.session_state.current_page = 'home'
                st.rerun()

    with cols[3]:
        if st.button(
                f"{nav_items['nav_undo']['icon']} {nav_items['nav_undo']['label']}",
                help="撤销上一步",
                key="nav_undo",
                use_container_width=True
        ):
            st.rerun()

    # 添加更精致的苹果风格分割线
    st.markdown("""
    <div style="
        height: 0.5px;
        width: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.08), transparent);
        margin: 20px 0 25px;
    "></div>
    """, unsafe_allow_html=True)


# 主页
def show_home_page():
    st.markdown("""
    <div class="main-title">销售积分红黑榜系统</div>
    <div class="main-subtitle">销售团队绩效评估与数据分析平台 - 提供实时洞察与绩效分析</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("""
        <div class="glass-card upload-area fade-in" style="animation-delay: 0.1s;">
            <h3 style="margin-bottom: 1.5rem; font-size: 1.8rem; color: #0A84FF;">📁 文件上传区域</h3>
            <p style="color: #86868B; font-size: 1.1rem;">请上传由销售积分系统生成的Excel文件</p>
        </div>
        """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "选择Excel文件",
        type=["xlsx"],
        help="请上传包含'员工积分数据'和'销售回款数据统计'工作表的Excel文件",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        try:
            # 将文件内容保存到session state中
            st.session_state.uploaded_file = uploaded_file.getvalue()

            # 使用BytesIO加载文件
            score_df, sales_df, error = load_excel_data(BytesIO(st.session_state.uploaded_file))

            if error:
                st.error(f"文件加载失败: {error}")
            else:
                st.session_state.score_df = score_df
                st.session_state.sales_df = sales_df
                st.session_state.data_loaded = True
                st.session_state.file_name = uploaded_file.name
                st.success(f"文件加载成功: {uploaded_file.name}")
        except Exception as e:
            st.error(f"文件处理出错: {str(e)}")


    with col2:
        st.markdown("""
        <div class="glass-card fade-in" style="animation-delay: 0.2s;">
            <h3 style="text-align: center; color: #BF5AF2; margin-bottom: 2.5rem; font-size: 1.8rem;">📊 功能菜单</h3>
        </div>
        """, unsafe_allow_html=True)

        disabled = not st.session_state.data_loaded

        if st.button("🏆 查看红黑榜", key="btn_leaderboard", disabled=disabled, use_container_width=True):
            if st.session_state.data_loaded:
                st.session_state.current_page = 'leaderboard'
                st.rerun()
            else:
                st.error("请添加文件后重试")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📊 查看员工积分明细", key="btn_scores", disabled=disabled, use_container_width=True):
            if st.session_state.data_loaded:
                st.session_state.current_page = 'scores'
                st.rerun()
            else:
                st.error("请添加文件后重试")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("💰 查看销售回款额明细", key="btn_sales", disabled=disabled, use_container_width=True):
            if st.session_state.data_loaded:
                st.session_state.current_page = 'sales'
                st.rerun()
            else:
                st.error("请添加文件后重试")


# 红黑榜页面
def show_leaderboard_page():
    if not st.session_state.data_loaded:
        st.error("请先上传数据文件")
        return

    red_df, black_df, group_data = get_leaderboard_data(st.session_state.score_df)
    display_leaderboard(red_df, black_df, st.session_state.sales_df)


# 积分明细页面
def show_scores_page():
    if not st.session_state.data_loaded:
        st.error("请先上传数据文件")
        return

    red_df, black_df, group_data = get_leaderboard_data(st.session_state.score_df)
    display_group_ranking(group_data, st.session_state.score_df)
    display_employee_details(st.session_state.score_df, None)


# 销售明细页面
def show_sales_page():
    if not st.session_state.data_loaded:
        st.error("请先上传数据文件")
        return

    if st.session_state.sales_df is not None:
        display_sales_overview(st.session_state.sales_df)
        display_weekly_analysis(st.session_state.sales_df)

    display_achievement_badges(st.session_state.score_df, st.session_state.sales_df)
    display_sales_employee_details(st.session_state.score_df, st.session_state.sales_df)


# 获取小组数据
def get_group_data(score_df):
    if score_df is None or score_df.empty:
        return None

    if '队名' not in score_df.columns:
        st.error("数据中缺少'队名'列")
        return None

    valid_data = score_df.dropna(subset=['队名'])
    if valid_data.empty:
        st.error("所有记录的队名都为空")
        return None

    group_data = valid_data[['队名', '加权小组总分']].drop_duplicates().sort_values(by='加权小组总分', ascending=False)
    group_data['排名'] = range(1, len(group_data) + 1)

    return group_data


# 获取红黑榜数据
def get_leaderboard_data(score_df):
    if score_df is None or score_df.empty:
        return None, None, None
    group_data = get_group_data(score_df)
    if group_data is None:
        return None, None, None
    red_groups = group_data.head(2)['队名'].tolist()
    red_df = score_df[score_df['队名'].isin(red_groups)].sort_values(by='个人总积分', ascending=False)
    black_groups = group_data.tail(2)['队名'].tolist()
    black_df = score_df[score_df['队名'].isin(black_groups)].sort_values(by='个人总积分', ascending=True)
    return red_df, black_df, group_data


# 创建员工头像
def create_avatar(name, color="default"):
    name_str = str(name) if name else ""
    initials = ''.join([n[0] for n in name_str.split() if n])[:2]
    if not initials:
        initials = name_str[:2] if len(name_str) >= 2 else name_str
    if not initials:
        initials = "US"

    color_class = "avatar"
    if color == "red":
        color_class = "red-avatar"
    elif color == "black":
        color_class = "black-avatar"

    st.markdown(f"""
    <style>
        .{color_class} {{
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: {'linear-gradient(135deg, #FF453A, #FF375F)' if color == "red" else
    'linear-gradient(135deg, #8E8E93, #636366)' if color == "black" else
    'linear-gradient(135deg, #0A84FF, #5E5CE6)'};
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 1.8rem;
            margin-right: 20px;
            flex-shrink: 0;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }}
    </style>
    """, unsafe_allow_html=True)

    return f'<div class="{color_class}">{escape(initials)}</div>'


# 显示红黑榜
def display_leaderboard(red_df, black_df, sales_df=None):
    if red_df is not None and not red_df.empty and '统计月份' in red_df.columns:
        month_info = red_df['统计月份'].iloc[0]
        st.markdown(f"""
        <div class="header fade-in">
            <h1 style="margin:0; text-align:center; font-size:3rem; font-family: 'SF Pro Display'; color: #1D1D1F;">销售积分红黑榜</h1>
            <p style="margin:10px 0 0; text-align:center; color:#86868B; font-size:1.3rem;">{month_info} 销售团队绩效评估系统</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="header fade-in">
            <h1 style="margin:0; text-align:center; font-size:3rem; font-family: 'SF Pro Display'; color: #1D1D1F;">销售积分红黑榜</h1>
            <p style="margin:10px 0 0; text-align:center; color:#86868B; font-size:1.3rem;">月度销售团队绩效评估系统</p>
        </div>
        """, unsafe_allow_html=True)

    if red_df is None or black_df is None:
        st.warning("请上传数据文件以查看红黑榜")
        return

    st.markdown("""
    <style>
        .leaderboard-container {
            display: flex;
            gap: 25px;
            margin-top: 40px;
        }
        .leaderboard-column {
            flex: 1;
        }
        .leaderboard-header {
            text-align: center;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }
        .leaderboard-item {
            display: flex;
            align-items: center;
            padding: 20px;
            margin-bottom: 20px;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            border: 0.5px solid rgba(0, 0, 0, 0.05);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        .leaderboard-item:hover {
            transform: translateY(-6px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
        }
        .rank {
            font-family: 'SF Pro Display';
            font-size: 2.2rem;
            font-weight: 700;
            width: 60px;
            text-align: center;
            color: #0A84FF;
        }
        .red-rank { color: #FF453A; }
        .black-rank { color: #8E8E93; }
        .medal {
            font-size: 2rem;
            margin-left: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<h3 class="section-title red-title fade-in">🏆 红榜 - 卓越团队</h3>', unsafe_allow_html=True)
        if not red_df.empty:
            for i, (_, row) in enumerate(red_df.iterrows()):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else ""
                st.markdown(
                    f'<div class="leaderboard-item fade-in" style="animation-delay: {0.1 + i * 0.05}s;">'
                    f'<div class="rank red-rank">#{i + 1}</div>'
                    f'{create_avatar(row["员工姓名"], "red")}'
                    f'<div style="flex-grow:1;">'
                    f'<div class="employee-name">{escape(str(row["员工姓名"]))}</div>'
                    f'<div class="employee-group">队名: <strong>{row["队名"]}</strong> · 积分: <strong>{row["个人总积分"]}</strong></div>'
                    f'</div>'
                    f'<div class="medal">{medal}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("暂无红榜数据", icon="ℹ️")
    with col2:
        st.markdown('<h3 class="section-title black-title fade-in">⚫ 黑榜 - 待提升团队</h3>', unsafe_allow_html=True)
        if not black_df.empty:
            for i, (_, row) in enumerate(black_df.iterrows()):
                st.markdown(
                    f'<div class="leaderboard-item fade-in" style="animation-delay: {0.1 + i * 0.05}s;">'
                    f'<div class="rank black-rank">#{i + 1}</div>'
                    f'{create_avatar(row["员工姓名"], "black")}'
                    f'<div style="flex-grow:1;">'
                    f'<div class="employee-name">{escape(str(row["员工姓名"]))}</div>'
                    f'<div class="employee-group">队名: <strong>{row["队名"]}</strong> · 积分: <strong>{row["个人总积分"]}</strong></div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("暂无黑榜数据", icon="ℹ️")


# 显示小组排名
def display_group_ranking(group_data, df):
    if group_data is None or df is None:
        return

    st.markdown('<h3 class="section-title fade-in">🏅 小组加权积分排名</h3>', unsafe_allow_html=True)

    st.markdown("""
    <style>
        .group-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            padding: 25px;
            margin-bottom: 25px;
            border: 0.5px solid rgba(0, 0, 0, 0.05);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.05);
        }
        .group-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 0.5px solid rgba(0, 0, 0, 0.05);
        }
        .group-badge {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0A84FF, #5E5CE6);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 1.5rem;
            margin-right: 20px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }
        .red-badge { background: linear-gradient(135deg, #FF453A, #FF375F); }
        .black-badge { background: linear-gradient(135deg, #8E8E93, #636366); }
        .gold { color: #FFD60A; font-weight: 700; }
        .silver { color: #8E8E93; font-weight: 700; }
        .bronze { color: #FF9F0A; font-weight: 700; }
        .member-card {
            display: flex;
            align-items: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.85);
            border-radius: 14px;
            margin-bottom: 15px;
            border: 0.5px solid rgba(0, 0, 0, 0.03);
            transition: all 0.3s ease;
        }
        .member-card:hover {
            transform: translateY(-3px);
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
        }
        .member-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0A84FF, #5E5CE6);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-right: 15px;
            flex-shrink: 0;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=group_data['加权小组总分'],
        y=group_data['队名'],
        orientation='h',
        marker=dict(
            color=['#FFD60A' if rank == 1 else '#8E8E93' if rank == 2 else '#FF9F0A' if rank == 3 else '#0A84FF' for
                   rank in group_data['排名']],
            line=dict(color='rgba(0,0,0,0.1)', width=1)
        ),
        text=group_data['加权小组总分'],
        textposition='auto',
        hoverinfo='text',
        hovertext=[f"{row['队名']}<br>加权总分: {row['加权小组总分']}<br>排名: {row['排名']}" for _, row in
                   group_data.iterrows()]
    ))

    fig.update_layout(
        height=500,
        margin=dict(l=150, r=50, t=80, b=50),
        title='小组加权总分排行榜',
        title_font=dict(size=26, color='#1D1D1F'),
        xaxis_title='加权小组总分',
        yaxis_title='队名',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1D1D1F'),
        yaxis=dict(
            tickfont=dict(size=14),
            autorange="reversed"
        ),
        xaxis=dict(
            gridcolor='rgba(0,0,0,0.05)'
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="SF Pro Text"
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<h3 class="section-title fade-in">👥 小组详情</h3>', unsafe_allow_html=True)
    cols = st.columns(3)
    group_cols = [group_data.iloc[i:i + 2] for i in range(0, len(group_data), 2)]
    for idx, groups in enumerate(group_cols):
        with cols[idx % 3]:
            for _, group_row in groups.iterrows():
                team_name = group_row['队名']
                weighted_team_score = group_row['加权小组总分']
                team_rank = group_row['排名']
                team_members = df[df['队名'] == team_name].sort_values(by='个人总积分', ascending=False)

                badge_class = "group-badge"
                if team_rank <= 2:
                    badge_class = "group-badge red-badge"
                elif team_rank >= len(group_data) - 1:
                    badge_class = "group-badge black-badge"

                rank_class = ""
                if team_rank == 1:
                    rank_class = "gold"
                elif team_rank == 2:
                    rank_class = "silver"
                elif team_rank == 3:
                    rank_class = "bronze"

                team_abbrev = str(team_name)[:2] if team_name and len(str(team_name)) >= 2 else str(team_name)

                st.markdown(f"""
                <div class="glass-card fade-in" style="animation-delay: {0.1 + idx * 0.1}s;">
                    <div class="group-header">
                        <span class="{badge_class}">{escape(team_abbrev)}</span>
                        <h3 style="margin:0; flex-grow:1; color:#1D1D1F; font-family: 'SF Pro Display';">{escape(str(team_name))}</h3>
                        <span style="font-size:1.8rem; font-weight:700;" class="{rank_class}">#{team_rank}</span>
                    </div>
                    <div style="text-align:center; margin-bottom:25px;">
                        <div style="font-size:1.3rem; color:#86868B; font-family: 'SF Pro Text';">加权小组总分</div>
                        <div style="font-size:2.8rem; font-weight:700; color:#0A84FF; font-family: 'SF Pro Display';">{weighted_team_score}</div>
                    </div>
                    <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">团队成员:</div>
                """, unsafe_allow_html=True)

                for _, member in team_members.iterrows():
                    member_name = str(member['员工姓名'])
                    member_initials = ''.join([n[0] for n in member_name.split() if n])[:2]
                    if not member_initials:
                        member_initials = member_name[:2] if len(member_name) >= 2 else member_name

                    st.markdown(f"""
                    <div class="member-card">
                        <div class="member-avatar">{escape(member_initials)}</div>
                        <div style="flex-grow:1;">
                            <div style="font-weight:600; color:#1D1D1F; font-family: 'SF Pro Display';">{escape(member_name)}</div>
                            <div style="font-family: 'SF Pro Text';">个人积分: <span style="color:#0A84FF; font-weight:500;">{member['个人总积分']}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)


# 显示成就详情
def display_achievement_badges(score_df, sales_df=None):
    if score_df is None or score_df.empty:
        return

    st.markdown("""
    <style>
        .achievement-section {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 30px;
            border: 0.5px solid rgba(0, 0, 0, 0.05);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.05);
        }
        .badge-container {
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            padding: 20px;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(10px);
            height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            border: 0.5px solid rgba(0, 0, 0, 0.03);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
        }
        .badge-container:hover {
            transform: translateY(-6px);
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
        }
        .badge-icon {
            font-size: 3.5rem;
            margin-bottom: 15px;
        }
        .badge-title {
            font-family: 'SF Pro Display';
            font-weight: 700;
            font-size: 1.4rem;
            margin-bottom: 8px;
            color: #1D1D1F;
        }
        .badge-recipient {
            font-family: 'SF Pro Text';
            font-size: 1.1rem;
            color: #86868B;
        }
    </style>
    """, unsafe_allow_html=True)

    df = score_df.copy()
    if sales_df is not None and not sales_df.empty:
        sales_cols = ['员工姓名', '本月销售额', '本月回款总额', '本月正常回款额', '本月超期回款额',
                      '本月超期欠款（未追回）']
        week_cols = [col for col in sales_df.columns if '周周' in col or '周销售额' in col or '周回款总额' in col]
        sales_cols.extend(week_cols)
        ref_cols = [col for col in sales_df.columns if '上月' in col and '参考' in col]
        sales_cols.extend(ref_cols)

        if '队名' in sales_df.columns:
            sales_cols.append('队名')
            existing_sales_cols = [col for col in sales_cols if col in sales_df.columns]
            df = pd.merge(df.drop(columns=['队名'], errors='ignore'),
                          sales_df[existing_sales_cols], on='员工姓名', how='left')
        else:
            existing_sales_cols = [col for col in sales_cols if col in sales_df.columns]
            df = pd.merge(df, sales_df[existing_sales_cols], on='员工姓名', how='left')

    available_columns = df.columns.tolist()
    achievements = {}

    if '本月销售额' in available_columns:
        max_sales_idx = df['本月销售额'].idxmax()
        achievements['销售之星'] = {'icon': '💰', 'recipient': df.loc[max_sales_idx, '员工姓名']}
    if '本月回款总额' in available_columns:
        max_payment_idx = df['本月回款总额'].idxmax()
        achievements['回款之王'] = {'icon': '💸', 'recipient': df.loc[max_payment_idx, '员工姓名']}

    if all(col in available_columns for col in ['本月销售额', '上月销售额(参考)', '本月回款总额', '上月回款额(参考)']):
        df['进步值'] = (
                (df['本月销售额'] - df['上月销售额(参考)'].fillna(0)) * 0.6 +
                (df['本月回款总额'] - df['上月回款额(参考)'].fillna(0)) * 0.4
        )
        max_progress_idx = df['进步值'].idxmax()
        achievements['进步最快'] = {'icon': '🚀', 'recipient': df.loc[max_progress_idx, '员工姓名']}

    if '本月超期回款额' in available_columns:
        max_recovery_idx = df['本月超期回款额'].idxmax()
        achievements['追款能手'] = {'icon': '🕵️', 'recipient': df.loc[max_recovery_idx, '员工姓名']}

    if all(col in available_columns for col in ['队名', '个人总积分', '加权小组总分']):
        df['个人贡献率'] = df['个人总积分'] / df['加权小组总分']
        max_contrib_idx = df['个人贡献率'].idxmax()
        achievements['团队核心'] = {'icon': '🤝', 'recipient': df.loc[max_contrib_idx, '员工姓名']}

    if '个人总积分' in available_columns:
        max_score_idx = df['个人总积分'].idxmax()
        achievements['全能冠军'] = {'icon': '🏆', 'recipient': df.loc[max_score_idx, '员工姓名']}

    if not achievements:
        st.warning("没有可用的数据来显示成就徽章")
        return

    st.markdown('<h3 class="section-title fade-in">🏆 本月成就徽章</h3>', unsafe_allow_html=True)

    st.markdown('<div class="achievement-section fade-in">', unsafe_allow_html=True)
    cols = st.columns(len(achievements))

    for i, (badge_name, badge_info) in enumerate(achievements.items()):
        with cols[i]:
            st.markdown(
                f'<div class="badge-container fade-in" style="animation-delay: {0.1 + i * 0.05}s;">'
                f'<div class="badge-icon">{badge_info["icon"]}</div>'
                f'<div class="badge-title">{badge_name}</div>'
                f'<div class="badge-recipient">{escape(str(badge_info["recipient"]))}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

    achievement_counts = {}
    for badge_name, badge_info in achievements.items():
        if badge_name == "团队核心" and isinstance(badge_info['recipient'], str):
            try:
                name_part = badge_info['recipient'].split('(')[0].strip()
                employee_row = df[df['员工姓名'] == name_part]
                if not employee_row.empty:
                    team = employee_row.iloc[0]['队名']
                    if pd.notna(team) and team != '':
                        achievement_counts[team] = achievement_counts.get(team, 0) + 1
            except Exception:
                pass
        else:
            try:
                if pd.notna(badge_info['recipient']):
                    employee_row = df[df['员工姓名'] == badge_info['recipient']]
                    if not employee_row.empty:
                        team = employee_row.iloc[0]['队名']
                        if pd.notna(team) and team != '':
                            achievement_counts[team] = achievement_counts.get(team, 0) + 1
            except Exception:
                pass

    if achievement_counts:
        st.markdown("### 📊 本月成就统计")
        achievement_df = pd.DataFrame({
            '队名': list(achievement_counts.keys()),
            '成就数量': list(achievement_counts.values())
        })
        fig = px.pie(
            achievement_df,
            values='成就数量',
            names='队名',
            hole=0.4,
            color_discrete_sequence=['#FF453A', '#0A84FF', '#BF5AF2', '#FF9F0A', '#30D158']
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hoverinfo='label+percent+value',
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )

        fig.update_layout(
            showlegend=False,
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            title='各队成就分布',
            font=dict(color='#1D1D1F'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("没有足够的成就数据来生成统计图表")


# 显示员工详情
def display_employee_details(score_df, sales_df=None):
    if score_df is None or score_df.empty:
        return
    st.markdown('<h3 class="section-title fade-in">📋 员工积分详情</h3>', unsafe_allow_html=True)
    if '员工姓名' not in score_df.columns or score_df['员工姓名'].empty:
        st.info("没有员工数据")
        return

    df = score_df.copy()
    if sales_df is not None and not sales_df.empty:
        sales_cols = ['员工姓名', '本月销售额', '本月回款总额', '本月正常回款额', '本月超期回款额',
                      '本月超期欠款（未追回）']
        week_cols = [col for col in sales_df.columns if '周周' in col or '周销售额' in col or '周回款总额' in col]
        sales_cols.extend(week_cols)
        ref_cols = [col for col in sales_df.columns if '上月' in col and '参考' in col]
        sales_cols.extend(ref_cols)

        if '队名' in sales_df.columns:
            sales_cols.append('队名')
            existing_sales_cols = [col for col in sales_cols if col in sales_df.columns]
            df = pd.merge(df.drop(columns=['队名'], errors='ignore'),
                          sales_df[existing_sales_cols], on='员工姓名', how='left')
        else:
            existing_sales_cols = [col for col in sales_cols if col in sales_df.columns]
            df = pd.merge(df, sales_df[existing_sales_cols], on='员工姓名', how='left')

    selected_employee = st.selectbox("选择员工查看积分详情", df['员工姓名'].unique())
    if selected_employee:
        emp_row = df[df['员工姓名'] == selected_employee]
        if emp_row.empty:
            st.warning("未找到该员工数据")
            return
        emp_data = emp_row.iloc[0]

        categories = ['销售额目标分', '回款额目标分', '超期账款追回分',
                      '销售排名分', '回款排名分',
                      '销售进步分', '回款进步分', '基础分', '小组加分']
        values = [emp_data.get(cat, 0) for cat in categories]

        st.markdown("""
        <style>
            .employee-card {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(20px);
                border-radius: 18px;
                padding: 25px;
                margin-bottom: 25px;
                border: 0.5px solid rgba(0, 0, 0, 0.05);
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.05);
            }
            .employee-header {
                text-align: center;
                padding-bottom: 20px;
                margin-bottom: 20px;
                border-bottom: 0.5px solid rgba(0, 0, 0, 0.05);
            }
            .employee-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 25px;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.85);
                border-radius: 14px;
                padding: 20px;
                text-align: center;
                border: 0.5px solid rgba(0, 0, 0, 0.03);
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
            }
            .stat-value {
                font-family: 'SF Pro Display';
                font-size: 2.2rem;
                font-weight: 700;
                margin: 15px 0;
                color: #0A84FF;
            }
            .stat-label {
                font-family: 'SF Pro Text';
                font-size: 1.05rem;
                color: #86868B;
            }
        </style>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        <div class="glass-card fade-in" style="animation-delay: 0.1s;">
            <div class="employee-header">
                <div style="font-size:1.8rem; font-weight:700; color:#1D1D1F; font-family: 'SF Pro Display';">{escape(str(selected_employee))}</div>
                <div class="employee-group" style="color:#0A84FF; font-family: 'SF Pro Text';">队名: {emp_data['队名']}</div>
            </div>
            <div class="employee-stats">
                <div class="stat-card">
                    <div class="stat-label">个人总积分</div>
                    <div class="stat-value">{emp_data['个人总积分']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">加权小组总分</div>
                    <div class="stat-value">{emp_data['加权小组总分']}</div>
                </div>
            </div>
            <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">积分构成:</div>
        """, unsafe_allow_html=True)

        for i, category in enumerate(categories):
            st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.05); font-size:1.05rem; font-family: 'SF Pro Text';">
                        <div>{category}:</div>
                        <div style="font-weight:500;">{values[i]}</div>
                    </div>
                    """, unsafe_allow_html=True)

        if sales_df is not None and '本月销售额' in emp_data:
            st.markdown("""
            <div style="margin-top:20px; padding-top:20px; border-top:0.5px solid rgba(0, 0, 0, 0.05);">
                <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">月度销售数据:</div>
            </div>
            """, unsafe_allow_html=True)

            monthly_items = [
                ('本月销售额', emp_data.get('本月销售额', 0)),
                ('本月回款总额', emp_data.get('本月回款总额', 0)),
                ('本月正常回款额', emp_data.get('本月正常回款额', 0)),
                ('本月超期回款额', emp_data.get('本月超期回款额', 0)),
                ('本月超期欠款（未追回）', emp_data.get('本月超期欠款（未追回）', 0))
            ]
            for label, value in monthly_items:
                if pd.notna(value):
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.03); font-size:1.05rem; font-family: 'SF Pro Text';">
                        <div>{label}:</div>
                        <div style="font-weight:500;">{value:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)

            ref_items = [
                ('上月销售额(参考)', emp_data.get('上月销售额(参考)', 0)),
                ('上月回款额(参考)', emp_data.get('上月回款额(参考)', 0))
            ]
            has_ref_data = any(pd.notna(emp_data.get(item[0], None)) for item in ref_items)

            if has_ref_data:
                st.markdown("""
                <div style="margin-top:20px; padding-top:15px; border-top:0.5px solid rgba(0, 0, 0, 0.03);">
                    <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">上月参考数据:</div>
                </div>
                """, unsafe_allow_html=True)
                for label, value in ref_items:
                    if pd.notna(value):
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.03); font-size:1.05rem; font-family: 'SF Pro Text';">
                            <div>{label}:</div>
                            <div style="font-weight:500;">{value:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

            week_data = []
            for i in range(1, 6):
                possible_sales_cols = [f'第{i}周周销售额', f'第{i}周销售额']
                possible_payment_cols = [f'第{i}周周回款总额', f'第{i}周回款总额']

                week_sales = None
                for col in possible_sales_cols:
                    if col in emp_data:
                        week_sales = emp_data[col]
                        break

                week_payment = None
                for col in possible_payment_cols:
                    if col in emp_data:
                        week_payment = emp_data[col]
                        break

                if pd.notna(week_sales) or pd.notna(week_payment):
                    week_data.append((i, week_sales, week_payment))

            if week_data:
                st.markdown("""
                <div style="margin-top:20px; padding-top:15px; border-top:0.5px solid rgba(0, 0, 0, 0.03);">
                    <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">周数据详情:</div>
                </div>
                """, unsafe_allow_html=True)
                for week_num, sales, payment in week_data:
                    if pd.notna(sales):
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.03); font-size:1.05rem; font-family: 'SF Pro Text';">
                            <div>第{week_num}周销售额:</div>
                            <div style="font-weight:500;">{sales:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    if pd.notna(payment):
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.03); font-size:1.05rem; font-family: 'SF Pro Text';">
                            <div>第{week_num}周回款额:</div>
                            <div style="font-weight:500;">{payment:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name='积分构成',
            line=dict(color='#0A84FF', width=3),
            fillcolor='rgba(10, 132, 255, 0.1)'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[-10, max(values) * 1.2 if max(values) > 0 else 1],
                    gridcolor='rgba(0,0,0,0.05)',
                    linecolor='rgba(0,0,0,0.1)'
                ),
                angularaxis=dict(
                    linecolor='rgba(0,0,0,0.1)',
                    gridcolor='rgba(0,0,0,0.05)'
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=False,
            height=500,
            margin=dict(l=100, r=100, t=80, b=80),
            title=f"{selected_employee}的积分构成",
            title_font=dict(size=24, color='#1D1D1F'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1D1D1F')
        )
        st.plotly_chart(fig, use_container_width=True)


# 销售回款相关的员工详情
def display_sales_employee_details(score_df, sales_df=None):
    if score_df is None or score_df.empty:
        return
    st.markdown('<h3 class="section-title fade-in">💰 员工销售回款详情</h3>', unsafe_allow_html=True)
    if '员工姓名' not in score_df.columns or score_df['员工姓名'].empty:
        st.info("没有员工数据")
        return

    df = score_df.copy()
    if sales_df is not None and not sales_df.empty:
        sales_cols = ['员工姓名', '本月销售额', '本月回款总额', '本月正常回款额', '本月超期回款额',
                      '本月超期欠款（未追回）']
        week_cols = [col for col in sales_df.columns if '周周' in col or '周销售额' in col or '周回款总额' in col]
        sales_cols.extend(week_cols)
        ref_cols = [col for col in sales_df.columns if '上月' in col and '参考' in col]
        sales_cols.extend(ref_cols)

        if '队名' in sales_df.columns:
            sales_cols.append('队名')
            existing_sales_cols = [col for col in sales_cols if col in sales_df.columns]
            df = pd.merge(df.drop(columns=['队名'], errors='ignore'),
                          sales_df[existing_sales_cols], on='员工姓名', how='left')
        else:
            existing_sales_cols = [col for col in sales_cols if col in sales_df.columns]
            df = pd.merge(df, sales_df[existing_sales_cols], on='员工姓名', how='left')

    selected_employee = st.selectbox("选择员工查看销售回款详情", df['员工姓名'].unique())
    if selected_employee:
        emp_row = df[df['员工姓名'] == selected_employee]
        if emp_row.empty:
            st.warning("未找到该员工数据")
            return
        emp_data = emp_row.iloc[0]

        sales_categories = ['本月销售额', '本月正常回款额', '本月超期回款额']
        sales_values = [emp_data.get(cat, 0) / 10000 for cat in sales_categories]
        sales_categories = [cat + '(万元)' for cat in sales_categories]

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"""
            <div class="glass-card fade-in" style="animation-delay: 0.1s;">
                <div class="employee-header">
                    <div style="font-size:1.8rem; font-weight:700; color:#1D1D1F; font-family: 'SF Pro Display';">{escape(str(selected_employee))}</div>
                    <div class="employee-group" style="color:#0A84FF; font-family: 'SF Pro Text';">队名: {emp_data['队名']}</div>
                </div>
                <div class="employee-stats">
                    <div class="stat-card">
                        <div class="stat-label">本月销售总额</div>
                        <div class="stat-value">{emp_data.get('本月销售额', 0):,.0f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">本月回款总额</div>
                        <div class="stat-value">{emp_data.get('本月回款总额', 0):,.0f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if '本月销售额' in emp_data:
                st.markdown("""
                <div style="margin-top:20px; padding-top:20px; border-top:0.5px solid rgba(0, 0, 0, 0.05);">
                    <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">月度销售数据:</div>
                </div>
                """, unsafe_allow_html=True)

                monthly_items = [
                    ('本月销售额', emp_data.get('本月销售额', 0)),
                    ('本月回款总额', emp_data.get('本月回款总额', 0)),
                    ('本月正常回款额', emp_data.get('本月正常回款额', 0)),
                    ('本月超期回款额', emp_data.get('本月超期回款额', 0)),
                    ('本月超期欠款（未追回）', emp_data.get('本月超期欠款（未追回）', 0))
                ]
                for label, value in monthly_items:
                    if pd.notna(value):
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.03); font-size:1.05rem; font-family: 'SF Pro Text';">
                            <div>{label}:</div>
                            <div style="font-weight:500;">{value:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                ref_items = [
                    ('上月销售额(参考)', emp_data.get('上月销售额(参考)', 0)),
                    ('上月回款额(参考)', emp_data.get('上月回款额(参考)', 0))
                ]
                has_ref_data = any(pd.notna(emp_data.get(item[0], None)) for item in ref_items)

                if has_ref_data:
                    st.markdown("""
                    <div style="margin-top:20px; padding-top:15px; border-top:0.5px solid rgba(0, 0, 0, 0.03);">
                        <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">上月参考数据:</div>
                    </div>
                    """, unsafe_allow_html=True)
                    for label, value in ref_items:
                        if pd.notna(value):
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.03); font-size:1.05rem; font-family: 'SF Pro Text';">
                                <div>{label}:</div>
                                <div style="font-weight:500;">{value:,.0f}</div>
                            </div>
                            """, unsafe_allow_html=True)

                week_data = []
                for i in range(1, 6):
                    possible_sales_cols = [f'第{i}周周销售额', f'第{i}周销售额']
                    possible_payment_cols = [f'第{i}周周回款总额', f'第{i}周回款总额']

                    week_sales = None
                    for col in possible_sales_cols:
                        if col in emp_data:
                            week_sales = emp_data[col]
                            break

                    week_payment = None
                    for col in possible_payment_cols:
                        if col in emp_data:
                            week_payment = emp_data[col]
                            break

                    if pd.notna(week_sales) or pd.notna(week_payment):
                        week_data.append((i, week_sales, week_payment))

                if week_data:
                    st.markdown("""
                    <div style="margin-top:20px; padding-top:15px; border-top:0.5px solid rgba(0, 0, 0, 0.03);">
                        <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">周数据详情:</div>
                    </div>
                    """, unsafe_allow_html=True)
                    for week_num, sales, payment in week_data:
                        if pd.notna(sales):
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.03); font-size:1.05rem; font-family: 'SF Pro Text';">
                                <div>第{week_num}周销售额:</div>
                                <div style="font-weight:500;">{sales:,.0f}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        if pd.notna(payment):
                            st.markdown(f"""
                            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:0.5px solid rgba(0, 0, 0, 0.03); font-size:1.05rem; font-family: 'SF Pro Text';">
                                <div>第{week_num}周回款额:</div>
                                <div style="font-weight:500;">{payment:,.0f}</div>
                            </div>
                            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=sales_values + [sales_values[0]],
                theta=sales_categories + [sales_categories[0]],
                fill='toself',
                name='销售回款数据',
                line=dict(color='#BF5AF2', width=3),
                fillcolor='rgba(191, 90, 242, 0.1)'
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(sales_values) * 1.2 if max(sales_values) > 0 else 1],
                        gridcolor='rgba(0,0,0,0.05)',
                        linecolor='rgba(0,0,0,0.1)'
                    ),
                    angularaxis=dict(
                        linecolor='rgba(0,0,0,0.1)',
                        gridcolor='rgba(0,0,0,0.05)'
                    ),
                    bgcolor='rgba(0,0,0,0)'
                ),
                showlegend=False,
                height=500,
                margin=dict(l=100, r=100, t=80, b=80),
                title=f"{selected_employee}的销售回款数据",
                title_font=dict(size=24, color='#1D1D1F'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1D1D1F')
            )
            st.plotly_chart(fig, use_container_width=True)


# 显示销售概览
def display_sales_overview(sales_df):
    if sales_df is None or sales_df.empty:
        return

    st.markdown('<h3 class="section-title fade-in">📊 销售回款概览</h3>', unsafe_allow_html=True)

    total_sales = sales_df['本月销售额'].sum() / 10000
    total_payment = sales_df['本月回款总额'].sum() / 10000
    avg_sales = sales_df['本月销售额'].mean() / 10000
    avg_payment = sales_df['本月回款总额'].mean() / 10000

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总销售额(万元)", f"{total_sales:,.2f}", help="本月所有员工销售额总和", delta_color="off")
    with col2:
        st.metric("总回款额(万元)", f"{total_payment:,.2f}", help="本月所有员工回款额总和", delta_color="off")
    with col3:
        st.metric("平均销售额(万元)", f"{avg_sales:,.2f}", help="本月员工平均销售额", delta_color="off")
    with col4:
        st.metric("平均回款额(万元)", f"{avg_payment:,.2f}", help="本月员工平均回款额", delta_color="off")

    if '队名' in sales_df.columns:
        team_sales = sales_df.groupby('队名').agg({
            '本月销售额': 'sum',
            '本月回款总额': 'sum',
            '员工姓名': 'count'
        }).rename(columns={'员工姓名': '团队人数'}).reset_index()

        team_sales['本月销售额(万元)'] = team_sales['本月销售额'] / 10000
        team_sales['本月回款总额(万元)'] = team_sales['本月回款总额'] / 10000

        fig = px.bar(team_sales, x='队名', y=['本月销售额(万元)', '本月回款总额(万元)'],
                     title='各队销售与回款对比（单位：万元）',
                     barmode='group',
                     labels={'value': '金额（万元）'},
                     color_discrete_sequence=['#0A84FF', '#BF5AF2'])
        fig.update_layout(
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title='金额（万元）',
            font=dict(color='#1D1D1F'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        fig.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
        fig.update_yaxes(gridcolor='rgba(0,0,0,0.05)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("销售数据中缺少'队名'列，无法按团队分组")


# 显示周分析
def display_weekly_analysis(sales_df):
    if sales_df is None or sales_df.empty:
        return

    st.markdown('<h3 class="section-title fade-in">📅 周数据分析</h3>', unsafe_allow_html=True)

    week_columns = [col for col in sales_df.columns if
                    '周周销售额' in col or '周周回款总额' in col or '周销售额' in col or '周回款总额' in col]
    if not week_columns:
        st.info("当前数据中没有周数据信息")
        return

    week_sales_cols = [col for col in sales_df.columns if '周销售额' in col]
    week_payment_cols = [col for col in sales_df.columns if '周回款总额' in col]

    if week_sales_cols and week_payment_cols:
        weekly_totals = {}
        for i in range(1, 6):
            possible_sales_cols = [f'第{i}周周销售额', f'第{i}周销售额']
            possible_payment_cols = [f'第{i}周周回款总额', f'第{i}周回款总额']

            sales_col = None
            for col in possible_sales_cols:
                if col in sales_df.columns:
                    sales_col = col
                    break

            payment_col = None
            for col in possible_payment_cols:
                if col in sales_df.columns:
                    payment_col = col
                    break

            if sales_col and payment_col:
                weekly_totals[f'第{i}周'] = {
                    '销售额(万元)': sales_df[sales_col].sum() / 10000,
                    '回款额(万元)': sales_df[payment_col].sum() / 10000
                }

        if weekly_totals:
            weeks = list(weekly_totals.keys())
            sales_values = [weekly_totals[week]['销售额(万元)'] for week in weeks]
            payment_values = [weekly_totals[week]['回款额(万元)'] for week in weeks]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=weeks, y=sales_values, mode='lines+markers',
                name='周销售额', line=dict(color='#0A84FF', width=3.5),
                marker=dict(size=10, color='#0A84FF')
            ))
            fig.add_trace(go.Scatter(
                x=weeks, y=payment_values, mode='lines+markers',
                name='周回款额', line=dict(color='#BF5AF2', width=3.5),
                marker=dict(size=10, color='#BF5AF2')
            ))

            fig.update_layout(
                title='各周销售与回款趋势（单位：万元）',
                xaxis_title='周次',
                yaxis_title='金额（万元）',
                height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1D1D1F'),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            fig.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
            fig.update_yaxes(gridcolor='rgba(0,0,0,0.05)')
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**各周销售额汇总**")
                week_sales_data = []
                for week, data in weekly_totals.items():
                    formatted_sales = format_amount(data['销售额(万元)'])
                    week_sales_data.append({
                        '周次': week,
                        '销售额': formatted_sales
                    })
                week_sales_df = pd.DataFrame(week_sales_data)
                st.dataframe(week_sales_df, use_container_width=True, hide_index=True)

            with col2:
                st.markdown("**各周回款额汇总**")
                week_payment_data = []
                for week, data in weekly_totals.items():
                    formatted_payment = format_amount(data['回款额(万元)'])
                    week_payment_data.append({
                        '周次': week,
                        '回款额': formatted_payment
                    })
                week_payment_df = pd.DataFrame(week_payment_data)
                st.dataframe(week_payment_df, use_container_width=True, hide_index=True)


def main():
    st.set_page_config(
        page_title="销售积分红黑榜系统",
        page_icon="🏆",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    load_css()

    # 检查session state中是否有已上传的文件内容
    if st.session_state.get('uploaded_file') and not st.session_state.data_loaded:
        try:
            # 使用BytesIO加载已保存的文件内容
            score_df, sales_df, error = load_excel_data(BytesIO(st.session_state.uploaded_file))
            if not error:
                st.session_state.score_df = score_df
                st.session_state.sales_df = sales_df
                st.session_state.data_loaded = True
        except Exception as e:
            st.error(f"重新加载文件时出错: {str(e)}")

    # 只在本地环境启用文件自动检测
    if not st.session_state.data_loaded and st.session_state.file_name is None:
        if not st.runtime.exists():  # 检查是否在Streamlit Sharing环境
            detected_file = auto_detect_excel_file()
            if detected_file:
                try:
                    score_df, sales_df, error = load_excel_data(detected_file)
                    if not error:
                        st.session_state.score_df = score_df
                        st.session_state.sales_df = sales_df
                        st.session_state.data_loaded = True
                        st.session_state.file_name = detected_file
                    else:
                        st.error(f"自动加载文件失败: {error}")
                except Exception as e:
                    st.error(f"文件加载错误: {str(e)}")

    if st.session_state.current_page != 'home':
        show_navigation()

    if st.session_state.current_page == 'home':
        show_home_page()
    elif st.session_state.current_page == 'leaderboard':
        show_leaderboard_page()
    elif st.session_state.current_page == 'scores':
        show_scores_page()
    elif st.session_state.current_page == 'sales':
        show_sales_page()

    st.markdown("---")
    st.markdown("""
    <div class="footer">
        销售积分红黑榜系统 | © 2025 销售绩效评估中心 | 版本 3.0
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
