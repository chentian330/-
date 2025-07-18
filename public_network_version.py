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
from contextlib import nullcontext
import re

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
if 'department_sales_df' not in st.session_state:
    st.session_state.department_sales_df = None
if 'ranking_df' not in st.session_state:
    st.session_state.ranking_df = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
# 添加历史数据相关的状态变量
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []  # 存储多个月份的数据
if 'historical_months' not in st.session_state:
    st.session_state.historical_months = []  # 存储月份标识


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

        /* 自定义选项卡样式 - 卡片式选项卡 */
        div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {{
            gap: 1rem !important;
            margin-bottom: 1.5rem !important;
        }}

        /* 选项卡按钮样式，模仿卡片效果 */
        div[data-testid="stTabs"] > div[data-testid="stMarkdown"] {{
            position: relative !important;
            z-index: 1 !important;
        }}

        div[data-testid="stTabs"] button[role="tab"] {{
            background: var(--glass-bg) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border-radius: 12px !important;
            border: 0.5px solid var(--glass-border) !important;
            box-shadow: 
                0 8px 20px rgba(0, 0, 0, 0.05),
                inset 0 0 0 1px rgba(255, 255, 255, 0.5) !important;
            padding: 12px 15px !important;
            margin: 0 5px 10px !important;
            transition: all 0.3s ease !important;
            font-family: 'SF Pro Text', sans-serif !important;
            font-weight: 500 !important;
            height: auto !important;
            min-width: 120px !important;
            color: var(--color-text-primary) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}

        div[data-testid="stTabs"] button[role="tab"]:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 
                0 10px 25px rgba(0, 0, 0, 0.08),
                inset 0 0 0 1px rgba(255, 255, 255, 0.7) !important;
        }}

        /* 选中的选项卡 */
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
            background: white !important;
            color: var(--color-primary) !important;
            border-color: var(--color-primary) !important;
            box-shadow: 
                0 8px 20px rgba(10, 132, 255, 0.15),
                inset 0 0 0 1px rgba(10, 132, 255, 0.3) !important;
        }}

        /* 每周选项卡样式 */
        div[data-baseweb="tab-list"]:has(button:contains("周")) button[role="tab"] {{
            border-bottom: none !important;
        }}

        /* 每周选项卡选中状态 */
        div[data-baseweb="tab-list"]:has(button:contains("周")) button[role="tab"][aria-selected="true"] {{
            border-color: var(--color-accent-blue) !important;
            color: var(--color-accent-blue) !important;
        }}

        /* 每月选项卡选中状态 */
        div[data-baseweb="tab-list"]:has(button:contains("月")) button[role="tab"][aria-selected="true"] {{
            border-color: var(--color-accent-purple) !important;
            color: var(--color-accent-purple) !important;
        }}

        /* 选项卡内容区域 */
        div[data-testid="stTabs"] div[data-baseweb="tab-panel"] {{
            padding: 1rem !important;
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
        # Load score_df (required)
        score_df = pd.read_excel(file_path, sheet_name='员工积分数据', engine='openpyxl')
        if '队名' not in score_df.columns:
            return None, None, None, None, "数据文件中缺少'队名'列"

        # Load sales_df (optional)
        sales_df = None
        try:
            sales_df = pd.read_excel(file_path, sheet_name='销售回款数据统计', engine='openpyxl')
        except:
            try:
                sales_df = pd.read_excel(file_path, sheet_name='销售回款数据', engine='openpyxl')
            except:
                pass

        # Load department_sales_df (optional)
        department_sales_df = None
        try:
            department_sales_df = pd.read_excel(file_path, sheet_name='部门销售回款统计', engine='openpyxl')
        except:
            pass

        # Load ranking_df (optional) - 员工排名数据
        ranking_df = None
        try:
            ranking_df = pd.read_excel(file_path, sheet_name='销售回款超期账款排名', engine='openpyxl')
        except:
            pass

        return score_df, sales_df, department_sales_df, ranking_df, None
    except Exception as e:
        return None, None, None, None, f"读取文件时出错: {str(e)}"


# 导航栏
def show_navigation():
    # 创建导航栏
    nav_items = {
        "nav_home": {"label": "首页", "icon": "🏠"},
        "nav_back": {"label": "返回", "icon": "⬅️"},
        "nav_undo": {"label": "撤销", "icon": "↩️"},
        "nav_history": {"label": "历史数据对比", "icon": "📊"}  # 添加历史数据对比选项
    }

    # 使用columns创建居中布局
    cols = st.columns([1, 2, 2, 2, 2, 1])  # 增加一列用于新按钮

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

    with cols[4]:
        if st.button(
                f"{nav_items['nav_history']['icon']} {nav_items['nav_history']['label']}",
                help="查看历史数据对比",
                key="nav_history",
                use_container_width=True
        ):
            st.session_state.current_page = 'history_compare'
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
            score_df, sales_df, department_sales_df, ranking_df, error = load_excel_data(uploaded_file)
            if error:
                st.error(f"文件加载失败: {error}")
            else:
                st.session_state.score_df = score_df
                st.session_state.sales_df = sales_df
                st.session_state.department_sales_df = department_sales_df
                st.session_state.ranking_df = ranking_df
                st.session_state.data_loaded = True
                st.session_state.file_name = uploaded_file.name
                st.success(f"文件加载成功: {uploaded_file.name}")

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

        if st.button("💰 查看销售回款统计", key="btn_sales", disabled=disabled, use_container_width=True):
            if st.session_state.data_loaded:
                st.session_state.current_page = 'sales'
                st.rerun()
            else:
                st.error("请添加文件后重试")

        st.markdown("<br>", unsafe_allow_html=True)

        ranking_data_loaded = st.session_state.ranking_df is not None
        if st.button("📈 查看员工排名", key="btn_ranking", disabled=not ranking_data_loaded,
                     use_container_width=True):
            if ranking_data_loaded:
                st.session_state.current_page = 'ranking'
                st.rerun()
            else:
                st.error("请上传包含排名数据的文件。")

        st.markdown("<br>", unsafe_allow_html=True)

        dept_data_loaded = st.session_state.department_sales_df is not None
        if st.button("🏢 查看部门销售回款明细", key="btn_dept_sales", disabled=not dept_data_loaded,
                     use_container_width=True):
            if dept_data_loaded:
                st.session_state.current_page = 'department_sales'
                st.rerun()
            else:
                st.error("请上传包含'部门销售回款统计'工作表的文件。")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📊 查看月度数据历史对比", key="btn_history_compare", use_container_width=True):
            st.session_state.current_page = 'history_compare'
            st.rerun()


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


# 部门销售回款明细页面
def show_department_sales_page():
    if st.session_state.department_sales_df is None:
        st.error("部门销售回款数据未加载。请上传有效文件。")
        st.session_state.current_page = 'home'
        return

    st.markdown('<h1 style="text-align: center; font-family: \'SF Pro Display\', sans-serif;">部门销售回款分析</h1>',
                unsafe_allow_html=True)

    # --- Data Preparation ---
    df = st.session_state.department_sales_df.copy()

    # Remove the '合计' (Total) row for rankings and charts
    df = df[df['部门'] != '合计'].copy()
    if df.empty:
        st.warning("数据文件中没有有效的部门数据。")
        return

    # --- CORRECTED COLUMN NAMES ---
    # Using full-width Chinese parentheses as specified
    payment_col_normal = '本月回未超期款'
    payment_col_overdue = '本月回超期款'

    if payment_col_normal in df.columns and payment_col_overdue in df.columns:
        df['月总回款额'] = df[payment_col_normal].fillna(0) + df[payment_col_overdue].fillna(0)
    else:
        st.error(f"月度回款列缺失，请检查文件中的列名是否为 '{payment_col_normal}' 和 '{payment_col_overdue}'。")
        return

    # Calculate total weekly payments using corrected column names
    for i in range(1, 6):
        week_payment_normal = f'第{i}周回未超期款'
        week_payment_overdue = f'第{i}周回超期款'
        if week_payment_normal in df.columns and week_payment_overdue in df.columns:
            df[f'第{i}周总回款额'] = df[week_payment_normal].fillna(0) + df[week_payment_overdue].fillna(0)

    # --- 1 & 2. Rankings ---
    st.markdown('<h3 class="section-title fade-in">月度排名</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 销售额排名 (部门)")
        sales_ranking_df = df.sort_values('本月销售额', ascending=False)
        fig_sales = px.bar(sales_ranking_df, x='本月销售额', y='部门', orientation='h', title='月销售额排名',
                           labels={'本月销售额': '销售额 (元)', '部门': '部门'}, text='本月销售额',
                           color_discrete_sequence=['#0A84FF'])
        fig_sales.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_sales.update_layout(yaxis={'categoryorder': 'total ascending'}, plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#1D1D1F'))
        st.plotly_chart(fig_sales, use_container_width=True)

    with col2:
        st.markdown("#### 回款额排名 (部门)")
        payment_ranking_df = df.sort_values('月总回款额', ascending=False)
        fig_payment = px.bar(payment_ranking_df, x='月总回款额', y='部门', orientation='h', title='月回款额排名',
                             labels={'月总回款额': '回款额 (元)', '部门': '部门'}, text='月总回款额',
                             color_discrete_sequence=['#BF5AF2'])
        fig_payment.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_payment.update_layout(yaxis={'categoryorder': 'total ascending'}, plot_bgcolor='rgba(0,0,0,0)',
                                  paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#1D1D1F'))
        st.plotly_chart(fig_payment, use_container_width=True)

    # --- 3 & 4. Weekly Trends ---
    st.markdown('<h3 class="section-title fade-in">各周走势</h3>', unsafe_allow_html=True)

    # Prepare data for line charts
    sales_cols = ['部门'] + [f'第{i}周销售额' for i in range(1, 6) if f'第{i}周销售额' in df.columns]
    payment_cols = ['部门'] + [f'第{i}周总回款额' for i in range(1, 6) if f'第{i}周总回款额' in df.columns]

    sales_melted = df[sales_cols].melt(id_vars='部门', var_name='周次', value_name='销售额').dropna()
    payment_melted = df[payment_cols].melt(id_vars='部门', var_name='周次', value_name='回款额').dropna()

    # Correctly extract week number for sorting
    sales_melted['周序号'] = sales_melted['周次'].str.extract(r'(\d+)').astype(int)
    payment_melted['周序号'] = payment_melted['周次'].str.replace('第', '').str.replace('周总回款额', '').astype(int)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### 各周销售额走势")
        if not sales_melted.empty:
            fig_sales_trend = px.line(sales_melted.sort_values('周序号'), x='周次', y='销售额', color='部门',
                                      title='各部门周销售额趋势', markers=True)
            fig_sales_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                          font=dict(color='#1D1D1F'), xaxis_title=None)
            st.plotly_chart(fig_sales_trend, use_container_width=True)
        else:
            st.info("无周销售额数据可供展示。")

    with col4:
        st.markdown("#### 各周回款额走势")
        if not payment_melted.empty:
            # Use custom sorting for the x-axis labels
            custom_x_labels = sorted(payment_melted['周次'].unique(),
                                     key=lambda x: int(x.replace('第', '').replace('周总回款额', '')))
            fig_payment_trend = px.line(payment_melted, x='周次', y='回款额', color='部门', title='各部门周回款额趋势',
                                        markers=True, category_orders={"周次": custom_x_labels})
            fig_payment_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                            font=dict(color='#1D1D1F'), xaxis_title=None)
            fig_payment_trend.update_xaxes(
                ticktext=[f"第 {x.replace('第', '').replace('周总回款额', '')} 周" for x in custom_x_labels],
                tickvals=custom_x_labels)
            st.plotly_chart(fig_payment_trend, use_container_width=True)
        else:
            st.info("无周回款额数据可供展示。")

    # --- 5. Department Details ---
    st.markdown('<h3 class="section-title fade-in">部门销售回款详情</h3>', unsafe_allow_html=True)

    departments = df['部门'].unique()
    selected_dept = st.selectbox("选择要查看的部门", departments, label_visibility="collapsed")

    if selected_dept:
        dept_data = df[df['部门'] == selected_dept].iloc[0]

        st.markdown(f"""
        <div class="glass-card fade-in">
            <h2 style="text-align:center; color: #BF5AF2; font-family: 'SF Pro Display';">{escape(selected_dept)} - 月度总览</h2>
            <div class="divider"></div> """, unsafe_allow_html=True)

        kpi_cols = st.columns(3)
        with kpi_cols[0]:
            st.metric("本月销售额", f"¥ {dept_data.get('本月销售额', 0):,.2f}")
        with kpi_cols[1]:
            st.metric("本月总回款额", f"¥ {dept_data.get('月总回款额', 0):,.2f}")
        with kpi_cols[2]:
            overdue_val = dept_data.get(payment_col_overdue, 0)
            total_payment = dept_data.get('月总回款额', 0)
            overdue_payment_pct = (overdue_val / total_payment * 100) if total_payment > 0 else 0
            st.metric("超期回款占比", f"{overdue_payment_pct:.2f}%", help=f"超期回款额: ¥ {overdue_val:,.2f}")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-top:20px; font-family: \'SF Pro Display\', sans-serif;">周度数据详情</h4>',
                    unsafe_allow_html=True)

        detail_cols = st.columns(2)
        with detail_cols[0]:
            st.markdown("##### 周销售额")
            weekly_sales_data = []
            for i in range(1, 6):
                col_name = f'第{i}周销售额'
                if col_name in dept_data and pd.notna(dept_data[col_name]):
                    weekly_sales_data.append({'周次': f'第 {i} 周', '销售额': dept_data[col_name]})
            if weekly_sales_data:
                st.dataframe(pd.DataFrame(weekly_sales_data).style.format({'销售额': '¥ {:,.2f}'}),
                             use_container_width=True, hide_index=True)
            else:
                st.info("无周销售数据")

        with detail_cols[1]:
            st.markdown("##### 周回款额")
            weekly_payment_data = []
            for i in range(1, 6):
                col_name = f'第{i}周总回款额'
                if col_name in dept_data and pd.notna(dept_data[col_name]):
                    weekly_payment_data.append({'周次': f'第 {i} 周', '回款额': dept_data[col_name]})
            if weekly_payment_data:
                st.dataframe(pd.DataFrame(weekly_payment_data).style.format({'回款额': '¥ {:,.2f}'}),
                             use_container_width=True, hide_index=True)
            else:
                st.info("无周回款数据")

        st.markdown("</div>", unsafe_allow_html=True)


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
        sales_cols = ['员工姓名', '本月销售额', '本月回款合计', '本月回未超期款', '本月回超期款',
                      '月末逾期未收回额']
        week_cols = [col for col in sales_df.columns if '周周' in col or '周销售额' in col or '周回款合计' in col]
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
    if '本月回款合计' in available_columns:
        max_payment_idx = df['本月回款合计'].idxmax()
        achievements['回款之王'] = {'icon': '💸', 'recipient': df.loc[max_payment_idx, '员工姓名']}

    if all(col in available_columns for col in ['本月销售额', '上月销售额(参考)', '本月回款合计', '上月回款额(参考)']):
        df['进步值'] = (
                (df['本月销售额'] - df['上月销售额(参考)'].fillna(0)) * 0.6 +
                (df['本月回款合计'] - df['上月回款额(参考)'].fillna(0)) * 0.4
        )
        max_progress_idx = df['进步值'].idxmax()
        achievements['进步最快'] = {'icon': '🚀', 'recipient': df.loc[max_progress_idx, '员工姓名']}

    if '本月回超期款' in available_columns:
        max_recovery_idx = df['本月回超期款'].idxmax()
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
    if score_df is None or score_df.shape[0] == 0:
        return
    st.markdown('<h3 class="section-title fade-in">📋 员工积分详情</h3>', unsafe_allow_html=True)
    if '员工姓名' not in score_df.columns or len(score_df['员工姓名']) == 0:
        st.info("没有员工数据")
        return

    df = score_df.copy()
    if sales_df is not None and not sales_df.empty:
        sales_cols = ['员工姓名', '本月销售额', '本月回款合计', '本月回未超期款', '本月回超期款',
                      '月末逾期未收回额']
        week_cols = [col for col in sales_df.columns if '周周' in col or '周销售额' in col or '周回款合计' in col]
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
        if len(emp_row) == 0:
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
                    ('本月回款合计', emp_data.get('本月回款合计', 0)),
                    ('本月回未超期款', emp_data.get('本月回未超期款', 0)),
                    ('本月回超期款', emp_data.get('本月回超期款', 0)),
                    ('月末逾期未收回额', emp_data.get('月末逾期未收回额', 0))
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
                if sales_df is not None:
                    for i in range(1, 6):
                        week_sales_col = f'第{i}周销售额'
                        week_payment_col = f'第{i}周回款合计'

                        week_sales = emp_data.get(week_sales_col, 0)
                        week_payment = emp_data.get(week_payment_col, 0)

                        if (pd.notna(week_sales) and week_sales != 0) or (pd.notna(week_payment) and week_payment != 0):
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
            # 根据有无进度数据选择不同的图表
            if '销售业绩完成进度' in emp_data and '回款业绩完成进度' in emp_data:
                # 创建仪表盘样式图表
                gauge_data = [
                    {'category': '销售任务完成率', 'value': emp_data['销售业绩完成进度']},
                    {'category': '回款任务完成率', 'value': emp_data['回款业绩完成进度']}
                ]

                fig = go.Figure()

                # 销售任务仪表盘
                sales_color = get_progress_color(emp_data['销售业绩完成进度'])
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=emp_data['销售业绩完成进度'] * 100,
                    domain={'x': [0, 1], 'y': [0.6, 1]},
                    title={'text': "销售任务完成率", 'font': {'size': 20}},
                    gauge={
                        'axis': {'range': [0, 150], 'tickwidth': 1},
                        'bar': {'color': sales_color},
                        'bgcolor': "white",
                        'steps': [
                            {'range': [0, 66], 'color': "rgba(255, 69, 58, 0.15)"},
                            {'range': [66, 100], 'color': "rgba(255, 214, 10, 0.15)"},
                            {'range': [100, 150], 'color': "rgba(48, 209, 88, 0.15)"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    },
                    number={'suffix': "%"}
                ))

                # 回款任务仪表盘
                payment_color = get_progress_color(emp_data['回款业绩完成进度'])
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=emp_data['回款业绩完成进度'] * 100,
                    domain={'x': [0, 1], 'y': [0.1, 0.5]},
                    title={'text': "回款任务完成率", 'font': {'size': 20}},
                    gauge={
                        'axis': {'range': [0, 150], 'tickwidth': 1},
                        'bar': {'color': payment_color},
                        'bgcolor': "white",
                        'steps': [
                            {'range': [0, 66], 'color': "rgba(255, 69, 58, 0.15)"},
                            {'range': [66, 100], 'color': "rgba(255, 214, 10, 0.15)"},
                            {'range': [100, 150], 'color': "rgba(48, 209, 88, 0.15)"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    },
                    number={'suffix': "%"}
                ))

                fig.update_layout(
                    title=f"{selected_employee}的任务完成情况",
                    title_font=dict(size=24, color='#1D1D1F'),
                    height=600,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1D1D1F')
                )

                st.plotly_chart(fig, use_container_width=True)

                # 添加销售和回款数据对比图表
                sales_data = {
                    'category': ['销售额', '销售任务'],
                    'value': [emp_data.get('本月销售额', 0) / 10000, emp_data.get('本月销售任务', 0) / 10000]
                }

                payment_data = {
                    'category': ['回款额', '回款任务'],
                    'value': [emp_data.get('本月回款合计', 0) / 10000, emp_data.get('本月回款任务', 0) / 10000]
                }

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=sales_data['category'],
                    y=sales_data['value'],
                    name='销售情况',
                    marker_color='#0A84FF',
                    text=[f"{val:.1f}万" for val in sales_data['value']],
                    textposition='auto',
                ))

                fig.add_trace(go.Bar(
                    x=payment_data['category'],
                    y=payment_data['value'],
                    name='回款情况',
                    marker_color='#BF5AF2',
                    text=[f"{val:.1f}万" for val in payment_data['value']],
                    textposition='auto',
                ))

                fig.update_layout(
                    title=f"{selected_employee}的销售与回款对比(万元)",
                    title_font=dict(size=20, color='#1D1D1F'),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1D1D1F')
                )

                st.plotly_chart(fig, use_container_width=True)

            else:
                # 原来的雷达图
                fig = go.Figure()

                # 创建积分构成雷达图
                categories = ['销售额目标分', '回款额目标分', '超期账款追回分',
                              '销售排名分', '回款排名分', '销售进步分',
                              '回款进步分', '基础分', '小组加分']
                values = [emp_data.get(cat, 0) for cat in categories]

                # 确保values和categories不为空
                if values and categories:
                    # 添加雷达图
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        name='积分构成',
                        line=dict(color='#BF5AF2', width=3),
                        fillcolor='rgba(191, 90, 242, 0.1)'
                    ))

                    # 设置图表布局
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[-10, max(values) * 1.2 if values else 1],
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
                        title=f"{selected_employee}的积分构成雷达图",
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

    # 用新列名
    total_sales = sales_df['本月销售额'].sum() / 10000
    total_payment = sales_df['本月回款合计'].sum() / 10000
    avg_sales = sales_df['本月销售额'].mean() / 10000
    avg_payment = sales_df['本月回款合计'].mean() / 10000

    # 计算任务完成情况（如果有数据）
    if '本月销售任务' in sales_df.columns and '销售业绩完成进度' in sales_df.columns:
        avg_sales_progress = sales_df['销售业绩完成进度'].mean() * 100
        progress_delta = f"{avg_sales_progress - 100:.1f}%" if avg_sales_progress >= 100 else f"{avg_sales_progress - 100:.1f}%"
        sales_delta_color = "normal" if avg_sales_progress >= 100 else "inverse"
    else:
        avg_sales_progress = None
        progress_delta = None
        sales_delta_color = "off"

    if '本月回款任务' in sales_df.columns and '回款业绩完成进度' in sales_df.columns:
        avg_payment_progress = sales_df['回款业绩完成进度'].mean() * 100
        payment_progress_delta = f"{avg_payment_progress - 100:.1f}%" if avg_payment_progress >= 100 else f"{avg_payment_progress - 100:.1f}%"
        payment_delta_color = "normal" if avg_payment_progress >= 100 else "inverse"
    else:
        avg_payment_progress = None
        payment_progress_delta = None
        payment_delta_color = "off"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 销售数据")
        sale_cols = st.columns(3)
        with sale_cols[0]:
            st.metric("总销售额(万元)", f"{total_sales:,.2f}", help="本月所有员工销售额总和", delta_color="off")
        with sale_cols[1]:
            st.metric("平均销售额(万元)", f"{avg_sales:,.2f}", help="本月员工平均销售额", delta_color="off")

        if avg_sales_progress is not None:
            with sale_cols[2]:
                st.metric("平均销售任务完成率", f"{avg_sales_progress:.1f}%",
                          progress_delta, delta_color=sales_delta_color,
                          help="销售额/销售任务的平均完成比例")

    with col2:
        st.markdown("#### 回款数据")
        payment_cols = st.columns(3)
        with payment_cols[0]:
            st.metric("总回款额(万元)", f"{total_payment:,.2f}", help="本月所有员工回款额总和", delta_color="off")
        with payment_cols[1]:
            st.metric("平均回款额(万元)", f"{avg_payment:,.2f}", help="本月员工平均回款额", delta_color="off")

        if avg_payment_progress is not None:
            with payment_cols[2]:
                st.metric("平均回款任务完成率", f"{avg_payment_progress:.1f}%",
                          payment_progress_delta, delta_color=payment_delta_color,
                          help="回款额/回款任务的平均完成比例")

    # 进度分布统计（如果有销售业绩进度数据）
    if '销售业绩完成进度' in sales_df.columns or '回款业绩完成进度' in sales_df.columns:
        st.markdown("#### 业绩完成进度分布")
        progress_cols = st.columns(2)

        # 销售业绩完成进度分布
        if '销售业绩完成进度' in sales_df.columns:
            with progress_cols[0]:
                # 分类
                sales_df['销售完成率分类'] = pd.cut(
                    sales_df['销售业绩完成进度'],
                    bins=[0, 0.66, 1.0, float('inf')],
                    labels=['低于66%', '66%-100%', '超过100%']
                )

                # 计算分类统计
                sales_progress_counts = sales_df['销售完成率分类'].value_counts().reset_index()
                sales_progress_counts.columns = ['完成率区间', '人数']

                # 饼图
                fig = px.pie(
                    sales_progress_counts,
                    values='人数',
                    names='完成率区间',
                    title='销售业绩完成率分布',
                    color_discrete_sequence=['#FF453A', '#FFD60A', '#30D158'],
                    category_orders={"完成率区间": ['低于66%', '66%-100%', '超过100%']}
                )
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

        # 回款业绩完成进度分布
        if '回款业绩完成进度' in sales_df.columns:
            with progress_cols[1]:
                # 分类
                sales_df['回款完成率分类'] = pd.cut(
                    sales_df['回款业绩完成进度'],
                    bins=[0, 0.66, 1.0, float('inf')],
                    labels=['低于66%', '66%-100%', '超过100%']
                )

                # 计算分类统计
                payment_progress_counts = sales_df['回款完成率分类'].value_counts().reset_index()
                payment_progress_counts.columns = ['完成率区间', '人数']

                # 饼图
                fig = px.pie(
                    payment_progress_counts,
                    values='人数',
                    names='完成率区间',
                    title='回款业绩完成率分布',
                    color_discrete_sequence=['#FF453A', '#FFD60A', '#30D158'],
                    category_orders={"完成率区间": ['低于66%', '66%-100%', '超过100%']}
                )
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

    # 团队销售与回款对比
    if '队名' in sales_df.columns:
        st.markdown("#### 团队业绩对比")
        team_sales = sales_df.groupby('队名').agg({
            '本月销售额': 'sum',
            '本月回款合计': 'sum',
            '员工姓名': 'count'
        }).rename(columns={'员工姓名': '团队人数'}).reset_index()

        team_sales['本月销售额(万元)'] = team_sales['本月销售额'] / 10000
        team_sales['本月回款合计(万元)'] = team_sales['本月回款合计'] / 10000

        # 如果有任务数据，计算团队整体完成率
        if '本月销售任务' in sales_df.columns and '本月回款任务' in sales_df.columns:
            team_tasks = sales_df.groupby('队名').agg({
                '本月销售任务': 'sum',
                '本月回款任务': 'sum'
            }).reset_index()

            team_sales = pd.merge(team_sales, team_tasks, on='队名', how='left')
            team_sales['销售任务完成率'] = team_sales['本月销售额'] / team_sales['本月销售任务']
            team_sales['回款任务完成率'] = team_sales['本月回款合计'] / team_sales['本月回款任务']

            # 只显示销售与回款对比图表
            fig = px.bar(team_sales, x='队名', y=['本月销售额(万元)', '本月回款合计(万元)'],
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
            # 原来的图表
            fig = px.bar(team_sales, x='队名', y=['本月销售额(万元)', '本月回款合计(万元)'],
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

    week_sales_cols = [f'第{i}周销售额' for i in range(1, 6) if f'第{i}周销售额' in sales_df.columns]
    week_payment_cols = [f'第{i}周回款合计' for i in range(1, 6) if f'第{i}周回款合计' in sales_df.columns]

    if week_sales_cols and week_payment_cols:
        weekly_totals = {}
        for i in range(1, 6):
            sales_col = f'第{i}周销售额'
            payment_col = f'第{i}周回款合计'
            if sales_col in sales_df.columns and payment_col in sales_df.columns:
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
    else:
        st.info("当前数据中没有周数据信息")


# 辅助函数：根据完成进度获取颜色
def get_progress_color(progress):
    if progress >= 1.0:
        return '#30D158'  # 绿色
    elif progress >= 0.66:
        return '#FFD60A'  # 黄色
    else:
        return '#FF453A'  # 红色


# 显示销售回款超期账款排名页面
def show_ranking_page():
    if st.session_state.ranking_df is None:
        st.error("员工排名数据未加载。请上传有效文件。")
        st.session_state.current_page = 'home'
        return

    st.markdown('<h1 class="section-title fade-in">📈 员工排名数据</h1>', unsafe_allow_html=True)

    ranking_df = st.session_state.ranking_df

    # 查找唯一的排名类型
    if '排名类型' in ranking_df.columns:
        ranking_types = ranking_df['排名类型'].unique()

        # 对排名类型进行分类
        weekly_types = [t for t in ranking_types if str(t).find('周') >= 0]
        monthly_types = [t for t in ranking_types if str(t).find('月') >= 0]
        overdue_types = [t for t in ranking_types if str(t) == '逾期清收失职警示榜']

        # 分类显示各类排名数据
        if weekly_types:
            st.markdown('<h2 class="section-title fade-in">🗓️ 每周排名数据</h2>', unsafe_allow_html=True)

            # 使用Streamlit原生的选项卡功能
            weekly_tab_labels = [f"{'📊' if '销售' in str(t) else '💸'} {str(t)}" for t in weekly_types]
            weekly_tabs = st.tabs(weekly_tab_labels)

            for i, tab_type in enumerate(weekly_types):
                with weekly_tabs[i]:
                    display_rank_data(None, tab_type, ranking_df)

        if monthly_types:
            st.markdown('<h2 class="section-title fade-in">📅 每月排名数据</h2>', unsafe_allow_html=True)

            # 使用Streamlit原生的选项卡功能
            monthly_tab_labels = [f"{'📊' if '销售' in str(t) else '💸'} {str(t)}" for t in monthly_types]
            monthly_tabs = st.tabs(monthly_tab_labels)

            for i, tab_type in enumerate(monthly_types):
                with monthly_tabs[i]:
                    display_rank_data(None, tab_type, ranking_df)

        # 添加各周员工销售和回款数据分析
        if st.session_state.sales_df is not None:
            display_weekly_employee_data(st.session_state.sales_df)

        if overdue_types:
            st.markdown('<h2 class="section-title fade-in">⚠️ 逾期账款警示榜</h2>', unsafe_allow_html=True)
            for rank_type in overdue_types:
                display_rank_data(None, rank_type, ranking_df)

        # 在页面底部显示完整排名数据
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title fade-in">📊 完整排名数据</h2>', unsafe_allow_html=True)
        st.dataframe(ranking_df, use_container_width=True)
    else:
        st.error("排名数据格式错误，缺少'排名类型'列")


# 辅助函数：显示排名数据
def display_rank_data(tab, rank_type, ranking_df):
    # 如果tab不为None，则使用tab上下文，否则直接显示内容
    display_context = tab if tab is not None else nullcontext()

    with display_context:
        # 转换为字符串，确保安全处理
        rank_type_str = str(rank_type)

        # 获取当前类型的数据
        type_data = ranking_df[ranking_df['排名类型'] == rank_type].copy()

        # 特殊处理逾期清收失职警示榜
        if rank_type_str == '逾期清收失职警示榜':
            st.markdown(f"""
            <div class="glass-card fade-in" style="animation-delay: 0.1s; background-color: rgba(255, 69, 58, 0.05);">
                <h3 style="color: #FF453A; text-align:center; margin-bottom: 20px;">⚠️ 逾期清收失职警示榜</h3>
                <p style="text-align:center; color: #86868B;">显示未能及时清收的逾期账款情况</p>
            </div>
            """, unsafe_allow_html=True)

            # 逾期清收数据的自定义显示
            if not type_data.empty:
                # 创建一个更美观的表格显示
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.markdown("#### 逾期清收排名")
                    for _, row in type_data.iterrows():
                        st.markdown(f"""
                        <div class="glass-card" style="margin-bottom:15px; padding:15px; background-color: rgba(255, 69, 58, 0.05);">
                            <div style="display:grid; grid-template-columns: auto 1fr; grid-gap: 15px; align-items:center;">
                                <div style="font-size:1.8rem; font-weight:700; color:#FF453A; text-align:center; 
                                    background-color:rgba(255,255,255,0.7); border-radius:50%; width:44px; height:44px; 
                                    display:flex; align-items:center; justify-content:center;">
                                    {row['排名']}
                                </div>
                                <div>
                                    <div style="font-weight:600; font-size:1.2rem; margin-bottom:8px;">{row['姓名']}</div>
                                    <div style="display:flex; align-items:center;">
                                        <span style="font-size:0.9rem; color:#86868B; margin-right:6px;">逾期账款:</span>
                                        <span style="color:#FF453A; font-weight:500; font-size:1.1rem;">{row['金额(万元)']:.2f} 万元</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                with col2:
                    # 创建条形图
                    fig = px.bar(
                        type_data,
                        x='金额(万元)',
                        y='姓名',
                        orientation='h',
                        text='金额(万元)',
                        color='金额(万元)',
                        color_continuous_scale=['#FF9F0A', '#FF453A'],
                        title='逾期账款金额（万元）'
                    )
                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    fig.update_layout(
                        height=400,
                        yaxis={'categoryorder': 'total ascending'},
                        yaxis_title=None,
                        xaxis_title="金额（万元）",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无逾期清收数据")

        # 处理其他类型的排名（销售额和回款额）
        else:
            is_sales = '销售额' in rank_type_str if isinstance(rank_type_str, str) else False

            if is_sales:
                color = '#0A84FF'
                icon = '💰'
            else:
                color = '#BF5AF2'
                icon = '💸'

            # 使用带有白色背景和动画效果的卡片
            st.markdown(f"""
            <div class="glass-card fade-in" style="animation-delay: 0.1s; background-color: white; border-radius: 12px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px; padding: 20px; border-top: 4px solid {color};">
                <h3 style="color: {color}; text-align:center; margin-bottom: 20px;">{icon} {rank_type_str}排名</h3>
            </div>
            """, unsafe_allow_html=True)

            if not type_data.empty:
                # 销售额/回款额排名的显示
                fig = px.bar(
                    type_data,
                    x='金额(万元)',
                    y='姓名',
                    orientation='h',
                    text='金额(万元)',
                    color='排名',
                    color_continuous_scale=['#30D158', '#0A84FF'] if is_sales else ['#30D158', '#BF5AF2'],
                    title=f'{rank_type_str}排名（万元）'
                )
                fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                fig.update_layout(
                    height=500,
                    yaxis={'categoryorder': 'total ascending'},
                    yaxis_title=None,
                    xaxis_title="金额（万元）",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)

                # 显示排名表格
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"#### {rank_type_str}前三名")
                    top_three = type_data.head(min(3, len(type_data)))
                    for i, (_, row) in enumerate(top_three.iterrows()):
                        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                        animation_delay = i * 0.2
                        st.markdown(f"""
                        <div class="glass-card fade-in" style="animation-delay: {animation_delay}s; margin-bottom:15px; padding:15px; 
                            background-color: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
                            transform: translateY(0); transition: transform 0.3s ease, box-shadow 0.3s ease;"
                            onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)';"
                            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.05)';">
                            <div style="display:flex; align-items:center;">
                                <div style="font-size:2rem; margin-right:15px;">{medal}</div>
                                <div style="flex-grow:1;">
                                    <div style="font-weight:600; font-size:1.2rem;">{row['姓名']}</div>
                                    <div style="color:{color}; font-weight:500;">{row['金额(万元)']:.0f} 万元</div>
                                </div>
                                <div style="font-size:1.5rem; font-weight:700; color:#8E8E93;">#{row['排名']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info(f"暂无{rank_type_str}数据")


# 销售回款相关的员工详情
def display_sales_employee_details(score_df, sales_df=None):
    if score_df is None or score_df.shape[0] == 0:
        return
    st.markdown('<h3 class="section-title fade-in">💰 员工销售回款详情</h3>', unsafe_allow_html=True)
    if '员工姓名' not in score_df.columns or len(score_df['员工姓名']) == 0:
        st.info("没有员工数据")
        return

    df = score_df.copy()
    if sales_df is not None and not sales_df.empty:
        sales_cols = ['员工姓名', '本月销售额', '本月回款合计', '本月回未超期款', '本月回超期款',
                      '月末逾期未收回额', '本月销售任务', '销售业绩完成进度',
                      '本月回款任务', '回款业绩完成进度']
        week_cols = [col for col in sales_df.columns if '周销售额' in col or '周回款合计' in col]
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

    selected_employee = st.selectbox("选择员工查看销售回款数据", df['员工姓名'].unique())
    if selected_employee:
        emp_row = df[df['员工姓名'] == selected_employee]
        if len(emp_row) == 0:
            st.warning("未找到该员工数据")
            return
        emp_data = emp_row.iloc[0]

        # 更新要显示的分类
        sales_categories = []
        sales_values = []

        # 基本销售和回款数据
        if '本月销售额' in emp_data:
            sales_categories.append('本月销售额(万元)')
            sales_values.append(emp_data['本月销售额'] / 10000)

        if '本月回未超期款' in emp_data:
            sales_categories.append('本月回未超期款(万元)')
            sales_values.append(emp_data['本月回未超期款'] / 10000)

        if '本月回超期款' in emp_data:
            sales_categories.append('本月回超期款(万元)')
            sales_values.append(emp_data['本月回超期款'] / 10000)

        if '本月回款合计' in emp_data:
            sales_categories.append('本月回款合计(万元)')
            sales_values.append(emp_data['本月回款合计'] / 10000)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"""
            <div class="glass-card fade-in" style="animation-delay: 0.1s;">
                <div class="employee-header">
                    <div style="font-size:1.8rem; font-weight:700; color:#1D1D1F; font-family: 'SF Pro Display';">{escape(str(selected_employee))}</div>
                    <div class="employee-group" style="color:#0A84FF; font-family: 'SF Pro Text';">队名: {emp_data.get('队名', '未知')}</div>
                </div>
                <div class="employee-stats">
                    <div class="stat-card">
                        <div class="stat-label">本月销售总额</div>
                        <div class="stat-value">{emp_data.get('本月销售额', 0):,.0f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">本月回款合计</div>
                        <div class="stat-value">{emp_data.get('本月回款合计', 0):,.0f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # 添加任务完成进度显示
            has_task_data = ('本月销售任务' in emp_data and '本月回款任务' in emp_data)

            if has_task_data:
                sales_task = emp_data.get('本月销售任务', 0)
                payment_task = emp_data.get('本月回款任务', 0)
                sales_progress = emp_data.get('销售业绩完成进度', 0) * 100
                payment_progress = emp_data.get('回款业绩完成进度', 0) * 100

                st.markdown("""
                <div style="margin-top:20px; padding-top:20px; border-top:0.5px solid rgba(0, 0, 0, 0.05);">
                    <div style="font-weight:600; margin-bottom:15px; color:#86868B; font-family: 'SF Pro Text';">任务完成情况:</div>
                </div>
                """, unsafe_allow_html=True)

                # 销售任务
                st.markdown(f"""
                <div style="margin-bottom:20px;">
                    <div style="display:flex; justify-content:space-between; font-size:1.05rem; font-family: 'SF Pro Text';">
                        <div>销售任务:</div>
                        <div style="font-weight:500;">¥ {sales_task:,.0f}</div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:1.05rem; font-family: 'SF Pro Text'; margin-bottom:5px;">
                        <div>完成进度:</div>
                        <div style="font-weight:500; color:{get_progress_color(sales_progress / 100)};">{sales_progress:.1f}%</div>
                    </div>
                    <div style="width:100%; height:8px; background:#E5E5EA; border-radius:4px; overflow:hidden;">
                        <div style="width:{min(sales_progress, 100)}%; height:100%; background:{get_progress_color(sales_progress / 100)};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 回款任务
                st.markdown(f"""
                <div style="margin-bottom:20px;">
                    <div style="display:flex; justify-content:space-between; font-size:1.05rem; font-family: 'SF Pro Text';">
                        <div>回款任务:</div>
                        <div style="font-weight:500;">¥ {payment_task:,.0f}</div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:1.05rem; font-family: 'SF Pro Text'; margin-bottom:5px;">
                        <div>完成进度:</div>
                        <div style="font-weight:500; color:{get_progress_color(payment_progress / 100)};">{payment_progress:.1f}%</div>
                    </div>
                    <div style="width:100%; height:8px; background:#E5E5EA; border-radius:4px; overflow:hidden;">
                        <div style="width:{min(payment_progress, 100)}%; height:100%; background:{get_progress_color(payment_progress / 100)};"></div>
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
                    ('本月回款合计', emp_data.get('本月回款合计', 0)),
                    ('本月回未超期款', emp_data.get('本月回未超期款', 0)),
                    ('本月回超期款', emp_data.get('本月回超期款', 0)),
                    ('月末逾期未收回额', emp_data.get('月末逾期未收回额', 0))
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
                if sales_df is not None:
                    for i in range(1, 6):
                        week_sales_col = f'第{i}周销售额'
                        week_payment_col = f'第{i}周回款合计'

                        week_sales = emp_data.get(week_sales_col, 0)
                        week_payment = emp_data.get(week_payment_col, 0)

                        if (pd.notna(week_sales) and week_sales != 0) or (pd.notna(week_payment) and week_payment != 0):
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
            # 根据有无进度数据选择不同的图表
            if '销售业绩完成进度' in emp_data and '回款业绩完成进度' in emp_data:
                # 创建仪表盘样式图表
                gauge_data = [
                    {'category': '销售任务完成率', 'value': emp_data['销售业绩完成进度']},
                    {'category': '回款任务完成率', 'value': emp_data['回款业绩完成进度']}
                ]

                fig = go.Figure()

                # 销售任务仪表盘
                sales_color = get_progress_color(emp_data['销售业绩完成进度'])
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=emp_data['销售业绩完成进度'] * 100,
                    domain={'x': [0, 1], 'y': [0.6, 1]},
                    title={'text': "销售任务完成率", 'font': {'size': 20}},
                    gauge={
                        'axis': {'range': [0, 150], 'tickwidth': 1},
                        'bar': {'color': sales_color},
                        'bgcolor': "white",
                        'steps': [
                            {'range': [0, 66], 'color': "rgba(255, 69, 58, 0.15)"},
                            {'range': [66, 100], 'color': "rgba(255, 214, 10, 0.15)"},
                            {'range': [100, 150], 'color': "rgba(48, 209, 88, 0.15)"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    },
                    number={'suffix': "%"}
                ))

                # 回款任务仪表盘
                payment_color = get_progress_color(emp_data['回款业绩完成进度'])
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=emp_data['回款业绩完成进度'] * 100,
                    domain={'x': [0, 1], 'y': [0.1, 0.5]},
                    title={'text': "回款任务完成率", 'font': {'size': 20}},
                    gauge={
                        'axis': {'range': [0, 150], 'tickwidth': 1},
                        'bar': {'color': payment_color},
                        'bgcolor': "white",
                        'steps': [
                            {'range': [0, 66], 'color': "rgba(255, 69, 58, 0.15)"},
                            {'range': [66, 100], 'color': "rgba(255, 214, 10, 0.15)"},
                            {'range': [100, 150], 'color': "rgba(48, 209, 88, 0.15)"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    },
                    number={'suffix': "%"}
                ))

                fig.update_layout(
                    title=f"{selected_employee}的任务完成情况",
                    title_font=dict(size=24, color='#1D1D1F'),
                    height=600,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1D1D1F')
                )

                st.plotly_chart(fig, use_container_width=True)

                # 添加销售和回款数据对比图表
                sales_data = {
                    'category': ['销售额', '销售任务'],
                    'value': [emp_data.get('本月销售额', 0) / 10000, emp_data.get('本月销售任务', 0) / 10000]
                }

                payment_data = {
                    'category': ['回款额', '回款任务'],
                    'value': [emp_data.get('本月回款合计', 0) / 10000, emp_data.get('本月回款任务', 0) / 10000]
                }

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=sales_data['category'],
                    y=sales_data['value'],
                    name='销售情况',
                    marker_color='#0A84FF',
                    text=[f"{val:.1f}万" for val in sales_data['value']],
                    textposition='auto',
                ))

                fig.add_trace(go.Bar(
                    x=payment_data['category'],
                    y=payment_data['value'],
                    name='回款情况',
                    marker_color='#BF5AF2',
                    text=[f"{val:.1f}万" for val in payment_data['value']],
                    textposition='auto',
                ))

                fig.update_layout(
                    title=f"{selected_employee}的销售与回款对比(万元)",
                    title_font=dict(size=20, color='#1D1D1F'),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1D1D1F')
                )

                st.plotly_chart(fig, use_container_width=True)

            else:
                # 创建积分构成雷达图
                fig = go.Figure()

                categories = ['销售额目标分', '回款额目标分', '超期账款追回分',
                              '销售排名分', '回款排名分', '销售进步分',
                              '回款进步分', '基础分', '小组加分']
                values = [emp_data.get(cat, 0) for cat in categories]

                # 确保values和categories不为空
                if values and categories:
                    # 添加雷达图
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        name='积分构成',
                        line=dict(color='#BF5AF2', width=3),
                        fillcolor='rgba(191, 90, 242, 0.1)'
                    ))

                    # 设置图表布局
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[-10, max(values) * 1.2 if values else 1],
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
                        title=f"{selected_employee}的积分构成雷达图",
                        title_font=dict(size=24, color='#1D1D1F'),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#1D1D1F')
                    )
                    st.plotly_chart(fig, use_container_width=True)


# 新增函数：显示各周员工销售和回款数据
def display_weekly_employee_data(sales_df):
    if sales_df is None or sales_df.empty:
        return

    st.markdown('<h2 class="section-title fade-in">📊 各周员工数据分析</h2>', unsafe_allow_html=True)

    # 获取周销售额和周回款额的列名
    week_sales_cols = [f'第{i}周销售额' for i in range(1, 6) if f'第{i}周销售额' in sales_df.columns]
    week_payment_cols = [f'第{i}周回款合计' for i in range(1, 6) if f'第{i}周回款合计' in sales_df.columns]

    if not week_sales_cols or not week_payment_cols:
        st.info("当前数据中没有周数据信息")
        return

    tabs = st.tabs(["各周销售数据", "各周回款数据"])

    # 各周销售数据选项卡
    with tabs[0]:
        st.markdown("""
        <div class="glass-card fade-in" style="animation-delay: 0.1s; background-color: rgba(10, 132, 255, 0.05);">
            <h3 style="color: #0A84FF; text-align:center; margin-bottom: 20px;">📈 各周销售数据</h3>
            <p style="text-align:center; color: #86868B;">显示所有员工在不同周的销售额数据</p>
        </div>
        """, unsafe_allow_html=True)

        # 准备数据
        weeks = [col.replace('销售额', '') for col in week_sales_cols]
        employee_sales_data = []

        for _, row in sales_df.iterrows():
            employee_name = row['员工姓名']
            for week_col in week_sales_cols:
                week = week_col.replace('销售额', '')
                sales_value = row[week_col] / 10000  # 转换为万元
                if sales_value > 0:  # 只显示有销售额的数据
                    employee_sales_data.append({
                        '员工姓名': employee_name,
                        '周次': week,
                        '销售额(万元)': sales_value
                    })

        if employee_sales_data:
            # 创建DataFrame
            employee_sales_df = pd.DataFrame(employee_sales_data)

            # 绘制折线图
            fig = px.line(
                employee_sales_df,
                x='周次',
                y='销售额(万元)',
                color='员工姓名',
                markers=True,
                title='各员工每周销售额趋势',
                color_discrete_sequence=px.colors.qualitative.Bold
            )

            fig.update_layout(
                xaxis_title='周次',
                yaxis_title='销售额(万元)',
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1D1D1F'),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            fig.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
            fig.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("没有找到销售额数据")

    # 各周回款数据选项卡
    with tabs[1]:
        st.markdown("""
        <div class="glass-card fade-in" style="animation-delay: 0.1s; background-color: rgba(191, 90, 242, 0.05);">
            <h3 style="color: #BF5AF2; text-align:center; margin-bottom: 20px;">💸 各周回款数据</h3>
            <p style="text-align:center; color: #86868B;">显示所有员工在不同周的回款额数据</p>
        </div>
        """, unsafe_allow_html=True)

        # 准备数据
        employee_payment_data = []

        for _, row in sales_df.iterrows():
            employee_name = row['员工姓名']
            for week_col in week_payment_cols:
                week = week_col.replace('回款合计', '')
                payment_value = row[week_col] / 10000  # 转换为万元
                if payment_value > 0:  # 只显示有回款额的数据
                    employee_payment_data.append({
                        '员工姓名': employee_name,
                        '周次': week,
                        '回款额(万元)': payment_value
                    })

        if employee_payment_data:
            # 创建DataFrame
            employee_payment_df = pd.DataFrame(employee_payment_data)

            # 绘制折线图
            fig = px.line(
                employee_payment_df,
                x='周次',
                y='回款额(万元)',
                color='员工姓名',
                markers=True,
                title='各员工每周回款额趋势',
                color_discrete_sequence=px.colors.qualitative.Vivid
            )

            fig.update_layout(
                xaxis_title='周次',
                yaxis_title='回款额(万元)',
                height=500,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1D1D1F'),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            fig.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
            fig.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("没有找到回款额数据")


# 历史数据对比页面
def show_history_compare_page():
    st.markdown('<h1 class="section-title fade-in">📊 历史数据对比</h1>', unsafe_allow_html=True)

    # 检查是否有历史数据
    if 'history_files' not in st.session_state:
        st.session_state.history_files = {}  # 用字典存储，键为"年月"，值为处理后的DataFrame

    st.markdown("""
    <div class="glass-card fade-in" style="animation-delay: 0.1s;">
        <h3 style="text-align: center; color: #0A84FF; margin-bottom: 1.5rem; font-size: 1.8rem;">
            📈 月度销售回款数据历史对比
        </h3>
        <p style="text-align: center; color: #86868B; font-size: 1.1rem;">
            上传多个月份的销售回款统计Excel文件，查看历史趋势和对比分析
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 文件上传区域
    st.markdown('<h3 class="section-title fade-in">📁 上传历史数据文件</h3>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "选择历史Excel文件（可多选）",
        type=["xlsx"],
        accept_multiple_files=True,
        help="请上传包含'销售回款数据统计'工作表的Excel文件，可同时选择多个文件",
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # 检查文件是否已经上传过
            file_already_exists = False
            for key, info in st.session_state.history_files.items():
                if info['file_name'] == uploaded_file.name:
                    file_already_exists = True
                    break

            if file_already_exists:
                continue

            # 加载Excel数据
            score_df, sales_df, department_sales_df, ranking_df, error = load_excel_data(uploaded_file)

            if error:
                st.error(f"文件 {uploaded_file.name} 加载失败: {error}")
            else:
                # 尝试从文件名或数据中提取年月信息
                month_info = None

                # 方法1：从文件名提取
                import re
                match = re.search(r'(\d{4})年(\d{1,2})月', uploaded_file.name)
                if match:
                    year = match.group(1)
                    month = match.group(2)
                    month_info = f"{year}年{month}月"

                # 方法2：从数据中提取
                if month_info is None and sales_df is not None and '统计月份' in sales_df.columns:
                    month_values = sales_df['统计月份'].unique()
                    if len(month_values) > 0 and pd.notna(month_values[0]):
                        month_info = str(month_values[0])

                if month_info is None and score_df is not None and '统计月份' in score_df.columns:
                    month_values = score_df['统计月份'].unique()
                    if len(month_values) > 0 and pd.notna(month_values[0]):
                        month_info = str(month_values[0])

                # 如果无法提取，使用文件名作为标识
                if month_info is None:
                    month_info = uploaded_file.name

                # 存储数据
                st.session_state.history_files[month_info] = {
                    'file_name': uploaded_file.name,
                    'sales_df': sales_df,
                    'department_sales_df': department_sales_df
                }

                st.success(f"成功加载 {month_info} 的数据")

    # 显示已加载的历史数据文件
    if st.session_state.history_files:
        st.markdown('<h3 class="section-title fade-in">📋 已加载的历史数据</h3>', unsafe_allow_html=True)

        # 创建一个表格显示已加载的文件
        file_data = []
        for month_key, file_info in st.session_state.history_files.items():
            file_data.append({
                "月份": month_key,
                "文件名": file_info['file_name']
            })

        file_df = pd.DataFrame(file_data)
        st.dataframe(file_df, use_container_width=True)

        # 添加删除特定文件的功能
        st.markdown("### 删除特定历史数据文件")
        selected_file_to_delete = st.selectbox(
            "选择要删除的文件",
            options=[f"{row['月份']} ({row['文件名']})" for _, row in file_df.iterrows()],
            key="file_to_delete"
        )

        if st.button("🗑️ 删除所选文件", key="delete_selected_file"):
            selected_month = selected_file_to_delete.split(" (")[0]
            if selected_month in st.session_state.history_files:
                del st.session_state.history_files[selected_month]
                st.success(f"已删除 {selected_month} 的数据")
                st.rerun()

        # 添加清空按钮
        if st.button("🗑️ 清空所有历史数据", key="clear_history"):
            st.session_state.history_files = {}
            st.success("已清空所有历史数据")
            st.rerun()

        # 如果有2个或以上的历史数据文件，显示对比分析
        if len(st.session_state.history_files) >= 2:
            st.markdown('<h3 class="section-title fade-in">📊 历史数据对比分析</h3>', unsafe_allow_html=True)

            # 创建选项卡
            tabs = st.tabs(["总体趋势", "部门详情", "员工详情"])

            # 总体趋势选项卡
            with tabs[0]:
                st.markdown("### 总体销售回款趋势")

                # 准备数据
                trend_data = []

                # 自定义排序函数，按年月排序
                def extract_year_month(key):
                    # 尝试提取年月
                    year_match = re.search(r'(\d{4})年', key)
                    month_match = re.search(r'年(\d{1,2})月', key)

                    year = year_match.group(1) if year_match else '0000'
                    month = month_match.group(1) if month_match else '00'

                    # 确保月份是两位数
                    if len(month) == 1:
                        month = '0' + month

                    return year + month

                # 按月份排序的键列表
                try:
                    sorted_months = sorted(st.session_state.history_files.keys(),
                                           key=extract_year_month)
                except Exception:
                    # 如果排序失败，使用原始顺序
                    sorted_months = list(st.session_state.history_files.keys())

                for month_key in sorted_months:
                    file_info = st.session_state.history_files[month_key]

                    # 总销售额
                    total_sales = 0
                    if file_info['sales_df'] is not None and '本月销售额' in file_info['sales_df'].columns:
                        total_sales = file_info['sales_df']['本月销售额'].sum() / 10000  # 转换为万元

                    # 总回款额
                    total_payment = 0
                    if file_info['sales_df'] is not None and '本月回款合计' in file_info['sales_df'].columns:
                        total_payment = file_info['sales_df']['本月回款合计'].sum() / 10000  # 转换为万元

                    # 总逾期未收回额
                    total_overdue = 0
                    if file_info['sales_df'] is not None and '月末逾期未收回额' in file_info['sales_df'].columns:
                        total_overdue = file_info['sales_df']['月末逾期未收回额'].sum() / 10000  # 转换为万元

                    trend_data.append({
                        '月份': month_key,
                        '总销售额(万元)': total_sales,
                        '总回款额(万元)': total_payment,
                        '总逾期未收回额(万元)': total_overdue
                    })

                # 创建趋势DataFrame
                trend_df = pd.DataFrame(trend_data)

                # 显示数据表格
                st.markdown("### 月度数据汇总表")
                st.dataframe(trend_df, use_container_width=True)

                # 如果有足够的数据，则显示趋势图
                if len(trend_df) >= 2:
                    # 创建三个图表
                    col1, col2 = st.columns(2)

                    # 总销售额趋势图
                    with col1:
                        fig_sales = px.line(
                            trend_df,
                            x='月份',
                            y='总销售额(万元)',
                            markers=True,
                            title='总销售额月度变化趋势',
                            color_discrete_sequence=['#0A84FF']
                        )

                        fig_sales.update_layout(
                            xaxis_title='月份',
                            yaxis_title='金额(万元)',
                            height=400,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        fig_sales.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                        fig_sales.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                        st.plotly_chart(fig_sales, use_container_width=True)

                    # 总回款额趋势图
                    with col2:
                        fig_payment = px.line(
                            trend_df,
                            x='月份',
                            y='总回款额(万元)',
                            markers=True,
                            title='总回款额月度变化趋势',
                            color_discrete_sequence=['#BF5AF2']
                        )

                        fig_payment.update_layout(
                            xaxis_title='月份',
                            yaxis_title='金额(万元)',
                            height=400,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        fig_payment.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                        fig_payment.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                        st.plotly_chart(fig_payment, use_container_width=True)

                    # 总逾期未收回额趋势图
                    fig_overdue = px.line(
                        trend_df,
                        x='月份',
                        y='总逾期未收回额(万元)',
                        markers=True,
                        title='总逾期未收回额月度变化趋势',
                        color_discrete_sequence=['#FF453A']
                    )

                    fig_overdue.update_layout(
                        xaxis_title='月份',
                        yaxis_title='金额(万元)',
                        height=400,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    fig_overdue.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                    fig_overdue.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                    st.plotly_chart(fig_overdue, use_container_width=True)

                    # 添加堆叠面积图，展示销售额和回款额的关系
                    st.markdown("### 销售额与回款额对比")

                    # 创建堆叠面积图
                    fig_area = go.Figure()

                    # 添加销售额
                    fig_area.add_trace(go.Scatter(
                        x=trend_df['月份'],
                        y=trend_df['总销售额(万元)'],
                        mode='lines',
                        line=dict(width=0.5, color='#0A84FF'),
                        fill='tonexty',
                        name='销售额'
                    ))

                    # 添加回款额
                    fig_area.add_trace(go.Scatter(
                        x=trend_df['月份'],
                        y=trend_df['总回款额(万元)'],
                        mode='lines',
                        line=dict(width=0.5, color='#BF5AF2'),
                        fill='tozeroy',
                        name='回款额'
                    ))

                    # 计算回款率
                    trend_df['回款率'] = trend_df['总回款额(万元)'] / trend_df['总销售额(万元)'] * 100
                    trend_df['回款率'] = trend_df['回款率'].fillna(0).round(2)

                    # 添加回款率（次坐标轴）
                    fig_area.add_trace(go.Scatter(
                        x=trend_df['月份'],
                        y=trend_df['回款率'],
                        mode='lines+markers',
                        line=dict(width=3, color='#FF453A', dash='dot'),
                        marker=dict(size=8, symbol='circle'),
                        name='回款率(%)',
                        yaxis='y2'
                    ))

                    # 更新布局
                    fig_area.update_layout(
                        title='销售额、回款额及回款率月度变化',
                        height=500,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5
                        ),
                        yaxis=dict(
                            title='金额(万元)',
                            gridcolor='rgba(0,0,0,0.05)'
                        ),
                        yaxis2=dict(
                            title=dict(
                                text='回款率(%)',
                                font=dict(color='#FF453A')
                            ),
                            tickfont=dict(color='#FF453A'),
                            anchor="x",
                            overlaying="y",
                            side="right",
                            range=[0, 120]
                        ),
                        hovermode="x unified"
                    )

                    fig_area.update_xaxes(gridcolor='rgba(0,0,0,0.05)')

                    st.plotly_chart(fig_area, use_container_width=True)

                    # 添加数据下载功能
                    csv = trend_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 下载总体趋势数据(CSV)",
                        data=csv,
                        file_name=f"销售回款总体趋势数据_{time.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="download_trend_data"
                    )
                else:
                    st.info("需要至少2个月份的数据才能显示趋势图")

            # 部门详情选项卡
            with tabs[1]:
                st.markdown("### 部门销售回款历史对比")

                # 获取所有部门列表
                all_departments = set()
                for month_key, file_info in st.session_state.history_files.items():
                    if file_info['department_sales_df'] is not None and '部门' in file_info[
                        'department_sales_df'].columns:
                        # 确保所有部门名称都是字符串类型，并排除'合计'
                        departments = [str(d) for d in file_info['department_sales_df']['部门'].unique()
                                       if pd.notna(d) and str(d) != '合计']
                        all_departments.update(departments)

                if all_departments:
                    # 部门选择
                    department_list = list(all_departments)
                    # 使用key函数进行安全排序
                    department_list.sort(key=lambda x: str(x).lower())

                    # 默认选择前3个部门
                    default_depts = department_list[:min(3, len(department_list))]

                    selected_departments = st.multiselect(
                        "选择要对比的部门",
                        options=department_list,
                        default=default_depts
                    )

                    if selected_departments:
                        # 准备部门数据
                        dept_data = []

                        for month_key in sorted_months:
                            file_info = st.session_state.history_files[month_key]

                            if file_info['department_sales_df'] is not None:
                                dept_df = file_info['department_sales_df']

                                for dept in selected_departments:
                                    dept_row = dept_df[dept_df['部门'] == dept]

                                    if not dept_row.empty:
                                        # 销售额
                                        sales_amount = 0
                                        if '本月销售额' in dept_row.columns:
                                            sales_amount = dept_row['本月销售额'].iloc[0] / 10000

                                        # 回款额
                                        payment_amount = 0
                                        payment_col_normal = '本月回未超期款'
                                        payment_col_overdue = '本月回超期款'

                                        if payment_col_normal in dept_row.columns and payment_col_overdue in dept_row.columns:
                                            payment_amount = (dept_row[payment_col_normal].iloc[0] +
                                                              dept_row[payment_col_overdue].iloc[0]) / 10000

                                        # 逾期未收回额
                                        overdue_amount = 0
                                        if '月末逾期未收回额' in dept_row.columns:
                                            overdue_amount = dept_row['月末逾期未收回额'].iloc[0] / 10000

                                        dept_data.append({
                                            '月份': month_key,
                                            '部门': dept,
                                            '销售额(万元)': sales_amount,
                                            '回款额(万元)': payment_amount,
                                            '逾期未收回额(万元)': overdue_amount
                                        })

                        if dept_data:
                            # 创建部门趋势DataFrame
                            dept_trend_df = pd.DataFrame(dept_data)

                            # 创建三个图表
                            # 部门销售额趋势图
                            fig_dept_sales = px.line(
                                dept_trend_df,
                                x='月份',
                                y='销售额(万元)',
                                color='部门',
                                markers=True,
                                title='部门销售额月度变化趋势',
                                color_discrete_sequence=px.colors.qualitative.Bold
                            )

                            fig_dept_sales.update_layout(
                                xaxis_title='月份',
                                yaxis_title='金额(万元)',
                                height=450,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.2,
                                    xanchor="center",
                                    x=0.5
                                )
                            )
                            fig_dept_sales.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                            fig_dept_sales.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                            st.plotly_chart(fig_dept_sales, use_container_width=True)

                            # 部门回款额趋势图
                            fig_dept_payment = px.line(
                                dept_trend_df,
                                x='月份',
                                y='回款额(万元)',
                                color='部门',
                                markers=True,
                                title='部门回款额月度变化趋势',
                                color_discrete_sequence=px.colors.qualitative.Bold
                            )

                            fig_dept_payment.update_layout(
                                xaxis_title='月份',
                                yaxis_title='金额(万元)',
                                height=450,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.2,
                                    xanchor="center",
                                    x=0.5
                                )
                            )
                            fig_dept_payment.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                            fig_dept_payment.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                            st.plotly_chart(fig_dept_payment, use_container_width=True)

                            # 部门逾期未收回额趋势图
                            fig_dept_overdue = px.line(
                                dept_trend_df,
                                x='月份',
                                y='逾期未收回额(万元)',
                                color='部门',
                                markers=True,
                                title='部门逾期未收回额月度变化趋势',
                                color_discrete_sequence=px.colors.qualitative.Bold
                            )

                            fig_dept_overdue.update_layout(
                                xaxis_title='月份',
                                yaxis_title='金额(万元)',
                                height=450,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.2,
                                    xanchor="center",
                                    x=0.5
                                )
                            )
                            fig_dept_overdue.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                            fig_dept_overdue.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                            st.plotly_chart(fig_dept_overdue, use_container_width=True)

                            # 显示数据表格
                            st.markdown("### 部门月度数据汇总表")
                            st.dataframe(dept_trend_df, use_container_width=True)

                            # 添加数据下载功能
                            csv = dept_trend_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 下载部门数据(CSV)",
                                data=csv,
                                file_name=f"部门销售回款历史数据_{time.strftime('%Y%m%d')}.csv",
                                mime="text/csv",
                                key="download_dept_data"
                            )

                            # 添加热力图展示
                            st.markdown("### 部门销售额热力图")
                            # 将数据透视为宽格式，以便创建热力图
                            pivot_sales = dept_trend_df.pivot_table(
                                values='销售额(万元)',
                                index='部门',
                                columns='月份'
                            ).fillna(0)

                            fig_heatmap = px.imshow(
                                pivot_sales,
                                text_auto=True,
                                color_continuous_scale='Blues',
                                labels=dict(x="月份", y="部门", color="销售额(万元)")
                            )

                            fig_heatmap.update_layout(
                                height=350,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)'
                            )

                            st.plotly_chart(fig_heatmap, use_container_width=True)
                        else:
                            st.info("没有找到所选部门的历史数据")
                    else:
                        st.info("请选择至少一个部门进行对比")
                else:
                    st.info("没有找到部门数据，请确保上传的Excel文件包含'部门销售回款统计'工作表")

            # 员工详情选项卡
            with tabs[2]:
                st.markdown("### 员工销售回款历史对比")

                # 获取所有员工列表
                all_employees = set()
                for month_key, file_info in st.session_state.history_files.items():
                    if file_info['sales_df'] is not None and '员工姓名' in file_info['sales_df'].columns:
                        # 确保所有员工名称都是字符串类型
                        employees = [str(emp) for emp in file_info['sales_df']['员工姓名'].unique() if pd.notna(emp)]
                        all_employees.update(employees)

                if all_employees:
                    # 员工选择
                    employee_list = list(all_employees)
                    # 使用key函数进行安全排序
                    employee_list.sort(key=lambda x: str(x).lower())

                    selected_employees = st.multiselect(
                        "选择要对比的员工",
                        options=employee_list,
                        default=[employee_list[0]] if employee_list else []  # 默认选择第一个员工
                    )

                    if selected_employees:
                        # 准备员工数据
                        employee_data = []

                        for month_key in sorted_months:
                            file_info = st.session_state.history_files[month_key]

                            if file_info['sales_df'] is not None:
                                sales_df = file_info['sales_df']

                                for employee in selected_employees:
                                    emp_row = sales_df[sales_df['员工姓名'] == employee]

                                    if not emp_row.empty:
                                        # 销售额
                                        sales_amount = 0
                                        if '本月销售额' in emp_row.columns:
                                            sales_amount = emp_row['本月销售额'].iloc[0] / 10000

                                        # 回款额
                                        payment_amount = 0
                                        if '本月回款合计' in emp_row.columns:
                                            payment_amount = emp_row['本月回款合计'].iloc[0] / 10000

                                        # 逾期未收回额
                                        overdue_amount = 0
                                        if '月末逾期未收回额' in emp_row.columns:
                                            overdue_amount = emp_row['月末逾期未收回额'].iloc[0] / 10000

                                        employee_data.append({
                                            '月份': month_key,
                                            '员工': employee,
                                            '销售额(万元)': sales_amount,
                                            '回款额(万元)': payment_amount,
                                            '逾期未收回额(万元)': overdue_amount
                                        })

                        if employee_data:
                            # 创建员工趋势DataFrame
                            employee_trend_df = pd.DataFrame(employee_data)

                            # 创建三个图表
                            # 员工销售额趋势图
                            fig_emp_sales = px.line(
                                employee_trend_df,
                                x='月份',
                                y='销售额(万元)',
                                color='员工',
                                markers=True,
                                title='员工销售额月度变化趋势',
                                color_discrete_sequence=px.colors.qualitative.Vivid
                            )

                            fig_emp_sales.update_layout(
                                xaxis_title='月份',
                                yaxis_title='金额(万元)',
                                height=450,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.2,
                                    xanchor="center",
                                    x=0.5
                                )
                            )
                            fig_emp_sales.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                            fig_emp_sales.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                            st.plotly_chart(fig_emp_sales, use_container_width=True)

                            # 员工回款额趋势图
                            fig_emp_payment = px.line(
                                employee_trend_df,
                                x='月份',
                                y='回款额(万元)',
                                color='员工',
                                markers=True,
                                title='员工回款额月度变化趋势',
                                color_discrete_sequence=px.colors.qualitative.Vivid
                            )

                            fig_emp_payment.update_layout(
                                xaxis_title='月份',
                                yaxis_title='金额(万元)',
                                height=450,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.2,
                                    xanchor="center",
                                    x=0.5
                                )
                            )
                            fig_emp_payment.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                            fig_emp_payment.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                            st.plotly_chart(fig_emp_payment, use_container_width=True)

                            # 员工逾期未收回额趋势图
                            fig_emp_overdue = px.line(
                                employee_trend_df,
                                x='月份',
                                y='逾期未收回额(万元)',
                                color='员工',
                                markers=True,
                                title='员工逾期未收回额月度变化趋势',
                                color_discrete_sequence=px.colors.qualitative.Vivid
                            )

                            fig_emp_overdue.update_layout(
                                xaxis_title='月份',
                                yaxis_title='金额(万元)',
                                height=450,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=-0.2,
                                    xanchor="center",
                                    x=0.5
                                )
                            )
                            fig_emp_overdue.update_xaxes(gridcolor='rgba(0,0,0,0.05)')
                            fig_emp_overdue.update_yaxes(gridcolor='rgba(0,0,0,0.05)')

                            st.plotly_chart(fig_emp_overdue, use_container_width=True)

                            # 显示数据表格
                            st.markdown("### 员工月度数据汇总表")
                            st.dataframe(employee_trend_df, use_container_width=True)

                            # 添加数据下载功能
                            csv = employee_trend_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 下载员工数据(CSV)",
                                data=csv,
                                file_name=f"员工销售回款历史数据_{time.strftime('%Y%m%d')}.csv",
                                mime="text/csv",
                                key="download_emp_data"
                            )

                            # 添加雷达图比较
                            if len(selected_employees) <= 5:  # 限制雷达图比较的员工数量
                                st.markdown("### 员工销售能力雷达图对比")

                                # 计算每个员工在各个维度的平均值
                                radar_data = employee_trend_df.groupby('员工').agg({
                                    '销售额(万元)': 'mean',
                                    '回款额(万元)': 'mean',
                                    '逾期未收回额(万元)': 'mean'
                                }).reset_index()

                                # 创建雷达图
                                fig_radar = go.Figure()

                                for i, employee in enumerate(radar_data['员工']):
                                    fig_radar.add_trace(go.Scatterpolar(
                                        r=[
                                            radar_data.loc[radar_data['员工'] == employee, '销售额(万元)'].iloc[0],
                                            radar_data.loc[radar_data['员工'] == employee, '回款额(万元)'].iloc[0],
                                            -radar_data.loc[radar_data['员工'] == employee, '逾期未收回额(万元)'].iloc[
                                                0]  # 负值表示逾期越少越好
                                        ],
                                        theta=['销售额', '回款额', '逾期控制'],
                                        fill='toself',
                                        name=employee
                                    ))

                                fig_radar.update_layout(
                                    polar=dict(
                                        radialaxis=dict(
                                            visible=True,
                                            showticklabels=False
                                        )
                                    ),
                                    showlegend=True,
                                    height=450,
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    legend=dict(
                                        orientation="h",
                                        yanchor="bottom",
                                        y=-0.2,
                                        xanchor="center",
                                        x=0.5
                                    )
                                )

                                st.plotly_chart(fig_radar, use_container_width=True)
                                st.caption("注：逾期控制维度中，值越高表示逾期未收回额越低，表现越好")
                        else:
                            st.info("没有找到所选员工的历史数据")
                    else:
                        st.info("请选择至少一个员工进行对比")
                else:
                    st.info("没有找到员工数据，请确保上传的Excel文件包含销售回款数据")
        else:
            st.info("请上传至少2个月份的数据文件，以便进行历史对比分析")
    else:
        st.info("请上传历史数据文件，以便进行历史对比分析")


# 主应用
def main():
    st.set_page_config(
        page_title="销售积分红黑榜系统",
        page_icon="🏆",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    load_css()

    if not st.session_state.data_loaded and st.session_state.file_name is None:
        detected_file = auto_detect_excel_file()
        if detected_file:
            score_df, sales_df, department_sales_df, ranking_df, error = load_excel_data(detected_file)
            if not error:
                st.session_state.score_df = score_df
                st.session_state.sales_df = sales_df
                st.session_state.department_sales_df = department_sales_df
                st.session_state.ranking_df = ranking_df
                st.session_state.data_loaded = True
                st.session_state.file_name = detected_file
            else:
                st.error(f"自动加载文件失败: {error}")

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
    elif st.session_state.current_page == 'department_sales':
        show_department_sales_page()
    elif st.session_state.current_page == 'ranking':
        show_ranking_page()
    elif st.session_state.current_page == 'history_compare':
        show_history_compare_page()

    st.markdown("---")
    st.markdown("""
    <div class="footer">
        销售积分红黑榜系统 | © 2025 销售绩效评估中心 | 版本 3.0
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
