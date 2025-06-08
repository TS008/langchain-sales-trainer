import streamlit as st
from src.core.agent_logic import create_agent, create_rag_agent
from src.rag.rag_system import create_vector_store
from src.chains.evaluation_chain import create_evaluation_chain
from src.utils.report_manager import report_manager
from src.utils.conversation_helper import get_conversation_tips, analyze_conversation_quality, get_next_step_suggestion

def show_simulation_page():
    """显示模拟对话页面"""
    # Sidebar
    with st.sidebar:
        st.title("设置")
        
        st.markdown("---")
        
        # Add option to use simple agent (without RAG) or RAG agent
        use_rag = st.checkbox("使用BERT向量数据库增强", value=False)
        
        if use_rag:
            st.info("首次使用需要下载BERT模型(约90MB)并创建向量索引，请耐心等待。")
            
            if st.button("初始化BERT向量数据库"):
                try:
                    # 创建进度条
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 模拟初始化步骤
                    status_text.text("🔄 正在检查环境...")
                    progress_bar.progress(20)
                    
                    status_text.text("📥 正在下载BERT模型...")
                    progress_bar.progress(40)
                    
                    status_text.text("🔧 正在初始化向量数据库...")
                    progress_bar.progress(60)
                    
                    success = create_vector_store()
                    
                    progress_bar.progress(80)
                    status_text.text("✅ 正在完成初始化...")
                    
                    progress_bar.progress(100)
                    
                    if success:
                        status_text.text("🎉 BERT向量数据库初始化完成！")
                        st.success("BERT向量数据库初始化完成！")
                        st.session_state.vector_store_ready = True
                    else:
                        status_text.text("⚠️ 初始化失败，使用备选方案")
                        st.error("向量数据库初始化失败，将使用关键词匹配作为备选方案。")
                    
                    # 清理进度显示
                    progress_bar.empty()
                    status_text.empty()
                            
                except Exception as e:
                    st.error(f"向量数据库初始化失败: {str(e)}")
                    st.info("建议取消勾选'使用BERT向量数据库增强'，使用基础模式。")

        st.title("场景选择")
        customer_persona = st.selectbox(
            "请选择您想练习的客户类型:",
            ("预算敏感型 (王女士)", "追求独特设计型 (李小姐)", "犹豫不决型 (张阿姨)"),
            key="persona_selector"
        )
        
        if st.button("开始模拟"):
            # 优化状态管理：只清理必要的状态
            keys_to_keep = ['vector_store_ready']
            temp_storage = {k: st.session_state.get(k) for k in keys_to_keep if k in st.session_state}
            
            # 清理对话相关状态
            conversation_keys = ['messages', 'agent', 'persona', 'use_rag', 'report', 'current_report_id', 'chat_container']
            for key in conversation_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            # 恢复保留的状态
            st.session_state.update(temp_storage)
            
            st.session_state.persona = customer_persona
            st.session_state.use_rag = use_rag
            
            try:
                def create_agent_with_monitoring():
                    if use_rag:
                        agent = create_rag_agent(customer_persona, use_deepseek=True)
                        if hasattr(st.session_state, 'vector_store_ready') and st.session_state.vector_store_ready:
                            st.success("使用BERT向量数据库增强模式")
                        else:
                            st.info("使用关键词匹配增强模式（备选方案）")
                        return agent
                    else:
                        agent = create_agent(customer_persona, use_deepseek=True)
                        st.info("使用基础对话模式")
                        return agent
                
                # 创建代理进度指示
                agent_progress = st.progress(0)
                agent_status = st.empty()
                
                agent_status.text("🤖 正在初始化AI代理...")
                agent_progress.progress(30)
                
                st.session_state.agent = create_agent_with_monitoring()
                
                agent_progress.progress(70)
                agent_status.text("💬 正在准备对话环境...")
                
                st.session_state.messages = []
                
                agent_progress.progress(100)
                agent_status.text("✅ 初始化完成！")
                
                # 清理进度显示
                agent_progress.empty()
                agent_status.empty()
                
                # 销售先说欢迎语
                welcome_message = "您好，欢迎光临！随便看看，有喜欢的可以叫我。"
                st.session_state.messages.append({"role": "salesperson", "content": welcome_message})
                
                # 立即生成客户的初始反应
                def get_initial_customer_response():
                    agent = st.session_state.agent
                    
                    if hasattr(st.session_state, 'use_rag') and st.session_state.use_rag:
                        # RAG agent
                        return agent.invoke({"input": welcome_message, "history": ""})
                    else:
                        # Simple conversation agent
                        return agent.predict(input=welcome_message)
                
                try:
                    customer_response = get_initial_customer_response()
                    st.session_state.messages.append({"role": "customer", "content": customer_response})
                except Exception as e:
                    # 如果AI生成失败，给一个默认的客户反应
                    default_responses = {
                        "预算敏感型 (王女士)": "嗯，我随便看看。你们这黄金手镯怎么卖的？多少钱一克？",
                        "追求独特设计型 (李小姐)": "你好，我想看看有什么设计比较特别的款式，不要太大众化的。",
                        "犹豫不决型 (张阿姨)": "你好，我想买个手镯，但是不知道选哪个好，你能帮我推荐一下吗？"
                    }
                    fallback_response = default_responses.get(customer_persona, "你好，我想看看手镯。")
                    st.session_state.messages.append({"role": "customer", "content": fallback_response})
                
                st.rerun()
            except Exception as e:
                st.error(f"创建AI代理失败: {str(e)}")

        if "messages" in st.session_state and st.session_state.messages:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 重新开始", help="清空当前对话，重新开始模拟"):
                    # 清理对话状态
                    conversation_keys = ['messages', 'agent', 'report', 'current_report_id']
                    for key in conversation_keys:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            with col2:
                if st.button("💾 保存对话", help="保存当前对话记录"):
                    try:
                        import json
                        from datetime import datetime
                        
                        conversation_data = {
                            "timestamp": datetime.now().isoformat(),
                            "persona": st.session_state.get('persona', 'Unknown'),
                            "messages": st.session_state.messages
                        }
                        
                        st.download_button(
                            label="📥 下载对话记录",
                            data=json.dumps(conversation_data, ensure_ascii=False, indent=2),
                            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    except Exception as e:
                        st.error(f"保存失败: {e}")
            
            with col3:
                generate_report_btn = st.button("📊 结束模拟 & 生成报告", type="primary")
            
            if generate_report_btn:
                try:
                    # 创建报告生成进度条
                    report_progress = st.progress(0)
                    report_status = st.empty()
                    
                    def generate_report():
                        eval_chain = create_evaluation_chain()
                        history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                        return eval_chain.invoke({"conversation_history": history})
                    
                    # 步骤1：分析对话
                    report_status.text("📊 正在分析对话内容...")
                    report_progress.progress(25)
                    
                    # 步骤2：生成评估
                    report_status.text("🤖 AI正在生成评估报告...")
                    report_progress.progress(50)
                    
                    report = generate_report()
                    st.session_state.report = report
                    
                    # 步骤3：保存报告
                    report_status.text("💾 正在保存报告...")
                    report_progress.progress(75)
                    
                    report_id = report_manager.save_report(
                        report_content=report,
                        persona=st.session_state.persona,
                        conversation_history=st.session_state.messages
                    )
                    st.session_state.current_report_id = report_id
                    
                    # 步骤4：完成
                    report_progress.progress(100)
                    report_status.text("✅ 报告生成完成！")
                    
                    st.success(f"📋 报告已保存，ID: {report_id}")
                    
                    # 清理进度显示
                    report_progress.empty()
                    report_status.empty()
                        
                    st.rerun()
                except Exception as e:
                    st.error(f"生成报告失败: {str(e)}")
                    st.info("请检查您的DeepSeek API配置。")

    # Main area - 重新组织布局
    if "report" in st.session_state:
        # 报告已生成，显示完整报告页面
        st.header("复盘分析仪表盘")
        
        # 显示报告保存信息
        if "current_report_id" in st.session_state:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📊 报告已保存，ID: {st.session_state.current_report_id}")
            with col2:
                report_data = report_manager.load_report(st.session_state.current_report_id)
                if report_data:
                    md_content = report_manager.export_report_to_markdown(report_data)
                    st.download_button(
                        label="📥 导出MD",
                        data=md_content,
                        file_name=f"report_{st.session_state.current_report_id}.md",
                        mime="text/markdown"
                    )
        
        st.markdown(st.session_state.report)
        st.markdown("---")
        
        # 显示对话记录
        st.header("对话记录")
        if "messages" in st.session_state:
            for message in st.session_state.messages:
                role_display = "👤 销售" if message["role"] == "salesperson" else "🤖 客户"
                with st.chat_message("user" if message["role"] == "salesperson" else "assistant"):
                    st.markdown(f"**{role_display}**: {message['content']}")
                    
    elif "messages" in st.session_state:
        # 对话进行中，显示聊天界面
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.header("模拟对话")
        with col2:
            st.metric("对话轮数", len(st.session_state.messages))
        with col3:
            if st.session_state.get('persona'):
                st.info(f"🎭 {st.session_state.persona}")
        
        # 初始化聊天容器（如果不存在）
        if 'chat_container' not in st.session_state:
            st.session_state.chat_container = st.empty()
        
        # 创建固定的聊天消息显示区域
        chat_placeholder = st.empty()
        
        # 显示所有聊天消息
        with chat_placeholder.container():
            for message in st.session_state.messages:
                role_display = "👤 销售" if message["role"] == "salesperson" else "🤖 客户"
                with st.chat_message("user" if message["role"] == "salesperson" else "assistant"):
                    st.markdown(f"**{role_display}**: {message['content']}")
        
        # 实时提示区域
        if len(st.session_state.messages) > 2:
            with st.expander("💡 实时提示", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    tips = get_conversation_tips(st.session_state.messages, st.session_state.get('persona', ''))
                    if tips:
                        st.markdown("**💡 销售提示:**")
                        for tip in tips:
                            st.markdown(f"- {tip}")
                
                with col2:
                    quality = analyze_conversation_quality(st.session_state.messages)
                    st.metric("对话质量", f"{quality['score']}/10")
                    if quality['suggestions']:
                        st.markdown("**🎯 改进建议:**")
                        for suggestion in quality['suggestions']:
                            st.markdown(f"- {suggestion}")
                
                # 下一步建议
                next_step = get_next_step_suggestion(st.session_state.messages, st.session_state.get('persona', ''))
                st.info(f"🎯 **下一步建议**: {next_step}")
        
        # 聊天输入框 - 确保在底部
        if prompt := st.chat_input("请输入您的销售话术（回应上面的客户）..."):
            # 添加销售消息到状态
            st.session_state.messages.append({"role": "salesperson", "content": prompt})
            
            # 立即更新聊天显示
            with chat_placeholder.container():
                for message in st.session_state.messages:
                    role_display = "👤 销售" if message["role"] == "salesperson" else "🤖 客户"
                    with st.chat_message("user" if message["role"] == "salesperson" else "assistant"):
                        st.markdown(f"**{role_display}**: {message['content']}")

            # 显示AI思考状态
            thinking_placeholder = st.empty()
            with thinking_placeholder:
                with st.chat_message("assistant"):
                    st.markdown("🤖 **客户**: 正在思考中...")

            try:
                def get_ai_response():
                    agent = st.session_state.agent
                    
                    # Handle different agent types
                    if hasattr(st.session_state, 'use_rag') and st.session_state.use_rag:
                        # RAG agent
                        history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                        return agent.invoke({"input": prompt, "history": history})
                    else:
                        # Simple conversation agent
                        return agent.predict(input=prompt)
                
                # 获取AI回复
                response = get_ai_response()
                
                # 清除思考状态
                thinking_placeholder.empty()
                
                # 添加客户回复到状态
                st.session_state.messages.append({"role": "customer", "content": response})
                
                # 更新完整的聊天显示
                with chat_placeholder.container():
                    for message in st.session_state.messages:
                        role_display = "👤 销售" if message["role"] == "salesperson" else "🤖 客户"
                        with st.chat_message("user" if message["role"] == "salesperson" else "assistant"):
                            st.markdown(f"**{role_display}**: {message['content']}")
                        
                # 重新运行以更新界面
                st.rerun()
                
            except Exception as e:
                thinking_placeholder.empty()
                st.error(f"AI回复失败: {str(e)}")
                st.info("请检查您的DeepSeek API配置和网络连接。")
                
    else:
        # 初始状态
        st.info("请在左侧选择一位客户并点击'开始模拟'。推荐首次使用时选择基础模式。")
        st.markdown("""
        ### 📝 模拟流程说明
        1. **选择客户类型**：预算敏感型、追求独特设计型、犹豫不决型
        2. **开始模拟**：系统会自动生成销售欢迎语和客户初始反应
        3. **销售应答**：您需要根据客户反应，输入合适的销售话术
        4. **客户回应**：AI客户会根据角色特征做出真实反应
        5. **完成模拟**：点击"结束模拟"即可获得详细的销售技能评估报告
        
        💡 **小贴士**：客户AI已经根据真实销售场景调校，会表现出不同的购买意向、价格敏感度和决策风格。
        """)
        
        # 显示客户角色特征预览
        with st.expander("👥 客户角色特征预览", expanded=False):
            st.markdown("""
            **🤑 预算敏感型 (王女士)**
            - 预算：5000-8000元
            - 特点：价格敏感，看重性价比和保值性
            - 行为：常问价格、重量、折扣，爱比价
            
            **🎨 追求独特设计型 (李小姐)**  
            - 特点：年轻白领，重视设计感和独特性
            - 行为：关注设计理念、是否限量、设计师背景
            
            **🤔 犹豫不决型 (张阿姨)**
            - 特点：选择困难，谨慎犹豫，需要安全感
            - 行为：常说"我再想想"，需要反复确认和建议
            """)

def show_reports_page():
    """显示历史报告页面"""
    st.header("📋 历史报告管理")
    
    # 获取所有报告
    reports = report_manager.get_all_reports()
    
    if not reports:
        st.info("暂无历史报告。完成模拟后会自动保存报告到这里。")
        return
    
    # 批量操作区域
    st.subheader("批量操作")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_reports = st.multiselect(
            "选择报告（可多选）",
            options=[f"{r['id']} - {r['persona']} ({r['date_formatted']})" for r in reports],
            key="selected_reports"
        )
    
    with col2:
        if selected_reports and st.button("📥 导出Excel"):
            try:
                # 提取报告ID
                selected_ids = [s.split(" - ")[0] for s in selected_reports]
                excel_data = report_manager.export_reports_to_excel(selected_ids)
                
                st.download_button(
                    label="下载Excel文件",
                    data=excel_data,
                    file_name=f"reports_export_{len(selected_ids)}_items.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"导出失败: {e}")
    
    with col3:
        if selected_reports and st.button("🗑️ 批量删除"):
            try:
                selected_ids = [s.split(" - ")[0] for s in selected_reports]
                for report_id in selected_ids:
                    report_manager.delete_report(report_id)
                st.success(f"已删除 {len(selected_ids)} 个报告")
                st.rerun()
            except Exception as e:
                st.error(f"删除失败: {e}")
    
    st.markdown("---")
    
    # 报告列表
    st.subheader("报告列表")
    
    for report in reports:
        with st.expander(f"📊 {report['persona']} - {report['date_formatted']} (对话{report['conversation_length']}轮)"):
            
            # 操作按钮
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(f"👁️ 查看", key=f"view_{report['id']}"):
                    st.session_state.viewing_report = report['id']
            
            with col2:
                report_data = report_manager.load_report(report['id'])
                if report_data:
                    md_content = report_manager.export_report_to_markdown(report_data)
                    st.download_button(
                        label="📄 导出MD",
                        data=md_content,
                        file_name=f"report_{report['id']}.md",
                        mime="text/markdown",
                        key=f"download_md_{report['id']}"
                    )
            
            with col3:
                if report_data:
                    excel_data = report_manager.export_reports_to_excel([report['id']])
                    st.download_button(
                        label="📊 导出Excel",
                        data=excel_data,
                        file_name=f"report_{report['id']}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_excel_{report['id']}"
                    )
            
            with col4:
                if st.button(f"🗑️ 删除", key=f"delete_{report['id']}"):
                    if report_manager.delete_report(report['id']):
                        st.success("报告已删除")
                        st.rerun()
                    else:
                        st.error("删除失败")
            
            # 显示报告详情（如果被选中查看）
            if st.session_state.get('viewing_report') == report['id']:
                report_data = report_manager.load_report(report['id'])
                if report_data:
                    st.markdown("### 评估报告")
                    st.markdown(report_data['report_content'])
                    
                    st.markdown("### 对话记录")
                    for i, message in enumerate(report_data['conversation_history'], 1):
                        role = "👤 销售" if message['role'] == 'salesperson' else "🤖 客户"
                        st.markdown(f"**{i}. {role}**: {message['content']}")

def main():
    st.set_page_config(page_title="金牌陪练 - AI 销售模拟系统", layout="wide")

    st.title("金牌陪练 - AI 销售模拟与陪练系统")
    
    # 页面导航
    tab1, tab2 = st.tabs(["🎯 模拟训练", "📋 历史报告"])
    
    with tab1:
        show_simulation_page()
    
    with tab2:
        show_reports_page()

if __name__ == "__main__":
    main() 